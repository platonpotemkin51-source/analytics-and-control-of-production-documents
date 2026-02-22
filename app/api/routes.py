from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_roles
from app.auth.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.entities import Client, Company, Shipment, ShipmentBatch, User, WarehouseBatch
from app.models.enums import BatchStatus, RoleEnum
from app.schemas.common import (
    BatchCreate,
    BatchOut,
    ClientCreate,
    ClientOut,
    CompanyCreate,
    CompanyOut,
    ShipmentCreate,
    ShipmentOut,
    Token,
    UserCreate,
    UserOut,
)
from app.services.excel_service import generate_documents

router = APIRouter(prefix="/api")


@router.post("/auth/bootstrap", response_model=UserOut)
def bootstrap_global_admin(payload: UserCreate, db: Session = Depends(get_db)):
    exists = db.scalar(select(func.count(User.id)))
    if exists:
        raise HTTPException(400, "System already initialized")
    if payload.role != RoleEnum.global_admin:
        raise HTTPException(400, "First user must be global_admin")
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        company_id=None,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form_data.username))
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Wrong email/password")
    return Token(access_token=create_access_token(str(user.id)))


@router.post("/companies", response_model=CompanyOut)
def create_company(
    payload: CompanyCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(RoleEnum.global_admin)),
):
    company = Company(name=payload.name)
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.post("/users", response_model=UserOut)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(get_current_user),
):
    if actor.role == RoleEnum.company_admin and payload.company_id != actor.company_id:
        raise HTTPException(403, "company mismatch")
    user = User(
        company_id=payload.company_id,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/clients", response_model=ClientOut)
def create_client(payload: ClientCreate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    if actor.company_id is None:
        raise HTTPException(400, "company user required")
    client = Client(company_id=actor.company_id, name=payload.name)
    db.add(client)
    db.commit()
    db.refresh(client)
    return client


@router.post("/warehouse/batches", response_model=BatchOut)
def create_batch(payload: BatchCreate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    if actor.role not in {RoleEnum.warehouse, RoleEnum.company_admin}:
        raise HTTPException(403, "Forbidden")
    batch = WarehouseBatch(company_id=actor.company_id, **payload.model_dump())
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


@router.get("/warehouse/batches", response_model=list[BatchOut])
def list_warehouse_batches(db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    rows = db.scalars(
        select(WarehouseBatch).where(
            WarehouseBatch.company_id == actor.company_id,
            WarehouseBatch.status != BatchStatus.shipped,
        )
    ).all()
    return rows


@router.post("/shipments/form", response_model=ShipmentOut)
def form_shipment(payload: ShipmentCreate, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    if actor.role not in {RoleEnum.manager, RoleEnum.company_admin}:
        raise HTTPException(403, "Forbidden")
    batches = db.scalars(
        select(WarehouseBatch).where(
            WarehouseBatch.id.in_(payload.batch_ids),
            WarehouseBatch.company_id == actor.company_id,
            WarehouseBatch.status == BatchStatus.warehouse,
        )
    ).all()
    if len(batches) != len(payload.batch_ids):
        raise HTTPException(400, "Some batches unavailable")

    shipment_data = payload.model_dump(exclude={"batch_ids"})
    shipment = Shipment(company_id=actor.company_id, **shipment_data)
    db.add(shipment)
    db.flush()

    for batch in batches:
        batch.status = BatchStatus.formed
        batch.reserved_by_shipment_id = shipment.id
        db.add(ShipmentBatch(shipment_id=shipment.id, batch_id=batch.id))

    db.commit()
    db.refresh(shipment)
    return shipment


@router.post("/shipments/{shipment_id}/ship")
def mark_shipped(shipment_id: int, db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    shipment = db.get(Shipment, shipment_id)
    if not shipment or shipment.company_id != actor.company_id:
        raise HTTPException(404, "Shipment not found")

    batches = db.scalars(select(WarehouseBatch).where(WarehouseBatch.reserved_by_shipment_id == shipment_id)).all()
    for batch in batches:
        batch.status = BatchStatus.shipped
    db.commit()

    docs = generate_documents(
        shipment_id,
        {
            "contract": shipment.contract,
            "container_number": shipment.container_number,
            "total_cost": str(shipment.total_cost),
            "batch_ids": [b.id for b in batches],
        },
    )
    return {"status": "ok", "excel_files": docs}


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db), actor: User = Depends(get_current_user)):
    company_id = actor.company_id
    revenue = db.scalar(select(func.coalesce(func.sum(Shipment.total_cost), Decimal("0"))).where(Shipment.company_id == company_id))
    shipments_count = db.scalar(select(func.count(Shipment.id)).where(Shipment.company_id == company_id))
    shipped_volume = db.scalar(
        select(func.coalesce(func.sum(WarehouseBatch.volume_actual_buyer), Decimal("0"))).where(
            WarehouseBatch.company_id == company_id,
            WarehouseBatch.status == BatchStatus.shipped,
        )
    )
    in_warehouse = db.scalar(
        select(func.count(WarehouseBatch.id)).where(
            WarehouseBatch.company_id == company_id,
            WarehouseBatch.status == BatchStatus.warehouse,
        )
    )

    by_month_raw = db.execute(
        select(func.strftime("%Y-%m", Shipment.shipment_date), func.coalesce(func.sum(Shipment.total_cost), 0))
        .where(Shipment.company_id == company_id)
        .group_by(func.strftime("%Y-%m", Shipment.shipment_date))
    ).all()

    client_rows = db.execute(
        select(Client.name, func.count(Shipment.id))
        .join(Shipment, Shipment.client_id == Client.id)
        .where(Shipment.company_id == company_id)
        .group_by(Client.name)
    ).all()

    contract_rows = db.execute(
        select(Shipment.contract, func.coalesce(func.sum(Shipment.volume_net), 0))
        .where(Shipment.company_id == company_id)
        .group_by(Shipment.contract)
    ).all()

    return {
        "kpi": {
            "revenue": str(revenue),
            "shipments_count": shipments_count,
            "shipped_volume": str(shipped_volume),
            "batches_in_warehouse": in_warehouse,
        },
        "charts": {
            "revenue_by_month": [{"month": m, "revenue": str(v)} for m, v in by_month_raw if m],
            "shipments_by_clients": [{"client": c, "count": cnt} for c, cnt in client_rows],
            "volume_by_contract": [{"contract": c, "volume": str(v)} for c, v in contract_rows],
        },
        "generated_at": datetime.utcnow().isoformat(),
    }

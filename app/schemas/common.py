from datetime import date
from decimal import Decimal

from pydantic import BaseModel, EmailStr

from app.models.enums import BatchStatus, RoleEnum


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    company_id: int | None = None
    email: EmailStr
    password: str
    role: RoleEnum


class UserOut(BaseModel):
    id: int
    company_id: int | None
    email: EmailStr
    role: RoleEnum
    is_active: bool

    class Config:
        from_attributes = True


class CompanyCreate(BaseModel):
    name: str


class CompanyOut(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class ClientCreate(BaseModel):
    name: str


class ClientOut(BaseModel):
    id: int
    company_id: int
    name: str

    class Config:
        from_attributes = True


class BatchCreate(BaseModel):
    batch_number: str
    sort: str
    width_nominal: int
    width_actual_buyer: int
    width_actual_custom: int
    thickness_nominal: int
    thickness_actual_buyer: int
    thickness_actual_custom: int
    length_nominal: int
    length_actual_buyer: int
    length_actual_custom: int
    quantity_pieces: int
    layers_count: int
    columns_count: int
    coefficient: Decimal = Decimal("0.92")
    volume_nominal: Decimal
    volume_actual_buyer: Decimal
    volume_actual_custom: Decimal
    weight_buyer: Decimal
    weight_custom: Decimal


class BatchOut(BatchCreate):
    id: int
    company_id: int
    status: BatchStatus
    reserved_by_shipment_id: int | None

    class Config:
        from_attributes = True


class ShipmentCreate(BaseModel):
    shipment_date: date
    contract: str
    client_id: int
    container_number: str
    places_count: int
    weight_net: Decimal
    weight_gross: Decimal
    volume_net: Decimal
    volume_gross: Decimal
    price: Decimal
    total_cost: Decimal
    truck_number: str
    trailer_number: str
    seal_number: str
    batch_ids: list[int]


class ShipmentOut(BaseModel):
    id: int
    company_id: int
    shipment_date: date
    contract: str
    client_id: int
    total_cost: Decimal
    truck_number: str

    class Config:
        from_attributes = True

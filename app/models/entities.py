from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import BatchStatus, RoleEnum


class Company(Base):
    __tablename__ = "companies"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Client(Base):
    __tablename__ = "clients"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class Shipment(Base):
    __tablename__ = "shipments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    shipment_date: Mapped[date] = mapped_column(Date, nullable=False)
    contract: Mapped[str] = mapped_column(String(128), nullable=False)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), nullable=False)
    container_number: Mapped[str] = mapped_column(String(64), nullable=False)
    places_count: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_net: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    weight_gross: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    volume_net: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    volume_gross: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    truck_number: Mapped[str] = mapped_column(String(64), nullable=False)
    trailer_number: Mapped[str] = mapped_column(String(64), nullable=False)
    seal_number: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class WarehouseBatch(Base):
    __tablename__ = "warehouse_batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    batch_number: Mapped[str] = mapped_column(String(128), nullable=False)
    sort: Mapped[str] = mapped_column(String(64), nullable=False)

    width_nominal: Mapped[int] = mapped_column(Integer, nullable=False)
    width_actual_buyer: Mapped[int] = mapped_column(Integer, nullable=False)
    width_actual_custom: Mapped[int] = mapped_column(Integer, nullable=False)
    thickness_nominal: Mapped[int] = mapped_column(Integer, nullable=False)
    thickness_actual_buyer: Mapped[int] = mapped_column(Integer, nullable=False)
    thickness_actual_custom: Mapped[int] = mapped_column(Integer, nullable=False)
    length_nominal: Mapped[int] = mapped_column(Integer, nullable=False)
    length_actual_buyer: Mapped[int] = mapped_column(Integer, nullable=False)
    length_actual_custom: Mapped[int] = mapped_column(Integer, nullable=False)

    quantity_pieces: Mapped[int] = mapped_column(Integer, nullable=False)
    layers_count: Mapped[int] = mapped_column(Integer, nullable=False)
    columns_count: Mapped[int] = mapped_column(Integer, nullable=False)
    coefficient: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0.92"), nullable=False)

    volume_nominal: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    volume_actual_buyer: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    volume_actual_custom: Mapped[Decimal] = mapped_column(Numeric(12, 3), nullable=False)
    weight_buyer: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    weight_custom: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.warehouse, nullable=False)
    reserved_by_shipment_id: Mapped[int | None] = mapped_column(ForeignKey("shipments.id"), nullable=True)

    __table_args__ = (UniqueConstraint("company_id", "batch_number", name="uq_company_batch_number"),)


class ShipmentBatch(Base):
    __tablename__ = "shipment_batches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    shipment_id: Mapped[int] = mapped_column(ForeignKey("shipments.id"), nullable=False)
    batch_id: Mapped[int] = mapped_column(ForeignKey("warehouse_batches.id"), nullable=False)

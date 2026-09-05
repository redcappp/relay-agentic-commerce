from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Merchant(Base):
    __tablename__ = "merchants"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(String(255))
    accent: Mapped[str] = mapped_column(String(20), default="#5eead4")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"), index=True)
    name: Mapped[str] = mapped_column(String(160))
    category: Mapped[str] = mapped_column(String(80), index=True)
    price: Mapped[float] = mapped_column(Float)
    inventory: Mapped[int] = mapped_column(Integer)
    specs: Mapped[str] = mapped_column(Text, default="")
    rating: Mapped[float] = mapped_column(Float, default=4.2)
    image: Mapped[str] = mapped_column(String(30), default="headphones")

class BuyerRequest(Base):
    __tablename__ = "buyer_requests"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    prompt: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    amount: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="CREATED")
    payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    execution_mode: Mapped[str] = mapped_column(String(30), default="NORMAL")
    selected_by: Mapped[str] = mapped_column(String(30), default="USER")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Feedback(Base):
    __tablename__ = "feedback"
    id: Mapped[int] = mapped_column(primary_key=True)
    merchant_id: Mapped[int] = mapped_column(ForeignKey("merchants.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    event: Mapped[str] = mapped_column(String(30)) # IMPRESSION | SELECTED | PURCHASED
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AgentEvent(Base):
    __tablename__ = "agent_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    agent: Mapped[str] = mapped_column(String(50))
    component: Mapped[str] = mapped_column(String(60))
    event_type: Mapped[str] = mapped_column(String(60))
    status: Mapped[str] = mapped_column(String(30))
    message: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    event_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="RECEIVED")
    payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

class Payment(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True)
    provider: Mapped[str] = mapped_column(String(40))
    provider_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    provider_payment_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(30), default="CREATED")
    verification_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    webhook_status: Mapped[str] = mapped_column(String(30), default="PENDING")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

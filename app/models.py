from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, nullable=False, index=True)

    customer_id = Column(String, nullable=False, index=True)

    customer_name = Column(String, nullable=True)
    customer_email = Column(String, nullable=True)

    shipping_address = Column(Text, nullable=True)
    shipping_city = Column(String, nullable=True)
    shipping_postal_code = Column(String, nullable=True)
    shipping_country = Column(String, nullable=True)

    total_amount = Column(DECIMAL(10, 2), default=0)
    currency = Column(String, default="EUR")

    status = Column(String, default="pending", index=True)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    shipped_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)

    items = relationship(
        "OrderItemModel", back_populates="order", cascade="all, delete-orphan"
    )


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)

    product_id = Column(String, nullable=False, index=True)

    product_name = Column(String, nullable=False)
    product_price = Column(DECIMAL(10, 2), nullable=False)
    product_sku = Column(String, nullable=True)
    product_description = Column(Text, nullable=True)

    quantity = Column(Integer, nullable=False, default=1)
    total_price = Column(DECIMAL(10, 2), nullable=False)

    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    order = relationship("OrderModel", back_populates="items")


class OrderEventModel(Base):
    __tablename__ = "order_events"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    event_data = Column(Text, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True
    )
    created_by = Column(String, nullable=True)

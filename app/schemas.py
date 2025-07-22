from typing import Optional, List, Literal
from pydantic import BaseModel, Field, ConfigDict, field_validator
from decimal import Decimal
from datetime import datetime


class OrderItemBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: str = Field(..., min_length=1)
    product_name: str = Field(..., min_length=1)
    product_price: Decimal = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    product_sku: Optional[str] = None
    product_description: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    pass


class OrderItemUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_name: Optional[str] = None
    product_price: Optional[Decimal] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, gt=0)
    product_sku: Optional[str] = None
    product_description: Optional[str] = None


class OrderItem(OrderItemBase):
    id: Optional[int] = None
    total_price: Optional[Decimal] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OrderBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str = Field(..., min_length=1)
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None
    currency: str = Field(default="EUR", max_length=3)


class OrderCreate(OrderBase):
    items: List[OrderItemCreate] = Field(..., min_length=1)

    @field_validator("items")
    def validate_items(cls, v):
        if not v:
            raise ValueError("La commande doit contenir au moins un article")
        return v


class OrderUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    shipping_address: Optional[str] = None
    shipping_city: Optional[str] = None
    shipping_postal_code: Optional[str] = None
    shipping_country: Optional[str] = None


class OrderStatusUpdate(BaseModel):
    status: Literal[
        "pending", "confirmed", "processing", "shipped", "delivered", "cancelled"
    ]
    notes: Optional[str] = None


class Order(OrderBase):
    id: Optional[int] = None
    order_id: Optional[str] = None
    total_amount: Optional[Decimal] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    items: List[OrderItem] = []


class OrderSummary(BaseModel):
    """Résumé d'une commande pour les listes"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    order_id: str
    customer_id: str
    customer_name: Optional[str] = None
    total_amount: Decimal
    status: str
    items_count: int
    created_at: datetime


class OrderStats(BaseModel):
    """Statistiques des commandes"""

    total_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    orders_by_status: dict
    recent_orders_count: int
    top_customers: List[dict]

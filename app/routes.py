# app/routes.py

import json
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, Depends, Security, APIRouter, Request, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.messaging.events import (
    ORDER_CREATED,
    ORDER_UPDATED,
    ORDER_STATUS_CHANGED,
    ORDER_CANCELLED,
)
from app.models import OrderModel, OrderItemModel, OrderEventModel
from app.schemas import (
    Order,
    OrderCreate,
    OrderUpdate,
    OrderStatusUpdate,
    OrderSummary,
    OrderStats,
)

API_TOKEN = os.getenv("API_TOKEN", "supersecrettoken123")
security = HTTPBearer()
router = APIRouter()

VALID_STATUSES = [
    "pending",
    "confirmed",
    "processing",
    "shipped",
    "delivered",
    "cancelled",
]
NON_CANCELLABLE_STATUSES = ["delivered", "cancelled"]


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API token authentication"""
    if credentials.scheme != "Bearer" or credentials.credentials != API_TOKEN:
        raise HTTPException(status_code=403, detail="Accès interdit")


async def publish_event_safe(request: Request, event_type: str, data: dict):
    """Publier un événement de manière sécurisée"""
    try:
        broker = getattr(request.app.state, "broker", None)
        if broker and broker.is_connected:
            await broker.publish_event(event_type, data)
            print(f"Event published: {event_type}")
        else:
            print(
                f"Warning: Message broker not available, event {event_type} not published"
            )
    except Exception as e:
        print(f"Error publishing event {event_type}: {str(e)}")


def generate_order_id() -> str:
    """Génère un ID unique pour la commande"""
    return f"ORD-{uuid.uuid4().hex[:8].upper()}"


async def create_order_event(
    db: Session, order_id: str, event_type: str, event_data: dict
):
    """Crée un événement d'audit pour la commande"""
    try:
        db_event = OrderEventModel(
            order_id=order_id,
            event_type=event_type,
            event_data=json.dumps(event_data, default=str),
            created_at=datetime.now(timezone.utc),
            created_by="system",
        )
        db.add(db_event)
    except Exception as e:
        print(f"Error creating order event: {e}")


def create_order_summary(order: OrderModel) -> OrderSummary:
    """Créer un résumé de commande à partir d'un modèle OrderModel"""
    return OrderSummary(
        id=order.id,
        order_id=order.order_id,
        customer_id=order.customer_id,
        customer_name=order.customer_name,
        total_amount=order.total_amount,
        status=order.status,
        items_count=len(order.items),
        created_at=order.created_at,
    )


def create_order_summaries_list(orders: List[OrderModel]) -> List[OrderSummary]:
    """Créer une liste de résumés de commandes"""
    return [create_order_summary(order) for order in orders]


def validate_status(status: str) -> str:
    """Valider le statut d'une commande"""
    if status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Statut invalide. Statuts valides: {', '.join(VALID_STATUSES)}",
        )
    return status


def parse_date(date_string: str, field_name: str) -> datetime:
    """Parser une date depuis une chaîne avec gestion d'erreur"""
    try:
        return datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Format de date invalide pour {field_name} (YYYY-MM-DD)",
        )


def get_order_by_id(db: Session, order_id: str) -> OrderModel:
    """Récupérer une commande par son ID avec gestion d'erreur"""
    order = db.query(OrderModel).filter(OrderModel.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Commande non trouvée")
    return order


def build_search_query(
    db: Session,
    q: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
):
    """Construire une requête de recherche avec filtres"""
    query = db.query(OrderModel)

    if q:
        query = query.filter(
            or_(
                OrderModel.order_id.ilike(f"%{q}%"),
                OrderModel.customer_id.ilike(f"%{q}%"),
                OrderModel.customer_name.ilike(f"%{q}%"),
                OrderModel.customer_email.ilike(f"%{q}%"),
            )
        )

    if min_amount is not None:
        query = query.filter(OrderModel.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(OrderModel.total_amount <= max_amount)

    if date_from:
        date_from_obj = parse_date(date_from, "date_from")
        query = query.filter(OrderModel.created_at >= date_from_obj)
    if date_to:
        date_to_obj = parse_date(date_to, "date_to")
        query = query.filter(OrderModel.created_at <= date_to_obj)

    if customer_id:
        query = query.filter(OrderModel.customer_id == customer_id)
    if status:
        query = query.filter(OrderModel.status == status)

    return query


@router.get("/")
def read_root():
    return {"message": "Orders API is running"}


@router.get("/orders/search", response_model=List[OrderSummary])
def search_orders(
    q: Optional[str] = Query(default=None, description="Recherche textuelle"),
    min_amount: Optional[float] = Query(default=None, ge=0),
    max_amount: Optional[float] = Query(default=None, ge=0),
    date_from: Optional[str] = Query(
        default=None, description="Date début (YYYY-MM-DD)"
    ),
    date_to: Optional[str] = Query(default=None, description="Date fin (YYYY-MM-DD)"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000, ge=1),
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Rechercher des commandes avec différents critères"""
    try:
        query = build_search_query(db, q, min_amount, max_amount, date_from, date_to)
        orders = (
            query.order_by(OrderModel.created_at.desc()).offset(skip).limit(limit).all()
        )
        return create_order_summaries_list(orders)
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error searching orders: {str(e)}")
        raise HTTPException(status_code=500, detail="Erreur lors de la recherche")


@router.get("/orders/status/{status}", response_model=List[OrderSummary])
def get_orders_by_status(
    status: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000, ge=1),
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Récupérer toutes les commandes avec un statut donné"""
    validate_status(status)

    orders = (
        db.query(OrderModel)
        .filter(OrderModel.status == status)
        .order_by(OrderModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return create_order_summaries_list(orders)


@router.get("/orders", response_model=List[OrderSummary])
def list_orders(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000, ge=1),
    customer_id: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Lister les commandes avec filtres optionnels"""
    query = build_search_query(db, customer_id=customer_id, status=status)
    orders = (
        query.order_by(OrderModel.created_at.desc()).offset(skip).limit(limit).all()
    )
    return create_order_summaries_list(orders)


@router.get("/orders/{order_id}", response_model=Order)
def get_order(
    order_id: str,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Récupérer une commande par son ID"""
    return get_order_by_id(db, order_id)


@router.post("/orders", response_model=Order)
async def create_order(
    order: OrderCreate,
    request: Request,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Créer une nouvelle commande"""
    try:
        order_id = generate_order_id()
        total_amount = sum(item.product_price * item.quantity for item in order.items)

        db_order = OrderModel(
            order_id=order_id,
            customer_id=order.customer_id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            shipping_address=order.shipping_address,
            shipping_city=order.shipping_city,
            shipping_postal_code=order.shipping_postal_code,
            shipping_country=order.shipping_country,
            currency=order.currency,
            total_amount=total_amount,
            status="pending",
        )

        db.add(db_order)
        db.flush()

        for item_data in order.items:
            item_total = item_data.product_price * item_data.quantity
            db_item = OrderItemModel(
                order_id=db_order.id,
                product_id=item_data.product_id,
                product_name=item_data.product_name,
                product_price=item_data.product_price,
                quantity=item_data.quantity,
                total_price=item_total,
                product_sku=item_data.product_sku,
                product_description=item_data.product_description,
            )
            db.add(db_item)

        await create_order_event(
            db,
            order_id,
            "order_created",
            {
                "customer_id": order.customer_id,
                "total_amount": str(total_amount),
                "items_count": len(order.items),
            },
        )

        db.commit()
        db.refresh(db_order)

        await publish_event_safe(
            request,
            ORDER_CREATED,
            {
                "order_id": order_id,
                "customer_id": order.customer_id,
                "total_amount": str(total_amount),
                "status": "pending",
                "items": [
                    {
                        "product_id": item.product_id,
                        "product_name": item.product_name,
                        "quantity": item.quantity,
                        "price": str(item.product_price),
                    }
                    for item in order.items
                ],
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return db_order

    except Exception as e:
        db.rollback()
        print(f"Error creating order: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la création de la commande"
        )


@router.put("/orders/{order_id}", response_model=Order)
async def update_order(
    order_id: str,
    updated_order: OrderUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Mettre à jour une commande"""
    try:
        order = get_order_by_id(db, order_id)

        old_values = {
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "shipping_address": order.shipping_address,
            "shipping_city": order.shipping_city,
            "shipping_postal_code": order.shipping_postal_code,
            "shipping_country": order.shipping_country,
        }

        changes = updated_order.model_dump(exclude_unset=True)
        for field, value in changes.items():
            setattr(order, field, value)

        order.updated_at = datetime.now(timezone.utc)

        await create_order_event(
            db,
            order_id,
            "order_updated",
            {"old_values": old_values, "changes": changes},
        )

        db.commit()
        db.refresh(order)

        await publish_event_safe(
            request,
            ORDER_UPDATED,
            {
                "order_id": order_id,
                "customer_id": order.customer_id,
                "changes": changes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return order

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating order: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la mise à jour de la commande"
        )


@router.put("/orders/{order_id}/status", response_model=Order)
async def update_order_status(
    order_id: str,
    status_update: OrderStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Mettre à jour le statut d'une commande"""
    try:
        order = get_order_by_id(db, order_id)
        old_status = order.status
        new_status = status_update.status

        if old_status == new_status:
            return order

        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)

        if new_status == "shipped":
            order.shipped_at = datetime.now(timezone.utc)
        elif new_status == "delivered":
            order.delivered_at = datetime.now(timezone.utc)

        await create_order_event(
            db,
            order_id,
            "status_changed",
            {
                "old_status": old_status,
                "new_status": new_status,
                "notes": status_update.notes,
            },
        )

        db.commit()
        db.refresh(order)

        await publish_event_safe(
            request,
            ORDER_STATUS_CHANGED,
            {
                "order_id": order_id,
                "customer_id": order.customer_id,
                "old_status": old_status,
                "new_status": new_status,
                "notes": status_update.notes,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return order

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating order status: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la mise à jour du statut"
        )


@router.post("/orders/{order_id}/cancel", response_model=Order)
async def cancel_order(
    order_id: str,
    request: Request,
    reason: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Annuler une commande"""
    try:
        order = get_order_by_id(db, order_id)

        if order.status in NON_CANCELLABLE_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"Impossible d'annuler une commande avec le statut: {order.status}",
            )

        old_status = order.status
        order.status = "cancelled"
        order.updated_at = datetime.now(timezone.utc)

        await create_order_event(
            db,
            order_id,
            "order_cancelled",
            {"old_status": old_status, "reason": reason},
        )

        db.commit()
        db.refresh(order)

        await publish_event_safe(
            request,
            ORDER_CANCELLED,
            {
                "order_id": order_id,
                "customer_id": order.customer_id,
                "reason": reason,
                "cancelled_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        return order

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error cancelling order: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de l'annulation de la commande"
        )


@router.delete("/orders/{order_id}")
async def delete_order(
    order_id: str,
    request: Request,
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Supprimer une commande"""
    try:
        order = get_order_by_id(db, order_id)
        db.delete(order)
        db.commit()
        return {"message": "Commande supprimée avec succès", "order_id": order_id}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting order: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors de la suppression de la commande"
        )


@router.get("/customers/{customer_id}/orders", response_model=List[OrderSummary])
def get_customer_orders(
    customer_id: str,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, le=1000, ge=1),
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Récupérer les commandes d'un client"""
    orders = (
        db.query(OrderModel)
        .filter(OrderModel.customer_id == customer_id)
        .order_by(OrderModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return create_order_summaries_list(orders)


@router.get("/stats", response_model=OrderStats)
def get_order_statistics(
    db: Session = Depends(get_db),
    _: HTTPAuthorizationCredentials = Security(verify_token),
):
    """Obtenir les statistiques des commandes"""
    try:
        total_orders = db.query(OrderModel).count()
        total_revenue = db.query(func.sum(OrderModel.total_amount)).scalar() or 0
        avg_order_value = db.query(func.avg(OrderModel.total_amount)).scalar() or 0

        status_counts = (
            db.query(OrderModel.status, func.count(OrderModel.id))
            .group_by(OrderModel.status)
            .all()
        )
        orders_by_status = {status: count for status, count in status_counts}

        from datetime import timedelta

        seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_orders = (
            db.query(OrderModel).filter(OrderModel.created_at >= seven_days_ago).count()
        )

        top_customers = (
            db.query(
                OrderModel.customer_id,
                OrderModel.customer_name,
                func.count(OrderModel.id).label("order_count"),
                func.sum(OrderModel.total_amount).label("total_spent"),
            )
            .group_by(OrderModel.customer_id, OrderModel.customer_name)
            .order_by(func.count(OrderModel.id).desc())
            .limit(10)
            .all()
        )

        top_customers_list = [
            {
                "customer_id": customer_id,
                "customer_name": customer_name or "Nom inconnu",
                "order_count": order_count,
                "total_spent": float(total_spent or 0),
            }
            for customer_id, customer_name, order_count, total_spent in top_customers
        ]

        return OrderStats(
            total_orders=total_orders,
            total_revenue=Decimal(str(total_revenue)),
            average_order_value=Decimal(str(avg_order_value)),
            orders_by_status=orders_by_status,
            recent_orders_count=recent_orders,
            top_customers=top_customers_list,
        )

    except Exception as e:
        print(f"Error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Erreur lors du calcul des statistiques"
        )


@router.get("/health/messaging")
async def check_messaging_health(request: Request):
    """Vérifier l'état du système de messagerie"""
    try:
        broker = getattr(request.app.state, "broker", None)
        if broker and broker.is_connected:
            return {
                "status": "healthy",
                "message_broker": "connected",
                "service": broker.service_name,
            }
        else:
            return {
                "status": "warning",
                "message_broker": "disconnected",
                "message": "API fonctionne mais les événements ne sont pas publiés",
            }
    except Exception as e:
        return {"status": "error", "message_broker": "error", "error": str(e)}

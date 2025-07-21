import os
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI
from dotenv import load_dotenv
import aio_pika

from app.db import Base, engine
from app.routes import router as orders_router
from app.messaging.broker import MessageBroker

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://admin:password@rabbitmq:5672/")
SERVICE_NAME = "orders-api"

broker = MessageBroker(RABBITMQ_URL, SERVICE_NAME)


async def handle_external_events(message: aio_pika.IncomingMessage):
    """Handler pour les événements provenant des autres services"""
    async with message.process():
        try:
            event = json.loads(message.body.decode())
            event_type = event.get("event_type")
            data = event.get("data", {})

            print(f"Received event: {event_type} from {event.get('service')}")

            if event_type == "customer.updated":
                customer_id = data.get("customer_id")
                print(f"Customer updated: {customer_id}")
                await update_customer_data_in_orders(customer_id, data)

            elif event_type == "customer.deleted":
                customer_id = data.get("customer_id")
                print(f"Customer deleted: {customer_id}")
                await handle_customer_deletion(customer_id)

            elif event_type == "product.updated":
                product_id = data.get("product_id")
                print(f"Product updated: {product_id}")
                await update_product_data_in_orders(product_id, data)

            elif event_type == "product.deleted":
                product_id = data.get("product_id")
                print(f"Product deleted: {product_id}")
                await handle_product_deletion(product_id)

        except json.JSONDecodeError:
            print("Error: Invalid JSON in message")
        except Exception as e:
            print(f"Error processing event: {str(e)}")


async def update_customer_data_in_orders(customer_id: str, customer_data: dict):
    """Met à jour les données client dénormalisées dans les commandes"""
    from app.db import SessionLocal
    from app.models import OrderModel

    db = SessionLocal()
    try:
        orders = (
            db.query(OrderModel).filter(OrderModel.customer_id == customer_id).all()
        )

        for order in orders:
            if "name" in customer_data:
                order.customer_name = customer_data["name"]
            if "username" in customer_data:
                order.customer_email = customer_data.get("username", "")

        db.commit()
        print(f"Updated customer data in {len(orders)} orders")

    except Exception as e:
        print(f"Error updating customer data in orders: {e}")
        db.rollback()
    finally:
        db.close()


async def handle_customer_deletion(customer_id: str):
    """Gère la suppression d'un client (anonymise les commandes)"""
    from app.db import SessionLocal
    from app.models import OrderModel

    db = SessionLocal()
    try:
        orders = (
            db.query(OrderModel).filter(OrderModel.customer_id == customer_id).all()
        )

        for order in orders:
            order.customer_name = f"Client supprimé ({customer_id})"
            order.customer_email = "client.supprime@anonyme.com"

        db.commit()
        print(f"Anonymized {len(orders)} orders for deleted customer {customer_id}")

    except Exception as e:
        print(f"Error handling customer deletion: {e}")
        db.rollback()
    finally:
        db.close()


async def update_product_data_in_orders(product_id: str, product_data: dict):
    """Met à jour les données produit dans les futurs items de commande"""
    print(f"Product {product_id} updated - historical orders preserved")


async def handle_product_deletion(product_id: str):
    """Gère la suppression d'un produit"""
    print(f"Product {product_id} deleted - historical orders preserved")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Orders API...")

    Base.metadata.create_all(bind=engine)
    print("Database tables created")

    try:
        print(f"🔗 Attempting to connect to RabbitMQ: {RABBITMQ_URL}")

        await broker.connect()
        print("Connected to message broker")

        await broker.subscribe_to_events(
            event_patterns=[
                "customer.created",
                "customer.updated",
                "customer.deleted",
                "product.created",
                "product.updated",
                "product.deleted",
            ],
            callback=handle_external_events,
        )
        print("Subscribed to external events")

    except Exception as e:
        print(f"Failed to connect to message broker: {str(e)}")
        print(f"Debug: RABBITMQ_URL = {RABBITMQ_URL}")

    app.state.broker = broker

    yield

    print("Shutting down Orders API...")
    if broker.connection and not broker.connection.is_closed:
        await broker.connection.close()
        print("Message broker connection closed")


app = FastAPI(
    title="API Gestion des Commandes",
    description="API REST pour la gestion des commandes PayeTonKawa",
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(orders_router)


@app.get("/health")
async def health_check():
    """Endpoint de vérification de santé"""
    broker_status = (
        "connected"
        if broker.connection and not broker.connection.is_closed
        else "disconnected"
    )
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "message_broker": broker_status,
    }

import aio_pika
import json
from typing import Dict, Any, List, Callable
import uuid
from datetime import datetime, timezone
import asyncio


class MessageBroker:
    """Client pour la communication via message broker (RabbitMQ)"""

    def __init__(self, connection_url: str, service_name: str):
        self.connection_url = connection_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.events_exchange = None

    async def connect(self, max_retries: int = 5, retry_delay: float = 2.0):
        """Établit la connexion avec RabbitMQ avec retry logic"""
        for attempt in range(max_retries):
            try:
                print(
                    f"Attempting RabbitMQ connection (attempt {attempt + 1}/{max_retries})"
                )

                self.connection = await aio_pika.connect_robust(
                    self.connection_url,
                    loop=asyncio.get_event_loop(),
                    connection_timeout=10.0,
                    heartbeat=60,
                )
                self.channel = await self.connection.channel()

                await self.channel.set_qos(prefetch_count=10)

                self.events_exchange = await self.channel.declare_exchange(
                    "payetonkawa.events", aio_pika.ExchangeType.TOPIC, durable=True
                )

                print(f"🔗 Message broker connected for service: {self.service_name}")
                return

            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {str(e)}")

                if attempt < max_retries - 1:
                    print(f"⏳ Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    print(
                        f"Failed to connect to message broker after {max_retries} attempts"
                    )
                    raise

    async def publish_event(self, event_type: str, data: Dict[str, Any]):
        """Publie un événement sur le message broker"""
        if not self.events_exchange:
            raise RuntimeError("Message broker not connected")

        message_body = {
            "event_type": event_type,
            "event_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": self.service_name,
            "data": data,
        }

        try:
            message = aio_pika.Message(
                json.dumps(message_body, ensure_ascii=False, default=str).encode(
                    "utf-8"
                ),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
                message_id=message_body["event_id"],
                timestamp=datetime.now(timezone.utc),
            )

            await self.events_exchange.publish(message, routing_key=event_type)

            print(f"📤 Published event: {event_type} | ID: {message_body['event_id']}")

        except Exception as e:
            print(f"Failed to publish event {event_type}: {str(e)}")
            raise

    async def subscribe_to_events(self, event_patterns: List[str], callback: Callable):
        """S'abonne aux événements spécifiés"""
        if not self.channel:
            raise RuntimeError("Message broker not connected")

        try:
            queue_name = f"{self.service_name}.events"
            queue = await self.channel.declare_queue(
                queue_name, durable=True, exclusive=False
            )

            for pattern in event_patterns:
                await queue.bind(self.events_exchange, routing_key=pattern)
                print(f"📥 Subscribed to pattern: {pattern}")

            await queue.consume(callback)

        except Exception as e:
            print(f"Failed to subscribe to events: {str(e)}")
            raise

    async def close(self):
        """Ferme la connexion proprement"""
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
            print(f"Message broker connection closed for {self.service_name}")

    @property
    def is_connected(self) -> bool:
        """Vérifie si la connexion est active"""
        return self.connection is not None and not self.connection.is_closed

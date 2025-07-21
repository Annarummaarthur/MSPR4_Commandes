# tests/test_db.py
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from app.db import engine


def test_connection_to_database():
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.fetchone()[0] == 1
    except SQLAlchemyError as e:
        assert False, f"Database connection failed: {e}"


def test_database_tables_creation():
    """Test que les tables sont créées correctement"""
    from app.models import OrderModel, OrderItemModel, OrderEventModel
    from app.db import Base

    try:
        # Créer les tables
        Base.metadata.create_all(bind=engine)

        # Vérifier que les tables existent
        with engine.connect() as connection:
            # Test table orders
            result = connection.execute(text("SELECT COUNT(*) FROM orders"))
            assert result.fetchone()[0] >= 0

            # Test table order_items
            result = connection.execute(text("SELECT COUNT(*) FROM order_items"))
            assert result.fetchone()[0] >= 0

            # Test table order_events
            result = connection.execute(text("SELECT COUNT(*) FROM order_events"))
            assert result.fetchone()[0] >= 0

    except SQLAlchemyError as e:
        assert False, f"Database tables creation failed: {e}"

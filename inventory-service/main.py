import threading
from fastapi import FastAPI
from sqlalchemy import Column, Integer, String
from shared.database import Base, SessionLocal, engine
from shared.kafka_utils import create_consumer, create_producer, publish_event

app = FastAPI(title='Inventory Service', version='1.0.0')
producer = create_producer()


class Inventory(Base):
    __tablename__ = 'inventory'
    product_id = Column(String(64), primary_key=True)
    available_quantity = Column(Integer, nullable=False)


Base.metadata.create_all(bind=engine)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'inventory-service'}


@app.get('/inventory/{product_id}')
def get_inventory(product_id: str):
    db = SessionLocal()
    try:
        item = db.query(Inventory).filter(Inventory.product_id == product_id).first()
        return {'product_id': product_id, 'available_quantity': item.available_quantity if item else 0}
    finally:
        db.close()


def consume_orders():
    consumer = create_consumer('order.created', 'inventory-service-group')
    for message in consumer:
        event = message.value
        db = SessionLocal()
        try:
            item = db.query(Inventory).filter(Inventory.product_id == event['product_id']).with_for_update().first()
            approved = bool(item and item.available_quantity >= event['quantity'])
            if approved:
                item.available_quantity -= event['quantity']
                db.commit()
                topic = 'inventory.reserved'
                event_type = 'INVENTORY_RESERVED'
            else:
                topic = 'inventory.rejected'
                event_type = 'INVENTORY_REJECTED'
            publish_event(producer, topic, {**event, 'event_type': event_type}, key=str(event['order_id']))
        except Exception as exc:
            db.rollback()
            publish_event(producer, 'order.dlq', {'source': 'inventory-service', 'error': str(exc), 'payload': event})
        finally:
            db.close()


@app.on_event('startup')
def start_consumer():
    threading.Thread(target=consume_orders, daemon=True).start()

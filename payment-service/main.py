import random
import threading
from datetime import datetime
from fastapi import FastAPI
from sqlalchemy import Column, DateTime, Integer, Numeric, String
from shared.database import Base, SessionLocal, engine
from shared.kafka_utils import create_consumer, create_producer, publish_event

app = FastAPI(title='Payment Service', version='1.0.0')
producer = create_producer()


class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(32), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'payment-service'}


def consume_inventory_reserved():
    consumer = create_consumer('inventory.reserved', 'payment-service-group')
    for message in consumer:
        event = message.value
        db = SessionLocal()
        try:
            approved = random.random() > 0.05
            status = 'APPROVED' if approved else 'FAILED'
            payment = Payment(order_id=event['order_id'], amount=event['amount'], status=status)
            db.add(payment)
            db.commit()
            topic = 'payment.approved' if approved else 'payment.failed'
            event_type = 'PAYMENT_APPROVED' if approved else 'PAYMENT_FAILED'
            publish_event(producer, topic, {**event, 'event_type': event_type, 'payment_status': status}, key=str(event['order_id']))
        except Exception as exc:
            db.rollback()
            publish_event(producer, 'order.dlq', {'source': 'payment-service', 'error': str(exc), 'payload': event})
        finally:
            db.close()


@app.on_event('startup')
def start_consumer():
    threading.Thread(target=consume_inventory_reserved, daemon=True).start()

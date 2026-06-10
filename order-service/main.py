from datetime import datetime, timedelta
from decimal import Decimal
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Session

from shared.database import Base, engine, get_db
from shared.kafka_utils import create_producer, publish_event
from shared.security import JWT_ALGORITHM, JWT_SECRET, verify_token

app = FastAPI(title='Order Service', version='1.0.0')
producer = create_producer()


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(64), nullable=False)
    product_id = Column(String(64), nullable=False)
    quantity = Column(Integer, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String(32), nullable=False, default='PENDING')
    created_at = Column(DateTime, default=datetime.utcnow)


class OrderCreate(BaseModel):
    customer_id: str = Field(..., examples=['CUST-101'])
    product_id: str = Field(..., examples=['P1001'])
    quantity: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)


class OrderResponse(BaseModel):
    id: int
    customer_id: str
    product_id: str
    quantity: int
    amount: Decimal
    status: str


Base.metadata.create_all(bind=engine)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'order-service'}


@app.post('/auth/demo-token')
def demo_token():
    payload = {'sub': 'demo-user', 'role': 'admin', 'exp': datetime.utcnow() + timedelta(hours=6)}
    return {'token': jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)}


@app.post('/orders', response_model=OrderResponse)
def create_order(order: OrderCreate, db: Annotated[Session, Depends(get_db)], _: dict = Depends(verify_token)):
    db_order = Order(
        customer_id=order.customer_id,
        product_id=order.product_id,
        quantity=order.quantity,
        amount=order.amount,
        status='PENDING',
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)

    publish_event(
        producer,
        'order.created',
        {
            'event_type': 'ORDER_CREATED',
            'order_id': db_order.id,
            'customer_id': db_order.customer_id,
            'product_id': db_order.product_id,
            'quantity': db_order.quantity,
            'amount': float(db_order.amount),
            'created_at': db_order.created_at.isoformat(),
        },
        key=str(db_order.id),
    )
    return db_order


@app.get('/orders/{order_id}', response_model=OrderResponse)
def get_order(order_id: int, db: Annotated[Session, Depends(get_db)]):
    return db.query(Order).filter(Order.id == order_id).first()

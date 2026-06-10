import os
import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

ORDER_SERVICE_URL = os.getenv('ORDER_SERVICE_URL', 'http://localhost:8001')
app = FastAPI(title='API Gateway', version='1.0.0')


class OrderRequest(BaseModel):
    customer_id: str = Field(..., examples=['CUST-101'])
    product_id: str = Field(..., examples=['P1001'])
    quantity: int = Field(..., gt=0)
    amount: float = Field(..., gt=0)


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'api-gateway'}


@app.post('/auth/demo-token')
def demo_token():
    response = requests.post(f'{ORDER_SERVICE_URL}/auth/demo-token', timeout=5)
    return response.json()


@app.post('/orders')
def create_order(order: OrderRequest, authorization: str = Header(default='')):
    if not authorization:
        raise HTTPException(status_code=401, detail='Missing Authorization header')
    response = requests.post(
        f'{ORDER_SERVICE_URL}/orders',
        json=order.model_dump(),
        headers={'Authorization': authorization},
        timeout=10,
    )
    return response.json()

# Event-Driven Order Processing Platform

A production-style event-driven microservices project built with **Python, FastAPI, Kafka, PostgreSQL, Docker, JWT authentication, and asynchronous event processing**.

This project demonstrates how modern backend systems decouple services using event streams instead of synchronous service-to-service calls.

## Architecture

```text
Client
  |
  v
API Gateway :8000
  |
  v
Order Service :8001 -- publishes --> order.created
  |
  v
Kafka
  |--> Inventory Service :8002 -- publishes --> inventory.reserved / inventory.rejected
  |--> Payment Service :8003 ---- publishes --> payment.approved / payment.failed
  |--> Notification Service :8004 consumes final status events
  |--> order.dlq for failed event processing
```

## Services

| Service | Port | Responsibility |
|---|---:|---|
| API Gateway | 8000 | Public entry point and request routing |
| Order Service | 8001 | Creates orders, validates JWT, publishes `order.created` |
| Inventory Service | 8002 | Reserves stock and publishes inventory events |
| Payment Service | 8003 | Simulates payment approval/failure |
| Notification Service | 8004 | Consumes final events and stores recent notifications |
| Kafka | 9092 | Event broker |
| PostgreSQL | 5432 | Persistent storage |

## Tech Stack

- Python 3.11
- FastAPI
- Kafka
- PostgreSQL
- SQLAlchemy
- Docker and Docker Compose
- JWT Authentication
- Event-driven architecture
- Dead-letter queue pattern

## Run Locally

```bash
docker compose up --build
```

Wait until Kafka and all services are running.

## Test the Flow

### 1. Get a demo JWT token

```bash
curl -X POST http://localhost:8000/auth/demo-token
```

Copy the returned token.

### 2. Create an order

```bash
curl -X POST http://localhost:8000/orders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "customer_id": "CUST-101",
    "product_id": "P1001",
    "quantity": 2,
    "amount": 149.99
  }'
```

### 3. Check inventory

```bash
curl http://localhost:8002/inventory/P1001
```

### 4. Check notifications

```bash
curl http://localhost:8004/notifications
```

## Kafka Topics

| Topic | Produced By | Consumed By |
|---|---|---|
| `order.created` | Order Service | Inventory Service |
| `inventory.reserved` | Inventory Service | Payment Service |
| `inventory.rejected` | Inventory Service | Notification Service |
| `payment.approved` | Payment Service | Notification Service |
| `payment.failed` | Payment Service | Notification Service |
| `order.dlq` | Any failed service | Notification Service |

## Resume Bullets

- Architected an **event-driven microservices platform** using **Python, FastAPI, PostgreSQL, Kafka, Docker, REST APIs, and JWT**, decoupling Order, Inventory, Payment, and Notification services through asynchronous event streams.
- Implemented Kafka-based event pipelines with retry-safe consumers, inventory reservation, simulated payment processing, and **dead-letter queue handling**, improving fault tolerance and service resilience.
- Containerized five backend services using **Docker Compose**, integrated PostgreSQL persistence, and documented API workflows, enabling reproducible local deployment and production-style system design.

## Production-Grade Extensions

You can extend this project with:

- Prometheus and Grafana dashboards
- Kafka UI
- Debezium CDC from PostgreSQL outbox table
- Outbox pattern
- Idempotency keys
- k6 load testing
- Kubernetes manifests
- GitHub Actions CI/CD

## Project Structure

```text
event-driven-microservices-python/
├── api-gateway/
├── order-service/
├── inventory-service/
├── payment-service/
├── notification-service/
├── shared/
├── scripts/
├── docs/
├── docker-compose.yml
└── README.md
```

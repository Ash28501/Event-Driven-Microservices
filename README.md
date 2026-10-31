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
- Kubernetes (Deployments, Services, probes, Kustomize)
- GitHub Actions CI (Ruff, pytest, kubeconform, image builds)

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

### 5. Check end-to-end latency

```bash
curl http://localhost:8004/latency    # p50/p95/p99 from order creation to final status event
```

## Load Test

```bash
python loadtest/run_load_test.py --orders 2000 --concurrency 100
```

The script reports orders/sec accepted, Kafka events/sec processed, API latency, and **end-to-end latency**. End-to-end latency is measured server-side, from the order's `created_at` until the Notification Service consumes the final status event. It needs only the Python standard library.

## Kubernetes

The manifests in [`k8s/`](k8s/) deploy the whole platform to a local kind or minikube cluster. Every service has readiness and liveness probes and resource limits, and rolls out with zero downtime. See [`k8s/README.md`](k8s/README.md).

## Kafka Topics

| Topic | Produced By | Consumed By |
|---|---|---|
| `order.created` | Order Service | Inventory Service |
| `inventory.reserved` | Inventory Service | Payment Service |
| `inventory.rejected` | Inventory Service | Notification Service |
| `payment.approved` | Payment Service | Notification Service |
| `payment.failed` | Payment Service | Notification Service |
| `order.dlq` | Any failed service | Notification Service |

## Production-Grade Extensions

You can extend this project with:

- Prometheus and Grafana dashboards
- Kafka UI
- Transactional outbox + Debezium CDC (removes the DB-write/Kafka-publish dual write in Order Service)
- Idempotency keys for consumers

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
├── k8s/                 # Kubernetes manifests (kubectl apply -k k8s/)
├── loadtest/            # load test with end-to-end latency
├── tests/
├── .github/workflows/   # CI
├── docker-compose.yml
└── README.md
```

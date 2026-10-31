# Kubernetes deployment

Runs the full platform (Postgres, single-node KRaft Kafka, and the five services) on a local cluster.
The services have readiness and liveness probes on `/health`, resource limits, and zero-downtime rolling updates (`maxUnavailable: 0`). The Order Service runs 2 replicas.

```bash
# 1. Create a local cluster (kind shown; minikube works too)
kind create cluster --name orders

# 2. Build the service images and load them into the cluster
for s in api-gateway order-service inventory-service payment-service notification-service; do
  docker build -t order-platform/$s:latest -f $s/Dockerfile .
  kind load docker-image order-platform/$s:latest --name orders
done

# 3. Deploy and wait
kubectl apply -k k8s/
kubectl -n order-platform rollout status deploy --timeout=180s
kubectl -n order-platform get pods

# 4. Reach the gateway and the notification service
kubectl -n order-platform port-forward svc/api-gateway 8000:8000 &
kubectl -n order-platform port-forward svc/notification-service 8004:8004 &
python loadtest/run_load_test.py --orders 500 --concurrency 50
```

The services keep restarting until Kafka is ready, which can take 20–40s on the first start. This is expected: the liveness probe restarts them, and they connect once the broker is up.

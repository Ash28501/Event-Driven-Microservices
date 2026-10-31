import threading

from fastapi import FastAPI

from shared.kafka_utils import create_consumer
from shared.latency import LatencyTracker

app = FastAPI(title='Notification Service', version='1.0.0')
notifications: list[dict] = []
latency = LatencyTracker()


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'notification-service'}


@app.get('/latency')
def latency_stats():
    """End-to-end latency from order creation to the final status event."""
    return latency.summary()


@app.post('/latency/reset')
def reset_latency():
    latency.reset()
    return {'status': 'reset'}


@app.get('/notifications')
def list_notifications():
    return {'count': len(notifications), 'items': notifications[-50:]}


def consume_notifications(topic: str):
    consumer = create_consumer(topic, f'notification-service-{topic}')
    for message in consumer:
        event = message.value
        payload = event.get('payload', event) if topic == 'order.dlq' else event
        latency_ms = latency.record_since(payload.get('created_at'))
        notification = {
            'topic': topic,
            'order_id': event.get('order_id'),
            'customer_id': event.get('customer_id'),
            'message': f"Order {event.get('order_id')} status event: {event.get('event_type')}",
            'end_to_end_ms': round(latency_ms, 1) if latency_ms is not None else None,
        }
        notifications.append(notification)
        print(notification, flush=True)


@app.on_event('startup')
def start_consumers():
    for topic in ['payment.approved', 'payment.failed', 'inventory.rejected', 'order.dlq']:
        threading.Thread(target=consume_notifications, args=(topic,), daemon=True).start()

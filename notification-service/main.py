import threading
from fastapi import FastAPI
from shared.kafka_utils import create_consumer

app = FastAPI(title='Notification Service', version='1.0.0')
notifications: list[dict] = []


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'notification-service'}


@app.get('/notifications')
def list_notifications():
    return {'count': len(notifications), 'items': notifications[-50:]}


def consume_notifications(topic: str):
    consumer = create_consumer(topic, f'notification-service-{topic}')
    for message in consumer:
        event = message.value
        notification = {
            'topic': topic,
            'order_id': event.get('order_id'),
            'customer_id': event.get('customer_id'),
            'message': f"Order {event.get('order_id')} status event: {event.get('event_type')}",
        }
        notifications.append(notification)
        print(notification, flush=True)


@app.on_event('startup')
def start_consumers():
    for topic in ['payment.approved', 'payment.failed', 'inventory.rejected', 'order.dlq']:
        threading.Thread(target=consume_notifications, args=(topic,), daemon=True).start()

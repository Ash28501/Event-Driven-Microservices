import json
import os
from kafka import KafkaProducer, KafkaConsumer

BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:29092')


def create_producer() -> KafkaProducer:
    return KafkaProducer(
        bootstrap_servers=BOOTSTRAP_SERVERS,
        value_serializer=lambda value: json.dumps(value).encode('utf-8'),
        key_serializer=lambda value: value.encode('utf-8') if value else None,
        retries=5,
    )


def create_consumer(topic: str, group_id: str) -> KafkaConsumer:
    return KafkaConsumer(
        topic,
        bootstrap_servers=BOOTSTRAP_SERVERS,
        group_id=group_id,
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda value: json.loads(value.decode('utf-8')),
    )


def publish_event(producer: KafkaProducer, topic: str, event: dict, key: str | None = None) -> None:
    producer.send(topic, value=event, key=key)
    producer.flush()

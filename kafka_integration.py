import json
import logging
from kafka import KafkaProducer, KafkaConsumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DEFAULT_BROKERS = ['localhost:9092']


def get_kafka_producer(brokers=None):
    brokers = brokers or DEFAULT_BROKERS
    return KafkaProducer(
        bootstrap_servers=brokers,
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        key_serializer=lambda k: str(k).encode('utf-8') if k is not None else None,
        retries=5,
        linger_ms=10,
    )


def get_kafka_consumer(topic, group_id='fraud-consumer-group', brokers=None, auto_offset_reset='earliest'):
    brokers = brokers or DEFAULT_BROKERS
    return KafkaConsumer(
        topic,
        bootstrap_servers=brokers,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode('utf-8')),
        auto_offset_reset=auto_offset_reset,
        enable_auto_commit=True,
        consumer_timeout_ms=1000,
    )

import logging
from kafka_integration import get_kafka_consumer
import requests
from fraud_predict import connect_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPIC = 'fraud-transactions'


def main():
    consumer = get_kafka_consumer(TOPIC)
    logger.info(f"Starting Kafka consumer on topic '{TOPIC}'...")

    try:
        while True:
            for message in consumer:
                event = message.value
                logger.info(f"[Kafka] Event received: partition={message.partition}, offset={message.offset}, value={event}")
                # Extended processing can be placed here (database update, alerts, etc.)

    except KeyboardInterrupt:
        logger.info('Consumer interrupted, shutting down.')
    except Exception as exc:
        logger.exception(f"Consumer crashed: {exc}")
    finally:
        consumer.close()


if __name__ == '__main__':
    main()

from confluent_kafka import Producer
import os
import logging
import json
from datetime import datetime
from constants import *
if not os.path.exists("logs"):
    os.makedirs("logs")

plant_name = 'bela'

logging.basicConfig(
    filename=f'logs/kafka-{plant_name}-{datetime.now().date()}.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
LOGGER = logging.getLogger(__name__)

class KafkaLocalClass:

    def __init__(self, client_name, usecase, topic_name=None) -> None:
        self.client_name = client_name
        self.usecase = usecase
        self.topic_name = topic_name if topic_name else f"{client_name}_{usecase}"
        self.kafka_config = self._get_kafka_config()

    @staticmethod
    def _get_kafka_config():
        return {
            "bootstrap.servers": BOOTSTRAP_SERVERS,
            "security.protocol": SECURITY_PROTOCOL,
            "sasl.mechanisms": SASL_MECHANISMS,
            "sasl.username": SASL_USERNAME,
            "sasl.password": SASL_PASSWORD,
            "session.timeout.ms": SESSION_TIMEOUT_MS,
            "client.id": CLIENT_ID
        }

    def produce(self, key, value):
        try:
            config = self.kafka_config.copy()
            topic = self.topic_name
            producer = Producer(config)
            LOGGER.info(producer)
            serialized_data = json.dumps(value)
            serialized_data = serialized_data.encode("utf-8")
            LOGGER.info(f"Producing record: {key}:{value}")
            producer.produce(topic, key=key, value=serialized_data)
            print(value)
            producer.flush()
            LOGGER.info(f"Produced message to topic {topic}: key = {key} value = {value}")
            return 200
        except Exception as e:
            LOGGER.error(f"Error occured during produce: {e}")
            return 500
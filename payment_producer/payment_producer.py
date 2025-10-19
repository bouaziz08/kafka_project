import json
import uuid
import random
import logging
from confluent_kafka import Producer
from prometheus_client import start_http_server, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_producer")

start_http_server(8011)
payments_sent = Counter("payments_sent_total", "Number of payments sent")

producer = Producer({"bootstrap.servers": "localhost:9092"})

def delivery_report(err, msg):
    if err:
        logger.error(f"Delivery failed: {err}")
    else:
        logger.info(f"Delivered payment: {msg.value().decode('utf-8')}")

def create_payment():
    return {
        "payment_id": str(uuid.uuid4()),
        "order_id": str(uuid.uuid4()),
        "method": random.choice(["credit_card", "paypal", "cash"]),
        "amount": random.randint(10, 100)
    }

for _ in range(5):
    payment = create_payment()
    producer.produce("payments", json.dumps(payment).encode("utf-8"), callback=delivery_report)
    payments_sent.inc()
    producer.flush()

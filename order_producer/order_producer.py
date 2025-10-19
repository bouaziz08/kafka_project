import json
import uuid
import random
import logging
from confluent_kafka import Producer
from prometheus_client import start_http_server, Counter

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_producer")

# Prometheus metrics
start_http_server(8010)
orders_sent = Counter("orders_sent_total", "Number of orders sent")

producer = Producer({"bootstrap.servers": "localhost:9092"})

def delivery_report(err, msg):
    if err:
        logger.error(f"Delivery failed: {err}")
    else:
        logger.info(f"Delivered order: {msg.value().decode('utf-8')}")

def create_order():
    users = ["lara", "tom", "sophia", "max"]
    items = ["pizza", "burger", "yogurt", "coffee"]
    return {
        "order_id": str(uuid.uuid4()),
        "user": random.choice(users),
        "item": random.choice(items),
        "quantity": random.randint(1, 5)
    }

for _ in range(5):
    order = create_order()
    producer.produce("orders", json.dumps(order).encode("utf-8"), callback=delivery_report)
    orders_sent.inc()
    producer.flush()

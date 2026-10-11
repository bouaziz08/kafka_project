import json
import logging
import os

import psycopg2
from confluent_kafka import Consumer
from prometheus_client import Counter, start_http_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_consumer")

start_http_server(8020)
orders_received = Counter(
    "orders_received_total",
    "Number of orders received",
)

consumer = Consumer({
    "bootstrap.servers": os.getenv("KAFKA_BROKER", "localhost:9092"),
    "group.id": "order-tracker-group",
    "auto.offset.reset": "earliest",
})

consumer.subscribe(["orders"])
logger.info("Order consumer started")

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    dbname=os.getenv("DB_NAME", "kafka_project"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "azerty@147"),
)
logger.info("Connected to PostgreSQL")

cursor = conn.cursor()
cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        order_id VARCHAR(255) PRIMARY KEY,
        user_name VARCHAR(255),
        item VARCHAR(255),
        quantity INT
    )
""")
conn.commit()

try:
    while True:
        message = consumer.poll(1.0)

        if message is None:
            continue

        if message.error():
            logger.error("Kafka error: %s", message.error())
            continue

        order = json.loads(message.value().decode("utf-8"))

        cursor.execute(
            """
            INSERT INTO orders (order_id, user_name, item, quantity)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (order_id) DO NOTHING
            """,
            (
                order["order_id"],
                order["user"],
                order["item"],
                order["quantity"],
            ),
        )
        conn.commit()

        logger.info("Processing order: %s", order)
        orders_received.inc()

except KeyboardInterrupt:
    logger.info("Stopping order consumer")
finally:
    consumer.close()
    cursor.close()
    conn.close()
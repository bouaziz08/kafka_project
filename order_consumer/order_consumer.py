import json, time
import logging, psycopg2
from confluent_kafka import Consumer
from prometheus_client import start_http_server, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_consumer")

start_http_server(8020)
orders_received = Counter("orders_received_total", "Number of orders received")


consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-tracker-group",
    "auto.offset.reset": "earliest"
})

consumer.subscribe(["orders"])
logger.info("Order consumer started")

# Database connection

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    dbname="kafka_project",
    user="admin",
    password="azerty@147"
)
print("✅ Connected to PostgreSQL")

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
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            logger.error(msg.error())
            continue

        order = json.loads(msg.value().decode("utf-8"))

        cursor.execute("""
                   INSERT INTO orders (order_id, user_name, item, quantity)
                   VALUES (%s, %s, %s, %s)
                   ON CONFLICT (order_id) DO NOTHING
               """, (order["order_id"], order["user"], order["item"], order["quantity"]))
        conn.commit()

        logger.info(f"📦 Processing order: {order}")
        orders_received.inc()
except KeyboardInterrupt:
    logger.info("Stopping order consumer")
finally:
    consumer.close()
    cursor.close()
    conn.close()

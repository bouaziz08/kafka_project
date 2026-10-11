import json
import logging, psycopg2
import os
from confluent_kafka import Consumer
from prometheus_client import start_http_server, Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_consumer")

start_http_server(8021)
payments_received = Counter("payments_received_total", "Number of payments received")

consumer = Consumer({
    "bootstrap.servers": os.getenv("KAFKA_BROKER", "localhost:9092"),
    "group.id": "payment-processor-group",
    "auto.offset.reset": "earliest"
})

consumer.subscribe(["payments"])
logger.info("Payment consumer started")

# Database connection
conn = psycopg2.connect(
    dbname=os.getenv("DB_NAME", "kafka_project"),
    user=os.getenv("DB_USER", "admin"),
    password=os.getenv("DB_PASSWORD", "azerty@147"),
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432")
)
if conn:
    print("✅ Connected to PostgreSQL")

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        payment_id VARCHAR(255) PRIMARY KEY,
        order_id VARCHAR(255) NOT NULL,
        amount FLOAT,
        method VARCHAR(255),
        CONSTRAINT fk_payment_order
            FOREIGN KEY (order_id) REFERENCES orders(order_id)
)
""")
conn.commit()

cursor.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname = 'fk_payment_order'
              AND conrelid = 'payments'::regclass
        ) THEN
            ALTER TABLE payments
                ADD CONSTRAINT fk_payment_order
                FOREIGN KEY (order_id) REFERENCES orders(order_id);
        END IF;
    END
    $$;
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

        payment = json.loads(msg.value().decode("utf-8"))

        cursor.execute("""
                    INSERT INTO payments (payment_id, order_id, amount, method)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (payment_id) DO NOTHING
                """, (
            payment["payment_id"],
            payment["order_id"],
            payment["amount"],
            payment["method"]
        ))
        conn.commit()

        logger.info(f"💰 Processing payment: {payment}")
        payments_received.inc()
except KeyboardInterrupt:
    logger.info("Stopping payment consumer")
finally:
    consumer.close()
    cursor.close()
    conn.close()
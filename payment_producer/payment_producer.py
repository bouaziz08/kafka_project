import json
import logging
import os
import uuid
from contextlib import closing
from typing import Literal

import psycopg2
from confluent_kafka import KafkaException, Producer
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, start_http_server
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment_api")

app = FastAPI(title="Payments API")
producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BROKER", "localhost:9092")})
payments_sent = Counter("payments_sent_total", "Number of payments sent by the API")
start_http_server(8011)


class PaymentInput(BaseModel):
    order_id: str = Field(min_length=1)
    method: Literal["credit_card", "paypal", "cash"]
    amount: float = Field(gt=0)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/payments", status_code=202)
def create_payment(payment_input: PaymentInput):
    try:
        with closing(
            psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                dbname=os.getenv("DB_NAME", "kafka_project"),
                user=os.getenv("DB_USER", "admin"),
                password=os.getenv("DB_PASSWORD", ""),
            )
        ) as connection:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT 1 FROM orders WHERE order_id = %s",
                        (payment_input.order_id,),
                    )
                    order_exists = cursor.fetchone() is not None
    except psycopg2.Error as error:
        logger.exception("Could not validate payment order")
        raise HTTPException(
            status_code=503,
            detail="Order database is unavailable",
        ) from error

    if not order_exists:
        raise HTTPException(status_code=404, detail="Order not found")

    payment = {
        "payment_id": str(uuid.uuid4()),
        "order_id": payment_input.order_id,
        "method": payment_input.method,
        "amount": payment_input.amount,
    }
    delivery_errors = []

    def on_delivery(error, message):
        if error:
            delivery_errors.append(str(error))
            logger.error("Payment delivery failed: %s", error)
        else:
            payments_sent.inc()
            logger.info("Payment delivered: %s", message.key().decode("utf-8"))

    try:
        producer.produce(
            "payments",
            key=payment["order_id"],
            value=json.dumps(payment).encode("utf-8"),
            callback=on_delivery,
        )
        pending = producer.flush(timeout=10)
    except (BufferError, KafkaException) as error:
        raise HTTPException(status_code=503, detail=f"Kafka unavailable: {error}") from error

    if delivery_errors:
        raise HTTPException(status_code=503, detail=delivery_errors[0])
    if pending:
        raise HTTPException(status_code=504, detail="Kafka did not confirm the payment in time")

    return {"status": "accepted", "payment": payment}

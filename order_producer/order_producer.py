import json
import logging
import os
import uuid

from confluent_kafka import KafkaException, Producer
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, start_http_server
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("order_api")

app = FastAPI(title="Orders API")
producer = Producer({"bootstrap.servers": os.getenv("KAFKA_BROKER", "localhost:9092")})
orders_sent = Counter("orders_sent_total", "Number of orders sent by the API")
start_http_server(8012)


class OrderInput(BaseModel):
	user: str = Field(min_length=1)
	item: str = Field(min_length=1)
	quantity: int = Field(gt=0)


@app.get("/health")
def health_check():
	return {"status": "ok"}


@app.post("/orders", status_code=202)
def create_order(order_input: OrderInput):
	order = {
		"order_id": str(uuid.uuid4()),
		"user": order_input.user,
		"item": order_input.item,
		"quantity": order_input.quantity,
	}
	delivery_errors = []

	def on_delivery(error, message):
		if error:
			delivery_errors.append(str(error))
			logger.error("Order delivery failed: %s", error)
		else:
			orders_sent.inc()
			logger.info("Order delivered: %s", message.key().decode("utf-8"))

	try:
		producer.produce(
			"orders",
			key=order["order_id"],
			value=json.dumps(order).encode("utf-8"),
			callback=on_delivery,
		)
		pending = producer.flush(timeout=10)
	except (BufferError, KafkaException) as error:
		raise HTTPException(status_code=503, detail=f"Kafka unavailable: {error}") from error

	if delivery_errors:
		raise HTTPException(status_code=503, detail=delivery_errors[0])
	if pending:
		raise HTTPException(status_code=504, detail="Kafka did not confirm the order in time")

	return {"status": "accepted", "order": order}

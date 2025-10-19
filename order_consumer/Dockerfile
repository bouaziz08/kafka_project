FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    KAFKA_BROKER=kafka:9092

EXPOSE 8020

CMD ["python", "order_consumer.py"]
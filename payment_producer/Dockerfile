FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    KAFKA_BROKER=kafka:9092

EXPOSE 8000 8011

CMD ["uvicorn", "payment_producer:app", "--host", "0.0.0.0", "--port", "8000"]
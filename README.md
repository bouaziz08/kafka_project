# 🧠 StreamWatch

## 📦 Overview
**StreamWatch** is a real-time data streaming and monitoring system built with **Kafka**, **PostgreSQL**, **Prometheus**, and **Grafana**.  
It demonstrates how to build a **microservices architecture** for event-driven systems using **Docker Compose**.

---

## 🧩 Architecture

### Services:
| Service | Description |
|----------|-------------|
| **order_producer** | Sends new order messages to the Kafka topic `orders`. |
| **payment_producer** | Sends payment messages to the Kafka topic `payments`. |
| **order_consumer** | Consumes `orders` messages and stores them in PostgreSQL. |
| **payment_consumer** | Consumes `payments` messages and stores them in PostgreSQL. |
| **Kafka** | Core message broker for streaming communication. |
| **PostgreSQL** | Persistent database for storing orders and payments. |
| **Prometheus** | Monitors the producers/consumers and collects metrics. |
| **Grafana** | Visualizes Prometheus metrics through dashboards. |

---

## 🏗️ Project Structure
StreamWatch/
│
├── docker-compose.yml
├── prometheus/
│ └── prometheus.yml
│
├── order_producer/
│ ├── Dockerfile
│ ├── main.py
│ └── requirements.txt
│
├── payment_producer/
│ ├── Dockerfile
│ ├── main.py
│ └── requirements.txt
│
├── order_consumer/
│ ├── Dockerfile
│ ├── main.py
│ └── requirements.txt
│
├── payment_consumer/
│ ├── Dockerfile
│ ├── main.py
│ └── requirements.txt
│
└── data/
└── db/

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

git clone repositoryUrl
cd StreamWatch
### 2. Start All Services
docker-compose up --build

📊 Monitoring
Prometheus
Access Prometheus UI: 👉 http://localhost:9090

Grafana
Access Grafana Dashboard: 👉 http://localhost:3000
Note: Add Prometheus as a data source (http://prometheus:9090) and import dashboards to visualize Kafka message flow and consumer metrics.

🛠️ Tech Stack
Backend: Python (Kafka Producer/Consumer)
Message Broker: Apache Kafka
Database: PostgreSQL
Monitoring: Prometheus + Grafana
Containerization: Docker & Docker Compose

👨‍💻 Author
Bakr Bouaziz
💼 Software enginner

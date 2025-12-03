SCMXpert Lite – Backend (FastAPI + MongoDB + Kafka)

This repository contains the backend service for SCMXpert Lite, built using FastAPI, MongoDB, and optional Kafka integration. It provides APIs for authentication, admin requests, shipment events, and real-time processing.


**Tech Stack**

1.FastAPI – Backend framework

2.MongoDB (Atlas or Local) – Database

3.Kafka / AIOKafka – Optional event streaming

4.Jinja2 – Template rendering

5.Uvicorn – ASGI server

6.JWT (python-jose) – Authentication

7.WebSockets – Real-time updates

**Project Structure**

project/
│── backend/
│   ├── auth/
│   ├── routers/
│   ├── database.py
│   ├── main.py
│── templates/
│── static/
│── requirements.txt
│── docker-compose.yml
│── .env (not included in repo)


**Environment Variables (.env file)**

MONGO_URI=<your mongo uri>
DB_NAME=<your database name>
SECRET_KEY=<jwt secret>
ALGORITHM=HS256

KAFKA_TOPIC=<optional>
KAFKA_BOOTSTRAP_SERVERS=<optional>

DEBUG=true

RECAPTCHA_SECRET_KEY=<your key>
RECAPTCHA_SITE_KEY=<your key>

MAIL_USERNAME=<email user>
MAIL_PASS=<email password or app password>
MAIL_USER=<email>
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com


**Installation
1️⃣ Clone the repository**
git clone <repo-url>
cd project-folder

**2️⃣ Create virtual environment**
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

**3️⃣ Install dependencies**
pip install -r requirements.txt

**▶️ Run the Application**
uvicorn backend.main:app --reload

**Run with Docker**

If using docker-compose.yml:

docker compose up --build

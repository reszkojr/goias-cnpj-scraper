import json
import os
import uuid
import pika
from fastapi import FastAPI, HTTPException
import redis

from app.models import ScrapeRequest
from worker.worker import get_rabbitmq_connection, get_redis_connection

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
QUEUE_NAME = "scrape_tasks"

app = FastAPI(
    title="API Scraper Sintegra",
    description="Desafio Técnico: FastAPI, RabbitMQ e Redis para scraping",
    version="0.1.0",
)


@app.get("/")
async def read_root():
    """Endpoint raiz da API para verificação de status"""
    return {"message": "API is running"}


@app.post("/scrape")
async def create_scrape_task(request: ScrapeRequest):
    """Endpoint para iniciar o processo de scraping"""
    try:
        task_id = str(uuid.uuid4())

        redis_client = get_redis_connection()
        task_data = {
            "task_id": task_id,
            "cnpj": request.cnpj,
            "status": "pending",
            "created_at": str(uuid.uuid1().time),
        }
        redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=3600)

        rabbit_connection = get_rabbitmq_connection()
        channel = rabbit_connection.channel()
        channel.queue_declare(queue=QUEUE_NAME, durable=True)

        message = {"task_id": task_id, "cnpj": request.cnpj}

        channel.basic_publish(
            exchange="",
            routing_key=QUEUE_NAME,
            body=json.dumps(message),
            properties=pika.BasicProperties(delivery_mode=2),
        )

        rabbit_connection.close()

        return {"message": "Webscraping iniciado", "task_id": task_id}
    except Exception as e:
        return HTTPException(
            status_code=500, detail=f"Erro ao criar a tarefa de scraping, {e}"
        )


@app.get("/results/{task_id}")
async def get_task_result(task_id: str):
    """Endpoint para obter os resultados do scraping"""
    return {"task_id": task_id, "status": "completed", "data": {}}

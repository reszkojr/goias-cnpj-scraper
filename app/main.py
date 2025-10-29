import json
import os
import time
import uuid

import aio_pika
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.concurrency import asynccontextmanager
from redis import asyncio as aioredis

from app.models import ScrapeRequest, TaskResponse, TaskStatus

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
QUEUE_NAME = "scrape_tasks"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerenciador de contexto para inicialização e finalização da API"""
    try:
        print("FastAPI - conectando ao RabbitMQ e Redis...")
        app.state.rabbit_connection = await aio_pika.connect_robust(
            host=RABBITMQ_HOST, login="user", password="password"
        )
        app.state.rabbit_channel = await app.state.rabbit_connection.channel()
        await app.state.rabbit_channel.declare_queue(QUEUE_NAME, durable=True)

        redis_pool = aioredis.ConnectionPool.from_url(
            f"redis://{REDIS_HOST}", encoding="utf-8", decode_responses=True
        )
        app.state.redis = aioredis.Redis(connection_pool=redis_pool)
        await app.state.redis.ping()
        print("FastAPI - conectado")
    except aioredis.ConnectionError as e:
        print(f"FastAPI - erro ao conectar ao Redis: {e}")
        raise
    except aio_pika.exceptions.AMQPConnectionError as e:
        print(f"FastAPI - erro ao conectar ao RabbitMQ: {e}")
        raise

    yield

    try:
        print("FastAPI - finalizando conexões...")
        await app.state.rabbit_channel.close()
        await app.state.rabbit_connection.close()
        await app.state.redis.close()
        print("FastAPI - conexões finalizadas")
    except aio_pika.exceptions.AMQPConnectionError as e:
        print(f"FastAPI - erro ao finalizar conexões: {e}")
        raise

    print("FastAPI - encerrado")


app = FastAPI(
    lifespan=lifespan,
    title="API Scraper Sintegra",
    description="Desafio Técnico: FastAPI, RabbitMQ e Redis para scraping",
    version="0.1.0",
)


@app.get("/", summary="Endpoint raiz da API")
async def read_root():
    """Endpoint raiz da API para verificação de status"""
    return {"message": "API is running"}


@app.post(
    "/scrape",
    response_model=TaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Iniciar tarefa de scraping",
)
async def create_scrape_task(
    request: ScrapeRequest,
):
    """Endpoint para iniciar o processo de scraping"""
    try:
        task_id = str(uuid.uuid4())

        redis_client = app.state.redis
        rabbit_connection = app.state.rabbit_connection
        channel = await rabbit_connection.channel()

        task_data = {
            "task_id": task_id,
            "cnpj": request.cnpj,
            "status": "pending",
            "created_at": time.time(),
        }
        await redis_client.set(f"task:{task_id}", json.dumps(task_data), ex=3600)

        message = {"task_id": task_id, "cnpj": request.cnpj}

        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=QUEUE_NAME,
        )

        return TaskResponse(
            task_id=task_id,
            status="pending",
            message="Tarefa de scraping criada com sucesso",
        )
    except Exception as e:
        print(f"FastAPI - Erro ao criar a tarefa de scraping: {e}")
        return HTTPException(
            status_code=500, detail=f"Erro ao criar a tarefa de scraping, {e}"
        )


@app.get(
    "/results/{task_id}",
    response_model=TaskStatus,
    summary="Obter resultados do scraping",
)
async def get_task_result(request: Request, task_id: str):
    """Endpoint para obter os resultados do scraping"""
    try:
        redis_client = request.app.state.redis

        task_data_json = await redis_client.get(f"task:{task_id}")

        if not task_data_json:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada"
            )

        task_data = json.loads(task_data_json)
        return task_data
    except Exception as e:
        print(f"FastAPI - Erro no /results/{task_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao consultar a tarefa {e}")

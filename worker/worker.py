import json
import os
import time

import pika
import redis

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "rabbitmq")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
QUEUE_NAME = "scrape_tasks"


def get_redis_connection():
    print("Tentando se conectar ao servidor do Redis...")
    retry_interval = 3
    for _ in range(10):
        try:
            redis_connection = redis.Redis(
                host=REDIS_HOST, port=6379, db=0, decode_responses=True
            )
            redis_connection.ping()
            print("Conectado ao Redis com sucesso.")
            return redis_connection
        except redis.exceptions.ConnectionError:
            print(
                f"Falha ao conectar ao Redis, tentando novamente em {retry_interval} segundos..."
            )
            time.sleep(retry_interval)
        raise Exception("Não foi possível se conectar ao Redis.")


def get_rabbitmq_connection():
    print("Tentando se conectar ao servidor do RabbitMQ...")
    credentials = pika.PlainCredentials("user", "password")
    parameters = pika.ConnectionParameters(host=RABBITMQ_HOST, credentials=credentials)
    retry_interval = 3
    for _ in range(10):
        try:
            connection = pika.BlockingConnection(parameters)
            print("Conectado ao RabbitMQ com sucesso.")
            return connection
        except pika.exceptions.AMQPConnectionError:
            print(
                f"Falha ao conectar ao RabbitMQ, tentando novamente em {retry_interval}"
            )
            time.sleep(retry_interval)
    raise Exception("Não foi possível se conectar ao RabbitMQ.")


def update_redis(redis_client, task_id, status, result=None):
    """Atualiza o status da tarefa no Redis."""
    try:
        task_key = f"task:{task_id}"
        task_data_json = redis_client.get(task_key)
        task_data = json.loads(task_data_json) if task_data_json else {}

        task_data["status"] = status
        if result:
            task_data["result"] = result

        redis_client.set(task_key, json.dumps(task_data), ex=3600)
        print(f"WORKER Tarefa: {task_id} Status atualizado para: {status}")
    except Exception as e:
        print(f"WORKER Tarefa: {task_id} ERRO ao atualizar Redis: {e}")


def process_task(task_id, cnpj, redis_client):
    print(f"WORKER Tarefa: {task_id} Recebido. Processando CNPJ: {cnpj}...")

    update_redis(redis_client, task_id, "processing")

    # TODO: desmockar a seção de scraping
    print(f"WORKER Tarefa: {task_id} Simulando scraping... (5 segundos)")
    time.sleep(5)

    mock_result = {
        "razao_social": f"EMPRESA FANTASIA QUE NAO EXISTE {cnpj}",
        "nome_fantasia": "NOME FANTASIA DE UMA EMPRESA QUE NAO EXISTE",
        "endereco": "RUA DOS BOBOS, 0",
        "situacao_cadastral": "ATIVA",
        "timestamp_processamento": time.time(),
        "storage_driver": "redis",
    }

    update_redis(redis_client, task_id, "completed", mock_result)

    print(f"WORKER [Tarefa: {task_id}] Processamento concluído.")


def main():
    print("WORKER: Iniciando o worker de processamento de tarefas...")
    redis_client = get_redis_connection()
    rabbit_connection = get_rabbitmq_connection()

    channel = rabbit_connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, properties, body):
        message = json.loads(body.decode())
        task_id = message.get("task_id")
        cnpj = message.get("cnpj")

        if not task_id or not cnpj:
            print(f"WORKER: Mensagem inválida recebida: {body}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        try:
            process_task(task_id, cnpj, redis_client)

            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"WORKER Tarefa: {task_id} Falha crítica no processamento: {e}")

            update_redis(redis_client, task_id, "failed", {"error": str(e)})

            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback)

    print("\nWORKER: [*] Aguardando tarefas. Para sair, pressione CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("WORKLER: Encerrando...")
        channel.stop_consuming()
    finally:
        rabbit_connection.close()
        print("WORKER: Conexão com RabbitMQ fechada.")


if __name__ == "__main__":
    main()

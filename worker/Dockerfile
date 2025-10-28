FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

COPY ./worker/worker.py .

CMD ["python", "worker.py"]
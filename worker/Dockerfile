FROM python:3.11-slim

WORKDIR /app

COPY ./requirements.txt .

RUN pip install --no-cache-dir --upgrade pip -r requirements.txt

COPY worker ./worker

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

CMD ["python", "-m", "worker.consumer"]
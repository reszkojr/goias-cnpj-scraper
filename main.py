from fastapi import FastAPI

app = FastAPI(
    title="API Scraper Sintegra",
    description="Desafio Técnico: FastAPI, RabbitMQ e Redis para scraping",
    version="0.1.0",
)


@app.get("/")
async def read_root():
    return {"message": "hello world"}

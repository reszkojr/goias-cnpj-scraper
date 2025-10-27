from fastapi import FastAPI

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
async def create_scrape_task():
    """Endpoint para iniciar o processo de scraping"""
    return {"message": "Scraping started", "task_id": "123-123-123-123"}


@app.get("/results/{task_id}")
async def get_task_result(task_id: str):
    """Endpoint para obter os resultados do scraping"""
    return {"task_id": task_id, "status": "completed", "data": {}}

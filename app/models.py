from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class ScrapeRequest(BaseModel):
    cnpj: str

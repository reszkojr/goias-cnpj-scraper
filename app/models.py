from pydantic import BaseModel


class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
    created_at: float | None = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class ScrapeRequest(BaseModel):
    cnpj: str

from pydantic import BaseModel


class ScrapeRequest(BaseModel):
    cnpj: str

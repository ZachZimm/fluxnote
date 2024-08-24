from pydantic import BaseModel

class WikiData(BaseModel):
    """Model for object that represents a Wikipedia article"""
    title: str
    summary: str
    content: str
    links: list[str]
    creation: float

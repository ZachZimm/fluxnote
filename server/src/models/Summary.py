from pydantic import BaseModel

class Idea(BaseModel):
    """Idea extracted from text"""
    idea: str
    embedding: list[float] = []

class Summary(BaseModel):
    """Summary of user text"""
    summary: list[Idea]
    
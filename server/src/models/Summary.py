from pydantic import BaseModel

class Idea(BaseModel):
    """Idea extracted from text"""
    idea: str

class Summary(BaseModel):
    """Summary of user text"""
    summary: list[Idea]
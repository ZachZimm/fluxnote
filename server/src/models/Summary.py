from pydantic import BaseModel 

class IdeaVerificationBool(BaseModel):
    """Boolean response for idea verification"""
    needs_work: bool
    improvement: str

class Idea(BaseModel):
    """Idea extracted from text"""
    idea: str
    embedding: list = []
    tags: list[str] = []

class Summary(BaseModel):
    """Summary of user text"""
    title: str
    summary: list[Idea]
    tags: list[str] = []

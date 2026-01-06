from pydantic import BaseModel
from typing import List


class ChatRequest(BaseModel):
    session_id: str
    question: str
    mode: str = "ask"


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    trace: List[str]
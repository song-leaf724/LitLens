from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.rag import Citation


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    document_id: Optional[str] = None
    use_rag: bool = True
    task_type: str = "qa"


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    citations: List[Citation] = []


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    task_type: str
    use_rag: bool
    created_at: str


from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.rag import Citation


class AnalysisRequest(BaseModel):
    document_id: Optional[str] = None
    query: Optional[str] = None
    passage: Optional[str] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class AnalysisResponse(BaseModel):
    task_type: str
    answer: str
    citations: List[Citation] = []


from typing import List, Optional

from pydantic import BaseModel, Field


class Citation(BaseModel):
    document_id: str
    filename: str
    chunk_id: str
    chunk_index: int
    source_location: str
    content: str
    score: Optional[float] = None


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1)
    document_id: Optional[str] = None
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    task_type: str = "qa"


class RagQueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = []


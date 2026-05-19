from typing import List, Optional

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    created_at: str
    title: Optional[str] = None
    author: Optional[str] = None
    source_name: Optional[str] = None
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None
    document_type: str = "unknown"
    type_confidence: float = 0.0
    type_reason: Optional[str] = None
    chunk_strategy: str = "modern"


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


class DocumentDeleteResponse(BaseModel):
    id: str
    deleted: bool = True

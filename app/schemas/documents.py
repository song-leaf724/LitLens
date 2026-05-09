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


class DocumentListResponse(BaseModel):
    documents: List[DocumentResponse]


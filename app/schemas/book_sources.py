from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.documents import DocumentResponse


class BookSearchResult(BaseModel):
    source: str
    source_id: str
    title: str
    author: Optional[str] = None
    language: Optional[str] = None
    source_url: Optional[str] = None
    license: Optional[str] = None


class BookSearchResponse(BaseModel):
    results: List[BookSearchResult]


class BookImportRequest(BaseModel):
    source: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)


class BookImportResponse(BaseModel):
    document: DocumentResponse

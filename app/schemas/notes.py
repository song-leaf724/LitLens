from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.rag import Citation


class NoteGenerateRequest(BaseModel):
    document_id: str
    focus: Optional[str] = Field(
        default=None,
        description="可选的阅读笔记重点，例如人物、主题、叙事结构等。",
    )
    top_k: Optional[int] = Field(default=None, ge=1, le=20)


class NoteGenerateResponse(BaseModel):
    answer: str
    citations: List[Citation] = []


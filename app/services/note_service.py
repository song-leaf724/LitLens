from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.schemas.rag import Citation
from app.services.analysis_service import analysis_service


class NoteService:
    async def generate_notes(
        self,
        db: Session,
        document_id: str,
        focus: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> Tuple[str, List[Citation]]:
        query = focus or "请生成结构化阅读笔记，覆盖作品概览、情节、人物、主题和摘录。"
        return await analysis_service.run_analysis(
            db=db,
            task_type="notes",
            query=query,
            document_id=document_id,
            top_k=top_k,
        )


note_service = NoteService()


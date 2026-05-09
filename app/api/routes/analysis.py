from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import analysis_service

router = APIRouter()


async def _run(
    task_type: str, request: AnalysisRequest, db: Session
) -> AnalysisResponse:
    if task_type in {"close_reading", "bilingual"} and not (
        request.passage or request.document_id
    ):
        raise HTTPException(status_code=400, detail="请提供 passage 或 document_id。")

    answer, citations = await analysis_service.run_analysis(
        db=db,
        task_type=task_type,
        query=request.query,
        document_id=request.document_id,
        passage=request.passage,
        top_k=request.top_k,
    )
    return AnalysisResponse(task_type=task_type, answer=answer, citations=citations)


@router.post("/plot", response_model=AnalysisResponse)
async def analyze_plot(
    request: AnalysisRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    return await _run("plot", request, db)


@router.post("/characters", response_model=AnalysisResponse)
async def analyze_characters(
    request: AnalysisRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    return await _run("characters", request, db)


@router.post("/themes", response_model=AnalysisResponse)
async def analyze_themes(
    request: AnalysisRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    return await _run("themes", request, db)


@router.post("/close-reading", response_model=AnalysisResponse)
async def close_reading(
    request: AnalysisRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    return await _run("close_reading", request, db)


@router.post("/bilingual", response_model=AnalysisResponse)
async def bilingual_reading(
    request: AnalysisRequest, db: Session = Depends(get_db)
) -> AnalysisResponse:
    return await _run("bilingual", request, db)


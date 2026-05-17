from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.routes.documents import document_to_response
from app.book_sources.base import BookSourceError
from app.db.session import get_db
from app.schemas.book_sources import BookImportRequest, BookImportResponse, BookSearchResponse, BookSearchResult
from app.services.book_import_service import book_import_service

router = APIRouter()


@router.get("/search", response_model=BookSearchResponse)
async def search_books(
    source: str = Query(..., min_length=1),
    q: str = Query(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=20),
) -> BookSearchResponse:
    try:
        results = await book_import_service.search(source=source, query=q, limit=limit)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except BookSourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return BookSearchResponse(results=[BookSearchResult(**item.__dict__) for item in results])


@router.post("/import", response_model=BookImportResponse)
async def import_book(
    request: BookImportRequest, db: Session = Depends(get_db)
) -> BookImportResponse:
    try:
        document = await book_import_service.import_book(
            db=db, source=request.source, source_id=request.source_id
        )
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except BookSourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return BookImportResponse(document=document_to_response(document))

from fastapi import APIRouter

from app.api.routes import agent, analysis, chat, documents, notes, rag, sessions

api_router = APIRouter()
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])


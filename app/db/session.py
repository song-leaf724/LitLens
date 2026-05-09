import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _connect_args() -> dict:
    if settings.database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def _ensure_sqlite_parent_dir() -> None:
    if not settings.database_url.startswith("sqlite:///"):
        return
    db_path = settings.database_url.replace("sqlite:///", "", 1)
    parent = os.path.dirname(db_path)
    if parent:
        os.makedirs(parent, exist_ok=True)


_ensure_sqlite_parent_dir()

engine = create_engine(
    settings.database_url,
    connect_args=_connect_args(),
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


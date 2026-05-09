from app.db.models import Base
from app.db.session import engine


def create_db_and_tables() -> None:
    Base.metadata.create_all(bind=engine)


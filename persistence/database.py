"""Configuration et session de base de données pour PostgreSQL / SQLite."""

from __future__ import annotations

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from persistence.models import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialise les tables de la base de données."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Générateur de session pour FastAPI ou scripts."""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


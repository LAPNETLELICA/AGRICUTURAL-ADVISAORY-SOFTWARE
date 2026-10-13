"""Modèles SQLAlchemy pour la persistance relationnelle de Backend 2 (compatibles 1.4 et 2.0)."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

try:
    from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

    class Base(DeclarativeBase):
        pass

    class CropEntity(Base):
        __tablename__ = "knowledge_crops"

        crop_id: Mapped[str] = mapped_column(String(50), primary_key=True)
        code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
        nom_courant: Mapped[str] = mapped_column(String(100))
        nom_scientifique: Mapped[str] = mapped_column(String(150))
        famille_code: Mapped[str] = mapped_column(String(50), index=True)
        cycle_optimal_jours: Mapped[int] = mapped_column(Integer, default=90)
        data: Mapped[dict] = mapped_column(JSON)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class RegionEntity(Base):
        __tablename__ = "knowledge_regions"

        region_id: Mapped[str] = mapped_column(String(50), primary_key=True)
        code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
        nom: Mapped[str] = mapped_column(String(100))
        chef_lieu: Mapped[str] = mapped_column(String(100))
        data: Mapped[dict] = mapped_column(JSON)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class SoilEntity(Base):
        __tablename__ = "knowledge_soils"

        soil_id: Mapped[str] = mapped_column(String(50), primary_key=True)
        code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
        nom: Mapped[str] = mapped_column(String(150))
        fao_code: Mapped[str] = mapped_column(String(50), default="")
        data: Mapped[dict] = mapped_column(JSON)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class RuleEntity(Base):
        __tablename__ = "knowledge_rules"

        rule_id: Mapped[str] = mapped_column(String(100), primary_key=True)
        crop_id: Mapped[str] = mapped_column(String(50), index=True)
        tree: Mapped[str] = mapped_column(String(10), index=True)
        domain: Mapped[str] = mapped_column(String(150))
        priority: Mapped[int] = mapped_column(Integer, default=100)
        status: Mapped[str] = mapped_column(String(30), default="published")
        conditions: Mapped[list] = mapped_column(JSON)
        candidate: Mapped[dict] = mapped_column(JSON)
        source_refs: Mapped[list] = mapped_column(JSON)
        data: Mapped[dict] = mapped_column(JSON)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    class ReleaseEntity(Base):
        __tablename__ = "knowledge_releases"

        release_id: Mapped[str] = mapped_column(String(50), primary_key=True)
        schema_version: Mapped[str] = mapped_column(String(20), default="2.0.0")
        status: Mapped[str] = mapped_column(String(30), default="published")
        sha256_hash: Mapped[str] = mapped_column(String(64))
        author: Mapped[str] = mapped_column(String(150))
        manifest: Mapped[dict] = mapped_column(JSON)
        published_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

except ImportError:
    from sqlalchemy.orm import declarative_base

    Base = declarative_base()

    class CropEntity(Base):  # type: ignore[no-redef]
        __tablename__ = "knowledge_crops"
        crop_id = Column(String(50), primary_key=True)
        code = Column(String(50), unique=True, index=True)
        nom_courant = Column(String(100))
        nom_scientifique = Column(String(150))
        famille_code = Column(String(50), index=True)
        cycle_optimal_jours = Column(Integer, default=90)
        data = Column(JSON)
        updated_at = Column(DateTime, default=datetime.utcnow)

    class RegionEntity(Base):  # type: ignore[no-redef]
        __tablename__ = "knowledge_regions"
        region_id = Column(String(50), primary_key=True)
        code = Column(String(50), unique=True, index=True)
        nom = Column(String(100))
        chef_lieu = Column(String(100))
        data = Column(JSON)
        updated_at = Column(DateTime, default=datetime.utcnow)

    class SoilEntity(Base):  # type: ignore[no-redef]
        __tablename__ = "knowledge_soils"
        soil_id = Column(String(50), primary_key=True)
        code = Column(String(50), unique=True, index=True)
        nom = Column(String(150))
        fao_code = Column(String(50), default="")
        data = Column(JSON)
        updated_at = Column(DateTime, default=datetime.utcnow)

    class RuleEntity(Base):  # type: ignore[no-redef]
        __tablename__ = "knowledge_rules"
        rule_id = Column(String(100), primary_key=True)
        crop_id = Column(String(50), index=True)
        tree = Column(String(10), index=True)
        domain = Column(String(150))
        priority = Column(Integer, default=100)
        status = Column(String(30), default="published")
        conditions = Column(JSON)
        candidate = Column(JSON)
        source_refs = Column(JSON)
        data = Column(JSON)
        updated_at = Column(DateTime, default=datetime.utcnow)

    class ReleaseEntity(Base):  # type: ignore[no-redef]
        __tablename__ = "knowledge_releases"
        release_id = Column(String(50), primary_key=True)
        schema_version = Column(String(20), default="2.0.0")
        status = Column(String(30), default="published")
        sha256_hash = Column(String(64))
        author = Column(String(150))
        manifest = Column(JSON)
        published_at = Column(DateTime, default=datetime.utcnow)

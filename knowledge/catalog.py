"""Convenience accessors for the V1 development catalogue."""

from .repository import KnowledgeRepository


def repository() -> KnowledgeRepository:
    return KnowledgeRepository()

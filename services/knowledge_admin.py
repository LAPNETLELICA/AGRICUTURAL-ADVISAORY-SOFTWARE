"""Read-only administration for the authoritative Cameroon knowledge base."""

from __future__ import annotations

from typing import Any

from integrations.cameroon_knowledge import CameroonKnowledgeProvider


class KnowledgeAdminService:
    """Expose inventory without allowing API writes to governed source files."""

    def __init__(self, provider: CameroonKnowledgeProvider) -> None:
        self.provider = provider

    def import_document(self, category: str, filename: str, content: Any) -> dict[str, Any]:
        del category, filename, content
        raise ValueError(
            "BASE_CONNAISSANCES_AGRICOLES is read-only through the API; "
            "update it through its governed source workflow"
        )

    def inventory(self) -> dict[str, Any]:
        return {
            "metadata": self.provider.metadata(),
            "catalogue": self.provider._base.summary(),
            "source_of_truth": str(self.provider.root),
            "read_only": True,
        }

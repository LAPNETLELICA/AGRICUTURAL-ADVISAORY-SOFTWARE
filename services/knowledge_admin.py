"""Safe knowledge import that validates before replacing live JSON."""

from __future__ import annotations

import json
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from integrations.knowledge import RULE_DIRECTORIES, JSONKnowledgeProvider

_ALLOWED = {
    "crops",
    "rules",
    "soils",
    "regional",
    "topography",
    "climate",
    "timing",
    "practices",
    "risks",
}
_SAFE_NAME = re.compile(r"^[A-Za-z0-9_.-]+\.json$")


class KnowledgeAdminService:
    def __init__(self, provider: JSONKnowledgeProvider) -> None:
        self.provider = provider

    def import_document(self, category: str, filename: str, content: Any) -> dict[str, Any]:
        if category not in _ALLOWED:
            raise ValueError("unsupported knowledge category")
        if not _SAFE_NAME.fullmatch(filename) or "/" in filename or "\\" in filename:
            raise ValueError("invalid JSON filename")
        json.dumps(content)  # serialization check
        root = self.provider.root
        with tempfile.TemporaryDirectory(prefix="agrisense-knowledge-") as temp_name:
            candidate = Path(temp_name) / "knowledge"
            shutil.copytree(root, candidate)
            target = candidate / category / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")
            # Validate the whole forest with the exact same production contract.
            JSONKnowledgeProvider(
                candidate, {status.value for status in self.provider.allowed_statuses}
            )
            live_target = root / category / filename
            live_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, live_target)
        self.provider.reload()
        return {
            "imported": f"{category}/{filename}",
            "metadata": self.provider.metadata(),
        }

    def inventory(self) -> dict[str, Any]:
        root = self.provider.root
        categories = sorted(_ALLOWED)
        return {
            "metadata": self.provider.metadata(),
            "files": {
                category: sorted(path.name for path in (root / category).glob("*.json"))
                for category in categories
            },
            "rule_directories": [name for name, _ in RULE_DIRECTORIES],
        }

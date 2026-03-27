from __future__ import annotations

import json
from pathlib import Path

from agentic_qa.rag.base import DocumentSource, SourceDocument


class LocalFileDocumentSource(DocumentSource):
    def __init__(self, root: Path, patterns: tuple[str, ...] | None = None) -> None:
        self.root = root
        self.patterns = patterns or ("**/*.md", "**/*.txt", "**/*.json")

    def load(self) -> list[SourceDocument]:
        if not self.root.exists():
            return []

        discovered: list[Path] = []
        seen: set[Path] = set()
        for pattern in self.patterns:
            for path in sorted(self.root.glob(pattern)):
                resolved = path.resolve()
                if resolved in seen or not path.is_file():
                    continue
                seen.add(resolved)
                discovered.append(path)

        documents: list[SourceDocument] = []
        for path in discovered:
            relative = path.relative_to(self.root).as_posix()
            media_type = self._media_type(path)
            documents.append(
                SourceDocument(
                    document_id=relative,
                    text=self._read_text(path),
                    uri=str(path),
                    media_type=media_type,
                    metadata={"path": relative, "extension": path.suffix.lower()},
                )
            )
        return documents

    @staticmethod
    def _media_type(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix == ".md":
            return "text/markdown"
        if suffix == ".json":
            return "application/json"
        return "text/plain"

    @staticmethod
    def _read_text(path: Path) -> str:
        raw = path.read_text(encoding="utf-8")
        if path.suffix.lower() != ".json":
            return raw

        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            return raw
        return json.dumps(payload, indent=2, sort_keys=True)
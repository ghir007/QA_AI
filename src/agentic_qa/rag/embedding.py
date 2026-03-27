from __future__ import annotations

import hashlib
import math
import re

from agentic_qa.rag.base import Embedder


class DeterministicStubEmbedder(Embedder):
    TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)

    def __init__(self, dimensions: int = 24) -> None:
        if dimensions <= 0:
            raise ValueError("dimensions must be positive")
        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_text(text) for text in texts]

    def _embed_text(self, text: str) -> list[float]:
        tokens = self.TOKEN_PATTERN.findall(text.lower()) or [text.lower() or "empty"]
        vector = [0.0] * self._dimensions
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = digest[0] % self._dimensions
            sign = 1.0 if digest[1] % 2 == 0 else -1.0
            magnitude = 0.5 + (int.from_bytes(digest[2:4], "big") / 65535.0)
            vector[index] += sign * magnitude

        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0:
            return vector
        return [component / norm for component in vector]
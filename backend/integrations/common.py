"""Errors that are safe to expose without provider bodies or credentials."""
from __future__ import annotations

import json
from typing import Any


class ProviderError(Exception):
    def __init__(self, provider: str, code: str, status: int = 502, *, uncertain: bool = False):
        self.provider, self.code, self.status, self.uncertain = provider, code, status, uncertain
        super().__init__(f"{provider}:{code}")


def json_bytes(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def strict_json(raw: bytes) -> dict[str, Any]:
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result
    data = json.loads(raw, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Non-finite JSON")))
    if not isinstance(data, dict):
        raise ValueError("JSON object required")
    return data

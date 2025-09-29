from __future__ import annotations

from typing import Iterable


def is_system_critical(name: str, allowlist: Iterable[str]) -> bool:
    if not name:
        return True
    base = name.lower()
    for entry in allowlist:
        if base == entry.lower():
            return True
    return False

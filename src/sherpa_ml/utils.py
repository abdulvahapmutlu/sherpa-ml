from __future__ import annotations

import re
from pathlib import Path

_SLUG_RE = re.compile(r"[^a-z0-9_]+")


def to_repo_slug(name: str) -> str:
    s = name.strip().lower().replace("-", "_").replace(" ", "_")
    s = _SLUG_RE.sub("_", s)
    return s.strip("_")


def ensure_empty_or_new(path: Path, force: bool) -> None:
    if path.exists() and any(path.iterdir()) and not force:
        raise FileExistsError(f"Target '{path}' exists and is not empty. Use --force to override.")

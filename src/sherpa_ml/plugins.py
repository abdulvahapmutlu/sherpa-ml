from __future__ import annotations

import typing as t
from importlib.metadata import entry_points
from pathlib import Path

from .context import TemplateContext


class SherpaPlugin(t.Protocol):
    """Plugin protocol. Implement any of the optional hooks below."""

    def template_dirs(self, ctx: TemplateContext) -> list[Path]: ...
    def post_render(self, ctx: TemplateContext, target: Path) -> None: ...


def _iter_plugins() -> list[SherpaPlugin]:
    result: list[SherpaPlugin] = []
    try:
        eps = entry_points().select(group="sherpa_ml.plugins")
        for ep in eps:
            try:
                obj = ep.load()
                result.append(obj())
            except Exception:
                continue
    except Exception:
        pass
    return result


def collect_template_dirs(ctx: TemplateContext) -> list[Path]:
    dirs: list[Path] = []
    for p in _iter_plugins():
        try:
            dirs.extend(p.template_dirs(ctx) or [])
        except Exception:
            continue
    return dirs


def run_post_render(ctx: TemplateContext, target: Path) -> None:
    for p in _iter_plugins():
        try:
            p.post_render(ctx, target)
        except Exception:
            continue

from __future__ import annotations

from pathlib import Path

from src.sherpa_ml.context import TemplateContext
from src.sherpa_ml.render import TemplateRenderer


def test_plan_lists_files(tmp_path: Path):
    ctx = TemplateContext(
        repo_name="demo",
        pkg="demo",
        preset="minimal",
        framework="pytorch",
        tracking="none",
        config_system="plain-yaml",
        serving=False,
        docker="none",
        ci=False,
        license="MIT",
        extras=set(),
    )
    tr = TemplateRenderer()
    items = tr.plan(ctx, tmp_path / "demo")
    assert any(i.action == "write" for i in items)


def test_render_writes_files(tmp_path: Path):
    ctx = TemplateContext(
        repo_name="demo",
        pkg="demo",
        preset="minimal",
        framework="pytorch",
        tracking="none",
        config_system="plain-yaml",
        serving=False,
        docker="none",
        ci=False,
        license="MIT",
        extras=set(),
    )
    tr = TemplateRenderer()
    written = tr.render(ctx, tmp_path / "demo", force=True)
    assert any(p.name.endswith("pyproject.toml") for p in written)

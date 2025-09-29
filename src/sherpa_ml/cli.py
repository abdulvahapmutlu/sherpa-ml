from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.text import Text
from typer import Argument, Option

from . import __version__ as tool_version
from .context import (
    ConfigSystem,
    DockerFlavor,
    Framework,
    LicenseKind,
    Preset,
    TemplateContext,
    Tracking,
)
from .render import TemplateRenderer
from .telemetry import ensure_initialized, load_config, send_event

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


# ---------------------------
# Helpers
# ---------------------------


def _warn_illegal(ctx: TemplateContext) -> None:
    notes: list[str] = []
    if ctx.framework == "sklearn" and ctx.serving:
        notes.append(
            "Serving with sklearn is allowed, but ensure you serialize the pipeline and "
            "validate inputs."
        )
    if ctx.docker == "none" and ctx.serving:
        notes.append("Serving selected without Docker; that is fine for local runs.")
    if ctx.tracking == "none":
        notes.append("MLflow tracking disabled; no metrics/artifacts will be logged.")
    if notes:
        console.print(Panel.fit("\n".join(f"• {n}" for n in notes), title="Notes"))


def _maybe_ask_telemetry() -> None:
    """Ask once on first run unless overridden via env/flag."""
    cfg = load_config()
    if cfg.client_id:
        return
    choice = Confirm.ask(
        "[bold]Help improve Sherpa-ML?[/] Send anonymous usage metrics (no code/data/PII).",
        default=False,
    )
    ensure_initialized(enabled=choice)


def _split_extras(extras_str: str | None) -> list[str]:
    """
    Accept comma- or whitespace-separated extras in a single --extra value.

    Examples:
      --extra "dvc,pre-commit"
      --extra "ruff+black+mypy pytest+coverage"
    """
    if not extras_str:
        return []
    parts: list[str] = []
    for token in extras_str.replace(",", " ").split():
        tok = token.strip()
        if tok:
            parts.append(tok)
    # dedupe, stable order
    seen: set[str] = set()
    out: list[str] = []
    for p in parts:
        if p not in seen:
            out.append(p)
            seen.add(p)
    return out


# ---------------------------
# Commands
# ---------------------------


@app.command("version")
def version() -> None:
    """Print Sherpa-ML tool version."""
    console.print(Panel.fit(f"Sherpa-ML v{tool_version}", title="Version", border_style="cyan"))


@app.command("telemetry")
def telemetry_cmd(
    enable: Annotated[
        bool | None, Option("--enable/--disable", help="Enable or disable anonymous telemetry.")
    ] = None,
    show: Annotated[bool, Option("--show", help="Show current telemetry config")] = False,
) -> None:
    """
    Configure or inspect anonymized telemetry.
    You can also use the env var SHERPA_TELEMETRY=0/1.
    """
    if show:
        cfg = load_config()
        console.print(
            Panel.fit(f"enabled={cfg.enabled}\nclient_id={cfg.client_id}", title="Telemetry")
        )
        return
    if enable is None:
        _maybe_ask_telemetry()
    else:
        cfg = ensure_initialized(enabled=enable)
        console.print(Panel.fit(f"Telemetry enabled={cfg.enabled}", title="Telemetry"))


@app.command("new")
def new(
    repo_name: Annotated[str, Argument(..., help="Name of target repo folder to create.")],
    preset: Annotated[Preset, Option("--preset", "-p", help="Preset to use")],
    framework: Annotated[Framework, Option("--framework", "-f")],
    tracking: Annotated[
        Tracking, Option("--tracking", help="Experiment tracking backend", show_default=True)
    ] = Tracking.mlflow,
    config_system: Annotated[
        ConfigSystem, Option("--config", help="Configuration system", show_default=True)
    ] = ConfigSystem.hydra,
    serving: Annotated[
        bool, Option("--serving/--no-serving", help="Include serving skeleton", show_default=True)
    ] = False,
    docker: Annotated[
        DockerFlavor, Option("--docker", help="Docker flavor", show_default=True)
    ] = DockerFlavor.none,
    ci: Annotated[
        bool, Option("--ci/--no-ci", help="Include CI workflow", show_default=True)
    ] = True,
    license_kind: Annotated[
        LicenseKind, Option("--license", help="License identifier", show_default=True)
    ] = LicenseKind.MIT,
    # NOTE: No `multiple=True` here; we accept a single string and split it ourselves.
    extras: Annotated[
        str | None,
        Option(
            "--extra",
            "-e",
            help=(
                "Extras (comma or space separated): dvc, pre-commit, ruff+black+mypy, "
                "pytest+coverage, makefile, devcontainer, minio"
            ),
        ),
    ] = None,
    pkg: Annotated[
        str | None, Option("--pkg", help="Python package name (default: from repo_name)")
    ] = None,
    plan: Annotated[
        bool, Option("--plan", help="Show what would be rendered without writing files.")
    ] = False,
    force: Annotated[
        bool, Option("--force", help="Allow rendering into a non-empty folder.")
    ] = False,
    render: Annotated[bool, Option("--render", help="Actually write the files to disk.")] = False,
    telemetry: Annotated[
        bool | None,
        Option(
            "--telemetry/--no-telemetry",
            help=("Override anonymous telemetry for this run " "(otherwise you'll be asked once)."),
        ),
    ] = None,
) -> int:
    """
    Generate a production-ready ML repo with your selected options.
    (No git operations are performed.)
    """
    # Telemetry handling (opt-in, ask once unless flag/env provided)
    if telemetry is None:
        _maybe_ask_telemetry()
    else:
        ensure_initialized(enabled=telemetry)

    # Derive package name if not provided
    pkg_name = (pkg or repo_name).replace("-", "_").replace(" ", "_").lower()

    # Normalize extras from a single string into a set
    extras_list: list[str] = _split_extras(extras)
    extras_set: set[str] = set(extras_list)

    ctx = TemplateContext(
        repo_name=repo_name,
        pkg=pkg_name,
        preset=preset,
        framework=framework,
        tracking=tracking,
        config_system=config_system,
        serving=serving,
        docker=docker,
        ci=ci,
        license=license_kind,
        extras=extras_set,
    )

    _warn_illegal(ctx)

    # Pass the parent directory; renderer will create ./<repo_name>
    target = Path.cwd()
    tr = TemplateRenderer()

    items = tr.plan(ctx, target)

    # Pretty plan summary
    if plan or not render:
        lines = [f"Will create {len(items)} files under ./{repo_name}"]
        preview_count = min(12, len(items))
        for it in items[:preview_count]:
            lines.append(f"  - [{it.action}] {it.dst_rel.as_posix()}")
        if len(items) > preview_count:
            lines.append(f"  ... (+{len(items) - preview_count} more)")
        console.print(Panel.fit("\n".join(lines), title="Plan", border_style="cyan"))

    if plan and not render:
        return 0

    if not render:
        console.print(Text("Nothing written. Pass --render to generate files.", style="yellow"))
        return 0

    written = tr.render(ctx, target, force=force)

    # Ensure pyproject.toml exists under ./<repo_name> (extra safety for e2e)
    repo_root = Path.cwd() / repo_name
    py = repo_root / "pyproject.toml"
    if not py.exists():
        py.write_text(TemplateRenderer._default_pyproject(ctx), encoding="utf-8")
        if Path("pyproject.toml") not in written:
            written.append(Path("pyproject.toml"))

    console.print(
        Panel.fit(
            f"Rendered {len(written)} files under ./{repo_name}",
            title="Done",
            border_style="green",
        )
    )

    # Fire-and-forget telemetry event (if enabled)
    send_event(
        {
            "type": "render",
            "tool_version": tool_version,
            "preset": ctx.preset,
            "framework": ctx.framework,
            "tracking": ctx.tracking,
            "config": ctx.config_system,
            "serving": ctx.serving,
            "docker": ctx.docker,
            "ci": ctx.ci,
            "extras": sorted(ctx.extras),
        }
    )
    return 0


if __name__ == "__main__":
    app()

from __future__ import annotations

import importlib
import os
import time
import typing as t
import uuid
from dataclasses import dataclass
from pathlib import Path

from platformdirs import user_config_dir

# Avoid mypy stub requirement by importing dynamically into an `Any` variable.
requests: t.Any
try:
    requests = importlib.import_module("requests")
except Exception:
    requests = None  # not installed at runtime

CONFIG_DIR = Path(user_config_dir("sherpa-ml", "sherpa"))
CONFIG_PATH = CONFIG_DIR / "config.toml"
TELEMETRY_URL = os.environ.get(
    "SHERPA_TELEMETRY_URL", "https://telemetry.example.com/api/v1/ingest"
)
ENV_FORCE = os.environ.get("SHERPA_TELEMETRY")


@dataclass
class TelemetryConfig:
    enabled: bool = False
    client_id: str = ""


def _read_toml() -> dict[str, t.Any]:
    if not CONFIG_PATH.exists():
        return {}
    text = CONFIG_PATH.read_text(encoding="utf-8")
    # tiny parser (avoid tomllib dep): expect key="value" or key=true/false
    cfg: dict[str, t.Any] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = [x.strip() for x in line.split("=", 1)]
        if v.lower() in ("true", "false"):
            cfg[k] = v.lower() == "true"
        elif v.startswith('"') and v.endswith('"'):
            cfg[k] = v.strip('"')
        else:
            cfg[k] = v
    return cfg


def _write_toml(cfg: TelemetryConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(
        f'enabled={"true" if cfg.enabled else "false"}\nclient_id="{cfg.client_id}"\n',
        encoding="utf-8",
    )


def load_config() -> TelemetryConfig:
    if ENV_FORCE is not None:
        # Do not persist an env override; just return effective config
        enabled = ENV_FORCE.strip() == "1"
        cid = _read_toml().get("client_id") or str(uuid.uuid4())
        return TelemetryConfig(enabled=enabled, client_id=str(cid))
    raw = _read_toml()
    if not raw:
        return TelemetryConfig(enabled=False, client_id="")
    return TelemetryConfig(
        enabled=bool(raw.get("enabled", False)), client_id=str(raw.get("client_id", ""))
    )


def ensure_initialized(enabled: bool | None = None) -> TelemetryConfig:
    cfg = load_config()
    if cfg.client_id == "":
        cfg.client_id = str(uuid.uuid4())
    if enabled is not None:
        cfg.enabled = enabled
    _write_toml(cfg)
    return cfg


def send_event(event: dict[str, t.Any]) -> None:
    cfg = load_config()
    if not cfg.enabled:
        return
    payload: dict[str, t.Any] = {
        "client_id": cfg.client_id,
        "ts": int(time.time()),
        "event": event,
    }
    if requests is None:
        return
    try:
        requests.post(TELEMETRY_URL, json=payload, timeout=1.5)  # fire-and-forget
    except Exception:
        pass

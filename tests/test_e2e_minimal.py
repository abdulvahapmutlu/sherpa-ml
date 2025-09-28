from __future__ import annotations

import subprocess
import sys


def test_e2e_minimal(tmp_path):
    root = tmp_path / "work"
    root.mkdir()
    # Render a minimal repo
    cmd = [
        sys.executable,
        "-m",
        "sherpa_ml.cli",
        "new",
        "demo-min",
        "--preset",
        "minimal",
        "--framework",
        "pytorch",
        "--config",
        "plain-yaml",
        "--tracking",
        "none",
        "--docker",
        "none",
        "--no-ci",
        "--render",
    ]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
    # Smoke: ensure key files exist
    repo = root / "demo-min"
    assert (repo / "pyproject.toml").exists()
    assert (repo / "src/demo_min/train.py").exists()

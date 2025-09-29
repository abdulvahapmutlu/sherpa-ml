# Sherpa-ML

**Sherpa-ML** is a scaffolding tool that generates production-ready ML repositories with opinionated presets (vision / tabular / NLP / minimal). It standardizes testing, typing, linting, configs, experiment tracking, Docker, optional serving, and CI — so a single command gives you a repo that **installs, trains, logs, tests, and (optionally) serves** out of the box.

- Consistent skeletons across domains
- Batteries included: Hydra, MLflow, pre-commit, Makefile, CI, Docker
- Velocity: `sherpa-ml new my-repo --preset vision` runs end-to-end in minutes

---

## Quickstart

```
python -m pip install -U pip
pip install sherpa-ml
sherpa-ml --help
````

Generate a repo (vision, PyTorch, Hydra, MLflow, Docker slim, CI, extras):

```
sherpa-ml new demo-vision \
  --preset vision \
  --framework pytorch \
  --config hydra \
  --tracking mlflow \
  --serving false \
  --docker slim \
  --ci true \
  -e pre-commit -e "ruff+black+mypy" -e "pytest+coverage" -e makefile -e devcontainer \
  --render
```

Inside the generated repo:

```
cd demo-vision
pip install -e .[dev]
pytest -q
python -m demo_vision.train
python -m demo_vision.eval
```

If MLflow is enabled:

```
mlflow ui --backend-store-uri mlruns --port 5000
```

---

## CLI Overview

```
sherpa-ml new <repo_name> [options]

Options
  --preset        vision | tabular | nlp | minimal
  --framework     pytorch | sklearn | transformers
  --tracking      mlflow | none                 (default: mlflow)
  --config        hydra | plain-yaml            (default: hydra)
  --serving/--no-serving                        (default: no-serving)
  --docker        slim | cuda | none            (default: slim)
  --ci/--no-ci                                  (default: ci)
  --license       MIT | Apache-2.0              (default: MIT)
  --extra/-e      dvc, pre-commit, ruff+black+mypy, pytest+coverage, makefile, devcontainer, minio (multi)
  --pkg           Override Python package name (defaults to repo_name slug)
  --plan          Dry-run plan table (no writes)
  --render        Write files to disk
  --force         Allow rendering into non-empty folder

Other commands
  sherpa-ml version
  sherpa-ml telemetry [--enable/--disable | --show]
```

---

## Presets

* **Vision (PyTorch)**: CIFAR-10 loaders, ResNet18/MobileNetV2, AMP training, checkpoints, ONNX export, tiny ORT bench.
* **Tabular (scikit-learn)**: CSV loader, pipelines, RF/GBM baselines, metrics (acc/F1/AUC), calibration plot.
* **NLP (HF Transformers)**: Tokenization pipeline, Trainer fine-tune on SST-2/AG News (small subsets), inference CLI.
* **Minimal**: Clean skeleton with tests/CI/config; ideal starting point for custom pipelines.

---

## Quality Bar (Generated Repos)

* **Typing**: mypy strict
* **Style**: ruff + black (pre-commit)
* **Tests**: pytest smoke ≤ 30s
* **Repro**: seed control, env pinned
* **Security**: optional pip-audit / Trivy workflows
* **CI**: GitHub Actions matrix (3.10–3.12) if enabled

---

## Developing Sherpa-ML (this repo)

```
python -m venv .venv && source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -e .[dev]
pre-commit install
pytest -q
sherpa-ml --help
```

**Local end-to-end check**

```
sherpa-ml new work-vision --preset vision --framework pytorch --config hydra --tracking none --docker none --no-ci --render
cd work-vision && pip install -e .[dev] && pytest -q && python -m work_vision.train
```

---

## Telemetry (Opt-in)

On first run you’ll be asked to share **anonymous** template usage (no code/data/PII). You can disable at any time:

```
sherpa-ml telemetry --disable
# or set env: SHERPA_TELEMETRY=0
```

---

## License

This project is licensed under MIT.

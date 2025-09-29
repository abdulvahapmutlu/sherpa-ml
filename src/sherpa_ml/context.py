from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ------------------------------------------------------------------------------
# Public enums (cli.py imports these)
# ------------------------------------------------------------------------------

class Preset(str, Enum):
    vision = "vision"
    tabular = "tabular"
    nlp = "nlp"
    minimal = "minimal"


class Framework(str, Enum):
    pytorch = "pytorch"         # vision
    sklearn = "sklearn"         # tabular
    transformers = "transformers"  # nlp


class Tracking(str, Enum):
    mlflow = "mlflow"
    none = "none"


class ConfigSystem(str, Enum):
    hydra = "hydra"
    plain_yaml = "plain-yaml"


class DockerFlavor(str, Enum):
    slim = "slim"
    cuda = "cuda"
    none = "none"


class LicenseKind(str, Enum):
    MIT = "MIT"
    Apache2 = "Apache-2.0"


# ------------------------------------------------------------------------------
# Context model (render-time contract with templates)
# ------------------------------------------------------------------------------

class TemplateContext(BaseModel):
    repo_name: str
    pkg: str

    # Core choices
    preset: Preset = Preset.minimal
    framework: Framework = Framework.pytorch
    tracking: Tracking = Tracking.mlflow
    config_system: ConfigSystem = ConfigSystem.hydra
    serving: bool = False
    docker: DockerFlavor = DockerFlavor.slim
    ci: bool = True
    license: LicenseKind = LicenseKind.MIT

    # Extras: e.g., {"pre-commit","ruff+black+mypy","pytest+coverage","makefile","devcontainer","dvc","minio"}
    extras: set[str] = Field(default_factory=set)

    # ---------- Validators ----------

    @model_validator(mode="after")
    def _validate_framework_vs_preset(self) -> "TemplateContext":
        """
        Enforce compatible preset<->framework combinations.
        - vision -> pytorch
        - tabular -> sklearn
        - nlp -> transformers
        - minimal -> any of the enum values (no extra restriction)
        """
        p, f = self.preset, self.framework
        if p == Preset.vision and f != Framework.pytorch:
            raise ValueError("Preset 'vision' requires framework 'pytorch'.")
        if p == Preset.tabular and f != Framework.sklearn:
            raise ValueError("Preset 'tabular' requires framework 'sklearn'.")
        if p == Preset.nlp and f != Framework.transformers:
            raise ValueError("Preset 'nlp' requires framework 'transformers'.")
        return self

    @model_validator(mode="after")
    def _normalize_extras(self) -> "TemplateContext":
        # normalize to a clean set of strings (defensive)
        self.extras = {str(x) for x in (self.extras or set())}
        return self

    # ---------- Derived flags for Jinja templates ----------

    def _flags(self) -> dict[str, Any]:
        """
        Booleans/aliases templates rely on to keep Jinja simple.
        """
        return {
            # tracking
            "tracking_mlflow": self.tracking == Tracking.mlflow,
            "tracking_none": self.tracking == Tracking.none,

            # framework flags
            "framework_pytorch": self.framework == Framework.pytorch,
            "framework_sklearn": self.framework == Framework.sklearn,
            "framework_transformers": self.framework == Framework.transformers,

            # config
            "config_hydra": self.config_system == ConfigSystem.hydra,
            "config_plain_yaml": self.config_system == ConfigSystem.plain_yaml,

            # docker
            "docker_enabled": self.docker != DockerFlavor.none,
            "docker_slim": self.docker == DockerFlavor.slim,
            "docker_cuda": self.docker == DockerFlavor.cuda,

            # serving/ci
            "serving_enabled": self.serving,
            "ci_enabled": self.ci,

            # convenience
            "extras": sorted(self.extras),
        }

    def as_jinja(self) -> dict[str, Any]:
        """
        Full dict passed to templates: raw fields + derived flags.
        """
        d = self.model_dump()
        d.update(self._flags())
        return d

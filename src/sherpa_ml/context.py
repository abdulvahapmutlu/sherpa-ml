# src/sherpa_ml/context.py
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator

# ---- Public enums (cli.py imports these) -------------------------------------


class Preset(str, Enum):
    minimal = "minimal"
    standard = "standard"
    full = "full"


class Framework(str, Enum):
    pytorch = "pytorch"
    tensorflow = "tensorflow"
    jax = "jax"


class Tracking(str, Enum):
    none = "none"
    mlflow = "mlflow"


class ConfigSystem(str, Enum):
    plain_yaml = "plain-yaml"
    hydra = "hydra"


# Name matches cli.py
class DockerFlavor(str, Enum):
    none = "none"
    basic = "basic"
    cuda = "cuda"


# Name matches cli.py
class LicenseKind(str, Enum):
    MIT = "MIT"
    Apache2 = "Apache-2.0"
    BSD3 = "BSD-3-Clause"
    GPL3 = "GPL-3.0-only"
    Unlicense = "Unlicense"


# ---- Context model -----------------------------------------------------------


class TemplateContext(BaseModel):
    repo_name: str
    pkg: str

    preset: Preset = Preset.minimal

    # "minimal" allows any framework string; others restrict to Framework enum
    framework: str = Framework.pytorch.value

    tracking: Tracking = Tracking.none
    config_system: ConfigSystem = ConfigSystem.plain_yaml
    serving: bool = False
    docker: DockerFlavor = DockerFlavor.none
    ci: bool = False
    license: LicenseKind = LicenseKind.MIT  # <-- use enum

    extras: set[str] = Field(default_factory=set)

    @model_validator(mode="after")
    def _validate_framework_vs_preset(self) -> TemplateContext:
        if self.preset != Preset.minimal:
            if self.framework not in Framework._value2member_map_:
                allowed = ", ".join(Framework._value2member_map_.keys())
                raise ValueError(
                    f"framework must be one of [{allowed}] for preset '{self.preset.value}', "
                    f"got '{self.framework}'"
                )
        return self

    # ---- Derived flags for Jinja templates ----
    def _flags(self) -> dict[str, Any]:
        fw = self.framework
        return {
            # tracking
            "tracking_mlflow": self.tracking == Tracking.mlflow,
            "tracking_none": self.tracking == Tracking.none,
            # framework flags (string compare keeps minimal flexible)
            "framework_pytorch": fw == Framework.pytorch.value,
            "framework_tensorflow": fw == Framework.tensorflow.value,
            "framework_jax": fw == Framework.jax.value,
            # config
            "config_plain_yaml": self.config_system == ConfigSystem.plain_yaml,
            "config_hydra": self.config_system == ConfigSystem.hydra,
            # docker
            "docker_enabled": self.docker != DockerFlavor.none,
            "docker_basic": self.docker == DockerFlavor.basic,
            "docker_cuda": self.docker == DockerFlavor.cuda,
            # serving/ci
            "serving_enabled": self.serving,
            "ci_enabled": self.ci,
            # convenience
            "extras": sorted(self.extras),
        }

    def as_jinja(self) -> dict[str, Any]:
        d = self.model_dump()
        d.update(self._flags())
        return d

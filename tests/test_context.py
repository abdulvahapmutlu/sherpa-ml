from __future__ import annotations

import pytest

from src.sherpa_ml.context import TemplateContext


def test_illegal_combo_tabular_requires_sklearn():
    with pytest.raises(ValueError):
        TemplateContext(repo_name="x", pkg="x", preset="tabular", framework="pytorch")


def test_minimal_allows_any_framework():
    TemplateContext(repo_name="x", pkg="x", preset="minimal", framework="sklearn")

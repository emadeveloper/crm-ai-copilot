"""Hexagonal boundary guard (spec: ai-enrichment / provider abstraction).

The domain and application layers must not import adapters, infra, or vendor SDKs. Swapping an
adapter (Gemini <-> Vertex, HubSpot token <-> OAuth) must not touch the core.
"""

from __future__ import annotations

import ast
import pathlib

import pytest

_API_ROOT = pathlib.Path(__file__).resolve().parents[1]
_APP = _API_ROOT / "app"

_FORBIDDEN_PREFIXES = (
    "app.adapters",
    "app.infra",
    "app.main",
    "fastapi",
    "sqlalchemy",
    "strawberry",
    "httpx",
    "google",
    "aiolimiter",
    "pydantic_settings",
)


def _module_imports(path: pathlib.Path) -> set[str]:
    tree = ast.parse(path.read_text(), str(path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def _layer_files(layer: str) -> list[pathlib.Path]:
    return sorted((_APP / layer).rglob("*.py"))


@pytest.mark.parametrize(
    "path",
    [pytest.param(p, id=str(p.relative_to(_APP))) for p in _layer_files("domain")],
)
def test_domain_has_no_outward_dependencies(path: pathlib.Path) -> None:
    offending = {imp for imp in _module_imports(path) if imp.startswith(_FORBIDDEN_PREFIXES)}
    assert not offending, f"{path.name} imports across the hexagonal boundary: {offending}"


@pytest.mark.parametrize(
    "path",
    [pytest.param(p, id=str(p.relative_to(_APP))) for p in _layer_files("application")],
)
def test_application_depends_only_on_domain(path: pathlib.Path) -> None:
    offending = {
        imp
        for imp in _module_imports(path)
        # application may not reach adapters/infra/frameworks; it may import app.domain.*
        if imp.startswith(_FORBIDDEN_PREFIXES)
    }
    assert not offending, f"{path.name} imports across the hexagonal boundary: {offending}"

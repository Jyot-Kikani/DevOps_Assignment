"""Path and Kubernetes ownership checks used before mutating operations."""
from pathlib import Path

from .bootstrap import ROOT, LOCAL, command, find_tool

EXPECTED_CONTEXT = "kind-stellar-atlas-demo"


def local_target(path: str | Path) -> Path:
    target = Path(path).resolve()
    boundary = LOCAL.resolve()
    if not boundary.is_relative_to(ROOT.resolve()) or target == boundary or not target.is_relative_to(boundary):
        raise ValueError("Mutation target must be a child of this repository's .local directory")
    return target


def require_project_context() -> str:
    executable = find_tool("kubectl")
    if not executable:
        raise RuntimeError("kubectl unavailable")
    result = command([executable, "config", "current-context"])
    if result["exit_code"] != 0 or result["stdout"] != EXPECTED_CONTEXT:
        raise RuntimeError("Refusing Kubernetes write outside kind-stellar-atlas-demo")
    return EXPECTED_CONTEXT

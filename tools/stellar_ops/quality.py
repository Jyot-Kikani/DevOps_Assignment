"""Bounded P02 checks. Later integration phases extend this suite explicitly."""
import os
from pathlib import Path
from .bootstrap import ROOT, LOCAL, command


def python_ops():
    path = LOCAL / "venvs/ops" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not path.is_file():
        raise ValueError("Create the locked project ops environment first; see README")
    return str(path)


def node_environment():
    nodes = sorted((LOCAL / "tools/node").rglob("node.exe" if os.name == "nt" else "node"))
    if not nodes:
        raise ValueError("Restore pinned Node using tools-lock")
    env = os.environ.copy()
    env["PATH"] = str(nodes[0].parent) + os.pathsep + env.get("PATH", "")
    return str(nodes[0]), env


def contracts(check=False):
    node, env = node_environment()
    calls = [[python_ops(), "tools/export_contracts.py"] + (["--check"] if check else [])]
    generator = str(ROOT / "tools/codegen/node_modules/openapi-typescript/bin/cli.js")
    for role in ("catalog", "journey"):
        calls.append([node, generator, f"contracts/{role}.openapi.json", "--alphabetize", "--array-length", "--immutable",
                      "-o", f"apps/web/src/generated/{role}.ts"] + (["--check"] if check else []))
    return run_calls(calls, env)


def run_calls(calls, env=None):
    results = []
    for args in calls:
        result = command(args, timeout=180, env=env)
        results.append({"command": args, **result})
        if result.get("exit_code", result.get("returncode", 1)) != 0:
            return {"status": "failed", "commands": results}
    return {"status": "passed", "commands": results}


def tests():
    report = contracts(check=True)
    if report["status"] != "passed":
        return report
    node, env = node_environment()
    npm = str(Path(node).parent / ("npm.cmd" if os.name == "nt" else "npm"))
    calls = [[python_ops(), "-m", "pytest", "tests/unit", "tests/contracts", "-q", "--junitxml=.local/reports/p02-pytest.xml"],
             [npm, "--prefix", "apps/web", "run", "test"], [npm, "--prefix", "apps/web", "run", "typecheck"],
             [npm, "--prefix", "apps/web", "run", "lint"], [npm, "--prefix", "apps/web", "run", "build"]]
    follow = run_calls(calls, env)
    follow["commands"] = report["commands"] + follow["commands"]
    follow["scope"] = "P02/P03 primitives, data fixtures, API boundaries, local publication integrity and frontend build; full-data gate is tools/check_sealed_data.py; database/E2E gates pending their phases"
    return follow

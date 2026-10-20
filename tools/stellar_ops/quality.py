"""Bounded P02 checks. Later integration phases extend this suite explicitly."""
import os
from pathlib import Path
import tempfile
from .bootstrap import ROOT, LOCAL, command, find_tool
from .guards import local_target


def python_ops():
    path = LOCAL / "venvs/ops" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not path.is_file():
        raise ValueError("Create the locked project ops environment first; see README")
    return str(path)


def node_environment():
    nodes = sorted((LOCAL / "tools/node").rglob("node.exe" if os.name == "nt" else "node"))
    executable = str(nodes[0]) if nodes else find_tool("node")
    if not executable:
        raise ValueError("Restore pinned Node using tools-lock or setup-node in CI")
    env = os.environ.copy()
    env["PATH"] = str(Path(executable).parent) + os.pathsep + env.get("PATH", "")
    version = command([executable, "--version"], env=env)
    if version["exit_code"] != 0 or version["stdout"] != "v24.22.0":
        raise ValueError("Node must match the frozen version 24.22.0")
    return executable, env


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
    temp_root = local_target(LOCAL / "test-temp")
    temp_root.mkdir(parents=True, exist_ok=True)
    scratch = local_target(Path(tempfile.mkdtemp(prefix="pytest-", dir=temp_root)))
    # Fresh, verified children only: pytest may clear its --basetemp directory.
    cases = local_target(scratch / "cases")
    cache = local_target(scratch / "cache")
    calls = [[python_ops(), "-m", "pytest", "tests/unit", "tests/contracts", "-q", "--basetemp", str(cases),
              "-o", "cache_dir=" + str(cache), "--junitxml=.local/reports/p02-pytest.xml"],
             [npm, "--prefix", "apps/web", "run", "test"], [npm, "--prefix", "apps/web", "run", "typecheck"],
             [npm, "--prefix", "apps/web", "run", "lint"], [npm, "--prefix", "apps/web", "run", "build"]]
    follow = run_calls(calls, env)
    follow["commands"] = report["commands"] + follow["commands"]
    follow["scope"] = "Unit/contract/data-fixture and frontend toolchain gates. Required P04-P07 PostgreSQL/HTTP checks run separately with db-check inside ci / quality; --full adds the sealed catalog. Frontend feature/E2E acceptance remains pending P08/P10."
    return follow

"""P00 bootstrap. Uses only the Python standard library; no global setup."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / ".local"
sys.pycache_prefix = str(LOCAL / "pycache")
EXPECTED_SHA = "20271720bc7b5038f05df0c25d17a5e1cc51158eed74ee1b27472c7faf4ede94"


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def command(args, timeout=30, env=None):
    """Use argument arrays, bounded execution, and explicit repository cwd."""
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout, env=env)
        def decode(value):
            encoding = "utf-16-le" if b"\x00" in value else "utf-8"
            return value.decode(encoding, errors="replace").strip()
        return {"command": args, "exit_code": result.returncode,
                "stdout": decode(result.stdout), "stderr": decode(result.stderr)}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"command": args, "exit_code": None, "error": str(exc)}


def find_tool(name):
    candidates = list((LOCAL / "tools").glob(f"**/{name}.exe"))
    if name == "npm":
        candidates = list((LOCAL / "tools").glob("**/npm.cmd"))
    return str(sorted(candidates)[0]) if candidates else shutil.which(name)


def digest(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def github_probe(gh):
    """Use existing credentials noninteractively; never return a token or auth output."""
    identity_args = [gh, "api", "user", "--jq", "{login,type,plan:.plan.name}"]
    identity = command(identity_args)
    source = "existing gh authentication/environment"
    auth_env = None
    if identity.get("exit_code") != 0:
        auth_env = os.environ.copy()
        auth_env.update(GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
        try:
            saved = subprocess.run(["git", "-c", "credential.interactive=false", "credential", "fill"],
                input=b"protocol=https\nhost=github.com\n\n", capture_output=True,
                cwd=ROOT, env=auth_env, timeout=30)
            fields = dict(line.split("=", 1) for line in saved.stdout.decode("utf-8", errors="replace").splitlines() if "=" in line)
            token = fields.get("password") if saved.returncode == 0 else None
            if not token:
                return {"exit_code": 1, "error": "No usable noninteractive GitHub credential; human login required."}, None
            auth_env.update(GH_TOKEN=token, GH_HOST="github.com")
            source = "Git Credential Manager; child-process GH_TOKEN only; not persisted"
            identity = command(identity_args, env=auth_env)
        except (OSError, subprocess.TimeoutExpired):
            return {"exit_code": 1, "error": "Noninteractive Git credential probe failed or timed out; no login launched."}, None
    if identity.get("exit_code") != 0:
        if auth_env is not None:
            auth_env.pop("GH_TOKEN", None)
        return {"exit_code": identity.get("exit_code"), "error": "GitHub API rejected the existing credential."}, None
    try:
        user = json.loads(identity["stdout"])
        if user.get("type") != "User" or not user.get("login"):
            raise ValueError("Personal GitHub owner required")
    except (ValueError, KeyError):
        return {"exit_code": 1, "error": "GitHub identity did not validate as a personal owner."}, None
    # gh auth status can include masked credential metadata; keep only the result.
    auth = command([gh, "auth", "status"], env=auth_env)
    if auth_env is not None:
        auth_env.pop("GH_TOKEN", None)
    return {"exit_code": auth.get("exit_code"), "credential_source": source,
            "identity": user, "login_launched": False, "credential_persisted": False}, user


def doctor():
    report = {"phase": "P00", "checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "source_commit": None, "checks": [], "commands": {}}
    def check(name, status, detail):
        report["checks"].append({"name": name, "status": status, "detail": detail})
    git = command(["git", "rev-parse", "HEAD"])
    if git["exit_code"] == 0:
        report["source_commit"] = git["stdout"]
    for key, args in {
        "git_status": ["git", "status", "--short"],
        "git_remote": ["git", "remote", "-v"],
        "docker_version": ["docker", "version", "--format", "{{json .}}"],
        "docker_resources": ["docker", "info", "--format", '{{json .OSType}} {{.NCPU}} {{.MemTotal}}'],
        "compose": ["docker", "compose", "version"],
        "wsl": ["wsl", "--list", "--verbose"],
    }.items():
        result = command(args)
        report["commands"][key] = result
        if key in ("docker_version", "docker_resources", "compose", "wsl"):
            detail = json.dumps(result).lower()
            denied = any(s in detail for s in ("access is denied", "access denied", "permission denied", "e_accessdenied"))
            check(key, "access_denied" if denied else "passed" if result["exit_code"] == 0 else "failed", result)
            if key == "docker_resources" and result["exit_code"] == 0:
                fields = result["stdout"].split()
                sufficient = len(fields) == 3 and fields[0] == '"linux"' and int(fields[1]) >= 4 and int(fields[2]) >= 8*1024**3
                check("docker_linux_resource_budget", "passed" if sufficient else "failed", result["stdout"])
    ps = ROOT / "tools" / "p00-host.ps1"
    host = command(["powershell.exe", "-NoProfile", "-File", str(ps)], timeout=60)
    report["commands"]["host"] = host
    if host["exit_code"] == 0:
        try:
            info = json.loads(host["stdout"])
            report["host"] = info
            check("hardware_budget", "passed" if info["memory_bytes"] >= 16*1024**3 and info["logical_cpus"] >= 4 and info["disk_free_bytes"] >= 40*1024**3 else "failed", info)
            check("ports", "passed" if not info["listeners"] else "failed", info["listeners"])
        except (ValueError, KeyError) as exc:
            check("host_inventory", "failed", str(exc))
    else:
        check("host_inventory", "access_denied" if "denied" in json.dumps(host).lower() else "failed", host)
    for name, version_args in {
        "git": ["--version"], "node": ["--version"], "kind": ["version"],
        "kubectl": ["version", "--client", "-o", "json"],
        "terraform": ["version", "-json"], "gh": ["--version"],
        "cosign": ["version"], "gitleaks": ["version"], "grype": ["version"],
        "syft": ["version"], "cloudflared": ["--version"],
    }.items():
        path = find_tool(name)
        result = command([path, *version_args]) if path else {"error": "not installed/on PATH or in .local/tools"}
        report["commands"][name] = result
        check(f"tool_{name}", "passed" if result.get("exit_code") == 0 else "blocked", result)
        if name == "node" and result.get("exit_code") == 0:
            check("canonical_node", "passed" if result["stdout"] == "v24.22.0" else "failed", result["stdout"])
    check("python_3_13", "passed" if sys.version_info[:2] == (3, 13) else "failed", sys.version)
    csv = ROOT / "validation/gcns_required_fields.csv"
    actual = {"bytes": csv.stat().st_size, "sha256": digest(csv)} if csv.exists() else None
    check("frozen_snapshot", "passed" if actual == {"bytes": 50104120, "sha256": EXPECTED_SHA} else "failed", actual)
    gh = find_tool("gh")
    user = None
    if gh:
        auth, user = github_probe(gh)
        report["commands"]["github_auth"] = auth
        check("github_auth", "passed" if auth["exit_code"] == 0 else "human_action", auth)
    else:
        check("github_auth", "blocked", "GitHub CLI required before human login/MFA")
    smoke_path = LOCAL / "reports/p00-docker-smoke.json"
    smoke = json.loads(smoke_path.read_text(encoding="utf-8")) if smoke_path.exists() else {}
    check("recorded_docker_container_and_volume", "passed" if smoke.get("status") == "passed" else "unverified",
          "Previously executed P00 probe; see .local/reports/p00-docker-smoke.json (not rerun by doctor).")
    cost_path = LOCAL / "reports/p00-cost-policy.json"
    budget_path = LOCAL / "reports/p00-github-budgets.json"
    cost = json.loads(cost_path.read_text(encoding="utf-8")) if cost_path.exists() else {}
    budget = json.loads(budget_path.read_text(encoding="utf-8")) if budget_path.exists() else {}
    rows = {row["product"]: row for row in budget.get("budgets", [])}
    controls_verified = (user is not None and budget.get("account") == user["login"]
        and budget.get("scope") == "Account" and cost.get("account_plan_verified")
        and cost.get("account_cost_controls_verified")
        and all(rows.get(name, {}).get("budget_usd") == "0.00"
                and rows[name].get("displayed_status") == "Usage blocked" for name in ("Actions", "Packages")))
    check("account_cost_controls", "passed" if controls_verified else "unverified",
          {"evidence": [".local/reports/p00-cost-policy.json", ".local/reports/p00-github-budgets.json"],
           "observed_at_utc": budget.get("checked_at_utc"), "live_billing_api_check": False})
    lock_path = ROOT / "tools/toolchain.lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {}
    check("complete_toolchain_lock", "passed" if lock.get("status") == "complete" else "blocked", lock.get("status", "missing"))
    access = lock.get("public_access", {})
    cloudflared = find_tool("cloudflared")
    expected = lock.get("tools", {}).get("cloudflared", {}).get("sha256")
    ready = (access.get("provider") == "cloudflare-quick-tunnel" and access.get("account_required") is False
             and cloudflared is not None and digest(Path(cloudflared)) == expected)
    check("quick_tunnel_prerequisites", "passed" if ready else "blocked",
          {"provider": access.get("provider"), "account_required": False,
           "verified_executable": bool(ready), "public_route_started": False,
           "application_external_smoke": "not run; P16 requires the real Kubernetes application"})
    report["status"] = "passed" if all(c["status"] == "passed" for c in report["checks"]) else "blocked"
    write_json(LOCAL / "reports/p00-doctor.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    for name, help_text in (("doctor", "Read-only host and prerequisites inventory"),
                            ("tools-lock", "Resolve/download P00 approved tools and provenance")):
        action = sub.add_parser(name, help=help_text)
        action.add_argument("--json", action="store_true")
    args = parser.parse_args()
    LOCAL.mkdir(exist_ok=True)
    (LOCAL / ".gitignore").write_text("*\n", encoding="utf-8")
    (LOCAL / "tools").mkdir(exist_ok=True)
    if args.action == "doctor":
        report = doctor()
    else:
        from p00_lock import resolve
        report = resolve()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"P00 {args.action}: {report['status']}; see .local/reports and docs/P00_PREREQUISITES.md")
    return 0 if report["status"] in ("passed", "complete") else 1


if __name__ == "__main__":
    raise SystemExit(main())

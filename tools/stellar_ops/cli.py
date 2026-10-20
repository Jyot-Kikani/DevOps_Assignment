"""Strict command dispatcher. Future actions remain unavailable until implemented."""
import argparse
from datetime import datetime, timezone
import json
import sys
import time

from .bootstrap import ROOT, LOCAL, doctor, write_json


def parser():
    result = argparse.ArgumentParser(description="Stellar Atlas host operations")
    commands = result.add_subparsers(dest="action", required=True)
    for name in ('dev-up', 'dev-down', 'smoke', 'compose-check', 'images-build'):
        action = commands.add_parser(name, help='Local application/images operation; see docs/P09_COMPOSE.md')
        action.add_argument('--json', action='store_true')
        if name == 'dev-up':
            action.add_argument('--no-build', action='store_true', help='Reuse already built images and metadata')
        if name == 'smoke':
            action.add_argument('--target', choices=['local'], default='local')
    for name, help_text in (("secrets-init", "Generate/reuse private local credentials"),
                            ("db-start", "Start only PostgreSQL with no host port"),
                            ("db-stop", "Stop only PostgreSQL, preserving its volume"),
                            ("db-bootstrap", "Bootstrap isolated roles/databases and explicitly migrate"),
                            ("catalog-import", "Verify and atomically activate the sealed full catalog"),
                            ("catalog-report", "Report imported and active snapshots"),
                            ("db-check", "Run real PostgreSQL/HTTP integration checks")):
        action = commands.add_parser(name, help=help_text)
        action.add_argument("--json", action="store_true")
        if name == "db-check":
            action.add_argument("--full", action="store_true")
            action.add_argument("--phase", choices=["P04", "P05", "P06", "P07"])
    action = commands.add_parser("doctor", help="Read-only prerequisites and GitHub/port checks")
    action.add_argument("--json", action="store_true")
    action = commands.add_parser("contracts", help="Regenerate API/schema contracts and pinned TypeScript types")
    action.add_argument("--check", action="store_true", help="Fail on drift without writing")
    action.add_argument("--json", action="store_true")
    action = commands.add_parser("test", help="Run implemented phase gates; integration gates grow with their phase")
    action.add_argument("--json", action="store_true")
    action = commands.add_parser("data-seal", help="Validate preserved baseline and create/reuse immutable local archive")
    action.add_argument("--json", action="store_true")
    action = commands.add_parser("data-publish", help="Stage immutable data locally; explicit --github publication belongs to P15")
    action.add_argument("--stage", help="Existing/new directory strictly beneath .local")
    action.add_argument("--github", action="store_true", help="Publish exact immutable assets after public repository setup in P15")
    action.add_argument("--repository", help="Explicit owner/DevOps_Assignment; required with --github")
    action.add_argument("--json", action="store_true")
    action = commands.add_parser("tools-lock", help="Verify locks or restore frozen tools; never select moving versions")
    action.add_argument("--verify-only", action="store_true")
    action.add_argument("--json", action="store_true")
    return result


def main(argv=None):
    arguments = parser().parse_args(argv)
    started_at = datetime.now(timezone.utc).isoformat()
    started = time.perf_counter()
    LOCAL.mkdir(exist_ok=True)
    (LOCAL / "reports").mkdir(exist_ok=True)
    try:
        if arguments.action in ('dev-up', 'dev-down', 'smoke', 'compose-check', 'images-build'):
            from .application import action
            report = action(arguments.action, no_build=getattr(arguments, 'no_build', False))
        elif arguments.action == "secrets-init":
            from .secrets import initialize
            report = initialize()
        elif arguments.action.startswith("db-") or arguments.action in ("catalog-import", "catalog-report"):
            from .db import action
            report = action(arguments.action, full=getattr(arguments, "full", False), phase=getattr(arguments, "phase", None))
        elif arguments.action == "doctor":
            report = doctor()
        elif arguments.action == "tools-lock":
            from .locks import verify_locks, restore_tools
            report = verify_locks() if arguments.verify_only else restore_tools()
        elif arguments.action == "contracts":
            from .quality import contracts
            report = contracts(check=arguments.check)
        elif arguments.action == "test":
            from .quality import tests
            report = tests()
        elif arguments.action == "data-seal":
            from .data import seal
            report = seal()
        elif arguments.action == "data-publish":
            from .data import publish
            report = publish(stage=arguments.stage, github=arguments.github, repository=arguments.repository)
    except Exception as exc:
        report = {"status": "failed", "error": str(exc), "action": arguments.action}
    report["action"] = arguments.action
    report["started_at_utc"] = started_at
    report["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["duration_seconds"] = round(time.perf_counter() - started, 3)
    write_json(LOCAL / "reports" / (arguments.action + ".json"), report)
    if arguments.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"{arguments.action}: {report['status']}; see .local/reports/{arguments.action}.json")
    return 0 if report["status"] == "passed" else 1

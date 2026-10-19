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
    action = commands.add_parser("doctor", help="Read-only prerequisites and GitHub/port checks")
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
        if arguments.action == "doctor":
            report = doctor()
        elif arguments.action == "tools-lock":
            from .locks import verify_locks, restore_tools
            report = verify_locks() if arguments.verify_only else restore_tools()
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

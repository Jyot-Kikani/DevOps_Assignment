"""Offline import and private maintenance CLI."""
import argparse
import json
from .validation import BASELINE_COUNTS, validate


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    baseline = commands.add_parser("validate-baseline")
    baseline.add_argument("path")
    for name in ("validate", "import"):
        command = commands.add_parser(name)
        command.add_argument("path")
        command.add_argument("--manifest", required=True)
        command.add_argument("--archive")
        command.add_argument("--aliases")
        command.add_argument("--json", action="store_true")
        if name == "import":
            command.add_argument("--activate", action="store_true")
    for name in ("report", "smoke", "retention"):
        commands.add_parser(name).add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "validate-baseline":
            result = validate(args.path, expected_sha256="20271720bc7b5038f05df0c25d17a5e1cc51158eed74ee1b27472c7faf4ede94", expected_counts=BASELINE_COUNTS)
        elif args.action == "validate":
            from .pipeline import preflight
            _, result, _ = preflight(args.path, args.manifest, args.archive, args.aliases)
        elif args.action == "import":
            from .pipeline import load_catalog
            result = load_catalog(args.path, args.manifest, archive=args.archive, aliases_path=args.aliases, activate=args.activate)
        elif args.action == "report":
            from .pipeline import report
            result = report()
        elif args.action == "smoke":
            from .maintenance import smoke
            result = smoke()
        else:
            from .maintenance import retention
            result = retention()
    except Exception as exc:
        print(json.dumps({"status": "failed", "error_type": type(exc).__name__, "message": "Operation failed; check the candidate and configured dependency"}))
        return 1
    print(json.dumps(result, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

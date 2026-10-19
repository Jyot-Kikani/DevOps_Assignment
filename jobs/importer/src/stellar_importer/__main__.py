"""Read-only baseline validator. Database import commands arrive in P05."""
import argparse
import json
from .validation import BASELINE_COUNTS, validate


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["validate-baseline"])
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        result = validate(args.path, expected_sha256="20271720bc7b5038f05df0c25d17a5e1cc51158eed74ee1b27472c7faf4ede94", expected_counts=BASELINE_COUNTS)
    except (OSError, ValueError) as exc:
        parser.exit(1, str(exc) + "\n")
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()

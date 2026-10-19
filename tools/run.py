"""Repository-independent command entry point; host bootstrap uses stdlib only."""
from stellar_ops.bootstrap import ROOT, LOCAL, EXPECTED_SHA, write_json, command, find_tool, digest, doctor, github_probe
from stellar_ops.cli import main

if __name__ == "__main__":
    raise SystemExit(main())

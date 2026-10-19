import sys
from pathlib import Path

# Test/tool schemas only; runtime services use installed wheels.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

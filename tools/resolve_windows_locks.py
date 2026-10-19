"""P01 Windows graph resolution constrained to the already frozen Linux versions."""
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
from pathlib import Path
import re
import subprocess

from stellar_ops.bootstrap import ROOT, LOCAL, write_json
from p00_lock import python_package


def main():
    compiler = LOCAL / "lock-venv/Scripts/python.exe"
    if not compiler.exists():
        raise RuntimeError("Install the locked ops environment before deliberately regenerating platform locks")
    groups = ["catalog", "journey", "importer", "quality", "ops"]
    reports = LOCAL / "reports"
    pins = {}
    for name in groups:
        for package, version in re.findall(r"^([\w.-]+)==([^\s;\\]+)", (ROOT / f"tools/locks/{name}.txt").read_text(), re.M):
            key = package.lower()
            if key in pins and pins[key] != version:
                raise ValueError("Frozen Linux graphs disagree on " + key)
            pins[key] = version
    constraint = reports / "p01-frozen-constraints.txt"
    constraint.write_text("\n".join(f"{p}=={v}" for p, v in sorted(pins.items())) + "\n")
    environment = os.environ.copy()
    environment["CUSTOM_COMPILE_COMMAND"] = "python tools/resolve_windows_locks.py"

    def resolve(name):
        target = reports / f"p01-{name}-windows-resolved.txt"
        args = [str(compiler), "-m", "piptools", "compile", "--resolver=backtracking", "--strip-extras",
                "--allow-unsafe", "--no-header", "--no-emit-index-url", "--index-url", "https://pypi.org/simple",
                "--cache-dir", str(LOCAL / "pip-tools-cache"), "--pip-args=--timeout 25 --retries 1",
                "--constraint", str(constraint), "--output-file", str(target), str(ROOT / f"tools/locks/{name}.in")]
        with (reports / f"p01-{name}-windows-resolve.log").open("w") as output:
            result = subprocess.run(args, cwd=ROOT, env=environment, stdout=output, stderr=subprocess.STDOUT, timeout=600)
        if result.returncode:
            raise RuntimeError("Windows resolution failed for " + name)
        return name, target

    with ThreadPoolExecutor(max_workers=3) as pool:
        resolved = dict(pool.map(resolve, groups))
    all_pins = set()
    for path in resolved.values():
        all_pins.update(re.findall(r"^([\w.-]+)==([^\s;\\]+)", path.read_text(), re.M))
    artifacts = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(python_package, name, version): (name, version) for name, version in all_pins}
        for future in as_completed(futures):
            artifacts[futures[future]] = future.result()
    for name, path in resolved.items():
        lines = ["# Windows amd64 / Python 3.13; frozen Linux versions plus required Windows dependencies.",
                 "# SHA-256s are from official versioned PyPI artifact metadata; use pip --require-hashes."]
        for line in path.read_text().splitlines():
            match = re.fullmatch(r"([\w.-]+)==([^\s;\\]+)(\s*;.*)?", line.strip())
            if not match:
                if line.strip() and not line.lstrip().startswith("#"):
                    raise ValueError("Unexpected non-pinned dependency: " + line)
                continue
            hashes = sorted({f["sha256"] for f in artifacts[(match[1], match[2])]["artifacts"]})
            if not hashes:
                raise ValueError("No upstream hashes for " + match[1])
            lines.append(line.strip() + " \\")
            lines.extend("    --hash=sha256:" + sha + (" \\" if i < len(hashes)-1 else "") for i, sha in enumerate(hashes))
        (ROOT / f"tools/locks/{name}-windows.txt").write_text("\n".join(lines) + "\n")
    write_json(reports / "p01-windows-locks.json", {"status": "passed", "groups": groups, "packages": len(all_pins)})
    print(json.dumps({"status": "passed", "groups": groups, "packages": len(all_pins)}))


if __name__ == "__main__":
    main()

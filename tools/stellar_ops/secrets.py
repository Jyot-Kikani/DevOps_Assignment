"""Generate/reuse local credentials; never return their values."""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
from .bootstrap import LOCAL
from .guards import local_target

NAMES = ("postgres_admin", "catalog_writer", "catalog_reader", "journey_owner", "journey_app", "grafana_admin")


def restrict(path, directory=False):
    if os.name == "nt":
        identity = subprocess.check_output(["whoami"], text=True).strip()
        if identity.split("\\")[-1].lower().startswith("codexsandbox"):
            raise ValueError("Run secrets-init in the normal Windows user session; sandbox identities must not own operator credentials")
        sid = subprocess.check_output(["whoami", "/user", "/fo", "csv", "/nh"], text=True).strip().split(",")[-1].strip('"')
        grant = "*" + sid + (":(OI)(CI)F" if directory else ":F")
        for args in (["icacls", str(path), "/grant:r", grant], ["icacls", str(path), "/inheritance:r"]):
            subprocess.run(args, check=True, capture_output=True, timeout=15)
        # Verify actual DACL identities, inheritance and rights, not just icacls's exit.
        env = os.environ.copy()
        env.pop("PSModulePath", None)  # Do not inject PowerShell 7 module paths into Windows PowerShell.
        shell = shutil.which("pwsh") or "powershell"
        env["STELLAR_ACL_PATH"] = str(path)
        # Remove explicit grants left by another execution identity before verification.
        env["STELLAR_ACL_SID"] = sid
        cleanup = "$a=Get-Acl -LiteralPath $env:STELLAR_ACL_PATH; @($a.Access|ForEach-Object{$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value})|ConvertTo-Json -Compress"
        identities = json.loads(subprocess.check_output([shell, "-NoProfile", "-Command", cleanup], env=env, text=True, timeout=15))
        for other in ([identities] if isinstance(identities, str) else identities):
            if other != sid:
                subprocess.run(["icacls", str(path), "/remove:g", "*" + other], check=True, capture_output=True, timeout=15)
        subprocess.run(["icacls", str(path), "/setowner", "*" + sid], check=True, capture_output=True, timeout=15)
        script = "$a=Get-Acl -LiteralPath $env:STELLAR_ACL_PATH; [pscustomobject]@{Protected=$a.AreAccessRulesProtected;Rules=@($a.Access|ForEach-Object{[pscustomobject]@{SID=$_.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]).Value;Type=$_.AccessControlType.ToString();Rights=$_.FileSystemRights.ToString()}})}|ConvertTo-Json -Depth 4 -Compress"
        result = json.loads(subprocess.check_output([shell, "-NoProfile", "-Command", script], env=env, text=True, timeout=15))
        if not result["Protected"] or not result["Rules"] or any(r["SID"] != sid or r["Type"] != "Allow" or "FullControl" not in r["Rights"] for r in result["Rules"]):
            raise ValueError("Secret filesystem ACL verification failed")
    else:
        path.chmod(0o700 if directory else 0o600)
        if path.stat().st_mode & 0o077:
            raise ValueError("Secret filesystem mode verification failed")


def initialize():
    target = local_target(LOCAL / "secrets")
    target.mkdir(parents=True, exist_ok=True)
    restrict(target, True)
    created = 0
    for name in NAMES:
        path = target / name
        if path.is_symlink():
            raise ValueError("Secret files must not be symlinks")
        if path.exists() and not path.is_file():
            raise ValueError("Secret path must be a regular file: " + name)
        if not path.exists():
            with path.open("x", encoding="utf-8") as output:
                output.write(secrets.token_urlsafe(36) + "\n")
            created += 1
        restrict(path)
    return {"status": "passed", "created": created, "reused": len(NAMES) - created,
            "filesystem_access": "verified current-user only", "values": "never printed"}

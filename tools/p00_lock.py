"""P00 official-source resolver. Partial results never count as a frozen toolchain."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

from run import ROOT, LOCAL, write_json

HEADERS = {"User-Agent": "stellar-atlas-course-p00/1.0"}
DOWNLOADS = LOCAL / "tools/downloads"
META = LOCAL / "reports/p00-upstream"
LOCK = ROOT / "tools/toolchain.lock.json"


def fetch(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def metadata(url):
    META.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    body_path, info_path = META / f"{key}.body", META / f"{key}.json"
    if body_path.exists() and info_path.exists():
        body = body_path.read_bytes()
        saved = json.loads(info_path.read_text(encoding="utf-8"))
        if saved["url"] == url and saved["sha256"] == hashlib.sha256(body).hexdigest():
            return body
    data = fetch(url)
    (META / f"{key}.body").write_bytes(data)
    write_json(META / f"{key}.json", {"url": url, "sha256": hashlib.sha256(data).hexdigest()})
    return data


def checksum(text, filename):
    for line in text.decode().splitlines():
        match = re.match(r"^([a-fA-F0-9]{64})\s+\*?(.+)$", line)
        if match and match[2].strip() == filename:
            return match[1].lower()
    raise ValueError(f"No published checksum for {filename}")


def artifact(name, version, url, sha, provenance, extract=False):
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    path = DOWNLOADS / url.rsplit("/", 1)[-1]
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
        temp = path.with_suffix(path.suffix + ".partial")
        temp.write_bytes(fetch(url))
        actual = hashlib.sha256(temp.read_bytes()).hexdigest()
        if actual != sha:
            raise ValueError(f"Checksum mismatch for {name}: expected {sha}, got {actual}")
        temp.replace(path)
    target = LOCAL / "tools" / name / version
    target.mkdir(parents=True, exist_ok=True)
    if extract:
        with zipfile.ZipFile(path) as archive:
            for member in archive.infolist():
                resolved = (target / member.filename).resolve()
                if not resolved.is_relative_to(target.resolve()):
                    raise ValueError("Archive path escapes tool directory")
            archive.extractall(target)
    else:
        shutil.copy2(path, target / (name + ".exe"))
    return {"version": version, "url": url, "sha256": sha,
            "provenance": provenance, "verified_download": True,
            "local_path": str(target.relative_to(ROOT))}


def release(repo, tag):
    url = f"https://api.github.com/repos/{repo}/releases/" + ("latest" if tag is None else f"tags/{tag}")
    data = json.loads(metadata(url))
    if data.get("draft") or data.get("prerelease"):
        raise ValueError("Release is not stable")
    return url, data


def github_tool(name, repo, tag, pattern, checksum_pattern=None, extract=False):
    source, data = release(repo, tag)
    asset = next(a for a in data["assets"] if re.fullmatch(pattern, a["name"]))
    provenance = {"mechanism": "upstream-checksum-over-https", "release": source}
    if checksum_pattern:
        sums = next(a for a in data["assets"] if re.fullmatch(checksum_pattern, a["name"]))
        sha = checksum(metadata(sums["browser_download_url"]), asset["name"])
        provenance["checksum_url"] = sums["browser_download_url"]
    elif asset.get("digest", "").startswith("sha256:"):
        sha = asset["digest"].split(":")[1]
        provenance["mechanism"] = "github-release-asset-digest-over-https"
    else:
        sha = hashlib.sha256(fetch(asset["browser_download_url"])).hexdigest()
        provenance["mechanism"] = "publisher-release-metadata-and-local-hash-no-upstream-checksum"
    return artifact(name, data["tag_name"].lstrip("v"), asset["browser_download_url"], sha, provenance, extract)


def node():
    version = "24.22.0"
    base = f"https://nodejs.org/dist/v{version}/"
    filename = f"node-v{version}-win-x64.zip"
    sha = checksum(metadata(base + "SHASUMS256.txt"), filename)
    return artifact("node", version, base + filename, sha,
                    {"mechanism": "upstream-checksum-over-https", "checksum_url": base + "SHASUMS256.txt"}, True)


def terraform():
    version = "1.16.6"
    base = f"https://releases.hashicorp.com/terraform/{version}/"
    filename = f"terraform_{version}_windows_amd64.zip"
    url = base + f"terraform_{version}_SHA256SUMS"
    return artifact("terraform", version, base + filename, checksum(metadata(url), filename),
                    {"mechanism": "upstream-checksum-over-https", "checksum_url": url}, True)


def kubectl():
    url = "https://dl.k8s.io/release/v1.35.8/bin/windows/amd64/kubectl.exe"
    sha = metadata(url + ".sha256").decode().strip()
    if not re.fullmatch("[0-9a-f]{64}", sha):
        raise ValueError("Invalid kubectl upstream checksum")
    return artifact("kubectl", "1.35.8", url, sha,
                    {"mechanism": "upstream-checksum-over-https", "checksum_url": url + ".sha256"})


def cloudflared():
    _, latest = release("cloudflare/cloudflared", None)
    source, data = release("cloudflare/cloudflared", latest["tag_name"])
    asset = next(a for a in data["assets"] if a["name"] == "cloudflared-windows-amd64.exe")
    match = re.search(r"^cloudflared-windows-amd64\.exe:\s*([a-f0-9]{64})$", data["body"], re.M)
    if not match or asset.get("digest") != "sha256:" + match[1]:
        raise ValueError("cloudflared published checksum and release asset digest do not agree")
    return artifact("cloudflared", data["tag_name"], asset["browser_download_url"], match[1],
                    {"mechanism": "publisher-release-body-sha256-and-github-asset-digest-over-https", "release": source})


def npm_package(name, version=None):
    base = "https://registry.npmjs.org/" + urllib.parse.quote(name, safe="@")
    data = json.loads(metadata(base + "/" + (version or "latest")))
    if "-" in data["version"]:
        raise ValueError("Prerelease package")
    return {"version": data["version"], "url": data["dist"]["tarball"],
            "integrity": data["dist"]["integrity"], "engines": data.get("engines", {}),
            "peer_dependencies": data.get("peerDependencies", {})}


def python_package(name, version=None):
    url = f"https://pypi.org/pypi/{name}/" + (f"{version}/json" if version else "json")
    data = json.loads(metadata(url))
    selected = data["info"]["version"]
    if not re.fullmatch(r"\d+(\.\d+)+(\.post\d+)?", selected):
        raise ValueError("Prerelease Python package")
    return {"version": selected, "requires_python": data["info"]["requires_python"],
            "metadata_url": url,
            "artifacts": [{"filename": f["filename"], "url": f["url"], "sha256": f["digests"]["sha256"]}
                          for f in data["urls"] if not f.get("yanked")]}


def image(ref):
    # Anonymous Docker Hub read only. Token is kept in memory and never logged.
    repository, tag = ref.rsplit(":", 1)
    repository = repository.removeprefix("docker.io/")
    if "/" not in repository:
        repository = "library/" + repository
    token_url = "https://auth.docker.io/token?" + urllib.parse.urlencode({"service": "registry.docker.io", "scope": f"repository:{repository}:pull"})
    token = json.loads(fetch(token_url))["token"]
    url = f"https://registry-1.docker.io/v2/{repository}/manifests/{tag}"
    request = urllib.request.Request(url, headers={**HEADERS, "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"})
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read()
        actual = "sha256:" + hashlib.sha256(body).hexdigest()
        if response.headers.get("Docker-Content-Digest") != actual:
            raise ValueError("Image registry content digest mismatch")
    document = json.loads(body)
    platforms = [{"digest": m["digest"], "platform": m.get("platform", {})} for m in document.get("manifests", [])]
    if platforms and not any(p["platform"].get("os") == "linux" and p["platform"].get("architecture") == "amd64" for p in platforms):
        raise ValueError("No Linux amd64 image")
    write_json(META / (repository.replace("/", "-") + ".image.json"), document)
    return {"source_tag": ref, "ref": f"docker.io/{repository}@{actual}", "digest": actual,
            "metadata_url": url, "platforms": platforms}


def action(repo):
    # Freeze the highest stable release, then dereference annotated tags to commits.
    release_url, data = release(repo, None)
    tag = data["tag_name"]
    url = f"https://api.github.com/repos/{repo}/git/ref/tags/{tag}"
    obj = json.loads(metadata(url))["object"]
    while obj["type"] == "tag":
        obj = json.loads(metadata(obj["url"]))["object"]
    if obj["type"] != "commit" or not re.fullmatch("[a-f0-9]{40}", obj["sha"]):
        raise ValueError("Action did not resolve to a full commit")
    return {"tag": tag, "sha": obj["sha"], "ref": f"{repo}@{obj['sha']}", "release_url": release_url}


def external_image(ref):
    registry, rest = ref.split("/", 1)
    repository, tag = rest.rsplit(":", 1)
    url = f"https://{registry}/v2/{repository}/manifests/{tag}"
    headers = {**HEADERS, "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json, application/vnd.docker.distribution.manifest.v2+json"}
    request = urllib.request.Request(url, headers=headers)
    try:
        response = urllib.request.urlopen(request, timeout=60)
    except urllib.error.HTTPError as exc:
        if exc.code != 401:
            raise
        fields = dict(re.findall(r'(\w+)="([^"]+)"', exc.headers.get("WWW-Authenticate", "")))
        realm = fields.pop("realm")
        if not realm.startswith("https://"):
            raise ValueError("Non-HTTPS registry token realm")
        token = json.loads(fetch(realm + "?" + urllib.parse.urlencode(fields)))
        headers["Authorization"] = "Bearer " + (token.get("token") or token["access_token"])
        response = urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60)
    with response:
        body = response.read()
        sha = "sha256:" + hashlib.sha256(body).hexdigest()
        declared = response.headers.get("Docker-Content-Digest")
        if declared and declared != sha:
            raise ValueError("External registry digest mismatch")
    doc = json.loads(body)
    if doc.get("schemaVersion") != 2:
        raise ValueError("Registry did not return modern image manifest")
    write_json(META / (registry + "-" + repository.replace("/", "-") + ".image.json"), doc)
    return {"source_tag": ref, "ref": f"{registry}/{repository}@{sha}", "digest": sha,
            "metadata_url": url, "platforms": doc.get("manifests", [])}


def vendor(name, url):
    body = metadata(url)
    path = ROOT / "tools/locks/vendor" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return {"url": url, "sha256": hashlib.sha256(body).hexdigest(), "path": str(path.relative_to(ROOT)),
            "provenance": "publisher-version-tag-over-https; locally computed SHA-256"}


def linux_tool(name, entry):
    version = entry["version"]
    if name in ("node", "terraform"):
        base = f"https://nodejs.org/dist/v{version}/" if name == "node" else f"https://releases.hashicorp.com/terraform/{version}/"
        filename = f"node-v{version}-linux-x64.tar.xz" if name == "node" else f"terraform_{version}_linux_amd64.zip"
        sums_url = entry["provenance"]["checksum_url"]
        sha = checksum(metadata(sums_url), filename)
        return {"version": version, "url": base + filename, "sha256": sha, "checksum_url": sums_url, "downloaded": False}
    if name == "kubectl":
        url = f"https://dl.k8s.io/release/v{version}/bin/linux/amd64/kubectl"
        return {"version": version, "url": url, "sha256": metadata(url + ".sha256").decode().strip(), "checksum_url": url + ".sha256", "downloaded": False}
    release_url = entry["provenance"]["release"]
    data = json.loads(metadata(release_url))
    if name == "cloudflared":
        asset = next(a for a in data["assets"] if a["name"] == "cloudflared-linux-amd64")
        match = re.search(r"^cloudflared-linux-amd64:\s*([a-f0-9]{64})$", data["body"], re.M)
        if not match or asset.get("digest") != "sha256:" + match[1]:
            raise ValueError("cloudflared Linux published digests disagree")
        return {"version": version, "url": asset["browser_download_url"], "sha256": match[1],
                "checksum_url": release_url, "downloaded": False}
    patterns = {"kind": r"kind-linux-amd64", "gh": r"gh_.*_linux_amd64.tar.gz", "cosign": r"cosign-linux-amd64", "gitleaks": r"gitleaks_.*_linux_x64.tar.gz", "grype": r"grype_.*_linux_amd64.tar.gz", "syft": r"syft_.*_linux_amd64.tar.gz"}
    asset = next(a for a in data["assets"] if re.fullmatch(patterns[name], a["name"]))
    if name == "kind":
        sums_url = asset["browser_download_url"] + ".sha256sum"
    else:
        sums_url = entry["provenance"]["checksum_url"]
    return {"version": version, "url": asset["browser_download_url"], "sha256": checksum(metadata(sums_url), asset["name"]), "checksum_url": sums_url, "downloaded": False}


def resolve():
    META.mkdir(parents=True, exist_ok=True)
    lock = json.loads(LOCK.read_text(encoding="utf-8")) if LOCK.exists() else {
        "schema_version": 1, "phase": "P00", "status": "partial", "tools": {},
        "npm": {}, "python": {}, "images": {}, "actions": {}, "vendor": {}, "errors": {}}
    lock["checked_at_utc"] = datetime.now(timezone.utc).isoformat()
    lock.setdefault("tools_linux", {})
    jobs = {("tools", "node"): node, ("tools", "terraform"): terraform, ("tools", "kubectl"): kubectl,
            ("tools", "cloudflared"): cloudflared}
    for name, repo, tag, pattern, sums, extract in [
        ("kind", "kubernetes-sigs/kind", "v0.33.0", r"kind-windows-amd64", r"kind-windows-amd64.sha256sum", False),
        ("gh", "cli/cli", None, r"gh_.*_windows_amd64.zip", r"gh_.*_checksums.txt", True),
        ("cosign", "sigstore/cosign", "v3.1.3", r"cosign-windows-amd64.exe", r"cosign_checksums.txt", False),
        ("gitleaks", "gitleaks/gitleaks", "v8.30.1", r"gitleaks_.*_windows_x64.zip", r"gitleaks_.*_checksums.txt", True),
        ("grype", "anchore/grype", "v0.120.1", r"grype_.*_windows_amd64.zip", r"grype_.*_checksums.txt", True),
        ("syft", "anchore/syft", None, r"syft_.*_windows_amd64.zip", r"syft_.*_checksums.txt", True),
    ]:
        jobs[("tools", name)] = lambda n=name, r=repo, t=tag, p=pattern, s=sums, e=extract: github_tool(n, r, t, p, s, e)
    npm = {"react": "19.3.1", "react-dom": "19.3.1", "vite": "8.3.4", "vitest": "5.0.5", "three": "0.186.1", "@playwright/test": "1.64.1", "typescript": None, "@types/react": None, "@types/react-dom": None, "@types/three": None}
    for name, version in npm.items():
        jobs[("npm", name)] = lambda n=name, v=version: npm_package(n, v)
    python = {"fastapi": "0.146.0", "SQLAlchemy": "2.1.5", "alembic": "1.20.0", "psycopg": "3.3.6", "httpx": None, "uvicorn": None, "pytest": None, "ruff": None, "bandit": None, "pip-audit": None, "prometheus-client": None, "checkov": "3.3.29", "pip-tools": None}
    for name, version in python.items():
        jobs[("python", name)] = lambda n=name, v=version: python_package(n, v)
    for ref in ("python:3.13-slim-bookworm", "postgres:17-bookworm", "nginxinc/nginx-unprivileged:stable-bookworm", "hello-world:linux", "busybox:1.37.0", "kindest/node:v1.35.8", "prom/prometheus:v3.15.0", "grafana/grafana:13.2.4", "redis:8.2.3-alpine"):
        jobs[("images", ref)] = lambda r=ref: image(r)
    for ref in ("registry.k8s.io/kube-state-metrics/kube-state-metrics:v2.20.0", "quay.io/argoproj/argocd:v3.5.5", "quay.io/calico/calico:v3.33.0", "quay.io/calico/third-party-cni-plugins:v3.33.0", "quay.io/calico/node:v3.33.0"):
        jobs[("images", ref)] = lambda r=ref: external_image(r)
    for repo in ("actions/checkout", "actions/setup-node", "actions/setup-python", "actions/upload-artifact", "actions/download-artifact", "actions/cache", "docker/setup-buildx-action"):
        jobs[("actions", repo)] = lambda r=repo: action(r)
    vendors = {
        "calico.yaml": "https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/manifests/calico.yaml",
        "calico-LICENSE": "https://raw.githubusercontent.com/projectcalico/calico/v3.33.0/LICENSE.md",
        "argocd-namespace-install.yaml": "https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.5/manifests/namespace-install.yaml",
        "argocd-crds.yaml": "https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.5/manifests/crds/application-crd.yaml",
        "argocd-appproject-crd.yaml": "https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.5/manifests/crds/appproject-crd.yaml",
        "argocd-LICENSE": "https://raw.githubusercontent.com/argoproj/argo-cd/v3.5.5/LICENSE",
    }
    for name, url in vendors.items():
        jobs[("vendor", name)] = lambda n=name, u=url: vendor(n, u)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(fn): key for key, fn in jobs.items()
                   if key[1] not in lock[key[0]] or key[0] + "/" + key[1] in lock["errors"]}
        for future in as_completed(futures):
            category, name = futures[future]
            key = category + "/" + name
            try:
                lock[category][name] = future.result()
                lock["errors"].pop(key, None)
                print("Resolved " + key, file=sys.stderr, flush=True)
            except Exception as exc:
                lock["errors"][key] = f"{type(exc).__name__}: {exc}"
                print("Blocked " + key + ": " + str(exc), file=sys.stderr, flush=True)
            write_json(LOCK, lock)
    for name, entry in lock["tools"].items():
        if name not in lock["tools_linux"]:
            try:
                lock["tools_linux"][name] = linux_tool(name, entry)
                lock["errors"].pop("tools_linux/" + name, None)
            except Exception as exc:
                lock["errors"]["tools_linux/" + name] = str(exc)
    # Account login is a phase prerequisite, separate from toolchain provenance.
    # Dependency generation is resumable and preserves already frozen versions.
    if not lock["errors"]:
        from p00_dependencies import generate
        generated = generate(lock)
        lock["dependency_resolution"] = {
            name: {k: v for k, v in result.items() if k in ("exit_code", "log", "errors", "packages", "provenance")}
            for name, result in generated.items()}
    lock["remaining"] = []
    generated = lock.get("dependency_resolution", {})
    for name in ("npm", "terraform", "python_resolve", "hashes"):
        if generated.get(name, {}).get("exit_code") != 0:
            lock["remaining"].append(name + " dependency lock not verified")
    expected = "sha256:07b2536e30b803ed61d1677a79df6115f798ce64c80f9e22f6ed45afd09323c0"
    if lock["images"].get("kindest/node:v1.35.8", {}).get("digest") != expected:
        lock["remaining"].append("kind node digest differs from approved baseline")
    support = LOCAL / "reports/p00-calico-support.json"
    if support.exists():
        info = json.loads(support.read_text(encoding="utf-8"))
        lock["calico_compatibility"] = {"url": info["url"], "sha256": info["sha256"],
            "published_support": "Calico 3.33 lists Kubernetes 1.35, 1.36 and 1.37", "integration_tested": False}
    else:
        lock["remaining"].append("Calico versioned support evidence missing")
    installer = LOCAL / "reports/p00-tailscale-installer.json"
    if installer.exists():
        lock.setdefault("retired_downloads", {})["tailscale_installer"] = {
            **json.loads(installer.read_text(encoding="utf-8")), "required": False,
            "reason": "User selected accountless Cloudflare Quick Tunnel on 2026-10-19"}
    lock.pop("tailscale_installer", None)
    lock["public_access"] = {"provider": "cloudflare-quick-tunnel", "account_required": False,
        "domain_purchase_required": False, "origin": "http://127.0.0.1:8080",
        "hostname_changes_on_restart": True, "uptime_guarantee": False,
        "source": "https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/",
        "decision": "docs/adr/0001-public-access-quick-tunnel.md"}
    sums = []
    for name, item in lock["vendor"].items():
        sums.append(item["sha256"] + "  " + name)
    (ROOT / "tools/locks/vendor/SHA256SUMS").write_text("\n".join(sorted(sums)) + "\n", encoding="utf-8")
    artifacts = {}
    for path in (ROOT / "tools/locks").rglob("*"):
        if path.is_file():
            artifacts[str(path.relative_to(ROOT)).replace("\\", "/")] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    lock["lock_artifacts"] = artifacts
    lock["status"] = "complete" if not lock["errors"] and not lock["remaining"] else "partial"
    write_json(LOCK, lock)
    return {"status": lock["status"], "resolved": {key: len(lock[key]) for key in ("tools", "npm", "python", "images", "actions", "vendor")}, "errors": lock["errors"], "remaining": lock["remaining"]}

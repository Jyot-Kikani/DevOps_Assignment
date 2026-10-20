import pytest
import subprocess
import ci_security
from ci_security import excluded


@pytest.mark.parametrize("path", [".local/operator.json", "services/catalog/.env", "validation/gcns_required_fields.csv",
    "validation/stars.bin", "data/catalog.csv.gz", "infra/terraform/terraform.tfstate", "x/private.tfvars",
    "apps/web/node_modules/package.json", "test-results/private.png", ".aws/credentials"])
def test_private_or_raw_files_are_excluded(path):
    assert excluded(path)


@pytest.mark.parametrize("path", [".env.example", "data/aliases.csv", "tests/fixtures/catalog/catalog.csv",
    "tests/fixtures/map/golden.bin", "design/mockups/01-explore.png", "infra/terraform/foundation/.terraform.lock.hcl"])
def test_intended_public_fixtures_and_source_are_allowed(path):
    assert not excluded(path)


def test_deleted_historical_raw_alias_is_rejected(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, check=True)

    git("init", "--initial-branch=main")
    safe = tmp_path / "tests/fixtures/example.csv"
    raw = tmp_path / "validation/old-raw.csv"
    safe.parent.mkdir(parents=True)
    raw.parent.mkdir(parents=True)
    safe.write_bytes(b"identical fixture bytes\n")
    raw.write_bytes(safe.read_bytes())
    git("add", ".")
    git("-c", "user.name=CI fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Fixture paths")
    git("rm", "validation/old-raw.csv")
    git("-c", "user.name=CI fixture", "-c", "user.email=fixture@example.invalid", "commit", "-m", "Remove raw alias")
    monkeypatch.setattr(ci_security, "ROOT", tmp_path)
    report = ci_security.publication_boundaries()
    assert report["status"] == "failed"
    assert report["violations"] == ["validation/old-raw.csv"]

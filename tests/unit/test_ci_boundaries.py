import pytest
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

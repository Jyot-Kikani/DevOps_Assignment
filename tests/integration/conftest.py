"""Required DB suite: absence is a failure, never a successful skip."""
import os
import pytest

def pytest_ignore_collect(collection_path, config):
    return collection_path.name == "test_full_data.py" and os.environ.get("STELLAR_FULL_DATA") != "1"

@pytest.fixture(scope="session", autouse=True)
def real_postgres_required():
    if os.environ.get("STELLAR_DB_TESTS") != "1":
        pytest.fail("Run integration checks through python tools/run.py db-check")

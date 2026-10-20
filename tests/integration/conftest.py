"""Required DB suite: absence is a failure, never a successful skip."""
import os
import pytest

@pytest.fixture(scope="session", autouse=True)
def real_postgres_required():
    if os.environ.get("STELLAR_DB_TESTS") != "1":
        pytest.fail("Run integration checks through python tools/run.py db-check")

"""Private smoke and batched retention actions for maintenance Jobs."""
import os
import httpx
from sqlalchemy import text
from stellar_common.database import engine_for


def retention():
    engine = engine_for("JOURNEY_DSN", "journey_app", "stellar_journey")
    deleted = 0
    try:
        while True:
            with engine.begin() as c:
                result = c.execute(text("""WITH expired AS (
                    SELECT id FROM journey.journeys WHERE expires_at + interval '7 days' <= now()
                    ORDER BY expires_at,id LIMIT 1000)
                    DELETE FROM journey.journeys WHERE id IN (SELECT id FROM expired) RETURNING id"""))
                count = len(result.all())
            deleted += count
            if count < 1000:
                break
        return {"status": "passed", "deleted": deleted, "batch_size": 1000}
    finally:
        engine.dispose()


def smoke():
    base = os.environ.get("CATALOG_INTERNAL_URL", "http://catalog:8000")
    sid = os.environ["CATALOG_SNAPSHOT_ID"]
    with httpx.Client(base_url=base, timeout=3, follow_redirects=False, trust_env=False) as client:
        response = client.get(f"/v1/snapshots/{sid}/map", params={"radius_ly": 50})
        response.raise_for_status()
        manifest = response.json()
        if manifest["snapshot"]["snapshot_id"] != sid or manifest["total_count"] < 1:
            raise ValueError("Smoke snapshot/count mismatch")
    return {"status": "passed", "snapshot_id": sid, "total_count": manifest["total_count"]}

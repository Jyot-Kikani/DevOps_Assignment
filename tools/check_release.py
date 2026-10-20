"""Validate the small release record; no signer/SBOM or publication assertions."""
import json
from pathlib import Path
import sys
from schema_models import Release

release = Release.model_validate_json(Path(sys.argv[1]).read_text(encoding='utf-8'))
print(json.dumps({'status': 'passed', 'source_sha': release.source_sha, 'release_id': release.release_id,
    'images': list(release.images.model_dump()), 'publication': 'not established by schema validation'}))

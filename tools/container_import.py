"""Verify the sealed build asset and atomically import it; no network download."""
import gzip
from pathlib import Path
import shutil
import tempfile
import json
from stellar_importer.pipeline import load_catalog

def main():
    with tempfile.TemporaryDirectory(prefix='stellar-import-') as scratch:
        raw = Path(scratch) / 'catalog.csv'
        with gzip.open('/data/catalog.csv.gz', 'rb') as source, raw.open('wb') as output:
            shutil.copyfileobj(source, output)
        result = load_catalog(raw, '/data/snapshot.lock.json', archive='/data/catalog.csv.gz', aliases_path='/data/aliases.csv', activate=True)
        print(json.dumps(result))

if __name__ == '__main__':
    try:
        main()
    except Exception:
        print('{"status":"failed","message":"Sealed import failed; active data preserved"}')
        raise SystemExit(1)

"""One isolated empty-volume Compose check; removes only its own temporary project."""
import json
import subprocess
from uuid import uuid4
from stellar_ops.application import compose, smoke
from stellar_ops.bootstrap import LOCAL, write_json
from stellar_ops.db import run

def main():
    normal = compose()
    project = 'stellar-atlas-check-' + uuid4().hex[:12]
    temporary = normal + ['-p', project]
    if run(['docker', 'ps', '-aq', '--filter', 'label=com.docker.compose.project=' + project]) or run(['docker', 'volume', 'ls', '-q', '--filter', 'label=com.docker.compose.project=' + project]):
        raise ValueError('Fresh-check project already has resources')
    run(normal + ['stop'])
    try:
        run(temporary + ['up', '-d', '--wait', '--wait-timeout', '90', 'postgres'])
        for job in ('bootstrap', 'catalog-migrate', 'journey-migrate', 'importer'):
            run(temporary + ['--profile', 'jobs', 'run', '--rm', '--no-deps', job], timeout=600)
        run(temporary + ['up', '-d', '--wait', '--wait-timeout', '90', 'web'])
        report = smoke()
        report.update(project=project, initial_volume='empty', expected_total_rows=331312,
            cleanup='Only the unique temporary test project and its new volume removed; original volume retained')
        write_json(LOCAL / 'reports/p09-fresh-compose.json', report)
        print(json.dumps(report, indent=2))
    finally:
        # This random project was verified empty before this invocation created it.
        subprocess.run(temporary + ['down', '--volumes'], check=True, timeout=90, capture_output=True)
        run(normal + ['up', '-d', '--wait', '--wait-timeout', '90', 'web'])

if __name__ == '__main__':
    main()

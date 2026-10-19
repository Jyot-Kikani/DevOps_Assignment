import concurrent.futures, json, os, subprocess, sys
from pathlib import Path
reports=Path('/reports'); reports.mkdir(exist_ok=True)
env=dict(os.environ, CUSTOM_COMPILE_COMMAND='python tools/run.py tools-lock (P00 Linux resolver)')
result=subprocess.run([sys.executable,'-m','pip','install','--disable-pip-version-check','--index-url','https://pypi.org/simple','--timeout','25','--retries','1','pip-tools==7.6.2'],stdout=(reports/'p00-linux-pip-tools.log').open('w'),stderr=subprocess.STDOUT,timeout=240,env=env)
if result.returncode: sys.exit(result.returncode)
def compile_lock(name):
    # Resolve on Linux first. Host code adds published PyPI SHA-256s to every
    # exact transitive pin, avoiding redundant downloads of foreign-ABI wheels.
    args=[sys.executable,'-m','piptools','compile','--resolver=backtracking','--strip-extras','--allow-unsafe','--no-header','--no-emit-index-url','--index-url','https://pypi.org/simple','--pip-args=--timeout 25 --retries 1','--output-file',f'/reports/p00-{name}-resolved.txt',f'/locks/{name}.in']
    try:
        with (reports/f'p00-python-{name}.log').open('w') as log:
            p=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=900,env=env)
        return name,{'exit_code':p.returncode,'command':args,'platform':'Linux amd64 / Python 3.13'}
    except subprocess.TimeoutExpired: return name,{'exit_code':None,'error':'900s timeout'}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    results=dict(pool.map(compile_lock,['catalog','journey','importer','quality','checkov','ops']))
(reports/'p00-python-locks.json').write_text(json.dumps(results,indent=2)+'\n')
print(json.dumps(results),flush=True)
sys.exit(0 if all(v['exit_code']==0 for v in results.values()) else 1)

"""Download a pinned public annotation release, keeping it out of Git."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
DEST = ROOT / 'data/raw/mtpedocs'

def download(item):
    revision, name = item
    destination = DEST / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    url = f'https://raw.githubusercontent.com/tr4lg/MTPEdocs-MQM/{revision}/{name}'
    if not destination.exists():
        subprocess.run(['curl.exe', '-fLsS', '--retry', '2', '--max-time', '90', url, '-o', str(destination)], check=True)
    return {'path': name, 'url': url, 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()}

if __name__ == '__main__':
    tree = json.loads((DEST / 'tree.json').read_text(encoding='utf-8'))
    revision = tree['sha']
    names = [x['path'] for x in tree['tree'] if x['path'].endswith('.json') or x['path'] == 'README.md']
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(download, [(revision, x) for x in names]))
    manifest = {'repository': 'https://github.com/tr4lg/MTPEdocs-MQM', 'revision': revision,
                'license': 'CC-BY-NC-SA-4.0; source documents excluded by upstream',
                'redistribution': 'Raw and processed sentence text excluded from Imi source distributions.', 'files': files}
    (ROOT / 'data/mtpedocs-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Downloaded and hashed {len(files)} files at {revision}', flush=True)

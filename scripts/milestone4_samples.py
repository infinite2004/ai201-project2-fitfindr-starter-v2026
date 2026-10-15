"""Run standalone tools and retain exact commands/output for Milestone 4.

Run from the repository root with the virtual environment activated:
    python scripts/milestone4_samples.py
Uses real model calls with AI201_CACHE=0; no cached answers or fake outputs.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('search', "from tools import search_listings; print([(x['id'], x['title'], x['size'], x['price'], x['platform']) for x in search_listings('graphic tee', size='M', max_price=30)])"),
    ('outfit', 'from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))'),
    ('card_1', "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"),
    ('card_2', "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"),
    ('card_3', "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"),
    ('empty_wardrobe', 'from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))'),
    ('empty_search', "from tools import search_listings; print(search_listings('designer ballgown', size='XXS', max_price=5))"),
    ('empty_outfit', "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('   ', load_listings()[0]))"),
]


def main():
    results = []
    env = {**os.environ, 'AI201_CACHE': '0'}
    for label, source in CASES:
        command = 'AI201_CACHE=0 python -c ' + shlex.quote(source)
        print('$ ' + command, flush=True)
        proc = subprocess.run([sys.executable, '-c', source], cwd=ROOT, env=env,
                              capture_output=True, text=True, timeout=180)
        print(proc.stdout, end='', flush=True)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr, end='', flush=True)
        results.append({'label': label, 'command': command, 'stdout': proc.stdout,
                        'stderr': proc.stderr, 'exit_code': proc.returncode})
        (ROOT / 'results' / 'milestone4-tools.json').write_text(json.dumps(results, indent=2))
        if proc.returncode:
            return proc.returncode
    print('Distinct captions:', len({r['stdout'] for r in results if r['label'].startswith('card_')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

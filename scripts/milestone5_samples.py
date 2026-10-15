"""Capture a live session, actual tool arguments, and both CLI branches.

Run from the repository root: python scripts/milestone5_samples.py
Uses four uncached model requests: two in the session and two in the CLI run.
"""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ['AI201_CACHE'] = '0'

import agent
from generate import call_count
from utils.data_loader import get_example_wardrobe


def main():
    calls = []
    real_outfit = agent.suggest_outfit
    real_card = agent.create_fit_card

    def record_outfit(item, wardrobe):
        calls.append({'tool': 'suggest_outfit', 'item': copy.deepcopy(item)})
        return real_outfit(item, wardrobe)

    def record_card(outfit, item):
        calls.append({'tool': 'create_fit_card', 'item': copy.deepcopy(item), 'outfit': outfit})
        return real_card(outfit, item)

    query = 'vintage graphic tee under $30'
    with patch.object(agent, 'suggest_outfit', side_effect=record_outfit), \
         patch.object(agent, 'create_fit_card', side_effect=record_card):
        session = agent.run_agent(query, get_example_wardrobe())
        happy_calls = call_count()
        print('Happy-path session:', flush=True)
        print(json.dumps(session, indent=2, ensure_ascii=False), flush=True)
        empty_session = agent.run_agent('designer ballgown size XXS under $5', get_example_wardrobe())
        empty_calls = call_count() - happy_calls
        print('Empty-search session:', flush=True)
        print(json.dumps(empty_session, indent=2, ensure_ascii=False), flush=True)

    evidence = {
        'happy_session': session, 'actual_tool_inputs': calls,
        'happy_model_calls': happy_calls, 'empty_session': empty_session,
        'empty_model_calls': empty_calls, 'cli_runs': [],
    }
    destination = ROOT / 'results' / 'milestone5-sessions.json'
    destination.write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
    assert session['error'] is None, session['error']
    assert [entry['tool'] for entry in calls] == ['suggest_outfit', 'create_fit_card']
    assert all(entry['item'] == session['selected_item'] for entry in calls)
    assert calls[1]['outfit'] == session['outfit_suggestion']
    assert empty_session['fit_card'] is None
    assert empty_session['error']
    assert happy_calls == 2 and empty_calls == 0
    print('State handoff verified; happy path made 2 model calls, empty path made 0.', flush=True)

    for text in (query, 'designer ballgown size XXS under $5'):
        command = "AI201_CACHE=0 python app.py ask '" + text + "'"
        proc = subprocess.run([sys.executable, 'app.py', 'ask', text], cwd=ROOT,
                              capture_output=True, text=True, timeout=180)
        print('$ ' + command, flush=True)
        print(proc.stdout, end='', flush=True)
        if proc.stderr:
            print(proc.stderr, end='', file=sys.stderr, flush=True)
        evidence['cli_runs'].append({'command': command, 'stdout': proc.stdout,
                                     'stderr': proc.stderr, 'exit_code': proc.returncode})
        destination.write_text(json.dumps(evidence, indent=2, ensure_ascii=False))
        assert proc.returncode == 0, proc.stderr
        if text == query:
            assert 'Fit card:' in proc.stdout
        else:
            assert '0 model calls' in proc.stdout and 'higher price limit' in proc.stdout
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Evaluate the unchanged five criteria with real, uncached model responses.

python run_eval.py --label before
python run_eval.py --label after

Each report includes JSON snapshots, actual tool arguments, mechanical checks,
and readable output. Caption grounding still requires reading the outputs;
mechanical caption results are provisional until the documented text review.
The first three trials form the requested submission table. Two supplemental
trials preserve the original five-trial targets. No criteria are rewritten.
"""
import argparse
import contextlib
import copy
import datetime as dt
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import re
from unittest.mock import patch

import agent
import config
import generate
import scenarios
import tools
from utils.data_loader import get_example_wardrobe, load_listings


def inspect_caption(text, item):
    sentences = [s for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s]
    prices = re.findall(r'\$\s*(\d+(?:\.\d+)?)', text)
    platform_mentions = len(re.findall(r'\b' + re.escape(item['platform']) + r'\b', text, re.I))
    # Fixed fixture: Levi's 501 jeans. This checks identification, not every fact.
    identified = all(re.search(r'\b' + token + r'\b', text, re.I) for token in ('Levi', '501', 'jeans'))
    checks = {
        'two_to_four_sentences': 2 <= len(sentences) <= 4,
        'identifies_fixture_item': identified,
        'correct_price_once': len(prices) == 1 and Decimal(prices[0]) == Decimal(str(item['price'])),
        'platform_once': platform_mentions == 1,
    }
    return {'checks': checks, 'sentence_count': len(sentences), 'price_mentions': prices,
            'platform_mentions': platform_mentions,
            'literal_unicode_escapes': re.findall(r'\\u[0-9a-fA-F]{4}', text)}


def observe_agent(query):
    """Spy on actual calls without replacing tool behavior or model responses."""
    calls = []

    def wrapper(name, function):
        def invoke(*args, **kwargs):
            record = {'tool': name, 'args': copy.deepcopy(args), 'kwargs': copy.deepcopy(kwargs)}
            calls.append(record)
            result = function(*args, **kwargs)
            record['returned'] = copy.deepcopy(result)
            return result
        return invoke

    with patch.object(agent, 'search_listings', wrapper('search_listings', tools.search_listings)), \
         patch.object(agent, 'suggest_outfit', wrapper('suggest_outfit', tools.suggest_outfit)), \
         patch.object(agent, 'create_fit_card', wrapper('create_fit_card', tools.create_fit_card)):
        session = agent.run_agent(query, get_example_wardrobe())
    return {'input': {'query': query}, 'session': session, 'calls': calls}


def run_trial(scenario, index):
    if scenario['mode'] == 'agent':
        return observe_agent(scenario['queries'][index])
    if scenario['mode'] == 'card':
        item = next(x for x in load_listings() if x['id'] == scenario['item_id'])
        text = tools.create_fit_card(scenario['outfit'], item)
        return {'input': {'item': item, 'outfit': scenario['outfit']}, 'fit_card': text,
                'caption_inspection': inspect_caption(text, item)}
    if scenario['mode'] == 'search':
        case = scenario['cases'][index]
        matches = tools.search_listings(case['description'], max_price=case['max_price'])
        return {'input': case, 'search_results': matches}
    raise ValueError('Unknown trial mode')


def score(number, record):
    if record.get('crashed'):
        return False, {'completed_without_exception': False}
    session = record.get('session', {})
    names = [c['tool'] for c in record.get('calls', [])]
    if number == 1:
        checks = {'all_three_calls': names == ['search_listings', 'suggest_outfit', 'create_fit_card'],
                  'no_error': session.get('error') is None,
                  'nonempty_card': bool((session.get('fit_card') or '').strip())}
    elif number == 2:
        message = session.get('error') or ''
        checks = {'search_only': names == ['search_listings'],
                  'empty_results': session.get('search_results') == [],
                  'no_card': session.get('fit_card') is None,
                  'actionable_message': all(x in message for x in ('broader description', 'different size', 'higher price limit'))}
    elif number == 3:
        fields = ('id', 'title', 'price', 'size', 'platform')
        selected = session.get('selected_item') or {}
        received = [c for c in record.get('calls', []) if c['tool'] in ('suggest_outfit', 'create_fit_card')]
        checks = {'both_downstream_calls': len(received) == 2,
                  'same_item_fields': bool(selected) and len(received) == 2 and all(
                      all(c['args'][0 if c['tool'] == 'suggest_outfit' else 1].get(k) == selected.get(k)
                          for k in fields) for c in received)}
    elif number == 4:
        checks = record['caption_inspection']['checks']
    else:
        matches = record['search_results']
        case = record['input']
        checks = {'known_match_present': case['known_id'] in [x['id'] for x in matches],
                  'all_within_budget': bool(matches) and all(x['price'] <= case['max_price'] for x in matches)}
    return all(checks.values()), checks


def unicode_regression():
    """Replay an existing real caption; explicitly NOT a fresh model trial."""
    source = config.RESULTS_DIR / 'milestone5-sessions.json'
    previous = json.loads(source.read_text())
    raw = previous['cli_runs'][0]['stdout'].split('  Fit card: ', 1)[1].split('\n\n', 1)[0]
    item = previous['happy_session']['selected_item']
    with patch.object(tools, 'generate', return_value=raw):
        result = tools.create_fit_card('jeans and white sneakers', item)
    return {'source': str(source.relative_to(config.ROOT)),
            'kind': 'replayed recorded response; model mocked; not an acceptance trial',
            'input_model_response': raw, 'tool_output': result,
            'escaped_punctuation_remaining': bool(re.search(r'\\u201[0-5]', result))}


def write_reports(report, stem):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    json_path = config.RESULTS_DIR / (stem + '.json')
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    lines = [f"# Run log — {report['label']}", '',
             f"Produced by `run_eval.py::main` at {report['started_utc']}.", '',
             f"Model: {report['model']}; temperature: {report['temperature']}; cache: OFF.", '',
             'Caption verdicts are mechanical candidates until the factual review in README.', '',
             '| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |',
             '|---|---|---|---|---|---|---|---|']
    for row in report['rows']:
        outcomes = ['PASS' if t['passed'] else 'FAIL' for t in row['tries']]
        count = sum(t['passed'] for t in row['tries'])
        verdict = ('MET' if count >= row['target'] else 'MISSED') if len(outcomes) == 5 else 'INCOMPLETE'
        cells = outcomes + ['—'] * (5-len(outcomes))
        lines.append(f"| {row['criterion']}. {row['name']} | {row['target']}/5 | " + ' | '.join(cells) + f' | {verdict} ({count}/5) |')
    for row in report['rows']:
        lines += ['', f"## Criterion {row['criterion']}: {row['name']}", '']
        for index, trial in enumerate(row['tries'], 1):
            lines += [f'### Try {index}', '', '```json', json.dumps(trial, indent=2, ensure_ascii=False), '```', '']
    if report.get('unicode_diagnostic'):
        lines += ['## Separate formatting regression (recorded response replay)', '',
                  '```json', json.dumps(report['unicode_diagnostic'], indent=2, ensure_ascii=False), '```']
    (config.RESULTS_DIR / (stem + '.md')).write_text('\n'.join(lines)+'\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, choices=('before', 'after'))
    parser.add_argument('--tries', '--trials', type=int, default=5)
    args = parser.parse_args()
    if args.tries not in (3, 5):
        parser.error('Use 3 for a partial run or 5 to measure the unchanged targets.')
    if scenarios.validate():
        parser.error('; '.join(scenarios.validate()))
    config.CACHE_ENABLED = False
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    stem = f'run_{stamp}_{args.label}'
    report = {'label': args.label, 'started_utc': stamp, 'model': config.MODEL,
              'temperature': config.TEMPERATURE, 'cache_enabled': False,
              'shared_observations': 'Criterion 3 inspects the exact criterion 1 runs; no extra calls or cache reuse.',
              'source_sha256': {name: hashlib.sha256((config.ROOT/name).read_bytes()).hexdigest()
                                for name in ('criteria.md', 'agent.py', 'tools.py', 'scenarios.py', 'run_eval.py')},
              'rows': []}
    print(f'Cache OFF. Saving {stem}.json and .md after every trial.', flush=True)
    for scenario in scenarios.SCENARIOS:
        row = {k: scenario[k] for k in ('criterion', 'name', 'target')}
        row['tries'] = []
        report['rows'].append(row)
        for index in range(args.tries):
            before_calls = generate.call_count()
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                try:
                    if scenario['mode'] == 'reuse':
                        original = next(r for r in report['rows'] if r['criterion'] == scenario['reuse_from'])
                        trial = copy.deepcopy(original['tries'][index])
                        trial['shared_from'] = f"criterion {scenario['reuse_from']}, try {index+1}"
                        trial['additional_model_calls'] = 0
                    else:
                        trial = run_trial(scenario, index)
                        trial['model_calls'] = generate.call_count() - before_calls
                except Exception as exc:
                    trial = {'crashed': f'{type(exc).__name__}: {exc}'}
            trial['stdout'] = output.getvalue()
            trial['passed'], trial['checks'] = score(scenario['criterion'], trial)
            row['tries'].append(trial)
            write_reports(report, stem)
            print(f"Criterion {row['criterion']}, try {index+1}: {'PASS' if trial['passed'] else 'FAIL'}", flush=True)
    report['unicode_diagnostic'] = unicode_regression()
    report['usage'] = generate.usage()
    write_reports(report, stem)
    print(report['usage'], flush=True)
    print(f'Wrote results/{stem}.json and .md', flush=True)


if __name__ == '__main__':
    main()

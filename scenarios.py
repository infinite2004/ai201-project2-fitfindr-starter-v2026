"""Fixed evaluation inputs for the five unchanged criteria.

Criteria 1 and 3 inspect the same five real agent runs. Sharing observations
avoids duplicate API calls; it does not reuse cached model responses.
"""
MATCHING_QUERIES = [
    'vintage graphic tee under $30',
    '90s track jacket in size M',
    'silk slip dress in midi length under $40',
    'platform sneakers size 8',
    'denim jacket under $50',
]
SCENARIOS = [
    {'criterion': 1, 'name': 'matching query completes', 'mode': 'agent',
     'target': 4, 'queries': MATCHING_QUERIES},
    {'criterion': 2, 'name': 'impossible query stops early', 'mode': 'agent',
     'target': 5, 'queries': ['designer ballgown size XXS under $5'] * 5},
    {'criterion': 3, 'name': 'selected item preserved', 'mode': 'reuse',
     'target': 5, 'reuse_from': 1},
    {'criterion': 4, 'name': 'short grounded fit card', 'mode': 'card',
     'target': 4, 'item_id': 'lst_001', 'outfit': 'jeans and white sneakers'},
    {'criterion': 5, 'name': 'inclusive price ceiling', 'mode': 'search',
     'target': 5, 'cases': [
         {'description': 'butterfly', 'max_price': 18.0, 'known_id': 'lst_002'},
         {'description': 'flannel', 'max_price': 22.0, 'known_id': 'lst_003'},
         {'description': 'bootleg', 'max_price': 24.0, 'known_id': 'lst_006'},
         {'description': 'corduroy', 'max_price': 32.0, 'known_id': 'lst_005'},
         {'description': 'track jacket', 'max_price': 45.0, 'known_id': 'lst_004'},
     ]},
]


def validate():
    problems = []
    if [s['criterion'] for s in SCENARIOS] != [1, 2, 3, 4, 5]:
        problems.append('Exactly criteria 1 through 5 must be present, in order.')
    for scenario in SCENARIOS:
        if scenario.get('queries') is not None and len(scenario['queries']) != 5:
            problems.append('Each query scenario must have five fixed inputs.')
        if scenario.get('cases') is not None and len(scenario['cases']) != 5:
            problems.append('Each search scenario must have five fixed inputs.')
    return problems

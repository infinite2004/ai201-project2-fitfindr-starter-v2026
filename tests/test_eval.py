"""Check evaluation logic before collecting the baseline."""
import copy
import unittest
from unittest.mock import patch

import run_eval
import tools
from utils.data_loader import load_listings


class EvaluationTests(unittest.TestCase):
    def test_caption_decimal_price_and_sentence_counts(self):
        item = load_listings()[0]
        good = "Vintage Levi's 501 jeans are $38.00 on depop. Pair them with white sneakers."
        self.assertTrue(all(run_eval.inspect_caption(good, item)['checks'].values()))
        for bad in (good.replace('$38.00', '$39.00'), good + ' Another $38.00 bargain.',
                    good + ' See depop.', 'No details.'):
            self.assertFalse(all(run_eval.inspect_caption(bad, item)['checks'].values()))

    def test_state_score_detects_changed_price(self):
        item = load_listings()[0]
        record = {'session': {'selected_item': item}, 'calls': [
            {'tool': 'suggest_outfit', 'args': [copy.deepcopy(item), {'items': []}]},
            {'tool': 'create_fit_card', 'args': ['Outfit', copy.deepcopy(item)]},
        ]}
        self.assertTrue(run_eval.score(3, record)[0])
        record['calls'][1]['args'][1]['price'] = 999
        self.assertFalse(run_eval.score(3, record)[0])

    def test_empty_result_cannot_pass_budget_test(self):
        record = {'input': {'known_id': 'lst_001', 'max_price': 38}, 'search_results': []}
        self.assertFalse(run_eval.score(5, record)[0])
        record['search_results'] = [load_listings()[0]]
        self.assertTrue(run_eval.score(5, record)[0])

    def test_observer_records_actual_calls(self):
        with patch.object(tools, 'generate', side_effect=['Outfit.', 'Caption.']):
            record = run_eval.observe_agent('graphic tee under $30')
        self.assertTrue(run_eval.score(1, record)[0])
        self.assertTrue(run_eval.score(3, record)[0])
        self.assertEqual(len(record['calls']), 3)


if __name__ == '__main__':
    unittest.main()

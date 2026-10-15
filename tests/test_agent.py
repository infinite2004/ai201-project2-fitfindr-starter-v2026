"""Offline checks for parsing, branching, and state passed to actual tools."""

import copy
import unittest
from unittest.mock import patch

import agent
import tools
from generate import ModelUnavailable
from utils.data_loader import get_example_wardrobe


class QueryTests(unittest.TestCase):
    def test_common_queries(self):
        for query, description, size, ceiling in [
            ('vintage graphic tee under $30, size M', 'vintage graphic tee', 'M', 30.0),
            ('platform sneakers size US 8.5 below $40.50', 'platform sneakers', 'US 8.5', 40.5),
            ('jeans size W30 L30 up to 38', 'jeans', 'W30 L30', 38.0),
            ('tee size S/M max $18', 'tee', 'S/M', 18.0),
            ('hat size One Size', 'hat', 'One Size', None),
            ('flannel size XL (oversized)', 'flannel', 'XL', None),
            ('jeans maximum $1,000', 'jeans', None, 1000.0),
            ('denim jacket', 'denim jacket', None, None),
            ('', '', None, None),
            ('tee under $0', 'tee', None, 0.0),
            ('tee below -5', 'tee', None, -5.0),
        ]:
            with self.subTest(query=query):
                self.assertEqual(agent.parse_query(query), {
                    'description': description, 'size': size, 'max_price': ceiling,
                })


class LoopTests(unittest.TestCase):
    def test_five_matching_queries_pass_stored_state_to_both_tools(self):
        for query in [
            'vintage graphic tee under $30', '90s track jacket in size M',
            'silk slip dress in midi length under $40',
            'platform sneakers size 8', 'denim jacket under $50',
        ]:
            with self.subTest(query=query):
                wardrobe = get_example_wardrobe()
                original_wardrobe = copy.deepcopy(wardrobe)
                calls = []

                def outfit(item, closet):
                    calls.append(('outfit', copy.deepcopy(item)))
                    return tools.suggest_outfit(item, closet)

                def card(text, item):
                    calls.append(('card', copy.deepcopy(item), text))
                    return tools.create_fit_card(text, item)

                with patch.object(tools, 'generate', side_effect=['An outfit.', 'A fit card.']), \
                     patch.object(agent, 'search_listings', wraps=tools.search_listings) as search, \
                     patch.object(agent, 'suggest_outfit', side_effect=outfit) as suggestion, \
                     patch.object(agent, 'create_fit_card', side_effect=card) as caption:
                    session = agent.run_agent(query, wardrobe)
                self.assertIsNone(session['error'])
                self.assertEqual(session['fit_card'], 'A fit card.')
                self.assertEqual(session['selected_item'], session['search_results'][0])
                self.assertEqual([call[0] for call in calls], ['outfit', 'card'])
                for call in calls:
                    self.assertEqual(call[1], session['selected_item'])
                self.assertEqual(calls[1][2], session['outfit_suggestion'])
                search.assert_called_once_with(**session['parsed'])
                self.assertIs(suggestion.call_args.args[0], session['selected_item'])
                self.assertIs(suggestion.call_args.args[1], session['wardrobe'])
                self.assertIs(caption.call_args.args[1], session['selected_item'])
                self.assertEqual(wardrobe, original_wardrobe)

    def test_five_empty_searches_never_call_model_tools(self):
        for query in [
            'designer ballgown size XXS under $5', 'zzzzunfindable',
            'graphic tee under $0', '', 'graphic tee size XXXS',
        ]:
            with self.subTest(query=query), \
                 patch.object(agent, 'suggest_outfit') as outfit, \
                 patch.object(agent, 'create_fit_card') as card:
                session = agent.run_agent(query, get_example_wardrobe())
                outfit.assert_not_called()
                card.assert_not_called()
                self.assertEqual(session['search_results'], [])
                for field in ('selected_item', 'outfit_suggestion', 'fit_card'):
                    self.assertIsNone(session[field])
                self.assertIn('broader description', session['error'])
                self.assertIn('different size', session['error'])
                self.assertIn('higher price limit', session['error'])

    def test_missing_generation_stops_before_card(self):
        with patch.object(tools, 'generate', return_value='  '), \
             patch.object(agent, 'create_fit_card') as card:
            session = agent.run_agent('graphic tee', get_example_wardrobe())
        card.assert_not_called()
        self.assertEqual(session['error'], tools.NO_OUTFIT_RESPONSE)
        self.assertIsNone(session['fit_card'])

    def test_blank_card_is_not_success(self):
        with patch.object(tools, 'generate', side_effect=['An outfit.', '  ']):
            session = agent.run_agent('graphic tee', get_example_wardrobe())
        self.assertEqual(session['error'], tools.NO_CARD_RESPONSE)

    def test_model_error_preserves_prior_state(self):
        with patch.object(tools, 'generate', side_effect=ModelUnavailable('Private diagnostics')):
            session = agent.run_agent('graphic tee', get_example_wardrobe())
        self.assertIsNotNone(session['selected_item'])
        self.assertIsNone(session['outfit_suggestion'])
        self.assertIsNone(session['fit_card'])
        self.assertIn('Check your API key', session['error'])
        self.assertNotIn('Private diagnostics', session['error'])

    def test_loop_limit_checked_before_next_call(self):
        with patch.object(agent.trace.config, 'MAX_ITERATIONS', 1), \
             patch.object(agent, 'suggest_outfit') as outfit:
            with self.assertRaisesRegex(RuntimeError, 'MAX_ITERATIONS'):
                agent.run_agent('graphic tee', get_example_wardrobe())
        outfit.assert_not_called()


if __name__ == '__main__':
    unittest.main()

"""Offline regression checks; these do not score model quality."""

import copy
import json
import unittest
from unittest.mock import patch

import tools
from generate import ModelUnavailable
from utils.data_loader import load_listings, get_example_wardrobe


class SearchTests(unittest.TestCase):
    def test_size_boundaries_and_alternatives(self):
        for requested, actual, expected in [
            ('M', 'S/M', True), ('m', 'M/L', True),
            ('S', 'US 9', False), ('L', 'XL', False),
            ('XL', 'XL (oversized)', True), ('S/M', 'M', True),
            ('8', 'US 8', True), ('US 8', 'US 8.5', False),
            ('W30', 'W30 L30', True), ('W30 L32', 'W30 L30', False),
            ('One Size', 'One Size / Oversized', True),
        ]:
            with self.subTest(requested=requested, actual=actual):
                self.assertEqual(tools._matches_size(actual, requested), expected)

    def test_all_three_filters_together(self):
        results = tools.search_listings('graphic tee', size='m', max_price=18)
        self.assertIn('lst_002', [item['id'] for item in results])
        for item in results:
            self.assertLessEqual(item['price'], 18)
            self.assertIn(item['size'], ('M', 'S/M', 'M/L'))
            self.assertTrue({'graphic', 'tee'} & tools._tokens(
                item['title'] + ' ' + item['description'] + ' ' + ' '.join(item['style_tags'])
            ))

    def test_empty_and_impossible_queries(self):
        for description in ('', '  ', 'looking for a', 'zzzzunfindable'):
            with self.subTest(description=description):
                self.assertEqual(tools.search_listings(description), [])
        self.assertEqual(tools.search_listings('designer ballgown', 'XXS', 5), [])

    def test_price_ceilings_include_known_items(self):
        # Five different budgets, including exact-price boundaries.
        for description, ceiling, known_id in [
            ('butterfly', 18, 'lst_002'), ('flannel', 22, 'lst_003'),
            ('bootleg', 24, 'lst_006'), ('corduroy', 32, 'lst_005'),
            ('track jacket', 45, 'lst_004'),
        ]:
            with self.subTest(ceiling=ceiling):
                results = tools.search_listings(description, max_price=ceiling)
                self.assertIn(known_id, [item['id'] for item in results])
                self.assertTrue(all(item['price'] <= ceiling for item in results))

    def test_ranking_stability_limit_and_null_brand(self):
        records = load_listings()[:3]
        for item in records:
            item.update(title='tee', description='', category='tops',
                        style_tags=[], colors=[], brand=None)
        records[2]['title'] = 'vintage tee'
        with patch.object(tools, 'load_listings', return_value=records), \
             patch.object(tools.config, 'SEARCH_RESULT_LIMIT', 2):
            results = tools.search_listings('vintage tee')
        self.assertEqual([item['id'] for item in results], ['lst_003', 'lst_001'])
        self.assertEqual(set(results[0]), set(records[0]))


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.item = load_listings()[1]  # null brand
        self.wardrobe = get_example_wardrobe()

    def test_populated_wardrobe_reaches_adapter_without_mutating_inputs(self):
        before = copy.deepcopy((self.item, self.wardrobe))
        with patch.object(tools, 'generate', return_value=' An outfit. ') as model:
            self.assertEqual(tools.suggest_outfit(self.item, self.wardrobe), 'An outfit.')
        prompt = model.call_args.args[0]
        data = json.loads(prompt.split('\nData:\n')[1])
        self.assertNotIn('brand', data['selected_item'])
        self.assertEqual(data['wardrobe_items'][0]['id'], self.wardrobe['items'][0]['id'])
        self.assertEqual((self.item, self.wardrobe), before)

    def test_empty_wardrobe_asks_for_general_advice(self):
        with patch.object(tools, 'generate', return_value='Consider sneakers.') as model:
            self.assertEqual(tools.suggest_outfit(self.item, {'items': []}), 'Consider sneakers.')
        self.assertIn('wardrobe is empty', model.call_args.args[0])
        self.assertIn('not pieces the user owns', model.call_args.args[0])

    def test_empty_inputs_do_not_call_model(self):
        with patch.object(tools, 'generate') as model:
            self.assertEqual(tools.suggest_outfit({}, self.wardrobe), tools.NO_ITEM_OUTFIT)
            self.assertEqual(tools.create_fit_card(' \n ', self.item), tools.NO_OUTFIT)
            self.assertEqual(tools.create_fit_card('An outfit.', {}), tools.NO_ITEM_CARD)
            model.assert_not_called()

    def test_blank_responses_are_explicit(self):
        with patch.object(tools, 'generate', return_value='  '):
            self.assertEqual(tools.suggest_outfit(self.item, self.wardrobe), tools.NO_OUTFIT_RESPONSE)
            self.assertEqual(tools.create_fit_card('An outfit.', self.item), tools.NO_CARD_RESPONSE)

    def test_model_failure_is_not_disguised_as_success(self):
        with patch.object(tools, 'generate', side_effect=ModelUnavailable('Offline')):
            with self.assertRaises(ModelUnavailable):
                tools.suggest_outfit(self.item, self.wardrobe)
            with self.assertRaises(ModelUnavailable):
                tools.create_fit_card('An outfit.', self.item)

    def test_card_receives_outfit_and_listing(self):
        before = copy.deepcopy(self.item)
        with patch.object(tools, 'generate', return_value='A caption.') as model:
            self.assertEqual(tools.create_fit_card('jeans and sneakers', self.item), 'A caption.')
        data = json.loads(model.call_args.args[0].split('\nData:\n')[1])
        self.assertEqual(data['outfit'], 'jeans and sneakers')
        self.assertEqual(data['selected_item']['id'], self.item['id'])
        self.assertEqual(self.item, before)


if __name__ == '__main__':
    unittest.main()

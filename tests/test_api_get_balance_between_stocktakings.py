from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from tests.test_helpers_stocktakings import TestHelpersStocktakingsTestCase


class GetBalanceBetweenStocktakingsAPITestCase(BaseAPITestCase):

    def test_get_balance_between_stocktakings(self):
        """
        This test ensures that the data returned by the API route for the
        balance between two stocktakingcollections is correct.
        """
        # The data required to generate the test case can be reused from the
        # unit test "test_helper_stocktakings".
        TestHelpersStocktakingsTestCase().\
            test_balance_between_stocktakings_two_stocktakings()

        # Prepare the request url and the request params.
        url = '/stocktakingcollections/balance'
        params = {'start_id': 1, 'end_id': 2}

        # Do the API request.
        res = self.get(url, role='admin', params=params)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'balance' in data
        balance = data['balance']

        # Check the data
        self.assertTrue('products' in balance)
        products = balance['products']

        # Check if all products are in the balance
        self.assertEqual({'1', '2', '3', '4'}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products['1']['purchase_count'], 3)
        self.assertEqual(products['2']['purchase_count'], 5)
        self.assertEqual(products['3']['purchase_count'], 8)
        self.assertEqual(products['4']['purchase_count'], 0)

        # Check purchase sum price
        self.assertEqual(products['1']['purchase_sum_price'], 900)
        self.assertEqual(products['2']['purchase_sum_price'], 250)
        self.assertEqual(products['3']['purchase_sum_price'], 800)
        self.assertEqual(products['4']['purchase_sum_price'], 0)

        # Check replenish count
        self.assertEqual(products['1']['replenish_count'], 10)
        self.assertEqual(products['2']['replenish_count'], 0)
        self.assertEqual(products['3']['replenish_count'], 5)
        self.assertEqual(products['4']['replenish_count'], 0)

        # Check differences
        self.assertEqual(products['1']['difference'], -57)
        self.assertEqual(products['2']['difference'], -20)
        self.assertEqual(products['3']['difference'], -10)
        self.assertEqual(products['4']['difference'], -30)

        # Check balance
        self.assertEqual(products['1']['balance'], -57 * 300)
        self.assertEqual(products['2']['balance'], -20 * 50)
        self.assertEqual(products['3']['balance'], -10 * 100)
        self.assertEqual(products['4']['balance'], -30 * 200)

        # Check overall balance
        self.assertEqual(balance['balance'], -25100)
        self.assertEqual(balance['loss'], 25100)
        self.assertEqual(balance['profit'], 0)

    def test_get_balance_between_stocktakings_missing_params(self):
        """
        This test ensures that the correct exceptions get raised when the
        request params are missing.
        """
        # Do a request without any params
        url = '/stocktakingcollections/balance'
        res = self.get(url, role='admin')
        self.assertException(res, exc.InvalidData)

        # Do a request with only the start id given.
        params = {'start_id': 1}
        res = self.get(url, role='admin', params=params)
        self.assertException(res, exc.InvalidData)

        # Do a request with only the end id given.
        params = {'end_id': 1}
        res = self.get(url, role='admin', params=params)
        self.assertException(res, exc.InvalidData)

    def test_get_balance_between_stocktakings_invalid_params(self):
        """
        This test ensures that the correct exceptions get raised when the
        request params are invalid.
        """
        # Do a request with only the end id given.
        params = {'start_id': 1, 'end_id': 'foo'}
        url = '/stocktakingcollections/balance'
        res = self.get(url, role='admin', params=params)
        self.assertException(res, exc.WrongType)

        # Do a request with with a lower end id than the start id.
        params = {'end_id': 1, 'start_id': 2}
        res = self.get(url, role='admin', params=params)
        self.assertException(res, exc.InvalidData)


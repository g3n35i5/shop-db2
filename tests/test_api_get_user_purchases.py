from shopdb.api import *
from tests.base_api import BaseAPITestCase
from flask import json


class GetUserPurchasesAPITestCase(BaseAPITestCase):

    def test_get_user_purchases(self):
        """This test ensures that all purchases made by a user are listed."""
        self.insert_default_purchases()
        res = self.get(url='/users/2/purchases')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'purchases' in data
        fields = ['id', 'timestamp', 'product_id', 'productprice', 'amount',
                  'revoked', 'price']        
        for i in data['purchases']:
            for x in fields:
                assert x in i

    def test_get_user_purchases_non_existing_user(self):
        """
        This test ensures that an exception is made if the user does not exist.
        """
        self.insert_default_purchases()
        res = self.get(url='/users/5/purchases')
        self.assertException(res, UserNotFound)

    def test_get_user_purchases_non_verified_user(self):
        """
        This test ensures that an exception is made if the user has not been
        verified yet.
        """
        self.insert_default_purchases()
        res = self.get(url='/users/4/purchases')
        self.assertException(res, UserIsNotVerified)

    def test_get_users_purchases_no_insert(self):
        """
        This test ensures that an empty list is returned for a user's
        purchases if he has not yet made any purchases.
        """
        res = self.get(url='/users/2/purchases')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'purchases' in data
        self.assertEqual(data['purchases'], [])

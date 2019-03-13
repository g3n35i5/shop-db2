from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class CreateStocktakingCollectionAPITestCase(BaseAPITestCase):

    def test_authorization(self):
        """This route should only be available for administrators"""
        res = self.post(url='/stocktakingcollections', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/stocktakingcollections', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_create_stocktaking_collection_as_admin(self):
        """Creating a StocktakingCollection as admin"""

        self.insert_default_stocktakingcollections()
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created stocktakingcollection.')

        collection = StocktakingCollection.query.filter_by(id=3).first()

        self.assertEqual(collection.id, 3)
        self.assertEqual(collection.admin_id, 1)
        self.assertFalse(collection.revoked)
        self.assertEqual(collection.revokehistory, [])
        api_stocktakings = collection.stocktakings.all()
        for i, _dict in enumerate(stocktakings):
            for key in _dict:
                self.assertEqual(getattr(api_stocktakings[i], key), _dict[key])

    def test_create_stocktakingcollection_non_existing_product(self):
        """
        If a product does not exist of an stocktakingcollection, an exception
        must be raised.
        """
        stocktakings = [{'product_id': 42, 'count': 100}]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_create_stocktakingcollection_set_product_inactive(self):
        """
        TODO
        """
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 0, 'set_inactive': True},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertFalse(Product.query.filter_by(id=2).first().active)

    def test_create_stocktakingcollection_set_product_inactive_wrong_count(self):
        """
        TODO
        """
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 10, 'set_inactive': True},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.CouldNotUpdateEntry)

    def test_create_stocktakingcollection_with_missing_data_I(self):
        """Creating a StocktakingCollection with missing data"""
        res = self.post(url='/stocktakingcollections', data={},
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_stocktakingcollection_with_missing_data_II(self):
        """Creating a StocktakingCollection with missing data for stocktaking"""
        stocktakings = [{'product_id': 1, 'count': 200},
                        {'product_id': 2}]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_stocktakingcollection_with_missing_data_III(self):
        """Creating a StocktakingCollection with empty stocktakings"""
        data = {'stocktakings': []}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_stocktakingcollection_with_unknown_field_I(self):
        """
        Creating a stocktakingcollection with unknown field in the
        collection itself should raise an exception.
        """
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings, 'Nonsense': 9}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_stocktakingcollection_with_unknown_field_II(self):
        """
        Creating a stocktakingcollection with unknown field in one of the
        stocktakings should raise an exception.
        """
        stocktakings = [
            {'product_id': 1, 'count': 100, 'Nonsense': 42},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_stocktakingcollection_with_wrong_type_I(self):
        """
        Creating a stocktakingcollection with wrong type in the
        stocktakingcollection itself should raise an exception.
        """
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': 42}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_stocktakingcollection_with_wrong_type_II(self):
        """
        Creating a stocktakingcollection with wrong type in one of the
        stocktakings should raise an exception.
        """
        stocktakings = [
            {'product_id': 1, 'count': '100'},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_stocktakingcollection_with_invalid_amount(self):
        """Creating a stocktakingcollection with negative amount"""
        stocktakings = [
            {'product_id': 1, 'count': -2},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)

    def test_create_stocktakingcollection_with_missing_product(self):
        """Creating a stocktakingcollection with missing product"""
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

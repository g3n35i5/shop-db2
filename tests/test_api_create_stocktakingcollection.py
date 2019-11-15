#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class CreateStocktakingCollectionAPITestCase(BaseAPITestCase):

    TIMESTAMP = datetime.datetime.strptime('2019-03-18 08:00:00',
                                           '%Y-%m-%d %H:%M:%S')

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

        # Set product 1 to non countable
        Product.query.filter_by(id=1).first().countable = False
        db.session.commit()

        stocktakings = [
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]

        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created stocktakingcollection.')

        collection = StocktakingCollection.query.filter_by(id=3).first()

        self.assertEqual(collection.id, 3)
        self.assertEqual(collection.timestamp, self.TIMESTAMP)
        self.assertEqual(collection.admin_id, 1)
        self.assertFalse(collection.revoked)
        self.assertEqual(collection.revokehistory, [])
        api_stocktakings = collection.stocktakings.all()
        for i, _dict in enumerate(stocktakings):
            for key in _dict:
                self.assertEqual(getattr(api_stocktakings[i], key), _dict[key])

    def test_create_stocktakingcollection_non_countable_product(self):
        """
        Only the products which are countable can be in a stocktaking.
        """
        # Set product 1 to non countable
        Product.query.filter_by(id=1).first().countable = False
        db.session.commit()

        stocktakings = [
            {'product_id': 1, 'count': 10},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]

        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidData)
        self.assertFalse(StocktakingCollection.query.all())

    def test_create_stocktakingcollection_non_existing_product(self):
        """
        If a product does not exist of an stocktakingcollection, an exception
        must be raised.
        """
        stocktakings = [{'product_id': 42, 'count': 100}]
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_create_stocktakingcollection_set_product_inactive(self):
        """
        This test ensures that a product is set to inactive if this is
        specified in the stocktaking.
        """
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 0, 'keep_active': True},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 0}
        ]
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Product.query.filter_by(id=2).first().active)
        self.assertFalse(Product.query.filter_by(id=4).first().active)

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
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_stocktakingcollection_with_missing_data_III(self):
        """Creating a StocktakingCollection with empty stocktakings"""
        data = {
            'stocktakings': [],
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
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
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp()),
            'Nonsense': 9
        }
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
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_stocktakingcollection_with_wrong_type_I(self):
        """
        Creating a stocktakingcollection with wrong type in the
        stocktakingcollection itself should raise an exception.
        """
        data = {
            'stocktakings': 42,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
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
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
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
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
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
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(self.TIMESTAMP.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_stocktakingcollection_with_missing_timestamp(self):
        """Creating a stocktakingcollection with missing product"""
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        data = {'stocktakings': stocktakings}
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_stocktakingcollection_with_invalid_timestamp(self):
        """Creating a stocktakingcollection with invalid timestamp"""
        stocktakings = [
            {'product_id': 1, 'count': 100},
            {'product_id': 2, 'count': 50},
            {'product_id': 3, 'count': 25},
            {'product_id': 4, 'count': 33}
        ]
        # Timestamp is invalid because it is in the future.
        timestamp = datetime.datetime.now() + datetime.timedelta(days=2)
        data = {
            'stocktakings': stocktakings,
            'timestamp': int(timestamp.timestamp())
        }
        res = self.post(url='/stocktakingcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidData)

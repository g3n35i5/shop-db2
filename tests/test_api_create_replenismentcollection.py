from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class CreateReplenishmentCollectionsAPITestCase(BaseAPITestCase):

    def test_create_replenishment_collection_as_admin(self):
        """Creating a ReplenishmentCollection as admin"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created replenishmentcollection.')

        replcoll = ReplenishmentCollection.query.filter_by(id=3).first()
        self.assertEqual(replcoll.id, 3)
        self.assertEqual(replcoll.admin_id, 1)
        self.assertEqual(replcoll.comment, 'My test comment')
        self.assertEqual(replcoll.price, 220)
        self.assertFalse(replcoll.revoked)
        self.assertEqual(replcoll.revokehistory, [])
        repls = replcoll.replenishments.all()
        for i, dict in enumerate(replenishments):
            for key in dict:
                self.assertEqual(getattr(repls[i], key), dict[key])

    def test_create_replenishmentcollection_as_user(self):
        """Creating a ReplenishmentCollection as user"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_create_replenishmentcollection_with_missing_data_I(self):
        """Creating a ReplenishmentCollection with missing data"""
        res = self.post(url='/replenishmentcollections', data={},
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishmentcollection_with_missing_data_II(self):
        """Creating a ReplenishmentCollection with missing data for repl"""
        replenishments = [{'product_id': 1, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishmentcollection_with_unknown_field_I(self):
        """
        Creating a replenishmentcollection with unknown field in the
        collection itself should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'Nonsense': 9,
                'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_replenishmentcollection_with_unknown_field_II(self):
        """
        Creating a replenishmentcollection with unknown field in one of the
        replenishments should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'Nonsense': 98,
                           'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_replenishmentcollection_with_wrong_type_I(self):
        """
        Creating a replenishmentcollection with wrong type in the
        replenishmentcollection itself should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 'Hallo',
                           'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_replenishmentcollection_with_wrong_type_II(self):
        """
        Creating a replenishmentcollection with wrong type in one of the
        replenishments should raise an exception.
        """
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': '2', 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_replenishmentcollection_with_invalid_amount(self):
        """Creating a replenishmentcollection with negative amount"""
        replenishments = [{'product_id': 1, 'amount': -10, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)

    def test_create_replenishmentcollection_with_non_existing_product(self):
        """Creating a replenishmentcollection with a non existing product_id"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 20, 'amount': 20, 'total_price': 20}]
        data = {'replenishments': replenishments, 'comment': 'My test comment'}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ProductNotFound)

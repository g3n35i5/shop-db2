from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
import pdb


class CreateReplenishmentCollectionsAPITestCase(BaseAPITestCase):

    def test_create_replenishment_collection_as_admin(self):
        """Creating a ReplenishmentCollection as admin"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Created deposit.')

        replcoll = ReplenishmentCollection.query.first()
        self.assertEqual(replcoll.id, 1)
        self.assertEqual(replcoll.admin_id, 1)
        self.assertEqual(replcoll.price, 220)
        self.assertFalse(replcoll.revoked)
        self.assertEqual(replcoll.revokehistory, [])
        repls = replcoll.replenishments.all()
        for i, dict in enumerate(replenishments):
            for key in dict:
                self.assertEqual(getattr(repls[i], key), dict[key])

    def test_create_replenishment_collection_as_user(self):
        """Creating a ReplenishmentCollection as user"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_create_replenishment_collection_with_missing_data_I(self):
        """Creating a ReplenishmentCollection with missing data for replcoll"""
        data = {'admin_id': 1}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishment_collection_with_missing_data_II(self):
        """Creating a ReplenishmentCollection with missing data for repl"""
        replenishments = [{'product_id': 1, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_replenishment_collection_with_unknown_field_I(self):
        """Creating a ReplenishmentCollection with unknown field in replcoll"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments, 'Nonsense': 9}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_replenishment_collection_with_unknown_field_II(self):
        """Creating a ReplenishmentCollection with unknown field in repl"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'Nonsense': 98,
                           'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_create_replenishment_collection_with_wrong_type_I(self):
        """Creating a ReplenishmentCollection with wrong type in replcoll"""
        replenishments = [{'product_id': 1, 'amount': 'Hallo',
                           'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_replenishment_collection_with_wrong_type_II(self):
        """Creating a ReplenishmentCollection with wrong type in repl"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': '2', 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_create_replenishment_collection_with_invalid_amount(self):
        """Creating a ReplenishmentCollection with negative amount"""
        replenishments = [{'product_id': 1, 'amount': -10, 'total_price': 200},
                          {'product_id': 2, 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidAmount)

    def test_create_replenishment_collection_with_invalid_product(self):
        """Creating a ReplenishmentCollection with a nonexisting product_id"""
        replenishments = [{'product_id': 1, 'amount': 100, 'total_price': 200},
                          {'product_id': 20, 'amount': 20, 'total_price': 20}]
        data = {'admin_id': 1, 'replenishments': replenishments}
        res = self.post(url='/replenishmentcollections', data=data,
                        role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ProductNotFound)

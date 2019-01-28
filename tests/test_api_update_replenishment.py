from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
import pdb


class UpdateReplenishmentAPITestCase(BaseAPITestCase):

    def test_update_replenishment_as_admin(self):
        """Updating amount and price of a single replenishment"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 20, 'total_price': 400}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message', 'updated_fields' in data
        self.assertEqual(data['message'], 'Updated replenishment.')
        self.assertEqual(data['updated_fields'], ['amount', 'total_price'])
        repl = Replenishment.query.filter_by(id=1).first()
        self.assertEqual(repl.amount, 20)
        self.assertEqual(repl.total_price, 400)

    def test_update_replenishment_no_changes(self):
        """Updating a single replenishment with same amount and price"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 10, 'total_price': 3000}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_replenishment_as_user(self):
        """Updating a single replenishment as user"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 0, 'total_price': 0}
        res = self.put(url='/replenishments/1', data=data, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_replenishment_with_invalid_id(self):
        """Updating a single replenishment that does not exist"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 0, 'total_price': 0}
        res = self.put(url='/replenishments/5', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_replenishment_with_forbidden_field(self):
        """Updating a forbidden field of a single replenishment"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 0, 'total_price': 0, 'product_id': 1}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_replenishment_with_unknown_field(self):
        """Updating a unknown field of a single replenishment"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 0, 'total_price': 0, 'Nonse': '2'}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_replenishment_with_wrong_type(self):
        """Updating a field of a single replenishment with a wrong type"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 0, 'total_price': '1'}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_replenishment_with_less_data(self):
        """Updating a single replenishment with less data"""
        self.insert_default_replenishmentcollections()
        data = {'amount': 0}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message', 'updated_fields' in data
        self.assertEqual(data['message'], 'Updated replenishment.')
        self.assertEqual(data['updated_fields'], ['amount'])

    def test_update_replenishment_revoke(self):
        """Revoking a single replenishment"""
        self.insert_default_replenishmentcollections()
        data = {'revoked': True}
        res = self.put(url='/replenishments/2', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message', 'updated_fields' in data
        self.assertEqual(data['message'], 'Updated replenishment.')
        self.assertEqual(data['updated_fields'], ['revoked'])
        repl = Replenishment.query.filter_by(id=2).first()
        self.assertTrue(repl.revoked)

    def test_update_replenishment_revoke_all(self):
        """Revoking a all replenishments of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        data = {'revoked': True}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message', 'updated_fields' in data
        self.assertEqual(data['message'], 'Updated replenishment.')
        self.assertEqual(data['updated_fields'], ['revoked'])
        repl = Replenishment.query.filter_by(id=1).first()
        self.assertTrue(repl.revoked)
        data = {'revoked': True}
        res = self.put(url='/replenishments/2', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message', 'updated_fields' in data
        self.assertEqual(data['message'],
                'Updated replenishment. Revoked ReplenishmentCollection ID: 1')
        self.assertEqual(data['updated_fields'], ['revoked'])
        repl = Replenishment.query.filter_by(id=2).first()
        self.assertTrue(repl.revoked)
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertTrue(replcoll.revoked)
        self.assertEqual(replcoll.price, 0)

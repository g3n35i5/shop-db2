from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
import pdb


class UpdateReplenishmentAPITestCase(BaseAPITestCase):
    def _insert_testdata(self):
        product1 = Product.query.filter_by(id=1).first()
        product2 = Product.query.filter_by(id=2).first()
        product3 = Product.query.filter_by(id=3).first()
        rc1 = ReplenishmentCollection(admin_id=1, revoked=False)
        rc2 = ReplenishmentCollection(admin_id=2, revoked=False)
        for r in [rc1, rc2]:
            db.session.add(r)
        db.session.flush()
        rep1 = Replenishment(replcoll_id=rc1.id, product_id=product1.id,
                             amount=10, total_price=10*product1.price)
        rep2 = Replenishment(replcoll_id=rc1.id, product_id=product2.id,
                             amount=20, total_price=20*product2.price)
        rep3 = Replenishment(replcoll_id=rc2.id, product_id=product3.id,
                             amount=5, total_price=5*product3.price)
        for r in [rep1, rep2, rep3]:
            db.session.add(r)
        db.session.commit()

    def test_delete_replenishment_as_admin_I(self):
        '''Deleting a single replenishment as admin'''
        self._insert_testdata()
        data = {'amount': 0, 'total_price': 0, 'delete': True}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Deleted Replenishment.')
        repl = Replenishment.query.filter_by(id=1).first()
        self.assertEqual(repl, None)

    def test_delete_replenishment_as_admin_II(self):
        '''Deleting a single replenishment leding to deletion of replcoll'''
        self._insert_testdata()
        data = {'amount': 0, 'total_price': 0, 'delete': True}
        res = self.put(url='/replenishments/3', data=data, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Deleted Replenishment. Deletetd'
                                          + ' ReplenishmentCollection ID: 2')
        repl = Replenishment.query.filter_by(id=3).first()
        self.assertEqual(repl, None)
        replcoll = ReplenishmentCollection.query.filter_by(id=2).first()
        self.assertEqual(replcoll, None)

    def test_update_replenishment_as_admin(self):
        '''Updating amount and price of a single replenishment'''
        self._insert_testdata()
        data = {'amount': 20, 'total_price': 400, 'delete': False}
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
        '''Updating a single replenishment with same amount and price'''
        self._insert_testdata()
        data = {'amount': 10, 'total_price': 3000, 'delete': False}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_replenishment_as_user(self):
        '''Updating a single replenishment as user'''
        data = {'amount': 0, 'total_price': 0, 'delete': True}
        res = self.put(url='/replenishments/1', data=data, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_replenishment_with_invalid_id(self):
        '''Updating a single replenishment that does not exist'''
        self._insert_testdata()
        data = {'amount': 0, 'total_price': 0, 'delete': True}
        res = self.put(url='/replenishments/4', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentNotFound)

    def test_update_replenishment_with_forbidden_field(self):
        '''Updating a forbidden field of a single replenishment'''
        self._insert_testdata()
        data = {'amount': 0, 'total_price': 0, 'delete': True, 'product_id': 1}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_replenishment_with_unknown_field(self):
        '''Updating a unknown field of a single replenishment'''
        self._insert_testdata()
        data = {'amount': 0, 'total_price': 0, 'delete': True, 'Nonse': '2'}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_replenishment_with_wrong_type(self):
        '''Updating a field of a single replenishment with a wrong type'''
        self._insert_testdata()
        data = {'amount': 0, 'total_price': 0, 'delete': 'yes'}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_replenishment_with_data_missing(self):
        '''Updating a single replenishment with no amount given'''
        self._insert_testdata()
        data = {'amount': 0, 'total_price': 0}
        res = self.put(url='/replenishments/1', data=data, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

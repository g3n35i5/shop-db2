from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
import pdb


class UpdateReplenishmentCollectionsAPITestCase(BaseAPITestCase):
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

    def test_revoke_replenishment_collection_as_admin_I(self):
        '''Revoke a replenishmentcollection as admin'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Revoked ReplenishmentCollection.')
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.revoked, True)
        required = ['id', 'revoked', 'timestamp']
        for item in required:
            assert item in replcoll.revokehistory[0]

    def test_revoke_replenishment_collection_as_admin_II(self):
        '''Revoke a replenishmentcollection as admin multiple times'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 201)
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': False}, role='admin')
        self.assertEqual(res.status_code, 201)
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 201)
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.revoked, True)
        self.assertEqual(len(replcoll.revokehistory), 3)
        required = ['id', 'revoked', 'timestamp']
        for i in replcoll.revokehistory:
            for item in required:
                assert item in i

    def test_revoke_replenishment_collection_as_user(self):
        '''Revoking a replenishmentcollection as user'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_replenishment_collection_no_changes(self):
        '''Revoking a replenishmentcollection with no changes'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': False}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_replenishment_collection_with_invalid_id(self):
        '''Revoking a replenishmentcollection that doesnt exist'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/4',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentCollectionNotFound)

    def test_update_replenishment_collection_with_forbidden_field(self):
        '''Revoking forbidden fields of a replenishmentcollection'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True, 'timestamp': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_replenishment_collection_with_unknown_field(self):
        '''Revoking nonexisting fields of a replenishmentcollection'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={'Nonsense': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_replenishment_collection_with_wrong_type(self):
        '''Revoking fields of a replenishmentcollection with wrong types'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': 'yes'}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_replenishment_collection_with_no_data(self):
        '''Revoking a replenishmentcollection with no data'''
        self._insert_testdata()
        res = self.put(url='/replenishmentcollections/1',
                       data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

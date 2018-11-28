from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateReplenishmentCollectionsAPITestCase(BaseAPITestCase):

    def test_revoke_replenishment_collection_as_admin_I(self):
        """Revoke a replenishmentcollection as admin"""
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Updated replenishmentcollection.')
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.revoked, True)
        required = ['id', 'revoked', 'timestamp']
        for item in required:
            assert item in replcoll.revokehistory[0]

    def test_revoke_replenishment_collection_as_admin_II(self):
        """Revoke a replenishmentcollection as admin multiple times"""
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
        """Revoking a replenishmentcollection as user"""
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_replenishment_collection_no_changes(self):
        """Revoking a replenishmentcollection with no changes"""
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': False}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_replenishment_collection_with_invalid_id(self):
        """Revoking a replenishmentcollection that doesnt exist"""
        res = self.put(url='/replenishmentcollections/4',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentCollectionNotFound)

    def test_update_replenishment_collection_with_forbidden_field(self):
        """Revoking forbidden fields of a replenishmentcollection"""
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True, 'timestamp': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_replenishment_collection_with_unknown_field(self):
        """Revoking nonexisting fields of a replenishmentcollection"""
        res = self.put(url='/replenishmentcollections/1',
                       data={'Nonsense': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_replenishment_collection_with_wrong_type(self):
        """Revoking fields of a replenishmentcollection with wrong types"""
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': 'yes'}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_replenishment_collection_with_no_data(self):
        """Revoking a replenishmentcollection with no data"""
        res = self.put(url='/replenishmentcollections/1',
                       data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

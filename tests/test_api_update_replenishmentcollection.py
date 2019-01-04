from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class UpdateReplenishmentCollectionsAPITestCase(BaseAPITestCase):

    def test_revoke_replenishmentcollection(self):
        """Revoke a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
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

    def test_revoke_replenishmentcollection_multiple_times(self):
        """Revoke a replenishmentcollection multiple times"""
        self.insert_default_replenishmentcollections()
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

    def test_update_replenishmentcollection_comment(self):
        """Update the comment of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        res = self.put(url='/replenishmentcollections/1',
                       data={'comment': 'FooBar'}, role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Updated replenishmentcollection.')
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll.comment, 'FooBar')

    def test_revoke_replenishmentcollection_as_user(self):
        """Revoking a replenishmentcollection as user should be forbidden"""
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_update_replenishmentcollection_no_changes(self):
        """Revoking a replenishmentcollection with no changes"""
        self.insert_default_replenishmentcollections()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': False}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_non_existing_replenishmentcollection(self):
        """Revoking a replenishmentcollection that doesnt exist"""
        self.insert_default_replenishmentcollections()
        res = self.put(url='/replenishmentcollections/4',
                       data={'revoked': True}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_replenishmentcollection_forbidden_field(self):
        """Updating forbidden fields of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': True, 'timestamp': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)

    def test_update_replenishmentcollection_unknown_field(self):
        """Update non existing fields of a replenishmentcollection"""
        self.insert_default_replenishmentcollections()
        res = self.put(url='/replenishmentcollections/1',
                       data={'Nonsense': ''}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_replenishmentcollection_wrong_type(self):
        """Update fields of a replenishmentcollection with wrong types"""
        self.insert_default_replenishmentcollections()
        res = self.put(url='/replenishmentcollections/1',
                       data={'revoked': 'yes'}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)

    def test_update_replenishmentcollection_with_no_data(self):
        """Update a replenishmentcollection with no data"""
        self.insert_default_replenishmentcollections()
        res = self.put(url='/replenishmentcollections/1',
                       data={}, role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class DeleteReplenishmentCollectionAPITestCase(BaseAPITestCase):

    def test_delete_replenishmentcolletion_as_admin(self):
        """Deleting a single replenishmentcollection as admin"""
        res = self.delete(url='/replenishmentcollections/1', role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        assert 'Deleted ReplenishmentCollection.' in data['message']
        assert 'Deleted Replenishment ID 1.' in data['message']
        assert 'Deleted Replenishment ID 2.' in data['message']
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll, None)
        repl1 = Replenishment.query.filter_by(id=1).first()
        self.assertEqual(repl1, None)
        repl2 = Replenishment.query.filter_by(id=2).first()
        self.assertEqual(repl2, None)

    def test_delete_replenishmentcollection_as_user(self):
        """Deleting a replenishmentcollection as user should raise an error"""
        res = self.delete(url='/replenishmentcollections/1', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_delete_replenishmentcollection_with_invalid_id(self):
        """Trying to delete a single replenishment with invalid id"""
        res = self.delete(url='/replenishmentcollections/3', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentCollectionNotFound)

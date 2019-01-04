from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class DeleteReplenishmentAPITestCase(BaseAPITestCase):

    def test_delete_replenishment_as_admin_I(self):
        """Deleting a single replenishment as admin"""
        self.insert_default_replenishmentcollections()
        res = self.delete(url='/replenishments/1', role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Deleted Replenishment.')
        repl = Replenishment.query.filter_by(id=1).first()
        self.assertEqual(repl, None)

    def test_delete_replenishment_as_admin_II(self):
        """
        If the last member of a replenishmentcollection is deleted, it should
        also be deleted itself.
        """
        self.insert_default_replenishmentcollections()
        self.delete(url='/replenishments/3', role='admin')
        res = self.delete(url='/replenishments/4', role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        self.assertEqual(data['message'], 'Deleted Replenishment. Deleted'
                                          + ' ReplenishmentCollection ID: 2')
        repl = Replenishment.query.filter_by(id=3).first()
        self.assertEqual(repl, None)
        replcoll = ReplenishmentCollection.query.filter_by(id=2).first()
        self.assertEqual(replcoll, None)

    def test_delete_replenishment_as_user(self):
        """Trying to delete a single replenishment as user"""
        res = self.delete(url='/replenishments/1', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_delete_replenishment_with_invalid_id(self):
        """Trying to delete a single replenishment with invalid id"""
        res = self.delete(url='/replenishments/5', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

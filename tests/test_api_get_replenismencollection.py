from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetReplenishmentCollectionAPITestCase(BaseAPITestCase):

    def test_get_replenishment_collection_as_admin(self):
        """Getting a single ReplenishmentCollection as admin"""
        res = self.get(url='/replenishmentcollections/1', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'replenishmentcollection' in data
        replcoll = data['replenishmentcollection']
        required_replcoll = ['id', 'timestamp', 'admin_id', 'price',
                             'replenishments', 'revoked', 'revokehistory']
        required_repl = ['id', 'replcoll_id', 'product_id', 'amount',
                         'total_price']
        assert all(x in replcoll for x in required_replcoll)
        repls = replcoll['replenishments']
        for repl in repls:
            assert all(x in repl for x in required_repl)

    def test_get_replenishment_collection_as_user(self):
        """Trying to get a single ReplenishmentCollection as user"""
        res = self.get(url='/replenishmentcollections/2', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_get_non_existing_replenishmentcollection(self):
        """
        This test ensures that an exception is raised if the requested
        replenishmentcollection does not exist.
        """
        res = self.get(url='/replenishmentcollections/5', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentCollectionNotFound)

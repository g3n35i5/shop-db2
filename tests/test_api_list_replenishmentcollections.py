from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListReplenishmentCollectionsAPITestCase(BaseAPITestCase):

    def test_list_replenishment_collections_as_admin(self):
        """Getting a list of all ReplenishmentCollections as admin"""
        self.insert_default_replenishmentcollections()
        res = self.get(url='/replenishmentcollections', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'replenishmentcollections' in data
        replcolls = data['replenishmentcollections']
        required = ['id', 'timestamp', 'admin_id', 'price', 'revoked',
                    'comment']
        for replcoll in replcolls:
            assert all(x in replcoll for x in required)

    def test_list_replenishment_collections_as_user(self):
        """Trying to get a list of all ReplenishmentCollections as user"""
        res = self.get(url='/replenishmentcollections', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

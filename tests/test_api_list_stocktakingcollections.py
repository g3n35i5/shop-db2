from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListStocktakingCollectionsAPITestCase(BaseAPITestCase):

    def test_list_stocktaking_collections_as_admin(self):
        """Getting a list of all StocktakingCollections as admin"""
        self.insert_default_stocktakingcollections()
        res = self.get(url='/stocktakingcollections', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'stocktakingcollections' in data
        collecttions = data['stocktakingcollections']
        required = ['id', 'timestamp', 'admin_id', 'revoked']
        for collection in collecttions:
            assert all(x in collection for x in required)

    def test_list_stocktaking_collections_as_user(self):
        """Trying to get a list of all StocktakingCollections as user"""
        res = self.get(url='/stocktakingcollections', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetRefundsAPITestCase(BaseAPITestCase):

    def test_get_refunds_as_admin(self):
        """Test for geting a single refund"""
        # Do 5 refunds
        self.insert_default_refunds()
        res = self.get(url='/refunds/2', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'refund' in data
        refund = data['refund']
        self.assertEqual(refund['id'], 2)
        self.assertEqual(refund['user_id'], 2)
        self.assertEqual(refund['total_price'], 200)
        self.assertFalse(refund['revoked'])

        required = ['id', 'timestamp', 'user_id', 'total_price', 'comment',
                    'revoked', 'revokehistory']
        assert all(x in refund for x in required)

    def test_get_non_existing_refund(self):
        """Getting a non existing refund should raise an exception"""
        self.insert_default_refunds()
        res = self.get(url='/refunds/6', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

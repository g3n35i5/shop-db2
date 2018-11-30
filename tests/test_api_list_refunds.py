from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListRefundsAPITestCase(BaseAPITestCase):

    def test_list_refunds_as_admin(self):
        """Test for listing all refunds as admin"""
        # Do 5 refunds
        self.insert_default_refunds()
        res = self.get(url='/refunds', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'refunds' in data
        refunds = data['refunds']
        self.assertEqual(len(refunds), 5)
        self.assertEqual(refunds[0]['user_id'], 1)
        self.assertEqual(refunds[1]['user_id'], 2)
        self.assertEqual(refunds[2]['user_id'], 2)
        self.assertEqual(refunds[3]['user_id'], 3)
        self.assertEqual(refunds[4]['user_id'], 1)

        required = ['id', 'timestamp', 'total_price', 'comment', 'admin_id',
                    'revoked']
        for refund in refunds:
            assert all(x in refund for x in required)

    def test_list_refunds_as_user(self):
        """Test for listing all refunds without token. This should not be
           possible."""
        res = self.get(url='/refunds')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

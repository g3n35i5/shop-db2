from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListDepositsAPITestCase(BaseAPITestCase):

    def test_list_deposits_as_admin(self):
        """Test for listing all deposits as admin"""
        # Do 5 deposits
        self.insert_default_deposits()
        res = self.get(url='/deposits', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'deposits' in data
        deposits = data['deposits']
        self.assertEqual(len(deposits), 5)
        self.assertEqual(deposits[0]['user_id'], 1)
        self.assertEqual(deposits[1]['user_id'], 2)
        self.assertEqual(deposits[2]['user_id'], 2)
        self.assertEqual(deposits[3]['user_id'], 3)
        self.assertEqual(deposits[4]['user_id'], 1)

        required = ['id', 'timestamp', 'amount', 'comment', 'admin_id',
                    'revoked']
        for deposit in deposits:
            assert all(x in deposit for x in required)

    def test_list_deposits_as_user(self):
        """Test for listing all deposits without token. This should not be
           possible."""
        res = self.get(url='/deposits')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListPayoffsAPITestCase(BaseAPITestCase):
    def test_authorization(self):
        """This route should only be available for administrators"""
        res = self.get(url='/payoffs')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url='/payoffs', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url='/payoffs', role='admin')
        self.assertEqual(res.status_code, 200)

    def test_list_payoffs_as_admin(self):
        """Test for listing all payoffs as admin"""
        # Do 2 payoffs
        self.insert_default_payoffs()
        res = self.get(url='/payoffs', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'payoffs' in data
        payoffs = data['payoffs']
        self.assertEqual(len(payoffs), 2)
        self.assertEqual(payoffs[0]['amount'], 100)
        self.assertEqual(payoffs[1]['amount'], 200)

        required = ['id', 'timestamp', 'amount', 'comment', 'admin_id',
                    'revoked']
        for payoff in payoffs:
            assert all(x in payoff for x in required)

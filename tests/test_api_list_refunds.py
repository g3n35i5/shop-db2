from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListRefundsAPITestCase(BaseAPITestCase):
    def insert_test_refunds(self):
        """Helper function to insert some test refunds"""
        r1 = Refund(user_id=1, total_price=100, admin_id=1,
                    comment='Test refund')
        r2 = Refund(user_id=2, total_price=200, admin_id=1,
                    comment='Test refund')
        r3 = Refund(user_id=2, total_price=500, admin_id=1,
                    comment='Test refund')
        r4 = Refund(user_id=3, total_price=300, admin_id=1,
                    comment='Test refund')
        r5 = Refund(user_id=1, total_price=600, admin_id=1,
                    comment='Test refund')
        for r in [r1, r2, r3, r4, r5]:
            db.session.add(r)
        db.session.commit()

    def test_list_refunds_as_admin(self):
        """Test for listing all refunds as admin"""
        # Do 5 refunds
        self.insert_test_refunds()
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

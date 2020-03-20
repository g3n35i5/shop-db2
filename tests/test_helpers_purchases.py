#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from datetime import datetime

import shopdb.helpers.purchases as purchase_helpers
from shopdb.api import db
from shopdb.models import Purchase
from tests.base_api import BaseAPITestCase


class TestHelpersPurchasesTestCase(BaseAPITestCase):
    def test_get_purchase_amount_in_interval(self):
        """
        This test checks the "get_purchase_amount_in_interval" helper function.
        """
        # Insert some purchases
        t1 = datetime.strptime('2018-02-01 09:00:00', '%Y-%m-%d %H:%M:%S')
        db.session.add(Purchase(user_id=1, product_id=1, amount=1, timestamp=t1))
        t2 = datetime.strptime('2018-02-02 09:00:00', '%Y-%m-%d %H:%M:%S')
        db.session.add(Purchase(user_id=1, product_id=1, amount=5, timestamp=t2, revoked=True))
        t3 = datetime.strptime('2018-02-03 09:00:00', '%Y-%m-%d %H:%M:%S')
        db.session.add(Purchase(user_id=2, product_id=1, amount=8, timestamp=t3))
        t4 = datetime.strptime('2018-02-04 09:00:00', '%Y-%m-%d %H:%M:%S')
        db.session.add(Purchase(user_id=3, product_id=2, amount=2, timestamp=t4))
        db.session.commit()

        # Get purchases in interval (second is revoked!)
        purchase_amount = purchase_helpers.get_purchase_amount_in_interval(product_id=1, start=t1, end=t4)
        self.assertEqual(9, purchase_amount)

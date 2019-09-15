#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
from tests.base import BaseTestCase


class RefundModelTestCase(BaseTestCase):

    def test_refund_link_to_its_user(self):
        """
        This test checks whether the reference to the user of a refund is
        working correctly.
        """
        db.session.add(Refund(
            user_id=1,
            total_price=1,
            admin_id=1,
            comment='Foo')
        )
        db.session.commit()
        refund = Refund.query.filter_by(id=1).first()
        self.assertEqual(refund.user, User.query.filter_by(id=1).first())

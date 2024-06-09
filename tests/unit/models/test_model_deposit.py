#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from shopdb.api import db
from shopdb.models import Deposit, User
from tests.base import BaseTestCase


class DepositModelTestCase(BaseTestCase):
    def test_deposit_link_to_its_user(self):
        """This test checks whether the reference to the user of a deposit is
        working correctly.
        """
        db.session.add(Deposit(user_id=1, amount=1, admin_id=1, comment="Foo"))
        db.session.commit()
        deposit = Deposit.query.filter_by(id=1).first()
        self.assertEqual(deposit.user, User.query.filter_by(id=1).first())

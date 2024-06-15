#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from tests.base_api import BaseAPITestCase


class ListDepositsAPITestCase(BaseAPITestCase):
    def test_list_deposits_as_admin(self) -> None:
        """Test for listing all deposits as admin"""
        # Do 5 deposits
        self.insert_default_deposits()
        res = self.get(url="/deposits", role="admin")
        self.assertEqual(res.status_code, 200)
        deposits = json.loads(res.data)
        self.assertEqual(len(deposits), 5)
        self.assertEqual(deposits[0]["user_id"], 1)
        self.assertEqual(deposits[1]["user_id"], 2)
        self.assertEqual(deposits[2]["user_id"], 2)
        self.assertEqual(deposits[3]["user_id"], 3)
        self.assertEqual(deposits[4]["user_id"], 1)

        required = ["id", "timestamp", "amount", "comment", "admin_id", "revoked"]
        for deposit in deposits:
            assert all(x in deposit for x in required)

    def test_list_deposits_as_user(self) -> None:
        """Test for listing all deposits without token. This should not be
        possible.
        """
        res = self.get(url="/deposits")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

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
        payoffs = json.loads(res.data)
        self.assertEqual(len(payoffs), 3)
        self.assertEqual(payoffs[0]['amount'], 100)
        self.assertEqual(payoffs[1]['amount'], 200)
        self.assertEqual(payoffs[2]['amount'], -50)

        required = ['id', 'timestamp', 'amount', 'comment', 'admin_id',
                    'revoked']
        for payoff in payoffs:
            assert all(x in payoff for x in required)

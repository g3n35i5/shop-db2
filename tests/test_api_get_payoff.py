#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetPayoffAPITestCase(BaseAPITestCase):

    def test_authorization(self):
        """This route should only be available for administrators"""
        self.insert_default_payoffs()
        res = self.get(url='/payoffs/2')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url='/payoffs/2', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url='/payoffs/2', role='admin')
        self.assertEqual(res.status_code, 200)

    def test_get_payoff(self):
        """Test for getting a single payoff"""
        self.insert_default_payoffs()
        res = self.get(url='/payoffs/2', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'payoff' in data
        payoff = data['payoff']
        self.assertEqual(payoff['id'], 2)
        self.assertEqual(payoff['amount'], 200)
        self.assertFalse(payoff['revoked'])

        required = ['id', 'timestamp', 'amount', 'comment',
                    'revoked', 'revokehistory']
        assert all(x in payoff for x in required)

    def test_get_non_existing_payoff(self):
        """Getting a non existing payoff should raise an exception"""
        self.insert_default_payoffs()
        res = self.get(url='/payoffs/3', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

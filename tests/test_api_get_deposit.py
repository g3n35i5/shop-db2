#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetDepositAPITestCase(BaseAPITestCase):

    def test_get_single_deposit(self):
        """Test for getting a single deposit"""
        # Insert test deposits
        self.insert_default_deposits()
        res = self.get(url='/deposits/3')
        self.assertEqual(res.status_code, 200)
        deposit = json.loads(res.data)
        self.assertEqual(deposit['id'], 3)
        self.assertEqual(deposit['user_id'], 2)
        self.assertEqual(deposit['amount'], 500)
        self.assertFalse(deposit['revoked'])

    def test_get_non_existing_deposit(self):
        """Getting a non existing deposit should raise an error."""
        res = self.get(url='/deposits/6')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_deposit_revokehistory(self):
        """Getting the revokehistory of a single deposit"""
        self.insert_default_deposits()
        deprevoke = DepositRevoke(deposit_id=1, admin_id=1, revoked=True)
        db.session.add(deprevoke)
        deprevoke = DepositRevoke(deposit_id=1, admin_id=1, revoked=False)
        db.session.add(deprevoke)
        deprevoke = DepositRevoke(deposit_id=1, admin_id=1, revoked=True)
        db.session.add(deprevoke)

        res = self.get(url='/deposits/1')
        deposit = json.loads(res.data)
        self.assertEqual(len(deposit['revokehistory']), 3)
        self.assertTrue(deposit['revokehistory'][0]['revoked'])
        self.assertFalse(deposit['revokehistory'][1]['revoked'])
        self.assertTrue(deposit['revokehistory'][2]['revoked'])

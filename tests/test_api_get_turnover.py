#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetTurnoverAPITestCase(BaseAPITestCase):

    def test_get_single_turnover(self):
        """Test for getting a single turnover"""
        # Insert test turnovers
        self.insert_default_turnovers()
        res = self.get(url='/turnovers/3')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'turnover' in data
        turnover = data['turnover']
        self.assertEqual(turnover['id'], 3)
        self.assertEqual(turnover['amount'], -100)
        self.assertFalse(turnover['revoked'])

    def test_get_non_existing_turnover(self):
        """Getting a non existing turnover should raise an error."""
        res = self.get(url='/turnovers/6')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_turnover_revokehistory(self):
        """Getting the revokehistory of a single turnover"""
        self.insert_default_turnovers()
        trevoke = TurnoverRevoke(turnover_id=1, admin_id=1, revoked=True)
        db.session.add(trevoke)
        trevoke = TurnoverRevoke(turnover_id=1, admin_id=1, revoked=False)
        db.session.add(trevoke)
        trevoke = TurnoverRevoke(turnover_id=1, admin_id=1, revoked=True)
        db.session.add(trevoke)

        res = self.get(url='/turnovers/1')
        data = json.loads(res.data)
        turnover = data['turnover']
        assert 'revokehistory' in turnover
        self.assertEqual(len(turnover['revokehistory']), 3)
        self.assertTrue(turnover['revokehistory'][0]['revoked'])
        self.assertFalse(turnover['revokehistory'][1]['revoked'])
        self.assertTrue(turnover['revokehistory'][2]['revoked'])

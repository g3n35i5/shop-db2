#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class PendingVerificationsAPITestCase(BaseAPITestCase):
    def test_get_pending_verifications(self):
        """Testing getting a list of all non verified users"""
        # This route should only be available for administrators
        res = self.get(url='/verifications')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

        res = self.get(url='/verifications', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

        res = self.get(url='/verifications', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'pending_validations' in data
        pending_validations = data['pending_validations']
        self.assertEqual(len(pending_validations), 1)
        self.assertEqual(pending_validations[0]['id'], 4)
        self.assertEqual(pending_validations[0]['firstname'], 'Daniel')
        self.assertEqual(pending_validations[0]['lastname'], 'Lee')

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.api import app
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ToggleMaintenanceAPITestCase(BaseAPITestCase):
    def test_toggle_maintenance_mode_authorization(self):
        """This route should only be available for administrators"""
        res = self.post(url='/maintenance', data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/maintenance', data={}, role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url='/maintenance', data={}, role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_turn_on_maintenance_mode(self):
        """
        This test ensures that the maintenance mode can be activated.
        """
        self.assertFalse(app.config['MAINTENANCE'])
        res = self.post(url='/maintenance', data={'state': True}, role='admin')
        self.assertTrue(app.config['MAINTENANCE'])
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['message'], 'Turned maintenance mode on.')

    def test_turn_off_maintenance_mode(self):
        """
        This test ensures that the maintenance mode can be deactivated.
        """
        app.config['MAINTENANCE'] = True
        res = self.post(url='/maintenance', data={'state': False}, role='admin')
        self.assertFalse(app.config['MAINTENANCE'])
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['message'], 'Turned maintenance mode off.')

    def test_toggle_maintenance_mode_without_change(self):
        """
        This test ensures that an exception is raised if the maintenance mode
        would not be changed by the request.
        """
        res = self.post(url='/maintenance', data={'state': False}, role='admin')
        self.assertException(res, exc.NothingHasChanged)

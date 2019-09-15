#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from shopdb.api import app, Purchase


class MiscAPITestCase(BaseAPITestCase):
    def test_empty_json(self):
        """An empty json body should raise an error."""
        res = self.client.post('/login', data=None)
        self.assertException(res, exc.InvalidJSON)

    def test_get_api_root(self):
        """An empty json body should raise an error."""
        res = self.client.get('/')
        message = json.loads(res.data)['message']
        self.assertEqual(message, 'Backend is online.')

    def test_404_exception(self):
        """Check the 404 exception message."""
        res = self.get('does_not_exist')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 404)
        self.assertEqual(data['message'], 'Page does not exist.')
        self.assertEqual(data['result'], 'error')

    def test_method_not_allowed_exception(self):
        """Check the MethodNotAllowed exception message."""
        res = self.client.get('/login')
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 405)
        self.assertEqual(data['message'], 'Method not allowed.')
        self.assertEqual(data['result'], 'error')

    def test_maintenance_mode(self):
        """
        This test checks the maintenance mode.

        If the application is in maintenance mode, all requests must be aborted
        and the appropriate exception raised. There must be no modification to
        the database.
        """
        # First make sure that the application is not in maintenance mode.
        self.assertFalse(app.config.get('MAINTENANCE'))

        # Put the application into maintenance mode.
        app.config['MAINTENANCE'] = True

        # Make sure that the application is in maintenance mode.
        self.assertTrue(app.config.get('MAINTENANCE'))

        # Do a simple request.
        res = self.client.get('/')
        self.assertException(res, exc.MaintenanceMode)

        # Do a purchase.
        data = {'user_id': 2, 'product_id': 1, 'amount': 1}
        res = self.post(url='/purchases', data=data)
        self.assertException(res, exc.MaintenanceMode)
        self.assertFalse(Purchase.query.all())

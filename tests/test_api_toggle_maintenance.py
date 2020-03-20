#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import os
import re
from distutils.util import strtobool

from flask import json

import shopdb.exceptions as exc
from configuration import PATH
from shopdb.api import app
from tests.base_api import BaseAPITestCase


class ToggleMaintenanceAPITestCase(BaseAPITestCase):
    @staticmethod
    def get_config_file_maintenance_mode() -> bool:
        """
        This helper function reads the config file content and returns the current maintenance state.

        :return: The current maintenance state in the config file
        """
        with open(os.path.join(PATH, "configuration.py"), "r") as configuration_file:
            content = configuration_file.read()
            match = re.findall(r"(.*)(MAINTENANCE)([^\w]*)(True|False)", content)
            assert match
            assert len(match) is 1
            groups = match[0]
            return strtobool(groups[3])

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
        # Check the maintenance state
        self.assertFalse(app.config['MAINTENANCE'])
        self.assertFalse(self.get_config_file_maintenance_mode())

        # Set the maintenance state to "True"
        res = self.post(url='/maintenance', data={'state': True}, role='admin')

        # Check the maintenance state
        self.assertTrue(app.config['MAINTENANCE'])
        self.assertTrue(self.get_config_file_maintenance_mode())

        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(data['message'], 'Turned maintenance mode on.')

        # Reset the maintenance state to "False"
        self.post(url='/maintenance', data={'state': False}, role='admin')

    def test_turn_off_maintenance_mode(self):
        """
        This test ensures that the maintenance mode can be deactivated.
        """
        # Set the maintenance state to "True"
        self.post(url='/maintenance', data={'state': True}, role='admin')

        # Check the maintenance state
        self.assertTrue(app.config['MAINTENANCE'])
        self.assertTrue(self.get_config_file_maintenance_mode())

        # Set the maintenance state to "False"
        res = self.post(url='/maintenance', data={'state': False}, role='admin')

        # Check the maintenance state
        self.assertFalse(self.get_config_file_maintenance_mode())
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

    def test_user_interaction_in_maintenance_mode(self):
        """
        This test ensures that an exception is raised if a user (no administrator) does any request.
        """
        # Set the maintenance state to "False"
        self.post(url='/maintenance', data={'state': True}, role='admin')

        # There might be more links listed here, but that should be enough...
        links = ["/", "/purchases", "/users", "/products", "/ranks", "/tags"]

        # Test all links for users, administrators and externals
        for link in links:
            # External
            self.assertEqual(503, self.get(link).status_code)
            # Registered user with password set
            self.assertEqual(503, self.get(link, role="user").status_code)
            # Administrator
            self.assertEqual(200, self.get(link, role="admin").status_code)

        # Reset the maintenance state to "False"
        self.post(url='/maintenance', data={'state': False}, role='admin')

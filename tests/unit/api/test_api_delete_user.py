#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from shop_db2.models import User
from tests.base_api import BaseAPITestCase


class DeleteUserAPITestCase(BaseAPITestCase):
    def test_delete_user(self) -> None:
        """Test for deleting a user"""
        # Create new user which is not verified
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "password": "supersecret",
            "password_repeat": "supersecret",
        }
        self.post(url="/users", data=data)
        user = User.query.filter_by(id=6).first()
        self.assertFalse(user.is_verified)
        res = self.delete(url="/users/6", role="admin")
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue("message" in data)
        self.assertEqual(data["message"], "User deleted.")
        user = User.query.filter_by(id=6).first()
        self.assertEqual(user, None)

    def test_delete_verified_user(self) -> None:
        """Deleting a user that has been verified should raise an error."""
        res = self.delete(url="/users/2", role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryCanNotBeDeleted)

    def test_delete_non_existing_user(self) -> None:
        """Deleting a user that has been verified should raise an error."""
        res = self.delete(url="/users/6", role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

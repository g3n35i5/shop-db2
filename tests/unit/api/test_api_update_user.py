#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import base64
import os

from flask import json

import shopdb.exceptions as exc
from shopdb.api import app
from shopdb.models import User
from tests.base import user_data
from tests.base_api import BaseAPITestCase


class UpdateUserAPITestCase(BaseAPITestCase):
    def test_update_authorization(self):
        """This route should only be available for administrators"""
        res = self.put(url="/users/2", data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url="/users/2", data={}, role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url="/users/2", data={}, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_user_non_verified(self):
        """This test ensures that a non verified user can only be updated if the required data is given"""
        user = User.query.filter_by(id=4).first()
        self.assertEqual(user.firstname, user_data[3]["firstname"])
        data = {"firstname": "Bob", "rank_id": 2}
        res = self.put(url="/users/4", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated user")
        self.assertEqual(data["updated_fields"], ["firstname", "rank_id"])
        self.assertTrue(User.query.filter_by(id=4).first().is_verified)
        self.assertEqual(2, User.query.filter_by(id=4).first().rank_id)

    def test_promote_user_to_admin(self):
        """Update the admin state of a user."""
        self.assertFalse(User.query.filter_by(id=2).first().is_admin)
        data = {"is_admin": True}
        res = self.put(url="/users/2", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated user")
        self.assertEqual(data["updated_fields"], ["is_admin"])
        self.assertTrue(User.query.filter_by(id=2).first().is_admin)

    def test_promote_user_to_admin_twice(self):
        """When a user gets promoted to an admin twice, nothing
        should change.
        """
        self.assertTrue(User.query.filter_by(id=1).first().is_admin)
        data = {"is_admin": True}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertTrue(User.query.filter_by(id=1).first().is_admin)

    def test_promote_user_to_admin_without_password(self):
        """Try to promote a user without password"""
        self.assertFalse(User.query.filter_by(id=3).first().is_admin)
        data = {"is_admin": True}
        res = self.put(url="/users/3", data=data, role="admin")
        self.assertException(res, exc.UserNeedsPassword)
        self.assertFalse(User.query.filter_by(id=3).first().is_admin)

    def test_make_contender_member(self):
        """Update a contender to a member"""
        self.assertEqual(User.query.filter_by(id=3).first().rank_id, 1)
        data = {"rank_id": 2}
        res = self.put(url="/users/3", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated user")
        self.assertEqual(data["updated_fields"], ["rank_id"])
        self.assertEqual(User.query.filter_by(id=3).first().rank_id, 2)

    def test_make_contender_member_twice(self):
        """Update a contender to a member twice should raise
        NothingHasChanged
        """
        self.assertEqual(User.query.filter_by(id=3).first().rank_id, 1)
        data = {"rank_id": 1}
        res = self.put(url="/users/3", data=data, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)
        self.assertEqual(User.query.filter_by(id=3).first().rank_id, 1)

    def test_update_user_image(self):
        """Set a user image"""
        # Assert that the user does not have an image
        user = User.query.filter_by(id=1).first()
        self.assertFalse(user.imagename)
        # Upload a product image
        filepath = app.config["UPLOAD_FOLDER"] + "valid_image.png"
        with open(filepath, "rb") as test:
            image_data = test.read()
        image = {
            "filename": "valid_image.png",
            "value": base64.b64encode(image_data).decode(),
        }
        data = {"imagename": image}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        user = User.query.filter_by(id=1).first()

        # Assert that the user has an imagename
        user = User.query.filter_by(id=1).first()
        self.assertTrue(isinstance(user.imagename, str))
        filepath = app.config["UPLOAD_FOLDER"] + user.imagename
        os.remove(filepath)

    def test_update_forbidden_field(self):
        """Updating a forbidden field should raise an error."""
        self.assertEqual(User.query.filter_by(id=1).first().credit, 0)
        data = {"credit": 10000}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(User.query.filter_by(id=1).first().credit, 0)

    def test_update_non_existing_user(self):
        """Updating a non existing user should raise an error."""
        data = {"firstname": "Peter"}
        res = self.put(url="/users/6", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_user_password_too_short(self):
        """This test ensures that an exception is made if the user's password is
        too short.
        """
        data = {"password": "short", "password_repeat": "short"}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertException(res, exc.PasswordTooShort)

    def test_update_user_password(self):
        """Update user password"""
        # Login should fail
        data = {"id": 1, "password": "SuperSecret"}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)

        # Update password
        data = {"password": "SuperSecret", "password_repeat": "SuperSecret"}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 201)

        # Login should work
        data = {"id": 1, "password": "SuperSecret"}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert all(item in data for item in ["token", "result"])
        self.assertTrue(data["result"])

    def test_update_wrong_type(self):
        """A wrong field type should raise an error"""
        user1 = User.query.filter_by(id=1).first()
        data = {"firstname": True}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        user2 = User.query.filter_by(id=1).first()
        self.assertEqual(user1, user2)

    def test_update_password_no_repeat(self):
        """Updating a password without repeat should raise an error"""
        data = {"password": "SuperSecret"}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_update_password_wrong_repeat(self):
        """Updating a password with a wrong repeat should raise an error"""
        data = {"password": "SuperSecret", "password_repeat": "Super...Ooops"}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.PasswordsDoNotMatch)

    def test_update_firstname(self):
        """Update the firstname of a user."""
        user = User.query.filter(User.id == 2).first()
        self.assertEqual(user.firstname, "Mary")
        data = {"firstname": "New-Mary"}
        res = self.put(url="/users/2", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated user")
        self.assertEqual(data["updated_fields"], ["firstname"])
        user = User.query.filter(User.id == 2).first()
        self.assertEqual(user.firstname, "New-Mary")

    def test_remove_last_admin_privileges(self):
        """Removing admin privileges from the only admin raises an error."""
        data = {"is_admin": False}
        res = self.put(url="/users/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.NoRemainingAdmin)

    def test_remove_admin_privileges(self):
        """Removing admin privileges from the only admin raises an error."""
        data = {"is_admin": True}
        res = self.put(url="/users/2", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated user")
        self.assertEqual(data["updated_fields"], ["is_admin"])
        user2 = User.query.filter_by(id=2).first()
        self.assertTrue(user2.is_admin)
        data = {"is_admin": False}
        res = self.put(url="/users/2", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated user")
        self.assertEqual(data["updated_fields"], ["is_admin"])
        self.assertFalse(user2.is_admin)

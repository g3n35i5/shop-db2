#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from copy import copy

import shop_db2.exceptions as exc
from shop_db2.models import User
from tests.base_api import BaseAPITestCase


class CreateUserAPITestCase(BaseAPITestCase):
    def test_create_user(self) -> None:
        """This test is designed to test the creation of a new user"""
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "password": "supersecret",
            "password_repeat": "supersecret",
        }
        res = self.post(url="/users", data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Created user.", res.data)

        user = User.query.filter_by(id=6).first()
        self.assertTrue(user)
        self.assertEqual(user.firstname, "John")
        self.assertEqual(user.lastname, "Doe")
        self.assertFalse(user.is_verified)

    def test_create_user_only_lastname(self) -> None:
        """It should be possible to create a user without a firstname."""
        data = {"lastname": "Doe"}
        res = self.post(url="/users", data=data)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Created user.", res.data)
        user = User.query.filter_by(id=6).first()
        self.assertEqual(user.firstname, None)
        self.assertEqual(user.lastname, "Doe")
        self.assertFalse(user.is_verified)

    def test_create_user_password_too_short(self) -> None:
        """This test should ensure that the correct exception gets returned
        on creating a user with a short password.
        """
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "password": "short",
            "password_repeat": "short",
        }
        res = self.post(url="/users", data=data)
        self.assertException(res, exc.PasswordTooShort)

        users = User.query.all()
        self.assertEqual(len(users), 5)

    def test_create_user_missing_data(self) -> None:
        """This test should ensure that the correct exception gets returned
        on creating a user with missing data.
        """
        data = {"firstname": "John"}
        res = self.post(url="/users", data=data)
        self.assertException(res, exc.DataIsMissing)

        users = User.query.all()
        self.assertEqual(len(users), 5)

    def test_create_user_wrong_type(self) -> None:
        """This test should ensure that the correct exception gets returned
        on creating a user with a wrong data type.
        """
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "password": "supersecret",
            "password_repeat": "supersecret",
        }

        for item in ["firstname", "lastname", "password", "password_repeat"]:
            data_copy = copy(data)
            data_copy[item] = 1234
            res = self.post(url="/users", data=data_copy)
            self.assertException(res, exc.WrongType)

        users = User.query.all()
        self.assertEqual(len(users), 5)

    def test_create_user_passwords_do_not_match(self) -> None:
        """This test should ensure that the correct exception gets returned
        on creating a user when the passwords do not match.
        """
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "password": "supersecret",
            "password_repeat": "supersecret_ooops",
        }
        res = self.post(url="/users", data=data)
        self.assertException(res, exc.PasswordsDoNotMatch)

        users = User.query.all()
        self.assertEqual(len(users), 5)

    def test_create_user_passwords_repeat_is_missing(self) -> None:
        """This test should ensure that the correct exception gets returned
        on creating a user when the password_repeat field is missing.
        """
        data = {"firstname": "John", "lastname": "Doe", "password": "supersecret"}
        res = self.post(url="/users", data=data)
        self.assertException(res, exc.DataIsMissing)
        users = User.query.all()
        self.assertEqual(len(users), 5)

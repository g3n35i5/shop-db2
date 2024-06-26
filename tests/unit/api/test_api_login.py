#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import jwt
from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import User
from tests.base import user_data
from tests.base_api import BaseAPITestCase


class LoginAPITestCase(BaseAPITestCase):
    def test_login_user(self) -> None:
        """This test is designed to test the login of an existing user with
        an id and password
        """
        data = {"id": 1, "password": user_data[0]["password"]}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert all(item in data for item in ["token", "result"])
        self.assertTrue(data["result"])
        decode = jwt.decode(data["token"], self.app.config["SECRET_KEY"])
        assert "user" in decode
        self.assertEqual(decode["user"]["id"], 1)
        self.assertEqual(decode["user"]["firstname"], user_data[0]["firstname"])
        self.assertEqual(decode["user"]["lastname"], user_data[0]["lastname"])

    def test_login_non_verified_user(self) -> None:
        """If an authentication attempt is made by a non verified user,
        the correct error message must be returned.
        """
        # Create a new user.
        data = {
            "firstname": "John",
            "lastname": "Doe",
            "password": "supersecret",
            "password_repeat": "supersecret",
        }
        self.post(url="/users", data=data)

        # Login.
        data = {"id": 6, "password": "supersecret"}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_login_as_inactive_user(self) -> None:
        """If an authentication attempt is made by an inactive user,
        the correct error message must be returned.
        """
        User.query.filter_by(id=1).first().set_rank_id(4, 1)
        db.session.commit()
        data = {"id": 1, "password": user_data[0]["password"]}
        res = self.post(url="/login", data=data)
        self.assertException(res, exc.UserIsInactive)

    def test_login_missing_password(self) -> None:
        """If an authentication attempt is made without a password,
        the correct error message must be returned.
        """
        data = {"id": 1}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        data = json.loads(res.data)
        assert "token" not in data

    def test_login_missing_id(self) -> None:
        """If an authentication attempt is made without an id,
        the correct error message must be returned.
        """
        data = {"password": user_data[0]["password"]}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        data = json.loads(res.data)
        assert "token" not in data

    def test_login_wrong_id(self) -> None:
        """If an authentication attempt is made with a wrong id,
        the correct error message must be returned.
        """
        data = {"id": 42, "password": user_data[0]["password"]}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert "token" not in data

    def test_login_user_without_password(self) -> None:
        """If an authentication attempt is made by a user who has not set
        a password yet, the correct error message must be returned.
        """
        data = {"id": 3, "password": "DontCare"}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert "token" not in data

    def test_login_wrong_password(self) -> None:
        """If an authentication attempt is made with a password,
        the correct error message must be returned.
        """
        data = {"id": 1, "password": "my_super_wrong_password"}
        res = self.post(url="/login", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.InvalidCredentials)
        data = json.loads(res.data)
        assert "token" not in data

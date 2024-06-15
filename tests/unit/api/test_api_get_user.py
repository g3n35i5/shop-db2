#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import User
from tests.base import user_data
from tests.base_api import BaseAPITestCase


class GetUserAPITestCase(BaseAPITestCase):
    def test_get_single_user(self) -> None:
        """Test for getting a single user"""
        res = self.get(url="/users/1")
        self.assertEqual(res.status_code, 200)
        user = json.loads(res.data)
        assert "password" not in user
        self.assertEqual(user["id"], 1)
        self.assertEqual(user["firstname"], user_data[0]["firstname"])
        self.assertEqual(user["lastname"], user_data[0]["lastname"])
        self.assertEqual(user["credit"], 0)
        self.assertTrue(isinstance(user["creation_date"], str))
        self.assertTrue(isinstance(user["verification_date"], str))

    def test_get_non_existing_user(self) -> None:
        """Getting a non existing user should raise an error."""
        res = self.get(url="/users/6")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_non_verified_user(self) -> None:
        """Getting a non verified user should raise an error."""
        res = self.get(url="/users/4")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsNotVerified)

    def test_get_user_inactive_user(self) -> None:
        """Getting an inactive user should raise an error."""
        User.query.filter_by(id=3).first().set_rank_id(4, 1)
        db.session.commit()
        res = self.get(url="/users/3")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UserIsInactive)

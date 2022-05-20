#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shopdb.exceptions as exc
from shopdb.api import db
from shopdb.models import Rank
from tests.base_api import BaseAPITestCase


class CreateRankAPITestCase(BaseAPITestCase):
    def test_create_rank_authorization(self):
        """This route should only be available for administrators"""
        res = self.post(url="/ranks", data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url="/ranks", data={}, role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url="/ranks", data={}, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_rank(self):
        """Create a rank as admin."""

        rank_data_list = [
            {"name": "Rank1"},
            {"name": "Rank2", "is_system_user": True},
            {"name": "Rank3", "debt_limit": -1234},
        ]

        for rank_data in rank_data_list:
            res = self.post(url="/ranks", role="admin", data=rank_data)
            self.assertEqual(res.status_code, 201)
            data = json.loads(res.data)
            self.assertEqual(data["message"], "Created Rank.")

        self.assertFalse(
            db.session.query(Rank)
            .filter(Rank.name == rank_data_list[0]["name"])
            .first()
            .is_system_user
        )
        self.assertTrue(
            db.session.query(Rank)
            .filter(Rank.name == rank_data_list[1]["name"])
            .first()
            .is_system_user
        )
        self.assertFalse(
            db.session.query(Rank)
            .filter(Rank.name == rank_data_list[2]["name"])
            .first()
            .is_system_user
        )

    def test_create_rank_wrong_type(self):
        """Create a rank as admin with wrong type(s)."""
        data = {"name": 1234.0}
        res = self.post(url="/ranks", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        self.assertEqual(len(Rank.query.all()), 4)

    def test_create_rank_missing_name(self):
        """Create a rank as admin with missing name."""
        data = {}
        res = self.post(url="/ranks", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertEqual(len(Rank.query.all()), 4)

    def test_create_rank_already_existing(self):
        """Creating a rank which already exists should not be possible."""
        data = {"name": "Contender"}
        res = self.post(url="/ranks", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryAlreadyExists)
        self.assertEqual(len(Rank.query.all()), 4)

    def test_create_rank_unknown_field(self):
        """Unknown fields should raise an exception."""
        data = {"name": "Bread", "price": 100}
        res = self.post(url="/ranks", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)
        self.assertEqual(len(Rank.query.all()), 4)

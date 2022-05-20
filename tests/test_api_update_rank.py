#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import shopdb.exceptions as exc
from shopdb.models import Rank
from tests.base_api import BaseAPITestCase


class UpdateRankAPITestCase(BaseAPITestCase):
    def test_update_authorization(self):
        """This route should only be available for administrators"""
        res = self.put(url="/ranks/2", data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url="/ranks/2", data={}, role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url="/ranks/2", data={}, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_non_existing_rank(self):
        """Updating a non existing rank should raise an error."""
        data = {"name": "Foo"}
        res = self.put(url="/ranks/6", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_wrong_type(self):
        """A wrong field type should raise an error"""
        rank1 = Rank.query.filter_by(id=1).first()
        data = {"name": True}
        res = self.put(url="/ranks/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        rank2 = Rank.query.filter_by(id=1).first()
        self.assertEqual(rank1, rank2)

    def test_update_unknown_field(self):
        """An unknown field should raise an error"""
        data = {"color": "red"}
        res = self.put(url="/ranks/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_rank_name(self):
        """Update rank name"""
        self.assertEqual(Rank.query.filter_by(id=1).first().name, "Contender")
        data = {"name": "Foo"}
        res = self.put(url="/ranks/1", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Rank.query.filter_by(id=1).first().name, "Foo")

    def test_update_rank_is_system_user(self):
        """
        Update the "is_system_user" field
        """
        self.assertFalse(Rank.query.filter_by(id=1).first().is_system_user)
        self.put(url="/ranks/1", data={"is_system_user": True}, role="admin")
        self.assertTrue(Rank.query.filter_by(id=1).first().is_system_user)

    def test_update_rank_debt_limit(self):
        """
        Update the "debt_limit" field
        """
        self.assertEqual(0, Rank.query.filter_by(id=1).first().debt_limit)
        self.put(url="/ranks/1", data={"debt_limit": 100}, role="admin")
        self.assertEqual(100, Rank.query.filter_by(id=1).first().debt_limit)

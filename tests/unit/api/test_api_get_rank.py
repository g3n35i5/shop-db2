#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from tests.base_api import BaseAPITestCase


class GetRankAPITestCase(BaseAPITestCase):
    def test_get_single_rank(self) -> None:
        """Test for getting a single rank"""
        res = self.get(url="/ranks/1")
        self.assertEqual(res.status_code, 200)
        rank = json.loads(res.data)
        self.assertEqual(rank["id"], 1)
        self.assertEqual(rank["name"], "Contender")
        self.assertEqual(rank["debt_limit"], 0)
        self.assertFalse(rank["is_system_user"])

    def test_get_non_existing_rank(self) -> None:
        """Getting a non existing rank should raise an error."""
        res = self.get(url="/ranks/6")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

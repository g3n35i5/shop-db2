#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

from tests.base import rank_data
from tests.base_api import BaseAPITestCase


class ListRanksAPITestCase(BaseAPITestCase):
    def test_list_ranks(self):
        """Test listing all ranks."""
        res = self.get(url="/ranks")
        self.assertEqual(res.status_code, 200)
        ranks = json.loads(res.data)
        self.assertEqual(len(ranks), 4)
        for index, rank in enumerate(ranks):
            self.assertEqual(rank["name"], rank_data[index]["name"])
            self.assertEqual(rank["id"], index + 1)

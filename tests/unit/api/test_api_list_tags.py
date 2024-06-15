#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

from tests.base import tag_data
from tests.base_api import BaseAPITestCase


class ListTagsAPITestCase(BaseAPITestCase):
    def test_list_tags(self) -> None:
        """Test for listing all tags"""
        res = self.get(url="/tags")
        self.assertEqual(res.status_code, 200)
        tags = json.loads(res.data)
        self.assertEqual(len(tags), 5)
        for i in range(5):
            self.assertEqual(tags[i]["name"], tag_data[i]["name"])
            self.assertEqual(tags[i]["created_by"], 1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import json

import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class GetTagAPITestCase(BaseAPITestCase):
    def test_get_single_tag(self):
        """Test for getting a single tag"""
        res = self.get(url='/tags/1')
        self.assertEqual(res.status_code, 200)
        tag = json.loads(res.data)
        self.assertEqual(tag['id'], 1)
        self.assertEqual(tag['name'], 'Food')
        self.assertEqual(tag['created_by'], 1)

    def test_get_non_existing_tag(self):
        """Getting a non existing tag should raise an error."""
        res = self.get(url='/tags/6')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

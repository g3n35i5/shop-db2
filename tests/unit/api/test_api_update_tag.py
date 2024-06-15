#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from shop_db2.models import Product, Tag
from tests.base_api import BaseAPITestCase


class UpdateTagAPITestCase(BaseAPITestCase):
    def test_update_authorization(self) -> None:
        """This route should only be available for administrators"""
        res = self.put(url="/tags/2", data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url="/tags/2", data={}, role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.put(url="/tags/2", data={}, role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertException(res, exc.NothingHasChanged)

    def test_update_forbidden_field(self) -> None:
        """Updating a forbidden field should raise an error."""
        self.assertTrue(Product.query.filter_by(id=1).first().countable)
        data = {"created_by": 2}
        res = self.put(url="/products/2", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ForbiddenField)
        self.assertEqual(Tag.query.filter_by(id=2).first().created_by, 1)

    def test_update_non_existing_tag(self) -> None:
        """Updating a non existing tag should raise an error."""
        data = {"name": "Foo"}
        res = self.put(url="/tags/6", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_update_wrong_type(self) -> None:
        """A wrong field type should raise an error"""
        tag1 = Tag.query.filter_by(id=1).first()
        data = {"name": True}
        res = self.put(url="/tags/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        tag2 = Tag.query.filter_by(id=1).first()
        self.assertEqual(tag1, tag2)

    def test_update_unknown_field(self) -> None:
        """An unknown field should raise an error"""
        data = {"color": "red"}
        res = self.put(url="/tags/1", data=data, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

    def test_update_tag_name(self) -> None:
        """Update tag name"""
        self.assertEqual(Tag.query.filter_by(id=1).first().name, "Food")
        data = {"name": "Foo"}
        res = self.put(url="/tags/1", data=data, role="admin")
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Updated tag")
        self.assertEqual(len(data["updated_fields"]), 1)
        self.assertEqual(data["updated_fields"][0], "name")
        self.assertEqual(Tag.query.filter_by(id=1).first().name, "Foo")

    def test_update_tag_is_for_sale(self) -> None:
        """Update the "is_for_sale" field"""
        self.assertTrue(Tag.query.filter_by(id=1).first().is_for_sale)
        self.put(url="/tags/1", data={"is_for_sale": False}, role="admin")
        self.assertFalse(Tag.query.filter_by(id=1).first().is_for_sale)

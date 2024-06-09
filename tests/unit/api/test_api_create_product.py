#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from copy import copy

from flask import json

import shopdb.exceptions as exc
from shopdb.api import db
from shopdb.models import Product
from tests.base_api import BaseAPITestCase


class CreateProductsAPITestCase(BaseAPITestCase):
    def test_create_product_authorization(self):
        """This route should only be available for administrators"""
        res = self.post(url="/products", data={})
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url="/products", data={}, role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.post(url="/products", data={}, role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)

    def test_create_product(self):
        """Create a Product as admin."""
        p_data = {
            "name": "Bread",
            "price": 100,
            "barcode": "12345678",
            "active": True,
            "countable": True,
            "revocable": True,
            "tags": [1],
        }

        res = self.post(url="/products", role="admin", data=p_data)
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data["message"], "Created Product.")
        product = Product.query.filter_by(name="Bread").first()

        del p_data["tags"]

        for field in p_data:
            self.assertEqual(getattr(product, field), p_data[field])
        self.assertEqual(product.created_by, 1)
        self.assertEqual(len(product.tags), 1)
        self.assertEqual(product.tags[0].id, 1)

    def test_create_product_wrong_type(self):
        """Create a Product as admin with wrong type(s)."""
        p_data = {
            "name": "Bread",
            "price": 100,
            "barcode": "12345678",
            "active": True,
            "countable": True,
            "revocable": True,
            "tags": [1],
        }

        for field in p_data:
            copy_data = copy(p_data)
            copy_data[field] = 100.0
            res = self.post(url="/products", role="admin", data=copy_data)
            self.assertEqual(res.status_code, 401)
            self.assertException(res, exc.WrongType)

        self.assertEqual(len(Product.query.all()), 4)

    def test_create_product_wrong_type_tags(self):
        """If the tags of a product are of the wrong type, an exception must
        be raised.
        """
        data = {"name": "Bread", "price": 100, "tags": ["1"]}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.WrongType)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_non_existing_tag(self):
        """If the tags of a product do not exist, an exception must be raised."""
        data = {"name": "Bread", "price": 100, "tags": [42]}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_missing_name(self):
        """Create a Product as admin with missing name."""
        data = {"price": 100, "tags": [1]}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_missing_price(self):
        """Create a Product as admin with missing price."""
        data = {"name": "Bread", "tags": [1]}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_missing_tags(self):
        """Create a Product as admin with missing tags."""
        data = {"name": "Bread", "price": 100}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.DataIsMissing)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_with_existing_name(self):
        """Creating a product which already exists should not be possible."""
        data = {"name": "Pizza", "price": 300, "tags": [1]}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryAlreadyExists)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_already_existing(self):
        """Creating a product with an existing barcode should not be possible."""
        Product.query.filter_by(id=1).first().barcode = "123456"
        db.session.commit()
        data = {"name": "FooBar", "price": 100, "barcode": "123456", "tags": [1]}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryAlreadyExists)
        self.assertFalse(Product.query.filter_by(id=5).first())

    def test_create_product_unknown_field(self):
        """Unknown fields should raise an exception."""
        data = {"name": "Bread", "price": 100, "tags": [1], "color": "blue"}
        res = self.post(url="/products", role="admin", data=data)
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnknownField)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import Product, Tag
from tests.base_api import BaseAPITestCase


class GetProductAPITestCase(BaseAPITestCase):
    def test_list_active_product_without_token(self):
        """Get a single active product as None"""
        res = self.get(url="/products/1")
        self.assertEqual(res.status_code, 200)
        product = json.loads(res.data)
        required = [
            "id",
            "name",
            "price",
            "barcode",
            "active",
            "creation_date",
            "countable",
            "revocable",
            "imagename",
            "tags",
            "purchase_sum",
            "replenishment_sum",
        ]
        assert all(x in product for x in required)

    def test_list_nonactive_product_without_token(self):
        """As None, getting a nonactive product should fail"""
        Product.query.filter(Product.id == 4).first().active = False
        db.session.commit()
        res = self.get(url="/products/4")
        self.assertEqual(res.status_code, 200)
        product = json.loads(res.data)
        not_included = ["price", "countable", "revocable"]
        assert all(x not in product for x in not_included)

    def test_list_nonactive_product_with_token(self):
        """Get a nonactive product as admin"""
        inactive_product = Product.query.filter(Product.id == 4).first()
        inactive_product.active = False
        db.session.commit()
        res = self.get(url="/products/4", role="admin")
        self.assertEqual(res.status_code, 200)
        product = json.loads(res.data)
        required = [
            "id",
            "name",
            "price",
            "barcode",
            "active",
            "creation_date",
            "countable",
            "revocable",
            "imagename",
            "tags",
            "purchase_sum",
            "replenishment_sum",
        ]
        assert all(x in product for x in required)

    def test_list_non_existing_product(self):
        """Getting a non existing product should fail"""
        res = self.get(url="/products/6")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

    def test_get_product_with_single_tag(self):
        product = Product.query.filter_by(id=1).first()
        tag = Tag.query.filter_by(id=1).first()
        tag.products.append(product)
        db.session.commit()
        res = self.get(url="/products/1")
        self.assertEqual(res.status_code, 200)
        product = json.loads(res.data)
        assert "tags" in product
        self.assertEqual(1, len(product["tags"]))
        self.assertEqual(1, product["tags"][0])

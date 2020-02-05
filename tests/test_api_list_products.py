#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
from tests.base_api import BaseAPITestCase
from flask import json


class ListProductsAPITestCase(BaseAPITestCase):
    def test_list_products(self):
        """Get a list of all products"""
        inactive_product = Product.query.filter(Product.id == 4).first()
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products', role='admin')
        self.assertEqual(res.status_code, 200)
        products = json.loads(res.data)
        self.assertEqual(len(products), 4)
        for product in products:
            for item in ['id', 'name', 'price', 'barcode', 'active',
                         'countable', 'revocable', 'imagename', 'tags',
                         'creation_date']:
                assert item in product
        for i in range(0, 3):
            self.assertTrue(products[i]['active'])
        self.assertFalse(products[3]['active'])

    def test_list_products_with_products_which_are_not_for_sale(self):
        """
        This test ensures that the product listing differs between administrators and "normal" users.
        Only if an administrator makes the request, all products should be returned, otherwise only those that
        are for sale.
        :return:
        """
        # Make sure all default tags are set
        self.insert_default_tag_assignments()

        # Make sure that the product is for sale
        self.assertTrue(Product.query.filter_by(id=1).first().is_for_sale)

        # Assign a "not for sale" tag to the product
        tag = db.session.query(Tag).filter(Tag.is_for_sale.is_(False)).first()
        product = Product.query.filter_by(id=1).first()
        product.tags.append(tag)
        db.session.commit()

        # Make sure that the product is not for sale
        self.assertFalse(Product.query.filter_by(id=1).first().is_for_sale)

        # Make sure that this product isn't listed when an unprivileged user lists all products
        products = json.loads(self.get(url='/products', role='user').data)
        self.assertTrue(1 not in list(map(lambda p: p['id'], products)))

        # Make sure that this product gets listed for administrators
        products = json.loads(self.get(url='/products', role='admin').data)
        self.assertTrue(1 in list(map(lambda p: p['id'], products)))

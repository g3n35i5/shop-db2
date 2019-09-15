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
        inactive_product = (Product.query.filter(Product.id == 4)
                            .first())
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'products' in data
        products = data['products']
        self.assertEqual(len(products), 4)
        for product in products:
            for item in ['id', 'name', 'price', 'barcode', 'active',
                         'countable', 'revocable', 'imagename', 'tags',
                         'creation_date']:
                assert item in product
        for i in range(0, 3):
            self.assertTrue(products[i]['active'])
        self.assertFalse(products[3]['active'])

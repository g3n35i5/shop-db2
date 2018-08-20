from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from time import sleep
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
from copy import copy
import pdb

class ListProductsAPITestCase(BaseAPITestCase):
    def test_list_products(self):
        '''Get a list of all products'''
        res = self.get(url='/products')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'products' in data
        products = data['products']
        self.assertEqual(len(products), 4)
        for product in products:
            for item in ['id', 'name', 'price', 'barcode', 'active',
                         'countable', 'revokable', 'imagename']:
                assert item in product

    def test_list_product(self):
        '''Get a single product'''
        res = self.get(url='/products/1')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'product' in data
        products = data['product']
        self.assertEqual(len(products), 1)
        for product in products:
            for item in ['id', 'name', 'price', 'barcode', 'active',
                         'countable', 'revokable', 'imagename']:
                assert item in product

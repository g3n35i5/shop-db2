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
    def test_list_products_without_token(self):
        '''Get a list of all products as user'''
        inactive_product = (Product.query.filter(Product.id == 4)
                           .first())
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'products' in data
        products = data['products']
        self.assertEqual(len(products), 3)
        for product in products:
            self.assertTrue(product['active'])
            for item in ['id', 'name', 'price', 'barcode', 'active',
                         'countable', 'revokable', 'imagename']:
                assert item in product
        db.session.rollback()
        self.assertEqual(len(Product.query.all()), 4)

    def test_list_products_with_token(self):
        '''Get a list of all products as admin'''
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
                         'countable', 'revokable', 'imagename']:
                assert item in product
        self.assertFalse(products[3]['active'])
        db.session.rollback()
        self.assertEqual(len(Product.query.all()), 4)


    def test_list_active_product_without_token(self):
        '''Get a single active product as None'''
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

    def test_list_nonactive_product_without_token(self):
        '''As None, getting a nonactive product should fail'''
        inactive_product = (Product.query.filter(Product.id == 4)
                           .first())
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products/4')
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertEqual(data['message'],
                    'You do not have the authorization to perform this action.')
        db.session.rollback()

    def test_list_nonactive_product_with_token(self):
        '''Get a nonactive product as admin'''
        inactive_product = (Product.query.filter(Product.id == 4)
                           .first())
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products/4', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'product' in data
        products = data['product']
        self.assertEqual(len(products), 1)
        for product in products:
            for item in ['id', 'name', 'price', 'barcode', 'active',
                         'countable', 'revokable', 'imagename']:
                assert item in product
        db.session.rollback()

    def test_list_nonexisting_product(self):
        '''Getting a nonexisting product should fail'''
        res = self.get(url='/products/6')
        self.assertEqual(res.status_code, 401)
        data = json.loads(res.data)
        self.assertEqual(data['message'],
                    'There is no product with this id.')

    def test_create_product_with_token(self):
        '''Create a Product as admin'''
        res = self.post(url='/products', role='admin', data={'name':'bread',
                        'price':100})
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertEqual(data['message'], 'Created Product.')
        self.assertEqual(data['created_fields'], ['name', 'price'])

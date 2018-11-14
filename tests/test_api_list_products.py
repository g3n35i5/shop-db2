from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class ListProductsAPITestCase(BaseAPITestCase):
    def test_list_products_without_token(self):
        """Get a list of all products as user"""
        inactive_product = Product.query.filter(Product.id == 4).first()
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'products' in data
        products = data['products']
        self.assertEqual(len(products), 3)
        required = ['id', 'name', 'price', 'barcode', 'active',
                    'countable', 'revokeable', 'imagename']
        for product in products:
            self.assertTrue(product['active'])
            self.assertTrue(all(x in product for x in required))
        self.assertEqual(len(Product.query.all()), 4)

    def test_list_products_with_token(self):
        """Get a list of all products as admin"""
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
                         'countable', 'revokeable', 'imagename']:
                assert item in product
        self.assertFalse(products[1]['active'])
        self.assertEqual(len(Product.query.all()), 4)

    def test_list_active_product_without_token(self):
        """Get a single active product as None"""
        res = self.get(url='/products/1')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'product' in data
        product = data['product']
        required = ['id', 'name', 'price', 'barcode', 'active',
                    'countable', 'revokeable', 'imagename']
        assert all(x in product for x in required)

    def test_list_nonactive_product_without_token(self):
        """As None, getting a nonactive product should fail"""
        inactive_product = (Product.query.filter(Product.id == 4)
                            .first())
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products/4')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_list_nonactive_product_with_token(self):
        """Get a nonactive product as admin"""
        inactive_product = (Product.query.filter(Product.id == 4)
                            .first())
        inactive_product.active = False
        db.session.commit()
        res = self.get(url='/products/4', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'product' in data
        assert 'product' in data
        product = data['product']
        required = ['id', 'name', 'price', 'barcode', 'active',
                    'countable', 'revokeable', 'imagename']
        assert all(x in product for x in required)

    def test_list_non_existing_product(self):
        """Getting a non existing product should fail"""
        res = self.get(url='/products/6')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ProductNotFound)

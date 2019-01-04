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
                    'countable', 'revocable', 'imagename']
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
                         'countable', 'revocable', 'imagename', 'tags']:
                assert item in product
        self.assertFalse(products[1]['active'])
        self.assertEqual(len(Product.query.all()), 4)

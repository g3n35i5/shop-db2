#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from tests.base import BaseTestCase


class TagModelTestCase(BaseTestCase):
    def test_insert_tag(self):
        """ Insert a tag should work. """
        self.assertEqual(len(Tag.query.all()), 4)
        db.session.add(Tag(name='Foo', created_by=1))
        db.session.commit()
        self.assertEqual(len(Tag.query.all()), 5)

    def test_assign_single_tag_to_product(self):
        """ Adding a single tag to a product. """
        product = Product.query.filter_by(id=1).first()
        self.assertEqual(len(product.tags), 0)
        tag = Tag.query.filter_by(id=1).first()
        self.assertEqual(tag.name, 'Food')
        tag.products.append(product)
        db.session.commit()
        product = Product.query.filter_by(id=1).first()
        self.assertEqual(len(product.tags), 1)
        self.assertEqual(product.tags[0], tag)
        self.assertEqual(len(tag.products.all()), 1)

    def test_assign_multiple_tags_to_product(self):
        """ Adding a multiple tags to a product. """
        product = Product.query.filter_by(id=2).first()
        self.assertEqual(len(product.tags), 0)
        tag1 = Tag.query.filter_by(id=3).first()
        self.assertEqual(tag1.name, 'Drinks')
        tag2 = Tag.query.filter_by(id=4).first()
        self.assertEqual(tag2.name, 'Coffee')
        tag1.products.append(product)
        tag2.products.append(product)
        db.session.commit()
        product = Product.query.filter_by(id=2).first()
        self.assertEqual(len(product.tags), 2)

    def test_remove_tag_from_product(self):
        """ Remove a tag from a product. """
        product = Product.query.filter_by(id=1).first()
        self.assertEqual(len(product.tags), 0)
        tag = Tag.query.filter_by(id=1).first()
        self.assertEqual(tag.name, 'Food')
        tag.products.append(product)
        db.session.commit()
        product = Product.query.filter_by(id=1).first()
        self.assertEqual(len(product.tags), 1)
        tag.products.remove(product)
        db.session.commit()
        product = Product.query.filter_by(id=1).first()
        self.assertEqual(len(product.tags), 0)

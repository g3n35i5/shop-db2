#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.shared import db

product_tag_assignments = db.Table(
    'product_tag_assignments',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'))
)

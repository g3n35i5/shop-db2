#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.shared import db


class Tag(db.Model):
    __tablename__ = 'tags'
    __updateable_fields__ = {'name': str, 'is_for_sale': bool}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_for_sale = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f'<Tag {self.name}>'

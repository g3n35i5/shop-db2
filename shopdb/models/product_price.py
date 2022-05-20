#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func
from sqlalchemy.orm import validates

from shopdb.exceptions import UnauthorizedAccess
from shopdb.shared import db


class ProductPrice(db.Model):
    __tablename__ = "productprices"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    @validates("admin_id")
    def validate_admin(self, key, admin_id):
        from .user import User

        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id

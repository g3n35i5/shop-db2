#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates

from shop_db2.exceptions import UnauthorizedAccess
from shop_db2.shared import db


class Revoke:
    """All revokes that must be executed by an administrator (Deposit,
    Replenishment, ...) had code duplications. For this reason, there
    is now a class from which all these revokes can inherit to save code.
    """

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)

    @declared_attr
    def admin_id(cls):
        return db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    @validates("admin_id")
    def validate_admin(self, key, admin_id):
        from .user import User

        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id

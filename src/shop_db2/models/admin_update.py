#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func
from sqlalchemy.orm import validates

from shop_db2.exceptions import UnauthorizedAccess
from shop_db2.shared import db


class AdminUpdate(db.Model):
    __tablename__ = "adminupdates"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    @validates("admin_id")
    def validate_admin(self, key, admin_id):
        from .user import User

        # If there are no admins in the database, the first user can promote
        # himself
        if not User.query.filter(User.is_admin is True).all():
            return admin_id

        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id

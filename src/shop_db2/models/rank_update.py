#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func
from sqlalchemy.orm import validates

from shop_db2.exceptions import UnauthorizedAccess
from shop_db2.shared import db


class RankUpdate(db.Model):
    __tablename__ = "rankupdates"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey("ranks.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    @validates("admin_id")
    def validate_admin(self, key, admin_id):
        from .user import User

        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id

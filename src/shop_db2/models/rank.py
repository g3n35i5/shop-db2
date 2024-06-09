#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from shop_db2.shared import db


class Rank(db.Model):
    __tablename__ = "ranks"
    __updateable_fields__ = {"name": str, "is_system_user": bool, "debt_limit": int}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    debt_limit = db.Column(db.Integer, nullable=True)
    is_system_user = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f"<Rank {self.name}>"

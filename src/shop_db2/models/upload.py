#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func

from shop_db2.shared import db


class Upload(db.Model):
    __tablename__ = "uploads"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    filename = db.Column(db.String(64), unique=True, nullable=False)

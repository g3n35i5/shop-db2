#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property

from shopdb.shared import db

from .revoke import Revoke


class DepositRevoke(Revoke, db.Model):
    __tablename__ = "depositrevokes"

    deposit_id = db.Column(db.Integer, db.ForeignKey("deposits.id"), nullable=False)


class Deposit(db.Model):
    __tablename__ = "deposits"
    __updateable_fields__ = {"revoked": bool}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(64), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)

    # Link to the user of the deposit.
    user = db.relationship("User", back_populates="deposits", foreign_keys=[user_id])

    @hybrid_method
    def set_revoked(self, revoked, admin_id):
        dr = DepositRevoke(revoked=revoked, admin_id=admin_id, deposit_id=self.id)
        self.revoked = revoked
        db.session.add(dr)

    @hybrid_property
    def revokehistory(self):
        res = DepositRevoke.query.filter(DepositRevoke.deposit_id == self.id).all()
        revokehistory = []
        for revoke in res:
            revokehistory.append(
                {
                    "id": revoke.id,
                    "timestamp": revoke.timestamp,
                    "revoked": revoke.revoked,
                }
            )
        return revokehistory

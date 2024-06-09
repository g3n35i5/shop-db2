#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import column_property

from shopdb.exceptions import EntryNotRevocable
from shopdb.helpers.utils import parse_timestamp
from shopdb.shared import db

from .revoke import Revoke


class ReplenishmentRevoke(Revoke, db.Model):
    __tablename__ = "replenishmentrevoke"

    repl_id = db.Column(db.Integer, db.ForeignKey("replenishments.id"), nullable=False)


class Replenishment(db.Model):
    __tablename__ = "replenishments"
    __updateable_fields__ = {"revoked": bool, "amount": int, "total_price": int}

    id = db.Column(db.Integer, primary_key=True)
    replcoll_id = db.Column(db.Integer, db.ForeignKey("replenishmentcollections.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    amount = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)

    # Link to the replenishmentcollection
    replenishmentcollection = db.relationship(
        "ReplenishmentCollection",
        back_populates="replenishments",
        foreign_keys=[replcoll_id],
    )

    @hybrid_method
    def set_revoked(self, revoked, admin_id):
        # Get all not revoked replenishments corresponding to the
        # replenishmentcollection before changes are made
        non_revoked_replenishments = self.replenishmentcollection.replenishments.filter_by(revoked=False).all()
        if not revoked and not non_revoked_replenishments:
            dr = ReplenishmentCollectionRevoke(
                revoked=False,
                admin_id=admin_id,
                replcoll_id=self.replenishmentcollection.id,
            )
            self.replenishmentcollection.revoked = False
            db.session.add(dr)

        dr = ReplenishmentRevoke(revoked=revoked, admin_id=admin_id, repl_id=self.id)
        self.revoked = revoked
        db.session.add(dr)

        # Check if ReplenishmentCollection still has non-revoked replenishments
        non_revoked_replenishments = self.replenishmentcollection.replenishments.filter_by(revoked=False).all()
        if not self.replenishmentcollection.revoked and not non_revoked_replenishments:
            dr = ReplenishmentCollectionRevoke(
                revoked=True,
                admin_id=admin_id,
                replcoll_id=self.replenishmentcollection.id,
            )
            self.replenishmentcollection.revoked = True
            db.session.add(dr)

    @hybrid_property
    def revokehistory(self):
        res = ReplenishmentRevoke.query.filter(ReplenishmentRevoke.repl_id == self.id).all()
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


class ReplenishmentCollectionRevoke(Revoke, db.Model):
    __tablename__ = "replenishmentcollectionrevoke"

    replcoll_id = db.Column(db.Integer, db.ForeignKey("replenishmentcollections.id"), nullable=False)


class ReplenishmentCollection(db.Model):
    __tablename__ = "replenishmentcollections"
    __updateable_fields__ = {"revoked": bool, "comment": str, "timestamp": str}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    comment = db.Column(db.String(64), nullable=False)
    replenishments = db.relationship("Replenishment", lazy="dynamic", foreign_keys="Replenishment.replcoll_id")

    price = column_property(
        select([func.coalesce(func.sum(Replenishment.total_price), 0)])
        .where(Replenishment.replcoll_id == id)
        .where(Replenishment.revoked.is_(False))
        .as_scalar()
    )

    @hybrid_method
    def set_revoked(self, revoked, admin_id):
        # Which replenishments are not revoked?
        non_revoked_replenishments = self.replenishments.filter_by(revoked=False).all()
        if not revoked and not non_revoked_replenishments:
            raise EntryNotRevocable()

        dr = ReplenishmentCollectionRevoke(revoked=revoked, admin_id=admin_id, replcoll_id=self.id)
        self.revoked = revoked
        db.session.add(dr)

    @hybrid_method
    def set_timestamp(self, timestamp: str):
        data = parse_timestamp({"timestamp": timestamp}, required=True)
        self.timestamp = data["timestamp"]

    @hybrid_property
    def revokehistory(self):
        res = ReplenishmentCollectionRevoke.query.filter(ReplenishmentCollectionRevoke.replcoll_id == self.id).all()
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

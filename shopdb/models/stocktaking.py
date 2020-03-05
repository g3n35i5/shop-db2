#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method

from shopdb.exceptions import InvalidAmount
from shopdb.shared import db
from .revoke import Revoke


class Stocktaking(db.Model):
    __tablename__ = 'stocktakings'
    __updateable_fields__ = {'count': int}

    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('stocktakingcollections.id'), nullable=False)

    @hybrid_method
    def set_count(self, count):
        if count < 0:
            raise InvalidAmount()
        self.count = count

    # Link to the stocktakingcollection
    stocktakingcollection = db.relationship(
        'StocktakingCollection',
        back_populates='stocktakings',
        foreign_keys=[collection_id]
    )


class StocktakingCollection(db.Model):
    __tablename__ = 'stocktakingcollections'
    __updateable_fields__ = {'revoked': bool}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stocktakings = db.relationship('Stocktaking', lazy='dynamic',
                                   foreign_keys='Stocktaking.collection_id')

    @hybrid_method
    def set_revoked(self, revoked, admin_id):
        sr = StocktakingCollectionRevoke(revoked=revoked, admin_id=admin_id, collection_id=self.id)
        self.revoked = revoked
        db.session.add(sr)

    @hybrid_property
    def revokehistory(self):
        res = (StocktakingCollectionRevoke.query
               .filter(StocktakingCollectionRevoke.collection_id == self.id)
               .all())
        revokehistory = []
        for revoke in res:
            revokehistory.append({
                'id': revoke.id,
                'timestamp': revoke.timestamp,
                'revoked': revoke.revoked
            })
        return revokehistory


class StocktakingCollectionRevoke(Revoke, db.Model):
    __tablename__ = 'stocktakingcollectionrevokes'

    collection_id = db.Column(db.Integer, db.ForeignKey('stocktakingcollections.id'), nullable=False)

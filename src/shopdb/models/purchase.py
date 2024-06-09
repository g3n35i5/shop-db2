#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from sqlalchemy import func
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import validates

from shopdb.exceptions import EntryNotRevocable, UserIsNotVerified
from shopdb.shared import db


class PurchaseRevoke(db.Model):
    __tablename__ = "purchaserevokes"

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey("purchases.id"), nullable=False)


class Purchase(db.Model):
    __tablename__ = "purchases"
    __updateable_fields__ = {"revoked": bool, "amount": int}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    productprice = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)

    # Link to the user who made the purchase.
    user = db.relationship("User", back_populates="purchases", foreign_keys=[user_id])

    # Link to the product
    product = db.relationship("Product", foreign_keys=[product_id])

    def __init__(self, **kwargs):
        from .product_price import ProductPrice

        super(Purchase, self).__init__(**kwargs)
        productprice = (
            ProductPrice.query.filter(ProductPrice.product_id == self.product_id)
            .order_by(ProductPrice.id.desc())
            .first()
        )
        self.productprice = productprice.price

    @validates("user_id")
    def validate_user(self, key, user_id):
        """Make sure that the user is verified"""
        from .user import User

        user = User.query.filter(User.id == user_id).first()
        if not user or not user.is_verified:
            raise UserIsNotVerified()

        return user_id

    @hybrid_method
    def set_revoked(self, revoked, admin_id=None):
        if not self.product.revocable:
            raise EntryNotRevocable()

        # Purchase, which have been inserted from administrators can only be revoked
        # by an administrator.
        if self.admin_id is not None and not admin_id:
            raise EntryNotRevocable()

        pr = PurchaseRevoke(purchase_id=self.id, revoked=revoked)
        self.revoked = revoked
        db.session.add(pr)

    @hybrid_property
    def price(self):
        return self.amount * self.productprice

    @hybrid_property
    def revokehistory(self):
        res = PurchaseRevoke.query.filter(PurchaseRevoke.purchase_id == self.id).all()
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

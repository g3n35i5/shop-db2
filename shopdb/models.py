#!/usr/bin/env python3

from shopdb.exceptions import *

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import validates
from sqlalchemy.sql import func
from sqlalchemy import event
import re
import pdb

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime, nullable=True)
    firstname = db.Column(db.String(32), unique=False, nullable=False)
    lastname = db.Column(db.String(32), unique=False, nullable=False)
    username = db.Column(db.String(32), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), unique=False, nullable=False)
    purchases = db.relationship('Purchase', lazy='dynamic',
                                foreign_keys='Purchase.user_id')
    deposits = db.relationship('Deposit', lazy='dynamic',
                               foreign_keys='Deposit.user_id')

    @validates('email')
    def validate_email(self, key, email):
        # Check email is None
        if not email:
            raise InvalidEmailAddress

        # Check email has invalid type
        if not isinstance(email, str):
            raise InvalidEmailAddress

        # Check email length
        if len(email) not in range(6, 257):
            raise InvalidEmailAddress

        # Check email regex
        if not re.match('^[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+' \
                        '(\.[a-z0-9-]+)*(\.[a-z]{2,4})$', email):
            raise InvalidEmailAddress

        return email

    def __repr__(self):
        return f'<User {self.id}: {self.lastname}, {self.firstname}>'

    def to_dict(self):
        '''This function creates a dictionary object of a user'''
        user = {}
        user['id'] = self.id
        user['firstname'] = self.firstname
        user['lastname'] = self.lastname
        user['username'] = self.username
        user['email'] = self.username

        return user

    @hybrid_property
    def is_admin(self):
        au = (AdminUpdate.query
              .filter_by(user_id=self.id)
              .order_by(AdminUpdate.id.desc())
              .first())
        if au is None:
            return False
        return au.is_admin

    @is_admin.setter
    def is_admin(self, is_admin, admin_id):
        if self.is_admin == is_admin:
            raise NothingHasChanged()
        au = AdminUpdate(is_admin=is_admin, admin_id=admin_id, user_id=self.id)
        db.session.add(au)

    @hybrid_property
    def is_verified(self):
        uv = UserVerification.query.filter_by(user_id=self.id).first()
        if uv is None or uv is False:
            return False
        return True

    @hybrid_method
    def verify(self, admin_id):
        if self.is_verified:
            raise UserAlreadyVerified()
        uv = UserVerification(user_id=self.id, admin_id=admin_id)
        db.session.add(uv)

    @hybrid_property
    def rank_id(self):
        return (RankUpdate.query
                .filter_by(user_id=self.id)
                .order_by(RankUpdate.id.desc())
                .first())

    @hybrid_method
    def set_rank_id(self, rank_id, admin_id):
        if self.rank_id == rank_id:
            raise NothingHasChanged()
        ru = RankUpdate(rank_id=rank_id, admin_id=admin_id, user_id=self.id)
        db.session.add(ru)

    @hybrid_property
    def rank(self):
        if self.rank_id:
            return Rank.get(self.rank_id)
        return None

    @hybrid_property
    def credit(self):
        credit = 0
        credit -= sum(p.price for p in self.purchases.all() if not p.revoked)
        credit += sum(d.amount for d in self.deposits.all() if not d.revoked)
        return credit


class UserVerification(db.Model):
    __tablename__ = 'userverifications'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        unique=True)


class AdminUpdate(db.Model):
    __tablename__ = 'adminupdates'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Rank(db.Model):
    __tablename__ = 'ranks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)

    def __repr__(self):
        return f'<Rank {self.name}>'


class RankUpdate(db.Model):
    __tablename__ = 'rankupdates'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('ranks.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    barcode = db.Column(db.String(32), unique=True, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    countable = db.Column(db.Boolean, nullable=False, default=True)
    revokable = db.Column(db.Boolean, nullable=False, default=True)
    imagename = db.Column(db.String(64), nullable=True)

    @hybrid_property
    def price(self):
        return (ProductPrice.query
                .filter(ProductPrice.product_id == self.id)
                .order_by(ProductPrice.id.desc())
                .first().price)

    @hybrid_method
    def set_price(self, price, admin_id):
        productprice = ProductPrice(
            price=price,
            product_id=self.id,
            admin_id=admin_id
        )
        db.session.add(productprice)

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductPrice(db.Model):
    __tablename__ = 'productprices'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Purchase(db.Model):
    __tablename__ = 'purchases'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           nullable=False)
    amount = db.Column(db.Integer, nullable=False)

    @hybrid_property
    def revoked(self):
        revoke = (PurchaseRevoke.query
                  .filter_by(purchase_id=self.id)
                  .order_by(PurchaseRevoke.id.desc())
                  .first())
        if revoke is None:
            return False
        return revoke.revoked

    @revoked.setter
    def revoked(self, revoked, admin_id):
        if self.revoked == revoked:
            raise NothingHasChanged
        pr = PurchaseRevoke(revoked=revoked, admin_id=admin_id)
        db.session.add(pr)

    @hybrid_property
    def price(self):
        productprice = (ProductPrice.query
                        .filter(ProductPrice.product_id == self.product_id)
                        .filter(ProductPrice.timestamp <= self.timestamp)
                        .order_by(ProductPrice.id.desc())
                        .first())
        return self.amount * productprice.price


@event.listens_for(Purchase, 'before_insert')
def purchase_hook(mapper, connect, purchase):
    user = User.query.filter_by(id=purchase.user_id).first()
    if not user.is_verified:
        raise UserIsNotVerified
    product = Product.query.filter_by(id=purchase.product_id).first()
    if not product.active:
        raise ProductIsInactive


class PurchaseRevoke(db.Model):
    __tablename__ = 'purchaserevokes'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                            nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class Deposit(db.Model):
    __tablename__ = 'deposits'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(64), nullable=False)

    @hybrid_property
    def revoked(self):
        revoke = DepositRevoke.query.filter_by(deposit_id=self.id).last()
        if revoke is None:
            return False
        return revoke.revoked

    @revoked.setter
    def revoked(self, revoked, admin_id):
        if self.revoked == revoked:
            raise NothingHasChanged
        dr = DepositRevoke(revoked=revoked, admin_id=admin_id)
        db.session.add(dr)


class DepositRevoke(db.Model):
    __tablename__ = 'depositrevokes'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    deposit_id = db.Column(db.Integer, db.ForeignKey('deposits.id'),
                           nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

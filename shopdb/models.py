#!/usr/bin/env python3

import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import validates, column_property

from shopdb.exceptions import *
from shopdb.helpers.uploads import insert_image
from shopdb.helpers.utils import parse_timestamp

db = SQLAlchemy()

product_tag_assignments = db.Table('product_tag_assignments',
                                   db.Column('product_id', db.Integer,
                                             db.ForeignKey('products.id')),
                                   db.Column('tag_id', db.Integer,
                                             db.ForeignKey('tags.id'))
                                   )


class Rank(db.Model):
    __tablename__ = 'ranks'
    __updateable_fields__ = {'name': str, 'is_system_user': bool, 'debt_limit': int}

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), unique=True, nullable=False)
    active = db.Column(db.Boolean, nullable=False, default=True)
    debt_limit = db.Column(db.Integer, nullable=True)
    is_system_user = db.Column(db.Boolean, nullable=False, default=False)

    def __repr__(self):
        return f'<Rank {self.name}>'


class RankUpdate(db.Model):
    __tablename__ = 'rankupdates'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rank_id = db.Column(db.Integer, db.ForeignKey('ranks.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('admin_id')
    def validate_admin(self, key, admin_id):
        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id


class UserVerification(db.Model):
    __tablename__ = 'userverifications'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False,
                        unique=True)

    @validates('admin_id')
    def validate_admin(self, key, admin_id):
        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id


class AdminUpdate(db.Model):
    __tablename__ = 'adminupdates'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('admin_id')
    def validate_admin(self, key, admin_id):
        # If there are no admins in the database, the first user can promote
        # himself
        if not User.query.filter(User.is_admin is True).all():
            return admin_id

        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id


class Upload(db.Model):
    __tablename__ = 'uploads'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(64), unique=True, nullable=False)


class ProductPrice(db.Model):
    __tablename__ = 'productprices'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('admin_id')
    def validate_admin(self, key, admin_id):
        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id


class Product(db.Model):
    __tablename__ = 'products'
    __updateable_fields__ = {
        'name': str, 'price': int, 'barcode': str, 'tags': list,
        'countable': bool, 'revocable': bool, 'imagename': dict
    }
    # that "imagename" is a dict and not a string is because the update compares
    # whether the values have changed. But since a product has no "image" but only an
    # "imagename", the data for the new image must be called "imagename" and thus be a dict.

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime, default=func.now(), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'),
                           nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    barcode = db.Column(db.String(32), unique=True, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    countable = db.Column(db.Boolean, nullable=False, default=True)
    revocable = db.Column(db.Boolean, nullable=False, default=True)
    image_upload_id = db.Column(db.Integer, db.ForeignKey('uploads.id'),
                                nullable=True)
    tags = db.relationship('Tag', secondary=product_tag_assignments,
                           backref=db.backref('products', lazy='dynamic'))

    # Column property for the price
    price = column_property(select([ProductPrice.price])
                            .where(ProductPrice.product_id == id)
                            .order_by(ProductPrice.id.desc())
                            .limit(1)
                            .as_scalar())

    @validates('created_by')
    def validate_admin(self, key, created_by):
        user = User.query.filter(User.id == created_by).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return created_by

    @property
    def is_for_sale(self):
        """
        Returns whether this product is for sale for unprivileged users
        """
        return all(map(lambda tag: tag.is_for_sale, self.tags))

    @hybrid_property
    def imagename(self):
        upload = Upload.query.filter_by(id=self.image_upload_id).first()
        if upload:
            return upload.filename
        return None

    @hybrid_method
    def get_pricehistory(self, start_date=None, end_date=None):

        # If the time range parameters are not set, we use the creation date
        # and the current date as range.

        try:
            if start_date:
                start = datetime.datetime.fromtimestamp(start_date)
            else:
                start = self.creation_date

            if end_date:
                end = datetime.datetime.fromtimestamp(end_date)
            else:
                end = datetime.datetime.now()
        except ValueError:
            raise InvalidData()

        # Make sure that we select the whole day by shifting the selected
        # range to the very beginning of the start day and to the end of the
        # end day.
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Query the pricehistory in the given range
        res = (db.session.query(ProductPrice)
               .filter(ProductPrice.product_id == self.id)
               .filter(ProductPrice.timestamp.between(start, end))
               .all())

        # Map the result to a dictionary containing all price changes.
        return list(map(lambda p: {
            'id': p.id, 'timestamp': p.timestamp, 'price': p.price
        }, res))

    @hybrid_method
    def set_price(self, price, admin_id):
        productprice = ProductPrice(
            price=price,
            product_id=self.id,
            admin_id=admin_id
        )
        db.session.add(productprice)

    @hybrid_method
    def set_barcode(self, barcode):
        if Product.query.filter_by(barcode=barcode).first():
            raise EntryAlreadyExists()
        self.barcode = barcode

    @hybrid_method
    def set_imagename(self, image, admin_id):
        filename = insert_image(image)
        # Create an upload
        try:
            u = Upload(filename=filename, admin_id=admin_id)
            db.session.add(u)
            db.session.flush()
            self.image_upload_id = u.id
        except IntegrityError:
            raise CouldNotCreateEntry()

    @hybrid_method
    def set_tags(self, tags):
        # All tag ids must be int
        if not all([isinstance(tag_id, int) for tag_id in tags]):
            raise InvalidData()

        # No changes?
        if sorted(tags) == sorted(self.tag_ids):
            raise NothingHasChanged()

        # If there are no remaining tags after the update, the request is invalid.
        if len(tags) == 0:
            raise NoRemainingTag()

        # Get a list of all new tag ids and a list of all removed tag ids
        added_tag_ids = [x for x in tags if x not in self.tag_ids]
        removed_tag_ids = [x for x in self.tag_ids if x not in tags]

        # Add all new tags in the added tag ids list
        for tag_id in added_tag_ids:
            tag = Tag.query.filter_by(id=tag_id).first()
            if tag is None:
                raise EntryNotFound()
            self.tags.append(tag)

        # Remove all tags in the remove tag ids list
        for tag_id in removed_tag_ids:
            tag = Tag.query.filter_by(id=tag_id).first()
            if tag is None:
                raise EntryNotFound()
            self.tags.remove(tag)

    @property
    def tag_ids(self):
        return [tag.id for tag in self.tags]

    def __repr__(self):
        return f'<Product {self.name}>'


class Tag(db.Model):
    __tablename__ = 'tags'
    __updateable_fields__ = {'name': str, 'is_for_sale': bool}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(24), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'),
                           nullable=False)
    is_for_sale = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f'<Tag {self.name}>'


class Purchase(db.Model):
    __tablename__ = 'purchases'
    __updateable_fields__ = {'revoked': bool, 'amount': int}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           nullable=False)
    productprice = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)

    # Link to the user who made the purchase.
    user = db.relationship(
        'User',
        back_populates='purchases',
        foreign_keys=[user_id]
    )

    # Link to the product
    product = db.relationship(
        'Product', foreign_keys=[product_id]
    )

    def __init__(self, **kwargs):
        super(Purchase, self).__init__(**kwargs)
        productprice = (ProductPrice.query
                        .filter(ProductPrice.product_id == self.product_id)
                        .order_by(ProductPrice.id.desc())
                        .first())
        self.productprice = productprice.price

    @validates('user_id')
    def validate_user(self, key, user_id):
        """Make sure that the user is verified"""
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
        res = (PurchaseRevoke.query
               .filter(PurchaseRevoke.purchase_id == self.id)
               .all())
        revokehistory = []
        for revoke in res:
            revokehistory.append({
                'id': revoke.id,
                'timestamp': revoke.timestamp,
                'revoked': revoke.revoked
            })
        return revokehistory


class Revoke:
    """
    All revokes that must be executed by an administrator (Deposit,
    Replenishment, ...) had code duplications. For this reason, there
    is now a class from which all these revokes can inherit to save code.
    """
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)

    @declared_attr
    def admin_id(cls):
        return db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    @validates('admin_id')
    def validate_admin(self, key, admin_id):
        user = User.query.filter(User.id == admin_id).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return admin_id


class Replenishment(db.Model):
    __tablename__ = 'replenishments'
    __updateable_fields__ = {'revoked': bool, 'amount': int, 'total_price': int}

    id = db.Column(db.Integer, primary_key=True)
    replcoll_id = db.Column(db.Integer,
                            db.ForeignKey('replenishmentcollections.id'),
                            nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    amount = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Integer, nullable=False)

    # Link to the replenishmentcollection
    replenishmentcollection = db.relationship(
        'ReplenishmentCollection',
        back_populates='replenishments',
        foreign_keys=[replcoll_id]
    )

    @hybrid_method
    def set_revoked(self, revoked, admin_id, skip_checks: bool = False):
        # Get all not revoked replenishments corresponding to the
        # replenishmentcollection before changes are made
        non_revoked_replenishments = self.replenishmentcollection.replenishments.filter_by(revoked=False).all()
        if not revoked and not non_revoked_replenishments:
            dr = ReplenishmentCollectionRevoke(revoked=False, admin_id=admin_id,
                                               replcoll_id=self.replenishmentcollection.id)
            self.replenishmentcollection.revoked = False
            db.session.add(dr)

        dr = ReplenishmentRevoke(revoked=revoked, admin_id=admin_id, repl_id=self.id)
        self.revoked = revoked
        db.session.add(dr)

        # Check if ReplenishmentCollection still has non-revoked replenishments
        non_revoked_replenishments = self.replenishmentcollection.replenishments.filter_by(revoked=False).all()
        if not self.replenishmentcollection.revoked and not non_revoked_replenishments:
            dr = ReplenishmentCollectionRevoke(revoked=True, admin_id=admin_id,
                                               replcoll_id=self.replenishmentcollection.id)
            self.replenishmentcollection.revoked = True
            db.session.add(dr)

    @hybrid_property
    def revokehistory(self):
        res = (ReplenishmentRevoke.query
               .filter(ReplenishmentRevoke.repl_id == self.id)
               .all())
        revokehistory = []
        for revoke in res:
            revokehistory.append({
                'id': revoke.id,
                'timestamp': revoke.timestamp,
                'revoked': revoke.revoked
            })
        return revokehistory


class ReplenishmentRevoke(Revoke, db.Model):
    __tablename__ = 'replenishmentrevoke'
    repl_id = db.Column(db.Integer,
                        db.ForeignKey('replenishments.id'),
                        nullable=False)


class ReplenishmentCollection(db.Model):
    __tablename__ = 'replenishmentcollections'
    __updateable_fields__ = {'revoked': bool, 'comment': str, 'timestamp': str}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    comment = db.Column(db.String(64), nullable=False)
    replenishments = db.relationship('Replenishment', lazy='dynamic',
                                     foreign_keys='Replenishment.replcoll_id')

    price = column_property(select([func.coalesce(func.sum(Replenishment.total_price), 0)])
                            .where(Replenishment.replcoll_id == id)
                            .where(Replenishment.revoked.is_(False))
                            .as_scalar())

    # @hybrid_property
    # def price(self):
    #     return sum(map(lambda x: x.total_price, self.replenishments.
    #                    filter_by(revoked=False).all()))

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
        data = parse_timestamp({'timestamp': timestamp}, required=True)
        self.timestamp = data['timestamp']

    @hybrid_property
    def revokehistory(self):
        res = (ReplenishmentCollectionRevoke.query
               .filter(ReplenishmentCollectionRevoke.replcoll_id == self.id)
               .all())
        revokehistory = []
        for revoke in res:
            revokehistory.append({
                'id': revoke.id,
                'timestamp': revoke.timestamp,
                'revoked': revoke.revoked
            })
        return revokehistory


class ReplenishmentCollectionRevoke(Revoke, db.Model):
    __tablename__ = 'replenishmentcollectionrevoke'
    replcoll_id = db.Column(db.Integer,
                            db.ForeignKey('replenishmentcollections.id'),
                            nullable=False)


class PurchaseRevoke(db.Model):
    __tablename__ = 'purchaserevokes'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False)
    purchase_id = db.Column(db.Integer, db.ForeignKey('purchases.id'),
                            nullable=False)


class Deposit(db.Model):
    __tablename__ = 'deposits'
    __updateable_fields__ = {'revoked': bool}

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=func.now(), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(64), nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)

    # Link to the user of the deposit.
    user = db.relationship(
        'User',
        back_populates='deposits',
        foreign_keys=[user_id]
    )

    @hybrid_method
    def set_revoked(self, revoked, admin_id):
        dr = DepositRevoke(revoked=revoked, admin_id=admin_id, deposit_id=self.id)
        self.revoked = revoked
        db.session.add(dr)

    @hybrid_property
    def revokehistory(self):
        res = (DepositRevoke.query
               .filter(DepositRevoke.deposit_id == self.id)
               .all())
        revokehistory = []
        for revoke in res:
            revokehistory.append({
                'id': revoke.id,
                'timestamp': revoke.timestamp,
                'revoked': revoke.revoked
            })
        return revokehistory


class DepositRevoke(Revoke, db.Model):
    __tablename__ = 'depositrevokes'
    deposit_id = db.Column(db.Integer, db.ForeignKey('deposits.id'),
                           nullable=False)


class User(db.Model):
    __tablename__ = 'users'
    __updateable_fields__ = {
        'firstname': str, 'lastname': str, 'password': bytes,
        'is_admin': bool, 'rank_id': int, 'imagename': dict
    }

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime, default=func.now(), nullable=False)
    firstname = db.Column(db.String(32), unique=False, nullable=True)
    lastname = db.Column(db.String(32), unique=False, nullable=False)
    password = db.Column(db.String(256), unique=False, nullable=True)
    is_verified = db.Column(db.Boolean, nullable=False, default=False)
    image_upload_id = db.Column(db.Integer, db.ForeignKey('uploads.id'), nullable=True)

    # Column property for the full name
    fullname = column_property(func.trim(func.coalesce(firstname, "") + " " + lastname))

    # Column property for the active state
    active = column_property(select([Rank.active])
                             .where(and_(RankUpdate.user_id == id, Rank.id == RankUpdate.rank_id))
                             .order_by(RankUpdate.id.desc())
                             .limit(1)
                             .as_scalar())

    # Column property for the is system user property
    is_system_user = column_property(select([Rank.is_system_user])
                                     .where(and_(RankUpdate.user_id == id, Rank.id == RankUpdate.rank_id))
                                     .order_by(RankUpdate.id.desc())
                                     .limit(1)
                                     .as_scalar())

    # Column property for the verification_date
    verification_date = column_property(select([UserVerification.timestamp])
                                        .where(UserVerification.user_id == id)
                                        .limit(1)
                                        .as_scalar())

    # Column property for the rank_id
    rank_id = column_property(select([Rank.id])
                              .where(and_(RankUpdate.user_id == id, Rank.id == RankUpdate.rank_id))
                              .order_by(RankUpdate.id.desc())
                              .limit(1)
                              .as_scalar())

    # Select statement for the sum of all non revoked purchases referring this user.
    # NOTE: func.coalesce(a, b) returns the first non-null value of (a, b). If there aren't any purchases
    #       (or deposits, ...) yet, the purchase (deposit, ...) sum is NULL. In this case, 0 gets returned.
    _purchase_sum = column_property(select([func.coalesce(func.sum(Purchase.price), 0)])
                                    .where(Purchase.user_id == id)
                                    .where(Purchase.revoked.is_(False))
                                    .as_scalar())

    # Select statement for the sum of all non revoked deposits referring this user.
    _deposit_sum = column_property(select([func.coalesce(func.sum(Deposit.amount), 0)])
                                   .where(Deposit.user_id == id)
                                   .where(Deposit.revoked.is_(False))
                                   .as_scalar())

    # Select statement for the sum of all non revoked refunds referring this user.
    _replenishmentcollection_sum = column_property(select([func.coalesce(func.sum(ReplenishmentCollection.price), 0)])
                                                   .where(ReplenishmentCollection.seller_id == id)
                                                   .where(ReplenishmentCollection.revoked.is_(False))
                                                   .as_scalar())

    # A users credit is the sum of all amounts that increase his credit (Deposits, ReplenishmentCollections)
    # and all amounts that decrease it (Purchases)
    credit = column_property(_replenishmentcollection_sum.expression + _deposit_sum.expression - _purchase_sum.expression)

    # Link to all purchases of a user.
    purchases = db.relationship(
        'Purchase', lazy='dynamic',
        foreign_keys='Purchase.user_id'
    )
    # Link to all deposits of a user.
    deposits = db.relationship(
        'Deposit', lazy='dynamic',
        foreign_keys='Deposit.user_id'
    )
    # Link to all deposits of a user.
    replenishmentcollections = db.relationship(
        'ReplenishmentCollection', lazy='dynamic',
        foreign_keys='ReplenishmentCollection.seller_id'
    )

    def __repr__(self):
        return f'<User {self.id}: {self.lastname}, {self.firstname}>'

    @hybrid_property
    def imagename(self):
        upload = Upload.query.filter_by(id=self.image_upload_id).first()
        if upload:
            return upload.filename
        return None

    @hybrid_method
    def set_imagename(self, image, admin_id):
        filename = insert_image(image)
        # Create an upload
        try:
            u = Upload(filename=filename, admin_id=admin_id)
            db.session.add(u)
            db.session.flush()
            self.image_upload_id = u.id
        except IntegrityError:
            raise CouldNotCreateEntry()

    @hybrid_property
    def is_admin(self):
        au = (AdminUpdate.query
              .filter_by(user_id=self.id)
              .order_by(AdminUpdate.id.desc())
              .first())
        if au is None:
            return False
        return au.is_admin

    @hybrid_method
    def set_admin(self, is_admin, admin_id):
        if is_admin and self.password is None:
            raise UserNeedsPassword()
        if self.is_admin == is_admin:
            raise NothingHasChanged()
        au = AdminUpdate(is_admin=is_admin, admin_id=admin_id, user_id=self.id)
        db.session.add(au)

    @hybrid_method
    def verify(self, admin_id, rank_id):
        if self.is_verified:
            raise UserAlreadyVerified()
        self.is_verified = True
        uv = UserVerification(user_id=self.id, admin_id=admin_id)
        self.set_rank_id(rank_id, admin_id)
        db.session.add(uv)

    @hybrid_method
    def set_rank_id(self, rank_id, admin_id):
        if self.is_verified:
            ru = RankUpdate(rank_id=rank_id, admin_id=admin_id, user_id=self.id)
            db.session.add(ru)
        else:
            self.verify(admin_id=admin_id, rank_id=rank_id)

    @hybrid_method
    def set_is_admin(self, is_admin, admin_id):
        self.set_admin(is_admin=is_admin, admin_id=admin_id)
        if not self.is_admin:
            users = User.query.all()
            admins = list(filter(lambda x: x.is_admin, users))
            if not admins:
                raise NoRemainingAdmin()

    @hybrid_property
    def rank(self):
        if self.rank_id:
            rank = Rank.query.filter(Rank.id == self.rank_id).first()
            if rank:
                return rank
        return None

    @hybrid_property
    def favorites(self):
        """
        Returns the product ids of the user's favorite products in
        descending order of number. Inactive products those who are
        not for sale are ignored.
        Args:
            self: self
        Returns:
            ids: A list of the favorite product ids in descending order.
        """
        # Get a list of all invalid tag ids (as SQL subquery)
        invalid_tag_ids = db.session.query(Tag.id).filter(Tag.is_for_sale.is_(False)).subquery()
        # Get a list of all products to which this tag is assigned
        invalid_product_ids = (db.session.query(product_tag_assignments.c.product_id)
                               .filter(product_tag_assignments.c.tag_id.in_(invalid_tag_ids))
                               .subquery())

        result = (db.session.query(Purchase, Product)
                  .filter(Product.id == Purchase.product_id)
                  .filter(Product.active.is_(True))
                  .filter(Product.id.notin_(invalid_product_ids))
                  .filter(Purchase.user_id == self.id)
                  .filter(Purchase.revoked.is_(False))
                  .group_by(Purchase.product_id)
                  .order_by(func.sum(Purchase.amount).desc())
                  .all())
        return [purchase.product_id for purchase, _ in result]


class Stocktaking(db.Model):
    __tablename__ = 'stocktakings'
    __updateable_fields__ = {'count': int}

    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'),
                           nullable=False)
    collection_id = db.Column(db.Integer,
                              db.ForeignKey('stocktakingcollections.id'),
                              nullable=False)

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
    collection_id = db.Column(db.Integer,
                              db.ForeignKey('stocktakingcollections.id'),
                              nullable=False)

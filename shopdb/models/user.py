#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy import func, and_
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.orm import column_property

from shopdb.exceptions import (CouldNotCreateEntry, UserNeedsPassword, NothingHasChanged, UserAlreadyVerified,
                               NoRemainingAdmin)
from shopdb.helpers.uploads import insert_image
from shopdb.shared import db


class User(db.Model):
    __tablename__ = 'users'
    __updateable_fields__ = {
        'firstname': str, 'lastname': str, 'password': bytes,
        'is_admin': bool, 'rank_id': int, 'imagename': dict
    }

    from .rank import Rank
    from .rank_update import RankUpdate
    from .user_verification import UserVerification
    from .purchase import Purchase
    from .deposit import Deposit
    from .replenishment import ReplenishmentCollection

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
    credit = column_property(
        _replenishmentcollection_sum.expression + _deposit_sum.expression - _purchase_sum.expression)

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
        from .upload import Upload
        upload = Upload.query.filter_by(id=self.image_upload_id).first()
        if upload:
            return upload.filename
        return None

    @hybrid_method
    def set_imagename(self, image, admin_id):
        filename = insert_image(image)
        # Create an upload
        try:
            from .upload import Upload
            u = Upload(filename=filename, admin_id=admin_id)
            db.session.add(u)
            db.session.flush()
            self.image_upload_id = u.id
        except IntegrityError:
            raise CouldNotCreateEntry()

    @hybrid_property
    def is_admin(self):
        from .admin_update import AdminUpdate
        au = (AdminUpdate.query
              .filter_by(user_id=self.id)
              .order_by(AdminUpdate.id.desc())
              .first())
        if au is None:
            return False
        return au.is_admin

    @hybrid_method
    def set_admin(self, is_admin, admin_id):
        from .admin_update import AdminUpdate
        if is_admin and self.password is None:
            raise UserNeedsPassword()
        if self.is_admin == is_admin:
            raise NothingHasChanged()
        au = AdminUpdate(is_admin=is_admin, admin_id=admin_id, user_id=self.id)
        db.session.add(au)

    @hybrid_method
    def verify(self, admin_id, rank_id):
        from .user_verification import UserVerification
        if self.is_verified:
            raise UserAlreadyVerified()
        self.is_verified = True
        uv = UserVerification(user_id=self.id, admin_id=admin_id)
        self.set_rank_id(rank_id, admin_id)
        db.session.add(uv)

    @hybrid_method
    def set_rank_id(self, rank_id, admin_id):
        from .rank_update import RankUpdate
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
        from .rank import Rank
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
        from .tag import Tag
        from .product_tag_assignment import product_tag_assignments
        from .purchase import Purchase
        from .product import Product
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import column_property, validates

from shop_db2.exceptions import (
    CouldNotCreateEntry,
    EntryAlreadyExists,
    EntryNotFound,
    InvalidData,
    NoRemainingTag,
    NothingHasChanged,
    UnauthorizedAccess,
)
from shop_db2.helpers.uploads import insert_image
from shop_db2.shared import db


class Product(db.Model):
    __tablename__ = "products"
    __updateable_fields__ = {
        "name": str,
        "price": int,
        "barcode": str,
        "tags": list,
        "countable": bool,
        "revocable": bool,
        "imagename": dict,
    }
    # that "imagename" is a dict and not a string is because the update compares
    # whether the values have changed. But since a product has no "image" but only an
    # "imagename", the data for the new image must be called "imagename" and thus be a dict.

    from .product_price import ProductPrice
    from .product_tag_assignment import product_tag_assignments
    from .purchase import Purchase
    from .replenishment import Replenishment

    id = db.Column(db.Integer, primary_key=True)
    creation_date = db.Column(db.DateTime, default=func.now(), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    barcode = db.Column(db.String(32), unique=True, nullable=True)
    active = db.Column(db.Boolean, nullable=False, default=True)
    countable = db.Column(db.Boolean, nullable=False, default=True)
    revocable = db.Column(db.Boolean, nullable=False, default=True)
    image_upload_id = db.Column(db.Integer, db.ForeignKey("uploads.id"), nullable=True)
    tags = db.relationship(
        "Tag",
        secondary=product_tag_assignments,
        backref=db.backref("products", lazy="dynamic"),
    )

    # Column property for the price
    price = column_property(
        select([ProductPrice.price])
        .where(ProductPrice.product_id == id)
        .order_by(ProductPrice.id.desc())
        .limit(1)
        .as_scalar()
    )

    # Column property for the purchase sum
    purchase_sum = column_property(
        select([func.coalesce(func.sum(Purchase.price), 0)])
        .where(Purchase.product_id == id)
        .where(Purchase.revoked.is_(False))
        .as_scalar()
    )

    # Column property for the replenishment sum
    replenishment_sum = column_property(
        select([func.coalesce(func.sum(Replenishment.total_price), 0)])
        .where(Replenishment.product_id == id)
        .where(Replenishment.revoked.is_(False))
        .as_scalar()
    )

    @validates("created_by")
    def validate_admin(self, key, created_by):
        from .user import User

        user = User.query.filter(User.id == created_by).first()
        if not user or not user.is_admin:
            raise UnauthorizedAccess()

        return created_by

    @property
    def is_for_sale(self):
        """Returns whether this product is for sale for unprivileged users"""
        return all(map(lambda tag: tag.is_for_sale, self.tags))

    @hybrid_property
    def imagename(self):
        from .upload import Upload

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

        from .product_price import ProductPrice

        # Query the pricehistory in the given range
        res = (
            db.session.query(ProductPrice)
            .filter(ProductPrice.product_id == self.id)
            .filter(ProductPrice.timestamp.between(start, end))
            .all()
        )

        # Map the result to a dictionary containing all price changes.
        return list(map(lambda p: {"id": p.id, "timestamp": p.timestamp, "price": p.price}, res))

    @hybrid_method
    def set_price(self, price, admin_id):
        from .product_price import ProductPrice

        productprice = ProductPrice(price=price, product_id=self.id, admin_id=admin_id)
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
            from .upload import Upload

            u = Upload(filename=filename, admin_id=admin_id)
            db.session.add(u)
            db.session.flush()
            self.image_upload_id = u.id
        except IntegrityError:
            raise CouldNotCreateEntry()

    @hybrid_method
    def set_tags(self, tags):
        from .tag import Tag

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
        return f"<Product {self.name}>"

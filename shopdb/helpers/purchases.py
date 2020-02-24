#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import datetime
from typing import Optional

from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

import shopdb.exceptions as exc
from shopdb.api import db
from shopdb.helpers.utils import parse_timestamp
from shopdb.helpers.validators import check_fields_and_types
from shopdb.models import Purchase
from shopdb.models import User, Product, Rank


def get_purchase_amount_in_interval(product_id: int, start: datetime.datetime, end: datetime.datetime) -> int:
    """
    Returns the sum of the amount of all purchases of the given product.
    """

    result = (db.session.query(
        func.sum(Purchase.amount))
              .filter(Purchase.product_id == product_id)
              .filter(Purchase.revoked.is_(False))
              .filter(Purchase.timestamp >= start)
              .filter(Purchase.timestamp <= end)
              .first())
    return result[0] or 0


def insert_purchase(admin: Optional[User], data: dict) -> None:
    """
    This helper function creates a single purchase without doing a commit.

    :param admin:                Is the administrator user, determined by @adminOptional.
    :param data:                 Is the purchase data.

    :return:                     None
    """
    required = {'user_id': int, 'product_id': int, 'amount': int}
    optional = {'timestamp': str}

    # If the request is not made by an administrator, the timestamp can't be set
    if admin is None and 'timestamp' in data:
        raise exc.ForbiddenField()

    check_fields_and_types(data, required, optional)

    # Check user
    user = User.query.filter_by(id=data['user_id']).first()
    if not user:
        raise exc.EntryNotFound()

    # Check if the user has been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the user is inactive
    if not user.active:
        raise exc.UserIsInactive()

    # Check the user rank. If it is a system user, only administrators are allowed to insert purchases
    if user.rank.is_system_user and admin is None:
        raise exc.UnauthorizedAccess()

    # Parse the timestamp
    data = parse_timestamp(data, required=False)

    # Check product
    product = Product.query.filter_by(id=data['product_id']).first()
    if not product:
        raise exc.EntryNotFound()
    if not admin and not product.active:
        raise exc.EntryIsInactive()

    # Check weather the product is for sale
    if any(map(lambda tag: not tag.is_for_sale, product.tags)):
        raise exc.EntryIsNotForSale()

    # Check amount
    if data['amount'] <= 0:
        raise exc.InvalidAmount()

    # If the purchase is made by an administrator, the credit limit
    # may be exceeded.
    if not admin:
        limit = Rank.query.filter_by(id=user.rank_id).first().debt_limit
        current_credit = user.credit
        future_credit = current_credit - (product.price * data['amount'])
        if future_credit < limit:
            raise exc.InsufficientCredit()

    try:
        purchase = Purchase(**data)
        db.session.add(purchase)
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

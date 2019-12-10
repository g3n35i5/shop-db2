#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import Purchase
from shopdb.api import db
from sqlalchemy.sql import func
import datetime


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

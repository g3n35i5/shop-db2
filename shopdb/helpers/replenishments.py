#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import datetime

from sqlalchemy.sql import func

from shopdb.api import db
from shopdb.models import Replenishment, ReplenishmentCollection


def get_replenishment_amount_in_interval(product_id: int, start: datetime.datetime, end: datetime.datetime) -> int:
    """
    Returns the sum of the amount of all replenishments of the given product.
    """

    result = (db.session.query(func.sum(Replenishment.amount))
              .join(ReplenishmentCollection, ReplenishmentCollection.id == Replenishment.replcoll_id)
              .filter(Replenishment.product_id == product_id)
              .filter(ReplenishmentCollection.revoked.is_(False))
              .filter(ReplenishmentCollection.timestamp >= start)
              .filter(ReplenishmentCollection.timestamp <= end)
              .first())

    if result is None:
        return 0
    return result[0] or 0

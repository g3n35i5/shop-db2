#!/usr/bin/env python3

from typing import Optional

from sqlalchemy import func, and_

from shopdb.api import db
from shopdb.helpers.products import _get_product_mean_price_in_time_range
from shopdb.models import (Purchase, Replenishment, Product, StocktakingCollection, Stocktaking,
                           ReplenishmentCollection)


def _get_balance_between_stocktakings(start, end):
    # Check the stocktaking collections
    if not all([start, end]):
        return None

    # Get a list of all product ids.
    products = Product.query.filter(Product.countable.is_(True)).all()
    product_ids = [p.id for p in products]

    start_product_ids = [s.product_id for s in start.stocktakings]
    end_product_ids = [s.product_id for s in end.stocktakings]

    out = {'profit': 0,
           'loss': 0,
           'balance': 0,
           'products': {}}

    for _id in product_ids:
        # Case 1: The product is active for the entire period of time.
        if _id in start_product_ids and _id in end_product_ids:
            s = next(s for s in start.stocktakings if s.product_id == _id).count
            e = next(s for s in end.stocktakings if s.product_id == _id).count
        # Case 2: The product has been set to inactive since the first
        # stocktaking.
        elif _id in start_product_ids and _id not in end_product_ids:
            s = next(s for s in start.stocktakings if s.product_id == _id).count
            e = 0
        # Case 3: The product did not exist during the first stocktaking.
        elif _id not in start_product_ids and _id in end_product_ids:
            s = 0
            e = next(s for s in end.stocktakings if s.product_id == _id).count
        # Case 4: The product has not been recorded in either stocktaking.
        else:
            s = 0
            e = 0

        # Determine how often the product was purchased in the period and at
        # what price.
        res = (db.session.query(
            func.sum(Purchase.amount),
            func.sum(Purchase.price))
               .filter(Purchase.product_id == _id)
               .filter(Purchase.revoked.is_(False))
               .filter(and_(Purchase.timestamp < end.timestamp,
                            Purchase.timestamp >= start.timestamp))
               .first())

        purchase_count = res[0] or 0
        purchase_sum_price = res[1] or 0

        # Determine how often the product was refilled in the time span and
        # how much was spent on it.
        res = (db.session.query(
            func.sum(Replenishment.amount),
            func.sum(Replenishment.total_price))
               .join(ReplenishmentCollection,
                     ReplenishmentCollection.id == Replenishment.replcoll_id)
               .filter(Replenishment.product_id == _id)
               .filter(Replenishment.revoked.is_(False))
               .filter(ReplenishmentCollection.revoked.is_(False))
               .filter(and_(ReplenishmentCollection.timestamp < end.timestamp,
                            ReplenishmentCollection.timestamp >= start.timestamp))
               .first())

        # Determine how often this product has been replenished during
        # this period.
        replenish_count = res[0] or 0
        replenish_sum_price = res[1] or 0

        # Get the mean product price.
        mean_price = _get_product_mean_price_in_time_range(_id,
                                                           start.timestamp,
                                                           end.timestamp)

        # Determine the number of products not purchased.
        difference = -(s - purchase_count + replenish_count - e)

        # Determine the balance
        balance = difference * mean_price

        # Increase the overall balance
        out['balance'] += balance

        # If the balance is negative, this means a loss, otherwise a profit.
        if balance < 0:
            out['loss'] += abs(balance)
        else:
            out['profit'] += abs(balance)

        # Write the data for the current product to the output dictionary.
        out['products'][_id] = {
            'start_count': s,
            'end_count': e,
            'purchase_count': purchase_count,
            'purchase_sum_price': purchase_sum_price,
            'replenish_count': replenish_count,
            'replenish_sum_price': replenish_sum_price,
            'difference': difference,
            'balance': balance
        }

    return out


def get_latest_non_revoked_stocktakingcollection() -> StocktakingCollection:
    """
    This helper function returns the latest, non revoked stocktakingcollection.
    """
    return (db.session.query(StocktakingCollection)
            .order_by(StocktakingCollection.id.desc())
            .filter(StocktakingCollection.revoked.is_(False))
            .first())


def get_latest_stocktaking_of_product(product_id: int) -> Optional[Stocktaking]:
    """
    This helper function returns the latest stocktaking of a product.
    """

    # Get the stocktaking count of the product
    result = (db.session.query(Stocktaking)
              .join(StocktakingCollection, StocktakingCollection.id == Stocktaking.collection_id)
              .filter(Stocktaking.product_id == product_id)
              .filter(StocktakingCollection.revoked.is_(False))
              .order_by(Stocktaking.id.desc())
              .first())

    return result

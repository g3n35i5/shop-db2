#!/usr/bin/env python3


import datetime

from sqlalchemy import and_

import shopdb.exceptions as exc
import shopdb.helpers.purchases as purchase_helpers
import shopdb.helpers.replenishments as replenishment_helpers
import shopdb.helpers.stocktakings as stocktaking_helpers
from shopdb.models import Product, ProductPrice


def _shift_date_to_begin_of_day(date):
    """
    This function moves a timestamp to the beginning of the day.

    :param date: Is the date to be moved.
    :return:     Is the shifted date.
    """
    return date.replace(hour=0, minute=0, second=0, microsecond=0)


def _shift_date_to_end_of_day(date):
    """
    This function moves a timestamp to the end of the day.

    :param date: Is the date to be moved.
    :return:     Is the shifted date.
    """
    return date.replace(hour=23, minute=59, second=59, microsecond=999999)


def _get_product_mean_price_in_time_range(product_id, start, end):
    """
    This function calculates the mean price in a given range of time.

    :param product_id: Is the product id.
    :param start:      Is the start date.
    :param end:        Is the end date.
    :return:           The mean product price in the given time range.
    """

    # Check if start and end dates are date objects.
    if not all([isinstance(d, datetime.datetime) for d in [start, end]]):
        raise exc.InvalidData()

    # If the end date lies before the start date, raise an exception.
    if end <= start:
        raise exc.InvalidData()

    # Check the product id
    if not Product.query.filter_by(id=product_id).first():
        raise exc.EntryNotFound()

    # Get product price at the time of the first stocktaking.
    res1 = (
        ProductPrice.query.filter(ProductPrice.product_id == product_id)
        .filter(ProductPrice.timestamp <= start)
        .order_by(ProductPrice.timestamp.desc())
        .first()
    )

    # Get all price changes in the range between the two stocktakings
    res2 = (
        ProductPrice.query.filter(ProductPrice.product_id == product_id)
        .filter(and_(ProductPrice.timestamp < end, ProductPrice.timestamp > start))
        .order_by(ProductPrice.timestamp)
        .all()
    )

    # Get a list of all product price changes
    changes = [res1] + res2

    # If no price could be determined, take the current price.
    if not changes or not changes[0]:
        return Product.query.filter_by(id=product_id).first().price
    # If there are no resulting changes, return the first price.
    elif len(changes) == 1:
        return changes[0].price

    # Iterate over all days in the time range and calculate the mean price
    else:
        # Get the timestamp of the first entry.
        first = changes[0].timestamp

        # Shift the first timestamp to the beginning of the day and the last
        # timestamp to the end of the day.
        first = _shift_date_to_begin_of_day(first)
        start = _shift_date_to_begin_of_day(start)
        end = _shift_date_to_end_of_day(end)

        # Shift the timestamp of all changes to the beginning of the day.
        for item in changes:
            item.timestamp = _shift_date_to_begin_of_day(item.timestamp)

        # Set the current date to the first entry.
        current_date = first
        current_price = changes[0].price
        day_count = 0
        sum_price = 0

        # Iterate over all days and increment the day count and sum all prices.
        while current_date <= end:
            current_date += datetime.timedelta(days=1)
            if current_date <= start:
                continue
            day_count += 1
            sum_price += current_price
            if current_date in list(map(lambda x: x.timestamp, changes)):
                current_price = next(
                    item for item in changes if item.timestamp == current_date
                ).price

        # Return the mean product price as integer.
        return int(round(sum_price / day_count))


def get_theoretical_stock_of_product(product_id: int) -> int:
    """
    Returns the theoretical stock level of a product.

    The theoretical stock level of a product is the result of the number
    determined in the last stocktaking minus the sum of the amount of purchases
    that were not revoked plus the sum of the amount of replenishments since then.
    """

    # Get the latest stocktaking of a product
    latest_stocktaking = stocktaking_helpers.get_latest_stocktaking_of_product(
        product_id
    )

    # If there has been a stocktaking, it defines the start timestamp.
    # Otherwise, we have to take all purchases of this product into account.
    if latest_stocktaking is not None:
        start = latest_stocktaking.stocktakingcollection.timestamp
        stocktaking_count = latest_stocktaking.count
    else:
        start = datetime.datetime.min
        stocktaking_count = 0

    end = datetime.datetime.utcnow()

    # Get the sum of all purchase amounts in the selected interval
    sum_purchase_amount = purchase_helpers.get_purchase_amount_in_interval(
        product_id, start, end
    )

    # Get the sum of all refund amounts in the selected interval
    sum_replenishment_amount = (
        replenishment_helpers.get_replenishment_amount_in_interval(
            product_id, start, end
        )
    )

    # Theoretical stock level
    return stocktaking_count - sum_purchase_amount + sum_replenishment_amount

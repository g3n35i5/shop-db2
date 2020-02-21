#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import jsonify

from shopdb.api import app
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.stocktakings import _get_balance_between_stocktakings
from shopdb.models import Purchase, Deposit, Turnover, Refund, ReplenishmentCollection, StocktakingCollection


@app.route('/financial_overview', methods=['GET'])
@adminRequired
def get_financial_overview(admin):
    """
    The financial status of the entire project can be retrieved via this route.
    All purchases, deposits, refunds and replenishmentcollections are
    used for this purpose. The items are cleared once to a number indicating
    whether the community has debt or surplus money. In addition, the
    individual items are returned separately in order to get a better
    breakdown of the items.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A dictionary with the individually calculated values.
    """

    # Query all purchases,
    purchases = Purchase.query.filter(Purchase.revoked.is_(False)).all()

    # Query all deposits.
    deposits = Deposit.query.filter(Deposit.revoked.is_(False)).all()

    # Query all turnovers.
    turnovers = Turnover.query.filter(Turnover.revoked.is_(False)).all()

    # Query all refunds.
    refunds = Refund.query.filter(Refund.revoked.is_(False)).all()

    # Query all replenishment collections.
    replcolls = (ReplenishmentCollection
                 .query
                 .filter(ReplenishmentCollection.revoked.is_(False))
                 .all())

    # Get the balance between the first and the last stocktaking.
    # If there is no stocktaking or only one stocktaking, the balance is 0.
    stock_first = (StocktakingCollection.query
                   .order_by(StocktakingCollection.id)
                   .first())
    stock_last = (StocktakingCollection.query
                  .order_by(StocktakingCollection.id.desc())
                  .first())

    if not all([stock_first, stock_last]) or stock_first is stock_last:
        pos_stock = 0
        neg_stock = 0
    else:
        balance = _get_balance_between_stocktakings(stock_first, stock_last)
        pos_stock = balance['profit']
        neg_stock = balance['loss']

    # Incomes are:
    # - Purchases                    with a positive price
    # - Deposits                     with a positive amount
    # - Turnovers                    with a positive amount
    # - Replenishmentcollections     with a negative price
    # - Refunds                      with a negative amount
    # - Profits between stocktakings

    pos_pur = sum(
        map(abs, list(filter(lambda x: x >= 0,
                             list(map(lambda x: x.price, purchases)))))
    )

    pos_dep = sum(
        map(abs, list(filter(lambda x: x >= 0,
                             list(map(lambda x: x.amount, deposits)))))
    )

    pos_turn = sum(
        map(abs, list(filter(lambda x: x >= 0,
                             list(map(lambda x: x.amount, turnovers)))))
    )

    neg_rep = sum(
        map(abs, list(filter(lambda x: x < 0,
                             list(map(lambda x: x.price, replcolls)))))
    )

    neg_ref = sum(
        map(abs, list(filter(lambda x: x < 0,
                             list(map(lambda x: x.total_price, refunds)))))
    )

    sum_incomes = sum([
        pos_pur, pos_dep, pos_turn, neg_rep, neg_ref, pos_stock
    ])

    incomes = {
        'amount': sum_incomes,
        'items': [
            {'name': 'Purchases', 'amount': pos_pur},
            {'name': 'Deposits', 'amount': pos_dep},
            {'name': 'Turnovers', 'amount': pos_turn},
            {'name': 'Replenishments', 'amount': neg_rep},
            {'name': 'Refunds', 'amount': neg_ref},
            {'name': 'Stocktakings', 'amount': pos_stock}
        ]
    }

    # Expenses are:
    # - Purchases                with a negative price
    # - Deposits                 with a negative amount
    # - Turnovers                with a negative amount
    # - Replenishmentcollections with a positive price
    # - Refunds                  with a positive amount
    # - Losses between stocktakings
    neg_pur = sum(
        map(abs, list(filter(lambda x: x < 0,
                             list(map(lambda x: x.price, purchases)))))
    )

    neg_dep = sum(
        map(abs, list(filter(lambda x: x < 0,
                             list(map(lambda x: x.amount, deposits)))))
    )

    neg_turn = sum(
        map(abs, list(filter(lambda x: x < 0,
                             list(map(lambda x: x.amount, turnovers)))))
    )

    pos_rep = sum(
        map(abs, list(filter(lambda x: x >= 0,
                             list(map(lambda x: x.price, replcolls)))))
    )

    pos_ref = sum(
        map(abs, list(filter(lambda x: x >= 0,
                             list(map(lambda x: x.total_price, refunds)))))
    )

    sum_expenses = sum([
        neg_pur, neg_dep, neg_turn, pos_rep, pos_ref, neg_stock
    ])

    expenses = {
        'amount': sum_expenses,
        'items': [
            {'name': 'Purchases', 'amount': neg_pur},
            {'name': 'Deposits', 'amount': neg_dep},
            {'name': 'Turnovers', 'amount': neg_turn},
            {'name': 'Replenishments', 'amount': pos_rep},
            {'name': 'Refunds', 'amount': pos_ref},
            {'name': 'Stocktakings', 'amount': neg_stock}
        ]
    }

    # The total balance is calculated as incomes minus expenses.
    total_balance = sum_incomes - sum_expenses

    financial_overview = {
        'total_balance': total_balance,
        'incomes': incomes,
        'expenses': expenses
    }
    return jsonify(financial_overview), 200

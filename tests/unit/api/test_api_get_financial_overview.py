#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from datetime import datetime

from flask import json

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.models import Deposit, ProductPrice, Purchase, ReplenishmentCollection
from tests.base_api import BaseAPITestCase


class GetFinancialOverviewAPITestCase(BaseAPITestCase):
    def test_authorization_get_financial_overview(self):
        """This route may only be accessible to administrators. An exception must
        be made for all other requests.
        """
        res = self.get(url="/financial_overview")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url="/financial_overview", role="user")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_get_financial_overview(self):
        """This test ensures that the entire financial overview is calculated
        correctly. To do this, some test entries are entered into the
        database, some of which are revoked. Then the amount is manually
        calculated which should come out at the end of the calculation and
        compared with the amount calculated by the API.
        """
        # Add a product with negative price
        p_data = {"name": "Negative", "price": -100, "tags": [1]}
        self.post(url="/products", role="admin", data=p_data)

        # Manipulate the product price timestamps
        ts = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        for product_price_id in [1, 2, 3, 4, 5]:
            ProductPrice.query.filter_by(id=product_price_id).first().timestamp = ts
        db.session.commit()

        # Insert the first stocktaking
        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 100},
            {"product_id": 3, "count": 100},
            {"product_id": 4, "count": 100},
            {"product_id": 5, "count": 100},
        ]
        t = datetime.strptime("2018-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        data = {"stocktakings": stocktakings, "timestamp": int(t.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Insert some purchases (some are revoked)
        t = datetime.strptime("2018-01-01 10:00:00", "%Y-%m-%d %H:%M:%S")
        p1 = Purchase(user_id=1, product_id=3, amount=4, revoked=True, timestamp=t)
        p2 = Purchase(user_id=2, product_id=2, amount=3, revoked=False, timestamp=t)  # <-
        p3 = Purchase(user_id=3, product_id=1, amount=2, revoked=False, timestamp=t)  # <-
        p4 = Purchase(user_id=1, product_id=2, amount=1, revoked=True, timestamp=t)
        p5 = Purchase(user_id=1, product_id=5, amount=1, revoked=False, timestamp=t)  # <-
        for p in [p1, p2, p3, p4, p5]:
            db.session.add(p)

        # Purchase amount should be 3 * 50 + 2 * 300 - 1 * 100
        psum = p2.price + p3.price + p5.price
        self.assertEqual(psum, 650)

        # Insert some deposits (some are revoked)
        d1 = Deposit(user_id=1, admin_id=1, comment="Foo", amount=100, revoked=False)  # <-
        d2 = Deposit(user_id=2, admin_id=1, comment="Foo", amount=500, revoked=True)
        d3 = Deposit(user_id=3, admin_id=1, comment="Foo", amount=300, revoked=False)  # <-
        d4 = Deposit(user_id=2, admin_id=1, comment="Foo", amount=200, revoked=True)
        d5 = Deposit(user_id=2, admin_id=1, comment="Negative", amount=-100, revoked=False)
        for d in [d1, d2, d3, d4, d5]:
            db.session.add(d)

        # Insert the replenishmentcollections and revoke the first one.
        self.insert_default_replenishmentcollections()
        rc = ReplenishmentCollection.query.filter_by(id=1).first()
        rc.set_revoked(admin_id=1, revoked=True)
        db.session.commit()

        # Manipulate the replenishment timestamps
        # First replenishment: 01.01.2017 (Before the first stocktaking!)
        ts = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        ReplenishmentCollection.query.filter_by(id=1).first().timestamp = ts
        # Second replenishment: 01.02.2019 (Between the stocktakings)
        ts = datetime.strptime("2018-02-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        ReplenishmentCollection.query.filter_by(id=2).first().timestamp = ts

        # Insert the second stocktaking
        stocktakings = [
            {"product_id": 1, "count": 110},  # Products have been added!
            {"product_id": 2, "count": 90},  # Products have been lost!
            {"product_id": 3, "count": 100},
            {"product_id": 4, "count": 100},
            {"product_id": 5, "count": 100},
        ]
        t = datetime.strptime("2018-03-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        data = {"stocktakings": stocktakings, "timestamp": int(t.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Calculate the total balance, incomes and expenses.

        # Incomes are:
        # - Purchases                    with a positive price
        # - Deposits                     with a positive amount
        # - Replenishmentcollections     with a negative price
        # - Profits between stocktakings
        positive_purchase_amount = 750
        positive_deposits_amount = 400
        negative_replenishmentcollections_price = 0
        profit_between_stocktakings = 600
        incomes = sum(
            [
                positive_purchase_amount,
                positive_deposits_amount,
                negative_replenishmentcollections_price,
                profit_between_stocktakings,
            ]
        )

        # Expenses are:
        # - Purchases                with a negative price
        # - Deposits                 with a negative amount
        # - Replenishmentcollections with a positive price
        # - Losses between stocktakings
        negative_purchase_amount = 100
        negative_deposits_amount = 100
        positive_replenishmentcollections_price = 3500
        loss_between_stocktakings = 950
        expenses = sum(
            [
                negative_purchase_amount,
                negative_deposits_amount,
                positive_replenishmentcollections_price,
                loss_between_stocktakings,
            ]
        )

        total_balance = incomes - expenses

        res = self.get(url="/financial_overview", role="admin")
        self.assertEqual(res.status_code, 200)
        overview = json.loads(res.data)
        self.assertEqual(overview["total_balance"], total_balance)
        self.assertEqual(overview["incomes"]["amount"], incomes)
        self.assertEqual(overview["expenses"]["amount"], expenses)

        # Check the incomes
        api_incomes = overview["incomes"]["items"]
        self.assertEqual(api_incomes[0]["name"], "Purchases")
        self.assertEqual(api_incomes[0]["amount"], positive_purchase_amount)
        self.assertEqual(api_incomes[1]["name"], "Deposits")
        self.assertEqual(api_incomes[1]["amount"], positive_deposits_amount)
        self.assertEqual(api_incomes[2]["name"], "Replenishments")
        self.assertEqual(api_incomes[2]["amount"], negative_replenishmentcollections_price)
        self.assertEqual(api_incomes[3]["name"], "Stocktakings")
        self.assertEqual(api_incomes[3]["amount"], profit_between_stocktakings)

        # Check the expenses
        api_incomes = overview["expenses"]["items"]
        self.assertEqual(api_incomes[0]["name"], "Purchases")
        self.assertEqual(api_incomes[0]["amount"], negative_purchase_amount)
        self.assertEqual(api_incomes[1]["name"], "Deposits")
        self.assertEqual(api_incomes[1]["amount"], negative_deposits_amount)
        self.assertEqual(api_incomes[2]["name"], "Replenishments")
        self.assertEqual(api_incomes[2]["amount"], positive_replenishmentcollections_price)
        self.assertEqual(api_incomes[3]["name"], "Stocktakings")
        self.assertEqual(api_incomes[3]["amount"], loss_between_stocktakings)

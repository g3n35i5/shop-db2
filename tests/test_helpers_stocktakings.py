#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from datetime import datetime

import shopdb.helpers.stocktakings as stocktaking_helpers
from shopdb.api import db
from shopdb.models import (Product, ProductPrice, Purchase,
                           ReplenishmentCollection, Stocktaking,
                           StocktakingCollection)
from tests.base_api import BaseAPITestCase


class TestHelpersStocktakingsTestCase(BaseAPITestCase):
    def test_balance_between_stocktakings_one_stocktaking(self):
        """
        If only one stocktaking was made, no balance calculation can be done.
        This is checked with this test.
        """
        # Insert the initial stocktaking.
        stocktakings = [
            {"product_id": 1, "count": 10},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
        ]

        timestamp = datetime.strptime("2018-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")

        data = {"stocktakings": stocktakings, "timestamp": int(timestamp.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Query the first stocktaking
        start = StocktakingCollection.query.first()

        result = stocktaking_helpers._get_balance_between_stocktakings(start, None)
        self.assertEqual(result, None)

    def test_balance_between_stocktakings_two_stocktakings(self):
        """
        This test checks whether the calculation of the balance works correctly
        between two stocktakings.
        """

        # Insert a purchase which lies before the first stocktaking.
        t = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=1, product_id=1, amount=100, timestamp=t))

        # Manipulate the product price timestamps
        ts = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        for product_price_id in [1, 2, 3, 4]:
            ProductPrice.query.filter_by(id=product_price_id).first().timestamp = ts
        db.session.commit()

        # Insert the default stocktaking collections.
        self.insert_default_stocktakingcollections()

        # Manipulate the stocktaking timestamps
        # First stocktaking: 01.01.2018
        ts = datetime.strptime("2018-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        StocktakingCollection.query.filter_by(id=1).first().timestamp = ts
        # Second stocktaking: 01.03.2018
        ts = datetime.strptime("2018-03-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        StocktakingCollection.query.filter_by(id=2).first().timestamp = ts

        # Insert the default replenishment collections.
        self.insert_default_replenishmentcollections()

        # Manipulate the replenishment timestamps
        # First replenishment: 01.01.2017 (Before the first stocktaking!)
        ts = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        ReplenishmentCollection.query.filter_by(id=1).first().timestamp = ts
        # Second replenishment: 05.02.2019 (Between the stocktakings)
        ts = datetime.strptime("2018-02-05 09:00:00", "%Y-%m-%d %H:%M:%S")
        ReplenishmentCollection.query.filter_by(id=2).first().timestamp = ts

        # Insert some purchases
        t = datetime.strptime("2018-02-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=1, product_id=1, amount=1, timestamp=t))
        t = datetime.strptime("2018-02-02 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=1, product_id=2, amount=5, timestamp=t))
        t = datetime.strptime("2018-02-03 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=2, product_id=3, amount=8, timestamp=t))
        t = datetime.strptime("2018-02-04 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=3, product_id=1, amount=2, timestamp=t))

        # Query the stocktakings.
        start = StocktakingCollection.query.filter_by(id=1).first()
        end = StocktakingCollection.query.filter_by(id=2).first()

        # Timeline
        # Date             Event
        #
        # 01.01.2017       Purchase: 100 x Product 1
        # 01.01.2017       Replenishment 1
        #                  (Both are not taken into account for the calculation)
        # -----------------------------------
        # 01.01.2018       Stocktaking 1
        #                   - Product 1: 100
        #                   - Product 2: 50
        #                   - Product 3: 25
        #                   - Product 4: 33
        #
        # 01.02.2018       Purchase: 1 x Product 1
        # 02.02.2018       Purchase: 5 x Product 2
        # 03.02.2018       Purchase: 8 x Product 3
        # 04.02.2018       Purchase: 2 x Product 1

        # 05.02.2018       Replenishment 2
        #                   - Product 1: 10
        #                   - Product 3: 5
        #
        # -----------------------------------
        # Balance:
        # Product 1: 100 (start) - 3 (purchase) + 10 (replenishment) = 107
        # Product 2:  50 (start) - 5 (purchase) +  0 (replenishment) = 45
        # Product 3:  25 (start) - 8 (purchase) +  5 (replenishment) = 22
        # Product 4:  33 (start) - 0 (purchase) +  0 (replenishment) = 33
        # -----------------------------------
        # 01.03.2018       Stocktaking 2
        #                   - Product 1: 50
        #                   - Product 2: 25
        #                   - Product 3: 12
        #                   - Product 4: 3
        # -----------------------------------
        # Loss
        # Product 1: 107 - 50 = 57
        # Product 2:  45 - 25 = 20
        # Product 3:  22 - 12 = 10
        # Product 4:  33 -  3 = 30

        result = stocktaking_helpers._get_balance_between_stocktakings(start, end)
        self.assertTrue("products" in result)
        products = result["products"]

        # Check if all products are in the balance
        self.assertEqual({1, 2, 3, 4}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products[1]["purchase_count"], 3)
        self.assertEqual(products[2]["purchase_count"], 5)
        self.assertEqual(products[3]["purchase_count"], 8)
        self.assertEqual(products[4]["purchase_count"], 0)

        # Check purchase sum price
        self.assertEqual(products[1]["purchase_sum_price"], 900)
        self.assertEqual(products[2]["purchase_sum_price"], 250)
        self.assertEqual(products[3]["purchase_sum_price"], 800)
        self.assertEqual(products[4]["purchase_sum_price"], 0)

        # Check replenish count
        self.assertEqual(products[1]["replenish_count"], 10)
        self.assertEqual(products[2]["replenish_count"], 0)
        self.assertEqual(products[3]["replenish_count"], 5)
        self.assertEqual(products[4]["replenish_count"], 0)

        # Check differences
        self.assertEqual(products[1]["difference"], -57)
        self.assertEqual(products[2]["difference"], -20)
        self.assertEqual(products[3]["difference"], -10)
        self.assertEqual(products[4]["difference"], -30)

        # Check balance
        self.assertEqual(products[1]["balance"], -57 * 300)
        self.assertEqual(products[2]["balance"], -20 * 50)
        self.assertEqual(products[3]["balance"], -10 * 100)
        self.assertEqual(products[4]["balance"], -30 * 200)

        # Check overall balance
        self.assertEqual(result["balance"], -25100)
        self.assertEqual(result["loss"], 25100)
        self.assertEqual(result["profit"], 0)

    def test_balance_between_stocktakings_multiple_stocktakings(self):
        """
        This test checks whether the calculation of the balance works
        correctly over several stocktakings.
        """
        # Since the start of this test is the same as the previous one, it
        # can be run again to generate the required data.
        self.test_balance_between_stocktakings_two_stocktakings()

        # Insert some purchases between the second and the third stocktaking
        t = datetime.strptime("2018-03-05 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=1, product_id=1, amount=2, timestamp=t))
        t = datetime.strptime("2018-03-06 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=1, product_id=2, amount=10, timestamp=t))
        t = datetime.strptime("2018-03-07 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=2, product_id=3, amount=5, timestamp=t))
        t = datetime.strptime("2018-03-08 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=3, product_id=1, amount=4, timestamp=t))

        # Insert the third stocktaking.
        t = datetime.strptime("2018-04-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(StocktakingCollection(admin_id=1, timestamp=t))
        db.session.flush()
        stocktakings = [
            {"product_id": 1, "count": 40},
            {"product_id": 2, "count": 5},
            {"product_id": 3, "count": 5},
            {"product_id": 4, "count": 0},
        ]

        for s in stocktakings:
            db.session.add(Stocktaking(collection_id=3, **s))

        # The count of product 4 is 0 so the product will be set inactive!
        Product.query.filter_by(id=4).first().active = False

        db.session.commit()

        # Query the stocktakings.
        start = StocktakingCollection.query.filter_by(id=1).first()
        end = StocktakingCollection.query.filter_by(id=3).first()

        # Timeline
        # Date             Event
        #
        # 01.01.2017       Purchase: 100 x Product 1
        # 01.01.2017       Replenishment 1
        #                  (Both are not taken into account for the calculation)
        # -----------------------------------
        # 01.01.2018       Stocktaking 1
        #                   - Product 1: 100
        #                   - Product 2: 50
        #                   - Product 3: 25
        #                   - Product 4: 33
        #
        # 01.02.2018       Purchase: 1 x Product 1
        # 02.02.2018       Purchase: 5 x Product 2
        # 03.02.2018       Purchase: 8 x Product 3
        # 04.02.2018       Purchase: 2 x Product 1
        # -----------------------------------
        # 05.02.2018       Replenishment 2
        #                   - Product 1: 10
        #                   - Product 3: 5
        #
        # -----------------------------------
        # 05.03.2018       Purchase:  2 x Product 1
        # 06.03.2018       Purchase: 10 x Product 2
        # 07.03.2018       Purchase:  5 x Product 3
        # 08.03.2018       Purchase:  4 x Product 1
        # -----------------------------------
        # 01.04.2018       Stocktaking 3
        #                   - Product 1: 40
        #                   - Product 2:  5
        #                   - Product 3:  5
        #                   - Product 4:  0
        # -----------------------------------
        # Balance:
        # Product 1: 100 (start) -  9 (purchase) + 10 (replenishment) = 101
        # Product 2:  50 (start) - 15 (purchase) +  0 (replenishment) =  35
        # Product 3:  25 (start) - 13 (purchase) +  5 (replenishment) =  17
        # Product 4:  33 (start) -  0 (purchase) +  0 (replenishment) =  33
        # -----------------------------------
        # Loss between first and third stocktaking
        # Product 1: 101 - 40 = 61
        # Product 2:  35 -  5 = 30
        # Product 3:  17 -  5 = 12
        # Product 4:  33 -  0 = 33

        result = stocktaking_helpers._get_balance_between_stocktakings(start, end)
        self.assertTrue("products" in result)
        products = result["products"]

        # Check if all products are in the balance
        self.assertEqual({1, 2, 3, 4}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products[1]["purchase_count"], 9)
        self.assertEqual(products[2]["purchase_count"], 15)
        self.assertEqual(products[3]["purchase_count"], 13)
        self.assertEqual(products[4]["purchase_count"], 0)

        # Check purchase sum price
        self.assertEqual(products[1]["purchase_sum_price"], 2700)
        self.assertEqual(products[2]["purchase_sum_price"], 750)
        self.assertEqual(products[3]["purchase_sum_price"], 1300)
        self.assertEqual(products[4]["purchase_sum_price"], 0)

        # Check replenish count
        self.assertEqual(products[1]["replenish_count"], 10)
        self.assertEqual(products[2]["replenish_count"], 0)
        self.assertEqual(products[3]["replenish_count"], 5)
        self.assertEqual(products[4]["replenish_count"], 0)

        # Check differences
        self.assertEqual(products[1]["difference"], -61)
        self.assertEqual(products[2]["difference"], -30)
        self.assertEqual(products[3]["difference"], -12)
        self.assertEqual(products[4]["difference"], -33)

        # Check balance
        self.assertEqual(products[1]["balance"], -61 * 300)
        self.assertEqual(products[2]["balance"], -30 * 50)
        self.assertEqual(products[3]["balance"], -12 * 100)
        self.assertEqual(products[4]["balance"], -33 * 200)

        # Check overall balance
        self.assertEqual(result["balance"], -27600)
        self.assertEqual(result["loss"], 27600)
        self.assertEqual(result["profit"], 0)

    def test_balance_between_stocktakings_forgotten_purchases_inactive_products(self):
        """
        TODO
        """
        # Since the start of this test is the same as the previous one, it
        # can be run again to generate the required data.
        self.test_balance_between_stocktakings_multiple_stocktakings()

        # Ooops. We forgot to insert some two purchases (inactive products). Lets do it now (AFTER THIRD STOCKTAKING!)
        self.assertFalse(Product.query.filter_by(id=4).first().active)
        t = datetime.strptime("2018-04-02 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=3, product_id=4, amount=2, timestamp=t))

        # Insert the fourth stocktaking.
        t = datetime.strptime("2018-04-05 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(StocktakingCollection(admin_id=1, timestamp=t))
        db.session.flush()
        stocktakings = [
            {"product_id": 1, "count": 40},
            {"product_id": 2, "count": 5},
            {"product_id": 3, "count": 5},
            {"product_id": 4, "count": 0},
        ]

        for s in stocktakings:
            db.session.add(Stocktaking(collection_id=4, **s))

        db.session.commit()

        # Query the stocktakings.
        start = StocktakingCollection.query.filter_by(id=1).first()
        end = StocktakingCollection.query.filter_by(id=4).first()

        result = stocktaking_helpers._get_balance_between_stocktakings(start, end)
        self.assertTrue("products" in result)
        products = result["products"]

        # Check if all products are in the balance
        self.assertEqual({1, 2, 3, 4}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products[1]["purchase_count"], 9)
        self.assertEqual(products[2]["purchase_count"], 15)
        self.assertEqual(products[3]["purchase_count"], 13)
        self.assertEqual(products[4]["purchase_count"], 2)

        # Check purchase sum price
        self.assertEqual(products[1]["purchase_sum_price"], 2700)
        self.assertEqual(products[2]["purchase_sum_price"], 750)
        self.assertEqual(products[3]["purchase_sum_price"], 1300)
        self.assertEqual(products[4]["purchase_sum_price"], 400)

        # Check replenish count
        self.assertEqual(products[1]["replenish_count"], 10)
        self.assertEqual(products[2]["replenish_count"], 0)
        self.assertEqual(products[3]["replenish_count"], 5)
        self.assertEqual(products[4]["replenish_count"], 0)

        # Check differences
        self.assertEqual(products[1]["difference"], -61)
        self.assertEqual(products[2]["difference"], -30)
        self.assertEqual(products[3]["difference"], -12)
        self.assertEqual(products[4]["difference"], -31)

        # Check balance
        self.assertEqual(products[1]["balance"], -61 * 300)
        self.assertEqual(products[2]["balance"], -30 * 50)
        self.assertEqual(products[3]["balance"], -12 * 100)
        self.assertEqual(products[4]["balance"], -31 * 200)

        # Check overall balance
        self.assertEqual(result["balance"], -27200)
        self.assertEqual(result["loss"], 27200)
        self.assertEqual(result["profit"], 0)

    def test_balance_between_stocktakings_product_set_to_inactive(self):
        """
        This test checks whether the calculation of the balance works
        correctly if a product has been set to inactive since the first
        stocktaking.
        """
        # Manipulate the product price timestamps
        ts = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        for product_price_id in [1, 2, 3, 4]:
            ProductPrice.query.filter_by(id=product_price_id).first().timestamp = ts
        db.session.commit()

        # Insert the first stocktaking
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.flush()

        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=1))

        # Manipulate first stocktaking timestamp
        # First stocktaking: 01.01.2018
        ts = datetime.strptime("2018-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        StocktakingCollection.query.filter_by(id=1).first().timestamp = ts

        # Insert a purchase.
        t = datetime.strptime("2018-03-05 09:00:00", "%Y-%m-%d %H:%M:%S")
        db.session.add(Purchase(user_id=1, product_id=1, amount=90, timestamp=t))

        # Insert the second stocktaking.
        stocktakings = [
            {"product_id": 1, "count": 0},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
        ]
        t = datetime.strptime("2018-04-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        data = {"stocktakings": stocktakings, "timestamp": int(t.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Insert the third stocktaking. (Product 1 is not included)
        stocktakings = [
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
        ]
        t = datetime.strptime("2018-04-02 09:00:00", "%Y-%m-%d %H:%M:%S")
        data = {"stocktakings": stocktakings, "timestamp": int(t.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Query the stocktakings.
        start = StocktakingCollection.query.filter_by(id=1).first()
        end = StocktakingCollection.query.filter_by(id=3).first()

        self.assertTrue(1 in [s.product_id for s in start.stocktakings])
        self.assertFalse(1 in [s.product_id for s in end.stocktakings])

        result = stocktaking_helpers._get_balance_between_stocktakings(start, end)
        self.assertTrue("products" in result)
        products = result["products"]

        # Check if all products are in the balance
        self.assertEqual({1, 2, 3, 4}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products[1]["purchase_count"], 90)
        self.assertEqual(products[2]["purchase_count"], 0)
        self.assertEqual(products[3]["purchase_count"], 0)
        self.assertEqual(products[4]["purchase_count"], 0)

        # Check purchase sum price
        self.assertEqual(products[1]["purchase_sum_price"], 27000)
        self.assertEqual(products[2]["purchase_sum_price"], 0)
        self.assertEqual(products[3]["purchase_sum_price"], 0)
        self.assertEqual(products[4]["purchase_sum_price"], 0)

        # Check replenish count
        self.assertEqual(products[1]["replenish_count"], 0)
        self.assertEqual(products[2]["replenish_count"], 0)
        self.assertEqual(products[3]["replenish_count"], 0)
        self.assertEqual(products[4]["replenish_count"], 0)

        # Check differences
        self.assertEqual(products[1]["difference"], -10)
        self.assertEqual(products[2]["difference"], 0)
        self.assertEqual(products[3]["difference"], 0)
        self.assertEqual(products[4]["difference"], 0)

        # Check balance
        self.assertEqual(products[1]["balance"], -10 * 300)
        self.assertEqual(products[2]["balance"], 0)
        self.assertEqual(products[3]["balance"], 0)
        self.assertEqual(products[4]["balance"], 0)

        # Check overall balance
        self.assertEqual(result["balance"], -3000)
        self.assertEqual(result["loss"], 3000)
        self.assertEqual(result["profit"], 0)

    def test_balance_between_stocktakings_product_creation(self):
        """
        This test checks whether the calculation of the balance works
        correctly if a new product has been added since the first stocktaking.
        """

        # Insert the first stocktaking
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.flush()

        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=1))

        # Manipulate first stocktaking timestamp
        # First stocktaking: 01.01.2018
        ts = datetime.strptime("2018-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        StocktakingCollection.query.filter_by(id=1).first().timestamp = ts

        # Create a product.
        data = {"name": "Bread", "price": 100, "tags": [1]}
        self.post(url="/products", role="admin", data=data)

        # Manipulate the product price timestamps
        ts = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        for product_price_id in [1, 2, 3, 4, 5]:
            ProductPrice.query.filter_by(id=product_price_id).first().timestamp = ts
        db.session.commit()

        # Create replenishment.
        replenishments = [{"product_id": 5, "amount": 20, "total_price": 2000}]
        data = {
            "replenishments": replenishments,
            "comment": "My test comment",
            "timestamp": "2020-02-24 12:00:00Z",
            "seller_id": 5,
        }
        self.post(url="/replenishmentcollections", data=data, role="admin")
        ts = datetime.strptime("2018-03-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        ReplenishmentCollection.query.filter_by(id=1).first().timestamp = ts
        db.session.commit()

        # Insert the second stocktaking.
        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
            {"product_id": 5, "count": 10},
        ]
        t = datetime.strptime("2018-04-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        data = {"stocktakings": stocktakings, "timestamp": int(t.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Query the stocktakings.
        start = StocktakingCollection.query.filter_by(id=1).first()
        end = StocktakingCollection.query.filter_by(id=2).first()

        self.assertFalse(5 in [s.product_id for s in start.stocktakings])
        self.assertTrue(5 in [s.product_id for s in end.stocktakings])

        result = stocktaking_helpers._get_balance_between_stocktakings(start, end)
        self.assertTrue("products" in result)
        products = result["products"]

        # Check if all products are in the balance
        self.assertEqual({1, 2, 3, 4, 5}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products[1]["purchase_count"], 0)
        self.assertEqual(products[2]["purchase_count"], 0)
        self.assertEqual(products[3]["purchase_count"], 0)
        self.assertEqual(products[4]["purchase_count"], 0)
        self.assertEqual(products[5]["purchase_count"], 0)

        # Check purchase sum price
        self.assertEqual(products[1]["purchase_sum_price"], 0)
        self.assertEqual(products[2]["purchase_sum_price"], 0)
        self.assertEqual(products[3]["purchase_sum_price"], 0)
        self.assertEqual(products[4]["purchase_sum_price"], 0)
        self.assertEqual(products[5]["purchase_sum_price"], 0)

        # Check replenish count
        self.assertEqual(products[1]["replenish_count"], 0)
        self.assertEqual(products[2]["replenish_count"], 0)
        self.assertEqual(products[3]["replenish_count"], 0)
        self.assertEqual(products[4]["replenish_count"], 0)
        self.assertEqual(products[5]["replenish_count"], 20)

        # Check differences
        self.assertEqual(products[1]["difference"], 0)
        self.assertEqual(products[2]["difference"], 0)
        self.assertEqual(products[3]["difference"], 0)
        self.assertEqual(products[4]["difference"], 0)
        self.assertEqual(products[5]["difference"], -10)

        # Check balance
        self.assertEqual(products[1]["balance"], 0)
        self.assertEqual(products[2]["balance"], 0)
        self.assertEqual(products[3]["balance"], 0)
        self.assertEqual(products[4]["balance"], 0)
        self.assertEqual(products[5]["balance"], -10 * 100)

        # Check overall balance
        self.assertEqual(result["balance"], -1000)
        self.assertEqual(result["profit"], 0)

    def test_balance_between_stocktakings_new_product_and_set_inactive(self):
        """
        If a product was created between the first and the last stocktaking,
        which was then reset to inactive, the calculation of the balance must
        still be carried out correctly. This functionality is checked with
        this test.
        """
        # Since the start of this test is the same as the previous one, it
        # can be run again to generate the required data.
        self.test_balance_between_stocktakings_product_creation()

        # Set the product 5 inactive with another stocktaking.
        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
            {"product_id": 5, "count": 0},
        ]
        t = datetime.strptime("2018-05-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        data = {"stocktakings": stocktakings, "timestamp": int(t.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Insert the last stocktaking. (Product 5 is not included)
        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 50},
            {"product_id": 3, "count": 25},
            {"product_id": 4, "count": 33},
        ]
        t = datetime.strptime("2018-06-02 09:00:00", "%Y-%m-%d %H:%M:%S")
        data = {"stocktakings": stocktakings, "timestamp": int(t.timestamp())}
        self.post(url="/stocktakingcollections", data=data, role="admin")

        # Query the stocktakings.
        start = StocktakingCollection.query.filter_by(id=1).first()
        end = StocktakingCollection.query.filter_by(id=4).first()

        self.assertFalse(5 in [s.product_id for s in start.stocktakings])
        self.assertFalse(5 in [s.product_id for s in end.stocktakings])

        result = stocktaking_helpers._get_balance_between_stocktakings(start, end)
        self.assertTrue("products" in result)
        products = result["products"]

        # Check if all products are in the balance
        self.assertEqual({1, 2, 3, 4, 5}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products[1]["purchase_count"], 0)
        self.assertEqual(products[2]["purchase_count"], 0)
        self.assertEqual(products[3]["purchase_count"], 0)
        self.assertEqual(products[4]["purchase_count"], 0)
        self.assertEqual(products[5]["purchase_count"], 0)

        # Check purchase sum price
        self.assertEqual(products[1]["purchase_sum_price"], 0)
        self.assertEqual(products[2]["purchase_sum_price"], 0)
        self.assertEqual(products[3]["purchase_sum_price"], 0)
        self.assertEqual(products[4]["purchase_sum_price"], 0)
        self.assertEqual(products[5]["purchase_sum_price"], 0)

        # Check replenish count
        self.assertEqual(products[1]["replenish_count"], 0)
        self.assertEqual(products[2]["replenish_count"], 0)
        self.assertEqual(products[3]["replenish_count"], 0)
        self.assertEqual(products[4]["replenish_count"], 0)
        self.assertEqual(products[5]["replenish_count"], 20)

        # Check differences
        self.assertEqual(products[1]["difference"], 0)
        self.assertEqual(products[2]["difference"], 0)
        self.assertEqual(products[3]["difference"], 0)
        self.assertEqual(products[4]["difference"], 0)
        self.assertEqual(products[5]["difference"], -20)

        # Check balance
        self.assertEqual(products[1]["balance"], 0)
        self.assertEqual(products[2]["balance"], 0)
        self.assertEqual(products[3]["balance"], 0)
        self.assertEqual(products[4]["balance"], 0)
        self.assertEqual(products[5]["balance"], -20 * 100)

        # Check overall balance
        self.assertEqual(result["balance"], -2000)
        self.assertEqual(result["loss"], 2000)
        self.assertEqual(result["profit"], 0)

    def test_balance_between_stocktakings_with_profit_and_loss(self):
        """
        This test checks whether the profits and losses and the resulting
        balance are calculated correctly.
        """
        # Manipulate the product price timestamps
        ts = datetime.strptime("2017-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        for id in [1, 2, 3, 4]:
            ProductPrice.query.filter_by(id=id).first().timestamp = ts
        db.session.commit()

        # Insert the first stocktaking
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.flush()

        stocktakings = [
            {"product_id": 1, "count": 100},
            {"product_id": 2, "count": 100},
            {"product_id": 3, "count": 100},
            {"product_id": 4, "count": 100},
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=1))

        # Manipulate first stocktaking timestamp
        # First stocktaking: 01.01.2018
        ts = datetime.strptime("2018-01-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        StocktakingCollection.query.filter_by(id=1).first().timestamp = ts

        # Insert the second stocktaking
        db.session.add(StocktakingCollection(admin_id=1))
        db.session.flush()

        stocktakings = [
            {"product_id": 1, "count": 110},  # Products have been added!
            {"product_id": 2, "count": 90},  # Products have been lost!
            {"product_id": 3, "count": 100},
            {"product_id": 4, "count": 100},
        ]
        for s in stocktakings:
            db.session.add(Stocktaking(**s, collection_id=2))

        # Manipulate second stocktaking timestamp
        # Second stocktaking: 01.02.2018
        ts = datetime.strptime("2018-02-01 09:00:00", "%Y-%m-%d %H:%M:%S")
        StocktakingCollection.query.filter_by(id=2).first().timestamp = ts

        # Query the stocktakings.
        start = StocktakingCollection.query.filter_by(id=1).first()
        end = StocktakingCollection.query.filter_by(id=2).first()

        result = stocktaking_helpers._get_balance_between_stocktakings(start, end)
        self.assertTrue("products" in result)
        products = result["products"]

        # Check if all products are in the balance
        self.assertEqual({1, 2, 3, 4}, set(products.keys()))

        # Check purchase count
        self.assertEqual(products[1]["purchase_count"], 0)
        self.assertEqual(products[2]["purchase_count"], 0)
        self.assertEqual(products[3]["purchase_count"], 0)
        self.assertEqual(products[4]["purchase_count"], 0)

        # Check purchase sum price
        self.assertEqual(products[1]["purchase_sum_price"], 0)
        self.assertEqual(products[2]["purchase_sum_price"], 0)
        self.assertEqual(products[3]["purchase_sum_price"], 0)
        self.assertEqual(products[4]["purchase_sum_price"], 0)

        # Check replenish count
        self.assertEqual(products[1]["replenish_count"], 0)
        self.assertEqual(products[2]["replenish_count"], 0)
        self.assertEqual(products[3]["replenish_count"], 0)
        self.assertEqual(products[4]["replenish_count"], 0)

        # Check differences
        self.assertEqual(products[1]["difference"], 10)
        self.assertEqual(products[2]["difference"], -10)
        self.assertEqual(products[3]["difference"], 0)
        self.assertEqual(products[4]["difference"], 0)

        # Check balance
        self.assertEqual(products[1]["balance"], 10 * 300)
        self.assertEqual(products[2]["balance"], -10 * 50)
        self.assertEqual(products[3]["balance"], 0)
        self.assertEqual(products[4]["balance"], 0)

        # Check overall balance
        self.assertEqual(result["balance"], 2500)
        self.assertEqual(result["loss"], 500)
        self.assertEqual(result["profit"], 3000)

    def test_get_latest_non_revoked_stocktakingcollection(self):
        """
        This test checks the "get_latest_non_revoked_stocktakingcollection" helper function.
        """
        # Insert the default stocktaking collections.
        self.insert_default_stocktakingcollections()

        # Check the latest collection
        collection = stocktaking_helpers.get_latest_non_revoked_stocktakingcollection()
        self.assertEqual(2, collection.id)

        # Revoke the latest stocktakingcollection
        StocktakingCollection.query.filter(
            StocktakingCollection.id == 2
        ).first().revoked = True
        db.session.commit()

        # Check the latest collection again
        collection = stocktaking_helpers.get_latest_non_revoked_stocktakingcollection()
        self.assertEqual(1, collection.id)

        # Revoke the last remaining non revoked stocktakingcollection
        StocktakingCollection.query.filter(
            StocktakingCollection.id == 1
        ).first().revoked = True
        collection = stocktaking_helpers.get_latest_non_revoked_stocktakingcollection()

        # The result should be None
        self.assertIsNone(collection)

    def test_get_latest_stocktaking_of_product(self):
        """
        This test checks the "get_latest_stocktaking_of_product" helper function.
        """
        # Insert the default stocktaking collections.
        self.insert_default_stocktakingcollections()

        # Check the latest stock
        stocktaking = stocktaking_helpers.get_latest_stocktaking_of_product(
            product_id=1
        )
        self.assertEqual(50, stocktaking.count)

        # Revoke the latest stocktakingcollection
        StocktakingCollection.query.filter(
            StocktakingCollection.id == 2
        ).first().revoked = True
        db.session.commit()

        # Check the latest stock again
        stocktaking = stocktaking_helpers.get_latest_stocktaking_of_product(
            product_id=1
        )
        self.assertEqual(100, stocktaking.count)

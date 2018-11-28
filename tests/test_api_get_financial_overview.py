from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class GetFinancialOverviewAPITestCase(BaseAPITestCase):
    def test_authorization_get_financial_overview(self):
        """
        This route may only be accessible to administrators. An exception must
        be made for all other requests.
        """
        res = self.get(url='/financial_overview')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url='/financial_overview', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_get_financial_overview(self):
        """
        This test ensures that the entire financial overview is calculated
        correctly. To do this, some test entries are entered into the
        database, some of which are revoked. Then the amount is manually
        calculated which should come out at the end of the calculation and
        compared with the amount calculated by the API.
        """

        # Insert some purchases (some are revoked)
        p1 = Purchase(user_id=1, product_id=3, amount=4, revoked=True)
        p2 = Purchase(user_id=2, product_id=2, amount=3, revoked=False)  # <-
        p3 = Purchase(user_id=3, product_id=1, amount=2, revoked=False)  # <-
        p4 = Purchase(user_id=1, product_id=2, amount=1, revoked=True)
        for p in [p1, p2, p3, p4]:
            db.session.add(p)

        # Purchase amount should be 3 * 50 + 2 * 300
        psum = p2.price + p3.price
        self.assertEqual(psum, 750)

        # Insert some deposits (some are revoked)
        d1 = Deposit(user_id=1, admin_id=1, comment='Foo',
                     amount=100, revoked=False)  # <-
        d2 = Deposit(user_id=2, admin_id=1, comment='Foo',
                     amount=500, revoked=True)
        d3 = Deposit(user_id=3, admin_id=1, comment='Foo',
                     amount=300, revoked=False)  # <-
        d4 = Deposit(user_id=2, admin_id=1, comment='Foo',
                     amount=200, revoked=True)
        for d in [d1, d2, d3, d4]:
            db.session.add(d)
        # Deposit amount should be 300 + 100
        dsum = d1.amount + d3.amount
        self.assertEqual(dsum, 400)

        # Insert some refunds (some are revoked)
        r1 = Refund(user_id=1, total_price=100, admin_id=1,
                    comment='Foo', revoked=True)
        r2 = Refund(user_id=3, total_price=200, admin_id=1,
                    comment='Foo', revoked=True)
        r3 = Refund(user_id=2, total_price=150, admin_id=1,
                    comment='Foo', revoked=False)  # <-
        r4 = Refund(user_id=1, total_price=700, admin_id=1,
                    comment='Foo', revoked=False)  # <-
        for r in [r1, r2, r3, r4]:
            db.session.add(r)

        # Refund sum should be 150 + 700 = 850
        rsum = r3.total_price + r4.total_price
        self.assertEqual(rsum, 850)

        # Commit the changes.
        db.session.commit()

        # Insert the replenishmentcollections and revoke the first one.
        self.insert_default_replenishmentcollections()
        rc = ReplenishmentCollection.query.filter_by(id=1).first()
        rc.toggle_revoke(admin_id=1, revoked=True)
        db.session.commit()
        rc = ReplenishmentCollection.query.filter_by(id=2).first()
        rcsum = rc.price
        self.assertEqual(3500, rcsum)

        # Calculate the total balance, incomes and expenses.
        incomes = psum
        expenses = sum([dsum, rsum, rcsum])
        total_balance = incomes - expenses

        res = self.get(url='/financial_overview', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'financial_overview' in data
        overview = data['financial_overview']
        self.assertEqual(overview['total_balance'], total_balance)
        self.assertEqual(overview['incomes']['amount'], incomes)
        self.assertEqual(overview['expenses']['amount'], expenses)
        self.assertEqual(overview['expenses']['items'][0]['name'], 'Deposits')
        self.assertEqual(overview['expenses']['items'][0]['amount'], dsum)
        self.assertEqual(overview['expenses']['items'][1]['name'], 'Refunds')
        self.assertEqual(overview['expenses']['items'][1]['amount'], rsum)
        self.assertEqual(overview['expenses']['items'][2]['name'],
                         'Replenishments')
        self.assertEqual(overview['expenses']['items'][2]['amount'], rcsum)


from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json
from datetime import datetime


class GetProductPricehistoryAPITestCase(BaseAPITestCase):
    def insert_pricehistory(self, dates=None):
        prices = [42, 43, 44, 45]
        timestamps = []
        if dates:
            for date in dates:
                timestamps.append(datetime.strptime(date, '%d.%m.%Y'))
        else:
            timestamps = [datetime.now()] * 4

        for i in range(4):
            p = ProductPrice(
                price=prices[i], product_id=1, admin_id=1,
                timestamp=timestamps[i])
            db.session.add(p)
        db.session.commit()

    def test_authorization(self):
        """
        This route should only be available for administrators.
        """
        res = self.get(url='/products/1/pricehistory')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)
        res = self.get(url='/products/1/pricehistory', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_get_pricehistory_non_existing_product(self):
        """
        There should be an exception when the requested product does not exist.
        """
        res = self.get(url='/products/10/pricehistory', role='admin')
        self.assertException(res, exc.EntryNotFound)

    def test_get_pricehistory_invalid_start_or_end_date(self):
        """
        There should be an exception when the start or end date are invalid.
        """
        # Testing start date
        url = '/products/1/pricehistory?start_date=trololol'
        res = self.get(url=url, role='admin')
        self.assertException(res, exc.WrongType)

        # Testing end date
        url = '/products/1/pricehistory?end_date=trololol'
        res = self.get(url=url, role='admin')
        self.assertException(res, exc.WrongType)

        # Testing start and end date
        url = '/products/1/pricehistory?start_date=trololol&end_date=trololol'
        res = self.get(url=url, role='admin')
        self.assertException(res, exc.WrongType)

    def test_get_pricehistory_defining_only_start_date(self):
        """
        Querying the pricehistory with only the start date given.
        """
        # Change the creation date of the product to 01.01.2019
        dt = datetime.strptime('01.01.2019', '%d.%m.%Y')
        Product.query.filter_by(id=1).first().creation_date = dt
        ProductPrice.query.filter_by(product_id=1).first().timestamp = dt
        db.session.commit()

        # Insert a pricehistory
        timestamps = ['02.01.2019', '03.01.2019', '08.01.2019', '10.01.2019']
        self.insert_pricehistory(timestamps)

        # Query all entries since 03.01.2019
        start = int(datetime(year=2019, month=1, day=3).timestamp())
        url = f'/products/1/pricehistory?start_date={start}'
        res = self.get(url=url, role='admin')
        data = json.loads(res.data)
        self.assertEqual(len(data['pricehistory']), 3)

    def test_get_pricehistory_defining_only_end_date(self):
        """
        Querying the pricehistory with only the end date given.
        """
        # Change the creation date of the product to 01.01.2019
        dt = datetime.strptime('01.01.2019', '%d.%m.%Y')
        Product.query.filter_by(id=1).first().creation_date = dt
        ProductPrice.query.filter_by(product_id=1).first().timestamp = dt
        db.session.commit()

        # Insert a pricehistory
        timestamps = ['02.01.2019', '03.01.2019', '08.01.2019', '10.01.2019']
        self.insert_pricehistory(timestamps)

        # Query all entries up to 02.01.2019
        end = int(datetime(year=2019, month=1, day=2).timestamp())
        url = f'/products/1/pricehistory?end_date={end}'
        res = self.get(url=url, role='admin')
        data = json.loads(res.data)
        # There should be only the entries [01.01.19 and 02.01.19]
        self.assertEqual(len(data['pricehistory']), 2)

    def test_get_pricehistory_defining_start_and_end_date(self):
        """
        Querying the pricehistory with start and end date given.
        """
        # Change the creation date of the product to 01.01.2019
        dt = datetime.strptime('01.01.2019', '%d.%m.%Y')
        Product.query.filter_by(id=1).first().creation_date = dt
        ProductPrice.query.filter_by(product_id=1).first().timestamp = dt
        db.session.commit()

        # Insert a pricehistory
        timestamps = ['02.01.2019', '03.01.2019', '08.01.2019', '10.01.2019']
        self.insert_pricehistory(timestamps)

        # Query all entries from the 02.01.19 to 08.01.19
        start = int(datetime(year=2019, month=1, day=2).timestamp())
        end = int(datetime(year=2019, month=1, day=8).timestamp())
        url = f'/products/1/pricehistory?start_date={start}&end_date={end}'
        res = self.get(url=url, role='admin')
        data = json.loads(res.data)
        # There should be only the entries [02.01.19, 03.01.19 and 08.01.19]
        self.assertEqual(len(data['pricehistory']), 3)




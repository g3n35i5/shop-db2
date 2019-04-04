from shopdb.api import *
import shopdb.exceptions as exc
from shopdb.helpers.products import _get_product_mean_price_in_time_range
from tests.base_api import BaseAPITestCase
from datetime import datetime


class TestHelpersProductsTestCase(BaseAPITestCase):
    def test_get_product_mean_price_in_range(self):
        """
        This test checks whether the average weighted price of a product is
        correctly determined within a given period of time.
        """
        # Manipulate the timestamp of the first product price.
        t = datetime.strptime('2017-01-01 09:00:00', '%Y-%m-%d %H:%M:%S')
        ProductPrice.query.filter_by(product_id=1).first().timestamp = t
        db.session.commit()
        self.assertEqual(
            ProductPrice.query.filter_by(product_id=1).first().timestamp,
            t)

        # Insert some product price changes.
        t1 = datetime.strptime('2017-02-01 09:00:00', '%Y-%m-%d %H:%M:%S')
        pp1 = ProductPrice(price=100, product_id=1, admin_id=1, timestamp=t1)
        t2 = datetime.strptime('2017-02-04 09:00:00', '%Y-%m-%d %H:%M:%S')
        pp2 = ProductPrice(price=50, product_id=1, admin_id=1, timestamp=t2)
        t3 = datetime.strptime('2017-02-06 09:00:00', '%Y-%m-%d %H:%M:%S')
        pp3 = ProductPrice(price=150, product_id=1, admin_id=1, timestamp=t3)
        t4 = datetime.strptime('2017-02-08 09:00:00', '%Y-%m-%d %H:%M:%S')
        pp4 = ProductPrice(price=200, product_id=1, admin_id=1, timestamp=t4)

        for pp in [pp1, pp2, pp3, pp4]:
            db.session.add(pp)
        db.session.commit()

        # The product current price should be 200.
        self.assertEqual(Product.query.filter_by(id=1).first().price, 200)

        # Check the mean product price in different time ranges.
        # Case 1: Mean price at one day.
        start = datetime.strptime('2017-02-01 09:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime('2017-02-01 10:00:00', '%Y-%m-%d %H:%M:%S')
        mean = _get_product_mean_price_in_time_range(1, start, end)
        self.assertEqual(mean, 100)

        # Case 2: Mean price at two days
        # Price on 03.02.2017: 100
        # Price on 04.02.2017:  50
        # Mean price: (1x100 + 1*50) / 2 = 75
        start = datetime.strptime('2017-02-03 09:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime('2017-02-04 10:00:00', '%Y-%m-%d %H:%M:%S')
        mean = _get_product_mean_price_in_time_range(1, start, end)
        self.assertEqual(mean, 75)

        # Case 2: Mean price at three days
        # Price on 03.02.2017: 100
        # Price on 04.02.2017:  50
        # Price on 05.02.2017:  50
        # Mean price: (1x100 + 1*50 + 1*50) / 3 = 66.6666 ~= 67
        start = datetime.strptime('2017-02-03 09:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime('2017-02-05 10:00:00', '%Y-%m-%d %H:%M:%S')
        mean = _get_product_mean_price_in_time_range(1, start, end)
        self.assertEqual(mean, 67)

        # Case 3: All days
        # Price on 31.01.2017: 300
        # Price on 01.02.2017: 100
        # Price on 02.02.2017: 100
        # Price on 03.02.2017: 100
        # Price on 04.02.2017:  50
        # Price on 05.02.2017:  50
        # Price on 06.02.2017: 150
        # Price on 07.02.2017: 150
        # Price on 08.02.2017: 200
        # Price on 09.02.2017: 200
        # Price on 10.02.2017: 200
        # Mean price: (300 + 3x100 + 2*50 + 2*150 + 3*200) / 11
        start = datetime.strptime('2017-01-31 09:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime('2017-02-10 10:00:00', '%Y-%m-%d %H:%M:%S')
        mean = _get_product_mean_price_in_time_range(1, start, end)
        self.assertEqual(mean, 145)

    def test_get_product_mean_price_in_range_invalid_params(self):
        """
        This test ensures that the helper function raises the corresponding
        exceptions for invalid parameters.
        """
        # Invalid dates
        with self.assertRaises(exc.InvalidData):
            _get_product_mean_price_in_time_range(1, '01.01.2018', '02.01.2018')

        # Invalid product
        start = datetime.strptime('2017-01-31 09:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime('2017-02-10 10:00:00', '%Y-%m-%d %H:%M:%S')
        with self.assertRaises(exc.EntryNotFound):
            _get_product_mean_price_in_time_range(42, start, end)

        # End timestamp lies before start timestamp
        start = datetime.strptime('2017-01-31 09:00:00', '%Y-%m-%d %H:%M:%S')
        end = datetime.strptime('2017-01-30 10:00:00', '%Y-%m-%d %H:%M:%S')
        with self.assertRaises(exc.InvalidData):
            _get_product_mean_price_in_time_range(1, start, end)

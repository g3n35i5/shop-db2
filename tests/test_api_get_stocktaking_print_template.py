#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import shopdb.exceptions as exc
from shopdb.api import db
from shopdb.models import Product
from tests.base_api import BaseAPITestCase


class GetStocktakingPrintTemplateAPITestCase(BaseAPITestCase):
    def test_get_stocktaking_template_file_type(self):
        """
        This test verifies that the file format returned by the API is correct.
        """
        # Skip this test if pdfkit is not available
        try:
            import pdfkit
        except ImportError:
            self.skipTest("Test skipped because pdfkit is not available on this system")

        res = self.get(url="/stocktakingcollections/template", role="admin")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data is not None)
        self.assertTrue(str(res.data).startswith("b'%PDF-"))

    def test_get_stocktaking_template_file_no_products(self):
        """
        This test verifies that the correct exception is made when there are no
        products available for stocktaking.
        """
        # Skip this test if pdfkit is not available
        try:
            import pdfkit
        except ImportError:
            self.skipTest("Test skipped because pdfkit is not available on this system")

        # Set all products inactive
        for product in Product.query.all():
            product.active = False
        db.session.commit()

        # We dont have any active products now so we wait for the exception.
        res = self.get(url="/stocktakingcollections/template", role="admin")
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

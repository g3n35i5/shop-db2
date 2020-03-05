#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import *
from shopdb.api import db
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase


class GetStocktakingPrintTemplateAPITestCase(BaseAPITestCase):

    def test_get_stocktaking_template_file_type(self):
        """
        This test verifies that the file format returned by the API is correct.
        """
        res = self.get(url='/stocktakingcollections/template', role='admin')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data is not None)
        self.assertTrue(str(res.data).startswith("b'%PDF-"))

    def test_get_stocktaking_template_file_no_products(self):
        """
        This test verifies that the correct exception is made when there are no
        products available for stocktaking.
        """
        # Set all products inactive
        for product in Product.query.all():
            product.active = False
        db.session.commit()

        # We dont have any active products now so we wait for the exception.
        res = self.get(url='/stocktakingcollections/template', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.EntryNotFound)

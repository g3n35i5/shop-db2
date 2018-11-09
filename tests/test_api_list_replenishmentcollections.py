from shopdb.api import *
import shopdb.models as models
import shopdb.exceptions as exc
from sqlalchemy.exc import *
from base import u_emails, u_passwords, u_firstnames, u_lastnames, u_usernames
from base_api import BaseAPITestCase
from flask import json
import jwt
import pdb


class ListReplenishmentCollectionsAPITestCase(BaseAPITestCase):
    def _insert_testdata(self):
        product1 = Product.query.filter_by(id=1).first()
        product2 = Product.query.filter_by(id=2).first()
        product3 = Product.query.filter_by(id=3).first()
        rc1 = ReplenishmentCollection(admin_id=1, revoked=False)
        rc2 = ReplenishmentCollection(admin_id=2, revoked=False)
        for r in [rc1, rc2]:
            db.session.add(r)
        db.session.flush()
        rep1 = Replenishment(replcoll_id=rc1.id, product_id=product1.id,
                             amount=10, total_price=10*product1.price)
        rep2 = Replenishment(replcoll_id=rc1.id, product_id=product2.id,
                             amount=20, total_price=20*product2.price)
        rep3 = Replenishment(replcoll_id=rc2.id, product_id=product3.id,
                             amount=5, total_price=5*product3.price)
        rep4 = Replenishment(replcoll_id=rc2.id, product_id=product1.id,
                             amount=10, total_price=10*product1.price)
        for r in [rep1, rep2, rep3, rep4]:
            db.session.add(r)
        db.session.commit()

    def test_list_replenishment_collections_as_admin(self):
        """Getting a list of all ReplenishmentCollections as admin"""
        self._insert_testdata()
        res = self.get(url='/replenishmentcollections', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'replenishmentcollections' in data
        replcolls = data['replenishmentcollections']
        required = ['id', 'timestamp', 'admin_id', 'price', 'revoked']
        for replcoll in replcolls:
            assert all(x in replcoll for x in required)

    def test_list_replenishment_collections_as_user(self):
        """Trying to get a list of all ReplenishmentCollections as user"""
        self._insert_testdata()
        res = self.get(url='/replenishmentcollections', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

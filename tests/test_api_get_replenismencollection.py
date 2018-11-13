from shopdb.api import *
import shopdb.exceptions as exc
from base_api import BaseAPITestCase
from flask import json
import pdb


class GetReplenishmentCollectionAPITestCase(BaseAPITestCase):
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

    def test_get_replenishment_collection_as_admin(self):
        """Getting a single ReplenishmentCollection as admin"""
        self._insert_testdata()
        res = self.get(url='/replenishmentcollections/1', role='admin')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        assert 'replenishmentcollection' in data
        replcoll = data['replenishmentcollection']
        required_replcoll = ['id', 'timestamp', 'admin_id', 'price',
                             'replenishments', 'revoked', 'revokehistory']
        required_repl = ['id', 'replcoll_id', 'product_id', 'amount',
                         'total_price']
        assert all(x in replcoll for x in required_replcoll)
        repls = replcoll['replenishments']
        for repl in repls:
            assert all(x in repl for x in required_repl)

    def test_get_replenishment_collection_as_user(self):
        """Trying to get a single ReplenishmentCollection as user"""
        self._insert_testdata()
        res = self.get(url='/replenishmentcollections/2', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_get_non_existing_replenishmentcollection(self):
        """
        This test ensures that an exception is raised if the requested
        replenishmentcollection does not exist.
        """
        res = self.get(url='/replenishmentcollections/5', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentCollectionNotFound)

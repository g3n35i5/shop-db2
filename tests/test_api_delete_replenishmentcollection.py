from shopdb.api import *
import shopdb.exceptions as exc
from tests.base_api import BaseAPITestCase
from flask import json


class DeleteReplenishmentCollectionAPITestCase(BaseAPITestCase):
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
        for r in [rep1, rep2, rep3]:
            db.session.add(r)
        db.session.commit()

    def test_delete_replenishmentcolletion_as_admin(self):
        """Deleting a single replenishmentcollection as admin"""
        self._insert_testdata()
        res = self.delete(url='/replenishmentcollections/1', role='admin')
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        assert 'message' in data
        assert 'Deleted ReplenishmentCollection.' in data['message']
        assert 'Deleted Replenishment ID 1.' in data['message']
        assert 'Deleted Replenishment ID 2.' in data['message']
        replcoll = ReplenishmentCollection.query.filter_by(id=1).first()
        self.assertEqual(replcoll, None)
        repl1 = Replenishment.query.filter_by(id=1).first()
        self.assertEqual(repl1, None)
        repl2 = Replenishment.query.filter_by(id=2).first()
        self.assertEqual(repl2, None)

    def test_delete_replenishmentcollection_as_user(self):
        """Deleting a replenishmentcollection as user should raise an error"""
        self._insert_testdata()
        res = self.delete(url='/replenishmentcollections/1', role='user')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.UnauthorizedAccess)

    def test_delete_replenishmentcollection_with_invalid_id(self):
        """Trying to delete a single replenishment with invalid id"""
        self._insert_testdata()
        res = self.delete(url='/replenishmentcollections/3', role='admin')
        self.assertEqual(res.status_code, 401)
        self.assertException(res, exc.ReplenishmentCollectionNotFound)

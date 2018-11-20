#!/usr/bin/env python3

import sys
import os
import sqlalchemy
from shopdb.models import *
from shopdb.api import *
import configuration as config
import pdb


def create_database():
    app.config.from_object(config.ProductiveConfig)
    app.app_context().push()
    db.create_all()
    db.session.commit()
    rank1 = Rank(name='Member', debt_limit=-2000)
    rank2 = Rank(name='Alumni', debt_limit=-2000)
    rank3 = Rank(name='Contender', debt_limit=0)
    try:
        for r in (rank1, rank2, rank3):
            db.session.add(r)
        db.session.commit()
    except IntegrityError:
        sys.exit('ERROR: Could not create database!')

    # Handle the user.
    userone = {'firstname': 'User', 'lastname': 'One',
               'password': 'passwd', 'password_repeat': 'passwd'}
    insert_user(userone)

    # Get the User
    user = User.query.filter_by(id=1).first()

    # Add User as Admin (is_admin, admin_id)
    user.set_admin(True, 1)

    # Verify the user (admin_id, rank_id)
    user.verify(1, 1)


if __name__ == '__main__':
    # path = shodb/shop.# DEBUG:
    database = os.path.isfile(config.ProductiveConfig.DATABASE_PATH)
    if not database:
        create_database()
    else:
        os.remove(config.ProductiveConfig.DATABASE_PATH)
        create_database()
        # sys.exit('ERROR: The database allready exists!')

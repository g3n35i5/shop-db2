#!/usr/bin/env python3

import sys
import os
from sqlalchemy.exc import IntegrityError
from shopdb.models import User, Rank
from shopdb.api import app, db, set_app, insert_user
import configuration as config


def create_database():
    set_app(config.ProductiveConfig)
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
    user_one = {'firstname': 'First', 'lastname': 'User',
                'password': 'my_password', 'password_repeat': 'my_password'}
    insert_user(user_one)

    # Get the User
    user = User.query.filter_by(id=1).first()

    # Add User as Admin (is_admin, admin_id)
    user.set_admin(True, 1)

    # Verify the user (admin_id, rank_id)
    user.verify(1, 1)
    db.session.commit()


if __name__ == '__main__':
    db_exists = os.path.isfile(config.ProductiveConfig.DATABASE_PATH)
    if db_exists:
        sys.exit('ERROR: The database already exists!')

    create_database()

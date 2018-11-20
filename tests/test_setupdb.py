#!/usr/bin/env python3

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from shopdb.models import *
import configuration as config
from setupdb import *
import os
import pdb


class TestSetupDB(unittest.TestCase):

    def test_setup_with_no_existing_db(self):
        database = os.path.isfile(config.ProductiveConfig.DATABASE_PATH)
        if not database:
            create_database()
        else:
            os.remove(config.ProductiveConfig.DATABASE_PATH)
            create_database()

        engine = create_engine(config.ProductiveConfig.SQLALCHEMY_DATABASE_URI)
        Session = sessionmaker(bind=engine)
        ses = Session()
        '''
        u = User(
            firstname='Tim',
            lastname='Test',
            password='blah')
        ses.add(u)
        ses.commit()
        '''
        users = ses.query(User).all()
        pdb.set_trace()
        assert len(users) == 1

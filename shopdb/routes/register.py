#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import jsonify
from sqlalchemy.exc import IntegrityError

import shopdb.exceptions as exc
from shopdb.api import app, db
from shopdb.helpers.decorators import deprecate_route
from shopdb.helpers.users import insert_user
from shopdb.helpers.utils import json_body


@app.route('/register', methods=['POST'])
@deprecate_route("The register route has been replaced with a POST request to the /users route")
def register():
    """
    Registration of new users.

    :return:                     A message that the registration was successful.

    :raises CouldNotCreateEntry: If the new user cannot be created.
    """
    insert_user(json_body())
    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created user.'}), 200

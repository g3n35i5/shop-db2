#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import jsonify
import shopdb.exceptions as exc
from sqlalchemy.sql import exists
from shopdb.api import (app, adminRequired, convert_minimal, db, check_fields_and_types, json_body)
from shopdb.models import UserVerification, User, Rank


@app.route('/verifications', methods=['GET'])
@adminRequired
def list_pending_validations(admin):
    """
    Returns a list of all non verified users.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all non verified users.
    """
    res = (db.session.query(User)
           .filter(~exists().where(UserVerification.user_id == User.id))
           .all())
    fields = ['id', 'firstname', 'lastname']
    return jsonify({'pending_validations': convert_minimal(res, fields)}), 200


@app.route('/verify/<int:id>', methods=['POST'])
@adminRequired
def verify_user(admin, id):
    """
    Verify a user.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.
    :param id:                   Is the user id.

    :return:                     A message that the verification was successful.

    :raises UserAlreadyVerified: If the user already has been verified.
    :raises DataIsMissing:       If the rank_id is not included in the request.
    :raises UnknownField:        If an unknown parameter exists in the request
                                 data.
    :raises InvalidType:         If one or more parameters have an invalid
                                 type.
    :raises EntryNotFound:       If the rank to be assigned to the user does
                                 not exist.
    """
    user = User.query.filter_by(id=id).first()
    if not user:
        raise exc.EntryNotFound()
    if user.is_verified:
        raise exc.UserAlreadyVerified()

    data = json_body()
    # Check all items in the json body.
    required = {'rank_id': int}
    check_fields_and_types(data, required)

    rank_id = data['rank_id']
    rank = Rank.query.filter_by(id=rank_id).first()
    if not rank:
        raise exc.EntryNotFound()

    user.verify(admin_id=admin.id, rank_id=rank_id)
    db.session.commit()
    return jsonify({'message': 'Verified user.'}), 201

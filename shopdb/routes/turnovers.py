#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from sqlalchemy.exc import IntegrityError
from flask import jsonify, request
import shopdb.exceptions as exc
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.validators import check_fields_and_types, check_forbidden
from shopdb.helpers.utils import convert_minimal, json_body, generic_update
from shopdb.helpers.query import QueryFromRequestParameters
from shopdb.api import app, db
from shopdb.models import Turnover


@app.route('/turnovers', methods=['GET'])
@adminRequired
def list_turnovers(admin):
    """
    Returns a list of all turnovers.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all turnovers.
    """
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked', 'admin_id']
    query = QueryFromRequestParameters(Turnover, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers['Content-Range'] = content_range
    return response


@app.route('/turnovers', methods=['POST'])
@adminRequired
def create_turnover(admin):
    """
    Insert a new turnover.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {'amount': int, 'comment': str}
    check_fields_and_types(data, required)

    # Check amount
    if data['amount'] == 0:
        raise exc.InvalidAmount()

    # Create and insert turnover
    try:
        turnover = Turnover(**data)
        turnover.admin_id = admin.id
        db.session.add(turnover)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({'message': 'Created turnover.'}), 200


@app.route('/turnovers/<int:id>', methods=['GET'])
def get_turnover(id):
    """
    Returns the turnover with the requested id.

    :param id:             Is the turnover id.

    :return:               The requested turnover as JSON object.

    :raises EntryNotFound: If the turnover with this ID does not exist.
    """
    # Query the turnover
    res = Turnover.query.filter_by(id=id).first()
    # If it not exists, return an error
    if not res:
        raise exc.EntryNotFound()
    # Convert the turnover to a JSON friendly format
    fields = ['id', 'timestamp', 'amount', 'comment', 'revoked',
              'revokehistory']
    return jsonify(convert_minimal(res, fields)[0]), 200


@app.route('/turnovers/<int:id>', methods=['PUT'])
@adminRequired
def update_turnover(admin, id):
    """
    Update the turnover with the given id.

    :param admin: Is the administrator user, determined by @adminRequired.
    :param id:    Is the turnover id.

    :return:      A message that the update was successful and a list of all updated fields.
    """
    return generic_update(Turnover, id, json_body(), admin)

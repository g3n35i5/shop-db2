##!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

import shop_db2.exceptions as exc
from shop_db2.api import app, db
from shop_db2.helpers.decorators import adminRequired
from shop_db2.helpers.query import QueryFromRequestParameters
from shop_db2.helpers.updater import generic_update
from shop_db2.helpers.utils import convert_minimal, json_body
from shop_db2.helpers.validators import check_fields_and_types
from shop_db2.models import Rank


@app.route("/ranks", methods=["GET"])
def list_ranks():
    """Returns a list of all ranks.

    :return: A list of all ranks.
    """
    fields = ["id", "name", "debt_limit", "is_system_user"]
    query = QueryFromRequestParameters(Rank, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers["Content-Range"] = content_range
    return response


@app.route("/ranks", methods=["POST"])
@adminRequired
def create_rank(admin):
    """Route to create a new rank.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.

    :return:                      A message that the creation was successful.

    :raises DataIsMissing:        If one or more fields are missing to create the rank.
    :raises UnknownField:         If an unknown parameter exists in the request data.
    :raises InvalidType:          If one or more parameters have an invalid type.
    :raises EntryAlreadyExists:   If a rank with this name already exists.
    :raises CouldNotCreateEntry:  If the new rank cannot be added to the database.

    """
    data = json_body()
    required = {"name": str}
    optional = {"is_system_user": bool, "debt_limit": int}

    # Check all required fields
    check_fields_and_types(data, required, optional)

    # Check if a tag with this name already exists
    if Rank.query.filter_by(name=data["name"]).first():
        raise exc.EntryAlreadyExists()

    try:
        rank = Rank(**data)
        db.session.add(rank)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({"message": "Created Rank."}), 201


@app.route("/ranks/<int:rank_id>", methods=["GET"])
def get_rank(rank_id):
    """Returns the rank with the requested id.

    :param rank_id:        Is the rank id.

    :return:               The requested rank as JSON object.

    :raises EntryNotFound: If the rank with this ID does not exist.
    """
    result = Rank.query.filter_by(id=rank_id).first()
    if not result:
        raise exc.EntryNotFound()

    rank = convert_minimal(result, ["id", "name", "debt_limit", "is_system_user"])[0]
    return jsonify(rank), 200


@app.route("/ranks/<int:rank_id>", methods=["PUT"])
@adminRequired
def update_rank(admin, rank_id):
    """Update the rank with the given id.

    :param admin:   Is the administrator user, determined by @adminRequired.
    :param rank_id: Is the product id.

    :return:        A message that the update was successful and a list of all updated fields.
    """
    return generic_update(Rank, rank_id, json_body(), admin)

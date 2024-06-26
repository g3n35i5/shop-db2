#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from shop_db2.models.user import User

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
from shop_db2.models import Tag


@app.route("/tags", methods=["GET"])
def list_tags():
    """Returns a list of all tags.

    :return: A list of all tags.
    """
    fields = ["id", "name", "created_by", "is_for_sale"]
    query = QueryFromRequestParameters(Tag, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers["Content-Range"] = content_range
    return response


@app.route("/tags/<int:tag_id>", methods=["GET"])
def get_tag(tag_id: int):
    """Returns the tag with the requested id.

    :param tag_id:         Is the tag id.

    :return:               The requested tag as JSON object.

    :raises EntryNotFound: If the tag with this ID does not exist.
    """
    result = Tag.query.filter_by(id=tag_id).first()
    if not result:
        raise exc.EntryNotFound()

    tag = convert_minimal(result, ["id", "name", "created_by", "is_for_sale"])[0]
    return jsonify(tag), 200


@app.route("/tags/<int:tag_id>", methods=["DELETE"])
@adminRequired
def delete_tag(admin: User, tag_id: int):
    """Delete a tag.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.
    :param tag_id:                Is the tag id.

    :return:                      A message that the deletion was successful.

    :raises EntryNotFound:        If the user with this ID does not exist.
    :raises EntryCanNotBeDeleted: If the tag can not be deleted.
    """
    tag = Tag.query.filter_by(id=tag_id).first()
    if not tag:
        raise exc.EntryNotFound()

    # You can't delete the last remaining tag
    tags = Tag.query.all()
    if len(tags) == 1:
        raise exc.NoRemainingTag()

    # Check all product tags
    for product in tag.products:
        if len(product.tags) == 1:
            raise exc.NoRemainingTag()

    # Delete the tag.
    try:
        db.session.delete(tag)
        db.session.commit()
    except IntegrityError:
        raise exc.EntryCanNotBeDeleted()

    return jsonify({"message": "Tag deleted."}), 200


@app.route("/tags", methods=["POST"])
@adminRequired
def create_tag(admin: User):
    """Route to create a new tag.

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.

    :return:                      A message that the creation was successful.

    :raises DataIsMissing:        If one or more fields are missing to create
                                  the tag.
    :raises UnknownField:         If an unknown parameter exists in the request
                                  data.
    :raises InvalidType:          If one or more parameters have an invalid
                                  type.
    :raises EntryAlreadyExists:   If a tag with this name already exists.
    :raises CouldNotCreateEntry:  If the new tag cannot be added to the
                                  database.

    """
    data = json_body()
    required = {"name": str}
    optional = {"is_for_sale": bool}

    # Check all required fields
    check_fields_and_types(data, required, optional)

    # Check if a tag with this name already exists
    if Tag.query.filter_by(name=data["name"]).first():
        raise exc.EntryAlreadyExists()

    try:
        tag = Tag(**data)
        tag.created_by = admin.id
        db.session.add(tag)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({"message": "Created Tag."}), 201


@app.route("/tags/<int:tag_id>", methods=["PUT"])
@adminRequired
def update_tag(admin: User, tag_id: int):
    """Update the tag with the given id.

    :param admin:  Is the administrator user, determined by @adminRequired.
    :param tag_id: Is the product id.

    :return:       A message that the update was successful and a list of all updated fields.
    """
    return generic_update(Tag, tag_id, json_body(), admin)

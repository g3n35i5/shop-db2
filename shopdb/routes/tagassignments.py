#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import jsonify
from sqlalchemy.exc import IntegrityError

import shopdb.exceptions as exc
from shopdb.api import app, db
from shopdb.helpers.decorators import adminRequired
from shopdb.helpers.utils import json_body
from shopdb.helpers.validators import check_fields_and_types
from shopdb.models import Product, Tag


@app.route("/tagassignment/<command>", methods=["POST"])
@adminRequired
def change_product_tag_assignment(admin, command):
    """
    Under this route, a tag can be added to a product or removed.

    :param admin:              Is the administrator user, determined by
                               @adminRequired.

    :return:                   A message that the assignment has been added or
                               removed.

    :raises ForbiddenField:    If a forbidden field is in the request data.
    :raises UnknownField:      If an unknown parameter exists in the request
                               data.
    :raises InvalidType:       If one or more parameters have an invalid type.
    :raises EntryNotFound      If the product with the specified ID does not
                               exist.
    :raises EntryNotFound:     If the tag with the specified ID does not exist.
    :raises NothingHasChanged: If no change occurred after the update or removal.
    """

    if command not in ["add", "remove"]:
        raise exc.UnauthorizedAccess()

    data = json_body()
    required = {"product_id": int, "tag_id": int}

    # Check all required fields
    check_fields_and_types(data, required)

    # Check if the product exists.
    product = Product.query.filter_by(id=data["product_id"]).first()
    if not product:
        raise exc.EntryNotFound()

    # Check if the tag exists.
    tag = Tag.query.filter_by(id=data["tag_id"]).first()
    if not tag:
        raise exc.EntryNotFound()

    if command == "add":
        if tag in product.tags:
            raise exc.NothingHasChanged()

        try:
            product.tags.append(tag)
            db.session.commit()
        except IntegrityError:
            raise exc.CouldNotUpdateEntry()

        return jsonify({"message": "Tag assignment has been added."}), 201
    else:
        if tag not in product.tags:
            raise exc.NothingHasChanged()

        if len(product.tags) <= 1:
            raise exc.NoRemainingTag()

        try:
            product.tags.remove(tag)
            db.session.commit()
        except IntegrityError:
            raise exc.CouldNotUpdateEntry()

        return jsonify({"message": "Tag assignment has been removed."}), 201

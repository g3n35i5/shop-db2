#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import shop_db2.models.user

__author__ = "g3n35i5"

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError

import shop_db2.exceptions as exc
from shop_db2.api import app, db
from shop_db2.helpers.decorators import adminRequired
from shop_db2.helpers.query import QueryFromRequestParameters
from shop_db2.helpers.updater import generic_update
from shop_db2.helpers.utils import convert_minimal, json_body, parse_timestamp
from shop_db2.helpers.validators import check_fields_and_types
from shop_db2.models import Product, Replenishment, ReplenishmentCollection, User


@app.route("/replenishmentcollections", methods=["GET"])
@adminRequired
def list_replenishmentcollections(admin):
    """Returns a list of all replenishmentcollections.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all replenishmentcollections.
    """
    fields = ["id", "timestamp", "admin_id", "seller_id", "price", "revoked", "comment"]
    query = QueryFromRequestParameters(ReplenishmentCollection, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers["Content-Range"] = content_range
    return response


@app.route("/replenishments", methods=["GET"])
@adminRequired
def list_replenishments(admin):
    """Returns a list of all replenishments.

    :param admin: Is the administrator user, determined by @adminRequired.

    :return:      A list of all replenishments.
    """
    fields = ["id", "product_id", "amount", "total_price", "revoked"]
    query = QueryFromRequestParameters(Replenishment, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers["Content-Range"] = content_range
    return response


@app.route("/replenishmentcollections/<int:collection_id>", methods=["GET"])
@adminRequired
def get_replenishmentcollection(admin: shop_db2.models.user.User, collection_id: int):
    """Returns the replenishmentcollection with the requested id. In addition,
    all replenishments that belong to this collection are returned.

    :param admin:          Is the administrator user,
                           determined by @adminRequired.
    :param collection_id:  Is the replenishmentcollection id.

    :return:               The requested replenishmentcollection and all
                           related replenishments JSON object.

    :raises EntryNotFound: If the replenishmentcollection with this ID does
                           not exist.
    """
    # Query the replenishmentcollection.
    replcoll = ReplenishmentCollection.query.filter_by(id=collection_id).first()
    # If it does not exist, raise an exception.
    if not replcoll:
        raise exc.EntryNotFound()

    fields_replcoll = [
        "id",
        "timestamp",
        "admin_id",
        "seller_id",
        "price",
        "revoked",
        "revokehistory",
        "comment",
    ]
    fields_repl = [
        "id",
        "replcoll_id",
        "product_id",
        "amount",
        "total_price",
        "revoked",
    ]
    repls = replcoll.replenishments.all()

    result = convert_minimal(replcoll, fields_replcoll)[0]
    result["replenishments"] = convert_minimal(repls, fields_repl)
    return jsonify(result), 200


@app.route("/replenishmentcollections", methods=["POST"])
@adminRequired
def create_replenishmentcollection(admin: shop_db2.models.user.User):
    """Insert a new replenishmentcollection.

    :param admin:                Is the administrator user, determined by
                                 @adminRequired.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises ForbiddenField :     If a forbidden field is in the data.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the product with with the id of any
                                 replenishment does not exist.
    :raises InvalidAmount:       If amount of any replenishment is less than
                                 or equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()
    required = {
        "replenishments": list,
        "comment": str,
        "timestamp": str,
        "seller_id": int,
    }
    required_repl = {"product_id": int, "amount": int, "total_price": int}

    # Check all required fields
    check_fields_and_types(data, required)

    # Check seller
    seller = User.query.filter_by(id=data["seller_id"]).first()
    if not seller:
        raise exc.EntryNotFound()

    # Check if the seller has been verified.
    if not seller.is_verified:
        raise exc.UserIsNotVerified()

    # Parse timestamp
    data = parse_timestamp(data, required=True)

    replenishments = data["replenishments"]
    # Check for the replenishments in the collection
    if not replenishments:
        raise exc.DataIsMissing()

    for repl in replenishments:
        # Check all required fields
        check_fields_and_types(repl, required_repl)

        product_id = repl.get("product_id")
        amount = repl.get("amount")

        # Check amount
        if amount <= 0:
            raise exc.InvalidAmount()
        # Check product
        product = Product.query.filter_by(id=product_id).first()
        if not product:
            raise exc.EntryNotFound()

        # If the product has been marked as inactive, it will now be marked as
        # active again.
        if not product.active:
            product.active = True

    # Create and insert replenishmentcollection
    try:
        collection = ReplenishmentCollection(
            admin_id=admin.id,
            seller_id=seller.id,
            timestamp=data["timestamp"],
            comment=data["comment"],
            revoked=False,
        )
        db.session.add(collection)
        db.session.flush()

        for repl in replenishments:
            rep = Replenishment(replcoll_id=collection.id, **repl)
            db.session.add(rep)
        db.session.commit()

    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({"message": "Created replenishmentcollection."}), 201


@app.route("/replenishmentcollections/<int:collection_id>", methods=["PUT"])
@adminRequired
def update_replenishmentcollection(admin: shop_db2.models.user.User, collection_id: int):
    """Update the replenishmentcollection with the given id.

    :param admin:         Is the administrator user, determined by @adminRequired.
    :param collection_id: Is the replenishmentcollection id.

    :return:              A message that the update was successful and a list of all updated fields.
    """
    return generic_update(ReplenishmentCollection, collection_id, json_body(), admin)


@app.route("/replenishments/<int:replenishment_id>", methods=["PUT"])
@adminRequired
def update_replenishment(admin: shop_db2.models.user.User, replenishment_id: int):
    """Update the replenishment with the given id.

    :param admin:            Is the administrator user, determined by @adminRequired.
    :param replenishment_id: Is the replenishment id.

    :return:                 A message that the update was successful and a list of all updated fields.
    """
    return generic_update(Replenishment, replenishment_id, json_body(), admin)

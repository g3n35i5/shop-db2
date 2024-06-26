#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Optional

from shop_db2.models.user import User

__author__ = "g3n35i5"

from flask import jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import exists

import shop_db2.exceptions as exc
from shop_db2.api import app, db
from shop_db2.helpers.decorators import adminOptional
from shop_db2.helpers.purchases import insert_purchase
from shop_db2.helpers.query import QueryFromRequestParameters
from shop_db2.helpers.updater import generic_update
from shop_db2.helpers.utils import convert_minimal, json_body
from shop_db2.models import Purchase, PurchaseRevoke


@app.route("/purchases", methods=["GET"])
@adminOptional
def list_purchases(admin: None):
    """Returns a list of all purchases. If this route is called by an
    administrator, all information is returned. However, if it is called
    without further rights, a minimal version is returned.

    :param admin: Is the administrator user, determined by @adminOptional.

    :return:      A list of all purchases.
    """
    if admin is not None:
        fields = [
            "id",
            "timestamp",
            "user_id",
            "admin_id",
            "product_id",
            "productprice",
            "amount",
            "revoked",
            "price",
        ]
    else:
        fields = ["id", "timestamp", "user_id", "admin_id", "product_id", "amount"]

    query = QueryFromRequestParameters(Purchase, request.args, fields)
    if admin is None:
        query = query.filter(~exists().where(PurchaseRevoke.purchase_id == Purchase.id))

    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers["Content-Range"] = content_range
    return response


@app.route("/purchases", methods=["POST"])
@adminOptional
def create_purchase(admin: Optional[User]):
    """Insert a new purchase.

    :param admin:                Is the administrator user, determined by @adminOptional.

    :return:                     A message that the creation was successful.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises EntryNotFound:       If the product with this ID does not exist.
    :raises EntryIsNotForSale:   If the product is not for sale.
    :raises EntryIsInactive:     If the product is inactive.
    :raises InvalidAmount:       If amount is less than or equal to zero.
    :raises InsufficientCredit:  If the credit balance of the user is not
                                 sufficient.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    data = json_body()

    # It is allowed to create multiple purchases at once
    if isinstance(data, list):
        for purchase in data:
            insert_purchase(admin, purchase)
    else:
        insert_purchase(admin, data)

    try:
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    return jsonify({"message": "Purchase created."}), 200


@app.route("/purchases/<int:purchase_id>", methods=["GET"])
def get_purchase(purchase_id: int):
    """Returns the purchase with the requested id.

    :param purchase_id:    Is the purchase id.

    :return:               The requested purchase as JSON object.

    :raises EntryNotFound: If the purchase with this ID does not exist.
    """
    purchase = Purchase.query.filter_by(id=purchase_id).first()
    if not purchase:
        raise exc.EntryNotFound()
    fields = [
        "id",
        "timestamp",
        "user_id",
        "admin_id",
        "product_id",
        "amount",
        "price",
        "productprice",
        "revoked",
        "revokehistory",
    ]
    return jsonify(convert_minimal(purchase, fields)[0]), 200


@app.route("/purchases/<int:purchase_id>", methods=["PUT"])
@adminOptional
def update_purchase(admin: Optional[User], purchase_id: int):
    """Update the purchase with the given id.

    :param admin:       Is the administrator user, determined by @adminRequired.
    :param purchase_id: Is the purchase id.

    :return:            A message that the update was successful and a list of all updated fields.
    """
    return generic_update(Purchase, purchase_id, json_body(), admin)

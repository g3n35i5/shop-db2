#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from typing import Any, Dict

from sqlalchemy.exc import IntegrityError

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.helpers.validators import check_fields_and_types
from shop_db2.models import Deposit, User


def insert_deposit(data: Dict[str, Any], admin: User) -> None:
    """This help function creates a new deposit with the given data.

    :raises DataIsMissing:       If not all required data is available.
    :raises WrongType:           If one or more data is of the wrong type.
    :raises EntryNotFound:       If the user with this ID does not exist.
    :raises UserIsNotVerified:   If the user has not yet been verified.
    :raises InvalidAmount:       If amount is equal to zero.
    :raises CouldNotCreateEntry: If any other error occurs.
    """
    required = {"user_id": int, "amount": int, "comment": str}
    check_fields_and_types(data, required)

    # Check user
    user = User.query.filter_by(id=data["user_id"]).first()
    if not user:
        raise exc.EntryNotFound()

    # Check if the user has been verified.
    if not user.is_verified:
        raise exc.UserIsNotVerified()

    # Check if the user is inactive
    if not user.active:
        raise exc.UserIsInactive()

    # Check amount
    if data["amount"] == 0:
        raise exc.InvalidAmount()

    # Create and insert deposit
    try:
        deposit = Deposit(**data)
        deposit.admin_id = admin.id
        db.session.add(deposit)
    except IntegrityError as error:
        raise exc.CouldNotCreateEntry() from error

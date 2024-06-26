#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from inspect import Signature, signature
from typing import Any, Optional

from flask import jsonify
from sqlalchemy.exc import IntegrityError

import shop_db2.exceptions as exc
from shop_db2.api import db
from shop_db2.helpers.validators import check_fields_and_types, check_forbidden
from shop_db2.models import User


def generic_update(model: db.Model, entry_id: int, data: dict, admin: Optional[User]) -> Any:
    """This is a generic function which handles all entry updates. "Normal" updates (like name, ...), which do not
    require any special treatment (like inserting other entries, ...) are handled with a simple "setattr(...)"
    operation. All other fields are updated by calling the set_FIELDNAME method, which must be implemented in the
    model class itself.

    :param model:                The database model.
    :param entry_id:             The primary key (id) of the entry to be updated.
    :param data:                 The dictionary with all update data.
    :param admin:                Is the administrator user, determined by @adminRequired.
    :return:                     A message that the update was successful and a list of all updated fields.

    :raises Exception:           If the selected model does not support the generic update (yet).
    :raises EntryNotFound:       If the item with this ID does not exist.
    :raises ForbiddenField:      If a forbidden field is in the request data.
    :raises UnknownField:        If an unknown parameter exists in the request data.
    :raises InvalidType:         If one or more parameters have an invalid type.
    :raises CouldNotUpdateEntry: If any other error occurs.
    """
    # If the data dictionary is empty, raise the "NothingHasChanged" exception
    if len(data) == 0:
        raise exc.NothingHasChanged()

    # Query the item
    item = model.query.filter(model.id == entry_id).first()
    if item is None:
        raise exc.EntryNotFound()

    # Get the updateable fields. This only works with supported models.
    if not hasattr(item, "__updateable_fields__"):
        raise ValueError("The generic_update() function can only used with supported models")

    # Get a dictionary containing all allowed fields and types
    updateable_fields: dict = item.__updateable_fields__
    # Check forbidden fields
    check_forbidden(data, updateable_fields, item)
    # Check types
    check_fields_and_types(data, None, updateable_fields)

    # List containing all updated fields
    updated_fields = []

    # Iterate over all update fields
    for field_name, field_value in data.items():
        # Check, whether the value hasn't changed
        if getattr(item, field_name) == field_value:
            raise exc.NothingHasChanged()

        # If the model has a "set_{FIELDNAME}" method, we need to
        # call it instead of the default setattr
        method = getattr(item, f"set_{field_name}", None)

        # Simple case: no set_{FIELDNAME} method, so we just call the setattr
        if method is None:
            setattr(item, field_name, field_value)

        # There is a set_{FIELDNAME} method
        else:
            # Check, whether the method requires an admin_id
            if "admin_id" in signature(method).parameters.keys():
                # If the admin_id parameter has a default value (e.g. def set_foo(admin_id=None, ...)), admin
                # privileges are not required to update the field
                admin_required = isinstance(signature(method).parameters["admin_id"].default, Signature.empty)
                if admin_required and admin is None:
                    raise exc.UnauthorizedAccess()

                # Call the "set_{FIELDNAME}" method, with or without admin id
                if admin and not admin_required:
                    method(field_value, admin_id=admin.id)
                else:
                    method(field_value, admin_id=None)
            else:
                method(field_value)

        updated_fields.append(field_name)

    # Apply changes
    try:
        db.session.commit()
    except IntegrityError as error:
        raise exc.CouldNotUpdateEntry() from error

    return (
        jsonify(
            {
                "message": f"Updated {model.__name__.lower()}",
                "updated_fields": sorted(updated_fields),
            }
        ),
        201,
    )

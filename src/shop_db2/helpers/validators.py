#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from typing import Any, Dict, Optional, Type

# from sqlalchemy.ext.declarative.api import Model

__author__ = "g3n35i5"

from flask import request

import shop_db2.exceptions as exc


def check_forbidden(data: Dict[str, Any], allowed_fields: Dict[str, Any], row: Any) -> None:
    """This function checks whether any illegal fields exist in the data sent to
    the API with the request. If so, an exception is raised and the request
    is canceled.

    :param data:             The data sent to the API.
    :param allowed_fields:   A list of all allowed fields.
    :param row:              The object for which you want to check whether the
                             fields are forbidden.

    :return:                 None

    :raises ForbiddenField : If a forbidden field is in the data.
    """
    for item in data:
        if (item not in allowed_fields) and (hasattr(row, item)):
            raise exc.ForbiddenField()


def check_fields_and_types(data: Dict[str, Any], required: Any, optional: Optional[Any] = None) -> None:
    """This function checks the given data for its types and existence.
    Required fields must exist, optional fields must not.

    :param data:            The data sent to the API.
    :param required:        A dictionary with all required entries and their
                            types.
    :param optional:        A dictionary with all optional entries and their
                            types.

    :return:                None

    :raises DataIsMissing:  If a required field is not in the data.
    :raises WrongType:      If a field is of the wrong type.
    """
    if required and optional:
        allowed = {**required, **optional}
    elif required:
        allowed = required
    else:
        allowed = optional

    # Check if there is an unknown field in the data
    if not all(x in allowed for x in data):
        raise exc.UnknownField()

    # Check whether all required data is available
    if required and any(item not in data for item in required):
        raise exc.DataIsMissing()

    # Check all data (including optional data) for their types
    for key, value in data.items():
        if not isinstance(value, allowed[key]):
            raise exc.WrongType()


def check_allowed_parameters(allowed: Dict[str, Type[int]]) -> Dict[str, int]:
    """This method checks all GET parameters for their type.

    :param allowed:               A dictionary containing all allowed parameters
                                  and types.

    :return:                      A dictionary with all converted and checked
                                  parameters.

    :raises UnauthorizedAccess:   If there's an illegal parameter in the data.
    :raises WrongType:            If an argument is of the wrong type.
    """
    result = {}
    if any(argument not in allowed for argument in request.args):
        raise exc.UnauthorizedAccess()

    for key in request.args:
        try:
            result[key] = allowed[key](request.args[key])
        except ValueError as error:
            raise exc.WrongType() from error

    return result

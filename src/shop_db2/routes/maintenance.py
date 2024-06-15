#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from shop_db2.models.user import User

__author__ = "g3n35i5"

import os
import re

from flask import jsonify

import shop_db2.exceptions as exc
from shop_db2.api import app
from shop_db2.helpers.decorators import adminRequired
from shop_db2.helpers.utils import json_body
from shop_db2.helpers.validators import check_fields_and_types

from configuration import PATH  # isort: skip


@app.route("/maintenance", methods=["GET"])
def get_maintenance_mode():
    """This route returns whether the app is in maintenance mode.

    :return: A message with the maintenance mode.
    """
    return jsonify(app.config["MAINTENANCE"])


@app.route("/maintenance", methods=["POST"], endpoint="maintenance")
@adminRequired
def set_maintenance_mode(admin: User):
    """This route can be used by an administrator to switch the maintenance mode
    on or off.

    :param admin:              Is the administrator user, determined by
                               @adminRequired.

    :raises DataIsMissing:     If the maintenance state is not included
                               in the request.
    :raises UnknownField:      If an unknown parameter exists in the request
                               data.
    :raises InvalidType:       If one or more parameters have an invalid type.
    :raises NothingHasChanged: If the maintenance mode is not changed by the
                               request.

    :return:                   A message with the new maintenance mode.
    """
    data = json_body()
    # Check all items in the json body.
    required = {"state": bool}
    check_fields_and_types(data, required)

    # Get the current maintenance state.
    current_state = app.config["MAINTENANCE"]

    # Get the new state.
    new_state = data["state"]

    # Handle the request.
    if current_state == new_state:
        raise exc.NothingHasChanged()

    # Change the config file persistently
    RE_MAINENTANCE_PATTERN = r"(.*)(MAINTENANCE)([^\w]*)(True|False)"
    with open(os.path.join(PATH, "configuration.py"), "r") as config_file:
        config_file_content = config_file.read()
    new_config_file = re.sub(RE_MAINENTANCE_PATTERN, r"\1\2\3{}".format(str(new_state)), config_file_content)
    with open(os.path.join(PATH, "configuration.py"), "w") as config_file:
        config_file.write(new_config_file)

    # Change the current app state
    app.config["MAINTENANCE"] = new_state

    message = "Turned maintenance mode " + ("on." if new_state else "off.")
    return jsonify({"message": message})

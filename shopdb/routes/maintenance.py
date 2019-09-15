#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import shopdb.exceptions as exc
from flask import jsonify
from shopdb.api import (app, adminRequired, check_fields_and_types, json_body)


@app.route('/maintenance', methods=['POST'], endpoint='maintenance')
@adminRequired
def set_maintenance(admin):
    """
    This route can be used by an administrator to switch the maintenance mode
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
    required = {'state': bool}
    check_fields_and_types(data, required)

    # Get the current maintenance state.
    current_state = app.config['MAINTENANCE']

    # Get the new state.
    new_state = data['state']

    # Handle the request.
    if current_state == new_state:
        raise exc.NothingHasChanged()

    app.config['MAINTENANCE'] = new_state

    message = 'Turned maintenance mode ' + ('on.' if new_state else 'off.')
    return jsonify({'message': message})

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import datetime
import logging
import time

from flask import g, request

import shop_db2.exceptions as exc
from shop_db2.api import app
from shop_db2.helpers.decorators import adminOptional


@app.before_request
@adminOptional
def before_request_hook(admin):
    """This function is executed before each request is processed. Its purpose is
    to check whether the application is currently in maintenance mode. If this
    is the case, the current request is aborted and a corresponding exception
    is raised.

    An exception to this is a request on the route
    "/maintenance" [POST]: Via this route the maintenance mode can be switched
    on and off (by an administrator) or on the route "/login", so that one can
    log in as administrator.

    The maintenance mode has no effect, when the request is made by an administrator.

    :param admin: Is the administrator user, determined by @adminOptional.

    :raises MaintenanceMode: if the application is in maintenance mode.
    """
    # Debug timer
    g.start = time.time()

    # If the request is done by an administrator, return.
    if admin:
        return

    # If the request method is OPTIONS, return.
    if request.method == "OPTIONS":
        return

    # Check for maintenance mode.
    exceptions = ["maintenance", "login"]

    if app.config.get("MAINTENANCE") and request.endpoint not in exceptions:
        raise exc.MaintenanceMode()


@app.after_request
def after_request_hook(response):
    """This functions gets executed each time a request is finished.

    :param response: is the response to be returned.
    :return:         The request response.
    """
    # If the app is in DEBUG mode, log the request execution time
    if app.logger.level == logging.DEBUG:
        execution_time = datetime.timedelta(seconds=(time.time() - g.start))
        app.logger.debug("Request execution time for '{}': {}".format(request.endpoint, execution_time))

    return response

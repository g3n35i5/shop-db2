#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import db
import shopdb.exceptions as exc
from flask import Flask, g, jsonify, request
from flask_bcrypt import Bcrypt
import datetime
import logging
import time
import configuration as config

app = Flask(__name__)

# Default app settings (to suppress unittest warnings) will be overwritten.
app.config.from_object(config.BaseConfig)

# Setting strict slash mapping to false ('/foo/' and '/foo' are same this way)
app.url_map.strict_slashes = False

db.init_app(app)
bcrypt = Bcrypt(app)


def set_app(configuration):
    """
    Sets all parameters of the applications to those defined in the dictionary
    "configuration" and returns the application object.

    :param configuration: The dictionary with all settings for the application

    :return:              The application object with the updated settings.
    """
    app.config.from_object(configuration)
    return app


@app.before_request
def before_request_hook():
    """
    This function is executed before each request is processed. Its purpose is
    to check whether the application is currently in maintenance mode. If this
    is the case, the current request is aborted and a corresponding exception
    is raised. An exception to this is a request on the route
    "/maintenance" [POST]: Via this route the maintenance mode can be switched
    on and off (by an administrator) or on the route "/login", so that one can
    log in as administrator.

    :raises MaintenanceMode: if the application is in maintenance mode.
    """

    # Debug timer
    g.start = time.time()

    # Check for maintenance mode.
    exceptions = ['maintenance', 'login']

    if app.config.get('MAINTENANCE') and request.endpoint not in exceptions:
        raise exc.MaintenanceMode()


@app.after_request
def after_request_hook(response):
    """
    This functions gets executed each time a request is finished.

    :param response: is the response to be returned.
    :return:         The request response.
    """
    # If the app is in DEBUG mode, log the request execution time
    if app.logger.level == logging.DEBUG:
        execution_time = datetime.timedelta(seconds=(time.time() - g.start))
        app.logger.debug("Request execution time for '{}': {}".format(request.endpoint, execution_time))

    return response


@app.route('/', methods=['GET'])
def index():
    """
    A route that simply returns that the backend is online.

    :return: A message which says that the backend is online.
    """
    return jsonify({'message': 'Backend is online.'})


"""
Below this comment are the imports of all used routes defined in "shopdb.routes"
"""

# Error handler
# noinspection PyUnresolvedReferences
import shopdb.helpers.errors  # noqa: E402

# Maintenance routes
# noinspection PyUnresolvedReferences
import shopdb.routes.maintenance  # noqa: E402

# Image routes
# noinspection PyUnresolvedReferences
import shopdb.routes.images  # noqa: E402

# Upload routes
# noinspection PyUnresolvedReferences
import shopdb.routes.uploads  # noqa: E402

# Backup routes
# noinspection PyUnresolvedReferences
import shopdb.routes.backups  # noqa: E402

# Financial overview route
# noinspection PyUnresolvedReferences
import shopdb.routes.financial_overview  # noqa: E402

# Login route
# noinspection PyUnresolvedReferences
import shopdb.routes.login  # noqa: E402

# Register route
# noinspection PyUnresolvedReferences
import shopdb.routes.register  # noqa: E402

# Verification routes#
# noinspection PyUnresolvedReferences
import shopdb.routes.verifications  # noqa: E402

# User routes
# noinspection PyUnresolvedReferences
import shopdb.routes.users  # noqa: E402

# Rank routes
# noinspection PyUnresolvedReferences
import shopdb.routes.ranks  # noqa: E402

# Tag routes
# noinspection PyUnresolvedReferences
import shopdb.routes.tags  # noqa: E402

# Tag assignment routes
# noinspection PyUnresolvedReferences
import shopdb.routes.tagassignments  # noqa: E402

# Product routes
# noinspection PyUnresolvedReferences
import shopdb.routes.products  # noqa: E402

# Purchase routes
# noinspection PyUnresolvedReferences
import shopdb.routes.purchases  # noqa: E402

# Deposit routes
# noinspection PyUnresolvedReferences
import shopdb.routes.deposits  # noqa: E402

# ReplenishmentCollection routes
# noinspection PyUnresolvedReferences
import shopdb.routes.replenishmentcollections  # noqa: E402

# Refund routes
# noinspection PyUnresolvedReferences
import shopdb.routes.refunds  # noqa: E402

# Payoff routes
# noinspection PyUnresolvedReferences
import shopdb.routes.payoffs  # noqa: E402

# StocktakingCollection routes
# noinspection PyUnresolvedReferences
import shopdb.routes.stocktakingcollections  # noqa: E402

# Turnover routes
# noinspection PyUnresolvedReferences
import shopdb.routes.turnovers  # noqa: E402

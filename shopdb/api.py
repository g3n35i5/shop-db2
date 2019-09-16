#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from shopdb.models import db
from flask import Flask, g
from flask_bcrypt import Bcrypt
import werkzeug.exceptions as werkzeug_exceptions
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

    # Check for maintenance mode.
    exceptions = ['maintenance', 'login']

    if app.config.get('MAINTENANCE') and request.endpoint not in exceptions:
        raise exc.MaintenanceMode()


def json_body():
    """
    Returns the json data from the current request.

    :return:             The json body from the current request.

    :raises InvalidJSON: If the json data cannot be interpreted.
    """
    jb = request.get_json()
    if jb is None:
        raise exc.InvalidJSON()
    return jb


@app.route('/', methods=['GET'])
def index():
    """
    A route that simply returns that the backend is online.

    :return: A message which says that the backend is online.
    """
    return jsonify({'message': 'Backend is online.'})


# Error handler
import shopdb.helpers.errors  # noqa: E402
# Maintenance routes
from shopdb.routes.maintenance import *  # noqa: E40


# Image routes
from shopdb.routes.images import *  # noqa: E402


# Upload routes
from shopdb.routes.uploads import *  # noqa: E402


# Backup routes
from shopdb.routes.backups import *  # noqa: E402


# Financial overview route ###################################################
from shopdb.routes.financial_overview import *  # noqa: E402


# Login route ################################################################
from shopdb.routes.login import *  # noqa: E402


# Register route #############################################################
from shopdb.routes.register import *  # noqa: E402


# Verification routes #########################################################
from shopdb.routes.verifications import *  # noqa: E402


# User routes ################################################################
from shopdb.routes.users import *  # noqa: E402


# Rank routes #############################################################
from shopdb.routes.ranks import *  # noqa: E402


# Tag routes #############################################################
from shopdb.routes.tags import *  # noqa: E402


# Tag assignment routes ######################################################
from shopdb.routes.tagassignments import *  # noqa: E402


# Product routes #############################################################
from shopdb.routes.products import *  # noqa: E402


# Purchase routes ############################################################
from shopdb.routes.purchases import *  # noqa: E402


# Deposit routes #############################################################
from shopdb.routes.deposits import *  # noqa: E402


# ReplenishmentCollection routes ##############################################
from shopdb.routes.replenishmentcollections import *  # noqa: E402


# Refund routes ##############################################################
from shopdb.routes.refunds import *  # noqa: E402


# Payoff routes ##############################################################
from shopdb.routes.payoffs import *  # noqa: E402


# StocktakingCollection routes ##############################################
from shopdb.routes.stocktakingcollections import *  # noqa: E402


# Turnover routes #############################################################
from shopdb.routes.turnovers import *  # noqa: E402

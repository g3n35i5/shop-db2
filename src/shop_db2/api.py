#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

from flask import Flask, jsonify
from flask_bcrypt import Bcrypt

from shop_db2.shared import db

import configuration as config  # isort: skip

app = Flask(__name__)

# Default app settings (to suppress unittest warnings) will be overwritten.
app.config.from_object(config.BaseConfig)

# Setting strict slash mapping to false ('/foo/' and '/foo' are same this way)
app.url_map.strict_slashes = False

db.init_app(app)
bcrypt = Bcrypt(app)


def set_app(configuration):
    """Sets all parameters of the applications to those defined in the dictionary
    "configuration" and returns the application object.

    :param configuration: The dictionary with all settings for the application

    :return:              The application object with the updated settings.
    """
    app.config.from_object(configuration)
    return app


@app.route("/", methods=["GET"])
def index():
    """A route that simply returns that the backend is online.

    :return: A message which says that the backend is online.
    """
    return jsonify({"message": "Backend is online."})


# Below this comment are the imports of all used routes defined in "shopdb.routes"

# Error handler
# noinspection PyUnresolvedReferences
import shop_db2.helpers.errors  # noqa: E402

# App hooks
# noinspection PyUnresolvedReferences
import shop_db2.helpers.hooks  # noqa: E402

# Backup routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.backups  # noqa: E402

# Deposit routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.deposits  # noqa: E402

# Financial overview route
# noinspection PyUnresolvedReferences
import shop_db2.routes.financial_overview  # noqa: E402

# Image routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.images  # noqa: E402

# Login route
# noinspection PyUnresolvedReferences
import shop_db2.routes.login  # noqa: E402

# Maintenance routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.maintenance  # noqa: E402

# Product routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.products  # noqa: E402

# Purchase routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.purchases  # noqa: E402

# Rank routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.ranks  # noqa: E402

# ReplenishmentCollection routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.replenishmentcollections  # noqa: E402

# StocktakingCollection routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.stocktakingcollections  # noqa: E402

# Tag assignment routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.tagassignments  # noqa: E402

# Tag routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.tags  # noqa: E402

# User routes
# noinspection PyUnresolvedReferences
import shop_db2.routes.users  # noqa: E402

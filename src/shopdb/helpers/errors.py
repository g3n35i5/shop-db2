#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import werkzeug.exceptions as werkzeug_exceptions
from flask import jsonify

import shopdb.exceptions as exc
from shopdb.api import app, db


@app.errorhandler(Exception)
def handle_error(error):
    """This wrapper catches all exceptions and, if possible, returns a user
    friendly response. Otherwise, it will raise the error

    :param error: Is the exception to be raised.

    :return:      Return a json response with the message that the page cannot
                  be found if it is a 404 error.
    :return:      Return a json response with the custom exception message,
                  if it is a custom exception.

    :raises:      Raises the passed exception if the application is in debug
                  mode or cannot be interpreted.
    """
    # Perform a rollback. All changes that have not yet been committed are
    # thus reset.
    db.session.rollback()

    # Catch the 404-error.
    if isinstance(error, werkzeug_exceptions.NotFound):
        return jsonify(result="error", message="Page does not exist."), 404

    # Catch the 'MethodNotAllowed' exception
    if isinstance(error, werkzeug_exceptions.MethodNotAllowed):
        return jsonify(result="error", message="Method not allowed."), 405

    # As long as the application is in debug mode, all other exceptions
    # should be output immediately.
    if app.config["DEBUG"] and not app.config["DEVELOPMENT"]:
        raise error  # pragma: no cover

    # Create, if possible, a user friendly response.
    if isinstance(error, exc.ShopdbException):
        return jsonify(result=error.type, message=error.message), error.code
    else:  # pragma: no cover
        raise error

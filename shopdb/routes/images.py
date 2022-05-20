#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import os

from flask import send_from_directory

import shopdb.exceptions as exc
from shopdb.api import app


@app.route("/images", methods=["GET"], defaults={"imagename": None})
@app.route("/images/<imagename>", methods=["GET"])
def get_image(imagename):
    """
    A picture can be requested via this route. If the image is not found or if
    the image name is empty, a default image will be returned.

    :param imagename: Is the name of the requested image.

    :return:          The requested image or the default image, if applicable.
    """
    if not imagename:
        return send_from_directory(app.config["UPLOAD_FOLDER"], "default.png")
    else:
        if os.path.isfile(app.config["UPLOAD_FOLDER"] + imagename):
            return send_from_directory(app.config["UPLOAD_FOLDER"], imagename)
        else:
            raise exc.EntryNotFound()

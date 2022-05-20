#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import base64
import binascii
import os
import random
import shutil
import tempfile

from PIL import Image

import configuration as config
import shopdb.exceptions as exc


def insert_image(file: dict) -> str:
    if not file:
        raise exc.NoFileIncluded()

    # Check if the filename is empty. There is no way to create a file with
    # empty filename in python so this can not be tested. Anyway, this is
    # a possible error vector.
    if "filename" not in file or file["filename"] == "":
        raise exc.InvalidFilename()

    # Check if the filename is valid
    filename = file["filename"].split(".")[0]
    if filename is "" or not filename:
        raise exc.InvalidFilename()

    # Check the file extension
    extension = file["filename"].split(".")[1].lower()
    valid_extension = extension in config.BaseConfig.VALID_EXTENSIONS
    if not valid_extension:
        raise exc.InvalidFileType()

    # Check if the image data has a value field.
    if "value" not in file:
        raise exc.NoFileIncluded()

    # Check the content size.
    if len(file["value"]) > config.BaseConfig.MAX_CONTENT_LENGTH:
        raise exc.FileTooLarge()

    # Check if the image is a valid image file.
    try:
        # Save the image to a temporary file.
        temporary_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{extension}"
        )
        base64_data = file["value"].replace("data:image/png;base64,", "")
        temporary_file.write(base64.b64decode(base64_data))
        temporary_file.close()
        image = Image.open(temporary_file.name)

    # An invalid file will lead to an exception.
    except (IOError, binascii.Error):
        raise exc.BrokenImage()

    # Check the real extension again
    if image.format not in [x.upper() for x in config.BaseConfig.VALID_EXTENSIONS]:
        raise exc.InvalidFileType()

    # Check aspect ratio
    width, height = image.size
    if width != height:
        raise exc.ImageMustBeQuadratic()

    # Move the temporary image to its destination path.
    destination_filename = os.path.basename(temporary_file.name)
    destination_path = os.path.join(
        config.BaseConfig.UPLOAD_FOLDER, destination_filename
    )
    shutil.move(temporary_file.name, destination_path)
    return destination_filename

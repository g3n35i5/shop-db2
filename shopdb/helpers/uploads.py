#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import os
import random
import shopdb.exceptions as exc
from PIL import Image
import configuration as config
import shutil
import base64
import binascii


def insert_image(file: dict) -> str:
    if not file:
        raise exc.NoFileIncluded()

    # Check if the filename is empty. There is no way to create a file with
    # empty filename in python so this can not be tested. Anyway, this is
    # a possible error vector.
    if 'filename' not in file or file['filename'] == '':
        raise exc.InvalidFilename()

    # Check if the filename is valid
    filename = file['filename'].split('.')[0]
    if filename is '' or not filename:
        raise exc.InvalidFilename()

    # Check the file extension
    extension = file['filename'].split('.')[1].lower()
    valid_extension = extension in config.BaseConfig.VALID_EXTENSIONS
    if not valid_extension:
        raise exc.InvalidFileType()

    # Check if the image data has a value field.
    if 'value' not in file:
        raise exc.NoFileIncluded()

    # Check the content size.
    if len(file['value']) > config.BaseConfig.MAX_CONTENT_LENGTH:
        raise exc.FileTooLarge()

    # Check if the image is a valid image file.
    try:
        # Save the image to a temporary file.
        temp_filename = '/tmp/' + file['filename']
        filedata = file['value'].replace('data:image/png;base64,', '')
        f = open(temp_filename, 'wb')
        f.write(base64.b64decode(filedata))
        f.close()
        image = Image.open(temp_filename)

    # An invalid file will lead to an exception.
    except (IOError, binascii.Error):
        os.remove(temp_filename)
        raise exc.BrokenImage()

    # Check the real extension again
    if image.format not in [x.upper() for x in config.BaseConfig.VALID_EXTENSIONS]:
        raise exc.InvalidFileType()

    # Check aspect ratio
    width, height = image.size
    if width != height:
        raise exc.ImageMustBeQuadratic()

    # Create a unique filename.
    can_be_used = False
    while not can_be_used:
        unique = ''.join(random.choice('0123456789abcdef') for i in range(32))
        filename = '.'.join([unique, extension])
        path = os.path.join(config.BaseConfig.UPLOAD_FOLDER, filename)
        can_be_used = not os.path.isfile(path)

    # Move the temporary image to its destination path.
    shutil.move(temp_filename, path)
    return filename

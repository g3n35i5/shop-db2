#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import os
import base64
import random
import shutil
from PIL import Image
from sqlalchemy.exc import IntegrityError
import shopdb.exceptions as exc
from flask import jsonify, request
from shopdb.api import (app, db, adminRequired)
from shopdb.models import Upload


@app.route('/upload', methods=['POST'])
@adminRequired
def upload(admin):
    """
    You can upload pictures via this route. The valid file formats can be
    set in the configuration under "VALID_EXTENSIONS".

    :param admin:                 Is the administrator user, determined by
                                  @adminRequired.

    :return:                      The generated file name under which the image
                                  has been stored.

    :raises NoFileIncluded:       If no data was found in the request.
    :raises InvalidFilename:      If the filename is empty empty or invalid in
                                  any other form.
    :raises InvalidFileType:      If the file format is not allowed.
    :raises FileTooLarge:         If the size of the file exceeds the maximum
                                  allowed file size.
    :raises BrokenImage:          If the image file could not be read.
    :raises ImageMustBeQuadratic: If the height and width of the image are not
                                  identical.
    :raises CouldNotCreateEntry:  If the new image cannot be added to the
                                  database.
    """
    # Get the file. Raise an exception if there is no data.
    file = request.get_json()
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
    valid_extension = extension in app.config['VALID_EXTENSIONS']
    if not valid_extension:
        raise exc.InvalidFileType()

    # Check if the image data has a value field.
    if 'value' not in file:
        raise exc.NoFileIncluded()

    # Check the content size.
    if len(file['value']) > app.config.get('MAX_CONTENT_LENGTH'):
        raise exc.FileTooLarge()

    # Check if the image is a valid image file.
    try:
        # Save the image to a temporary file.
        temp_filename = '/tmp/' + file['filename']
        filedata = file['value']
        f = open(temp_filename, 'wb')
        f.write(base64.b64decode(filedata))
        f.close()
        image = Image.open(temp_filename)

    # An invalid file will lead to an exception.
    except IOError:
        os.remove(temp_filename)
        raise exc.BrokenImage()

    # Check the real extension again
    if image.format not in [x.upper() for x in app.config['VALID_EXTENSIONS']]:
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
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        can_be_used = not os.path.isfile(path)

    # Move the temporary image to its destination path.
    shutil.move(temp_filename, path)

    # Create an upload
    try:
        upload = Upload(filename=filename, admin_id=admin.id)
        db.session.add(upload)
        db.session.commit()
    except IntegrityError:
        raise exc.CouldNotCreateEntry()

    # Make response
    return jsonify({
        'message': 'Image uploaded successfully.',
        'filename': filename}), 200

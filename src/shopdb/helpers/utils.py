#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "g3n35i5"

import datetime

import dateutil.parser
from flask import request

import shopdb.exceptions as exc


def json_body():
    """Returns the json data from the current request.

    :return:             The json body from the current request.

    :raises InvalidJSON: If the json data cannot be interpreted.
    """
    jb = request.get_json()
    if jb is None:
        raise exc.InvalidJSON()
    return jb


def convert_minimal(data, fields):
    """This function returns only the required attributes of all objects in
    given list.

    :param data:   The object from which the attributes are obtained.
    :param fields: A list of all attributes to be output.

    :return:       A dictionary with all requested attributes.
    """
    if not isinstance(data, list):
        data = [data]

    if len(data) == 0:
        return []
    out = []

    for item in data:
        element = {}
        for field in fields:
            element[field] = getattr(item, field, None)

        out.append(element)

    return out


def parse_timestamp(data: dict, required: bool) -> dict:
    """Parses a timestamp in a input dictionary. If there is no timestamp and it's not required, nothing happens.
    Otherwise an exception gets raised. If a timestamp exists, it gets parsed.

    :param data:       The input dictionary
    :param required:   Flag whether the timestamp is required.
    :return:           The parsed input dictionary.
    """
    # If the timestamp is missing but it is required, raise an exception.
    # Otherwise return the (non-modified) input data.
    if "timestamp" not in data:
        if required:
            raise exc.DataIsMissing()
        else:
            return data

    # Get the timestamp
    timestamp = data.get("timestamp")

    # If the timestamp is not a string, raise an exception
    if not isinstance(timestamp, str):
        raise exc.WrongType()

    # Catch empty string timestamp which is caused by some JS date pickers
    # inputs when they get cleared. If the timestamp is required, raise an exception.
    if timestamp == "":
        if required:
            raise exc.DataIsMissing()
        else:
            del data["timestamp"]
            return data
    else:
        try:
            timestamp = dateutil.parser.parse(data["timestamp"])
            assert isinstance(timestamp, datetime.datetime)
            assert timestamp < datetime.datetime.now(datetime.timezone.utc)
            data["timestamp"] = timestamp.replace(microsecond=0)
        except (TypeError, ValueError, AssertionError):
            raise exc.InvalidData()

    return data

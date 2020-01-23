##!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import jsonify, request
from shopdb.api import app
from shopdb.helpers.utils import convert_minimal
from shopdb.helpers.query import QueryFromRequestParameters
from shopdb.models import Rank


@app.route('/ranks', methods=['GET'])
def list_ranks():
    """
    Returns a list of all ranks.

    :return: A list of all ranks.
    """
    fields = ['id', 'name', 'debt_limit']
    query = QueryFromRequestParameters(Rank, request.args, fields)
    result, content_range = query.result()
    response = jsonify(convert_minimal(result, fields))
    response.headers['Content-Range'] = content_range
    return response

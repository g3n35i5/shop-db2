##!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

from flask import jsonify
from shopdb.api import (app, convert_minimal)
from shopdb.models import Rank


@app.route('/ranks', methods=['GET'])
def list_ranks():
    """
    Returns a list of all ranks.

    :return: A list of all ranks.
    """
    result = Rank.query.all()
    ranks = convert_minimal(result, ['id', 'name', 'debt_limit'])
    return jsonify({'ranks': ranks}), 200

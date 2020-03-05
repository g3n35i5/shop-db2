#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = 'g3n35i5'

import json
import re
from typing import Optional, Tuple, List

from sqlalchemy import func, types
from sqlalchemy.sql.expression import BinaryExpression
from werkzeug import ImmutableMultiDict

import shopdb.exceptions as exc
from shopdb.api import db


class QueryFromRequestParameters:
    __valid_fields_and_types__ = {'filter': dict, 'pagination': dict, 'sort': dict}

    def __init__(self, model: db.Model, arguments: ImmutableMultiDict, fields=List[str]) -> None:
        # Database table
        self._model: db.Model = model
        # Column mapper for validation and column access
        self._column_mapper = self._model.__mapper__.columns
        # List of all valid columns for filtering and sorting
        self._valid_columns = fields
        # Request query arguments
        self._arguments: dict = arguments.to_dict()
        # Parse request arguments
        self._parse_arguments()
        # Validate request arguments
        self._validate_arguments()

        # Prepare base query
        self._query = db.session.query(self._model)

    def _parse_arguments(self) -> None:
        """
        This function parses the input ImmutableMultiDict into a vanilla python dictionary.
        All key, value pairs are processed with the json.loads() method to correctly load
        lists and dictionaries in string representation.

        :param arguments:               The input query arguments

        :raises InvalidQueryParameters: Gets raised when there are illegal query parameters or corrupt data.

        :return:                        None
        """
        # Output dictionary
        parsed_arguments = dict()

        # Iterate all items in the request query arguments
        for argument_key, argument_value in self._arguments.items():
            # The argument key must be in the list of valid fields and types
            try:
                assert argument_key in self.__valid_fields_and_types__.keys()
            except AssertionError:
                raise exc.InvalidQueryParameters()

            # Clean possible non-JSON conforming quoting
            try:
                argument_value = argument_value.strip("'<>() ").replace('\'', '\"')
                argument_value = argument_value.replace('False', 'false')
                argument_value = argument_value.replace('True', 'true')
            except AttributeError:
                # Maybe there is a chance to parse it anyway
                pass
            except Exception:
                # All other exceptions need to raise "InvalidQueryParameters"
                raise exc.InvalidQueryParameters()

            # Parse the value from string and process it
            try:
                parsed_value = json.loads(argument_value)
                # The type must be correct
                assert isinstance(parsed_value, self.__valid_fields_and_types__.get(argument_key))
                parsed_arguments[argument_key] = parsed_value
            except (AssertionError, json.decoder.JSONDecodeError):
                raise exc.InvalidQueryParameters()

        # Save the parsed (but yet not fully validated) parameters
        self._arguments = parsed_arguments

    def _validate_arguments(self) -> None:
        """
        This method validates all query parameters.

        :raises InvalidQueryParameters if there are invalid parameters.

        :return: None
        """
        regex_sanitize_pattern = r"[a-zA-Z\u00C0-\u017F0-9\s\-\_]*"
        try:
            # Validate filter(s)
            if self.filters is not None:
                for filter_key, filter_value in self.filters.items():
                    # The filter key must be of type string
                    assert isinstance(filter_key, str)
                    # The filter key must not be empty
                    assert len(filter_key) > 0
                    # The filter key must be in the list of valid columns
                    assert filter_key in self._valid_columns
                    # The filter key must match the regex_sanitize_pattern to avoid injections
                    assert re.fullmatch(regex_sanitize_pattern, filter_key)
                    # At this point it must be distinguished whether one or more filter values are specified
                    # Valid cases are:
                    #   - One value: {str, int, float}
                    #   - Multiple values: List of {str, int, float}, but all of the same type
                    assert isinstance(filter_value, (str, list, int, float, bool))
                    # Case 1: Single value
                    if isinstance(filter_value, (str, int, float, bool)):
                        if isinstance(filter_value, str):
                            assert re.fullmatch(regex_sanitize_pattern, filter_value)
                    # Case 2: Multiple values
                    elif isinstance(filter_value, list):
                        all_types = [type(x) for x in filter_value]
                        # All types must be {str, int, float}
                        assert all([isinstance(x, (str, int, float, bool)) for x in filter_value])
                        # With this condition it is assured that all types are equal
                        assert all_types.count(all_types[0]) == len(all_types)
                        # All filter values must match the regex_sanitize_pattern to avoid injections
                        for item in filter_value:
                            if isinstance(item, str):
                                assert re.fullmatch(regex_sanitize_pattern, item)
                    else:
                        # Raise an exception here, just to be sure
                        assert True is False

            # Validate pagination
            if self.pagination is not None:
                # Pagination must be a dict
                assert isinstance(self.pagination, dict)
                # Only the keys ["page", "perPage"] are allowed
                assert ["page", "perPage"] == list(self.pagination.keys())
                # All values must be of type integer
                assert all([isinstance(x, int) for x in self.pagination.values()])
                # All values must be greater than 0
                assert all([x > 0 for x in self.pagination.values()])

            # Validate sorting
            if self.sorting is not None:
                # Sort param must be a dict
                assert isinstance(self.sorting, dict)
                # Only the keys ["field", "order"] are allowed
                assert ["field", "order"] == list(self.sorting.keys())
                # All values must be of type string
                assert all([isinstance(x, str) for x in self.sorting.values()])
                # The sorting field must be in the list of valid columns
                assert self.sorting.get("field") in self._valid_columns
                # The sorting direction must be in the list ['asc', 'ASC', 'desc', 'DESC']
                assert self.sorting.get("order") in ['asc', 'ASC', 'desc', 'DESC']
                # Both, sorting key and direction, must match the regex_sanitize_pattern to avoid injections
                assert re.fullmatch(regex_sanitize_pattern, self.sorting.get("field"))
                assert re.fullmatch(regex_sanitize_pattern, self.sorting.get("order"))

        except AssertionError:
            raise exc.InvalidQueryParameters()

    def filter(self, expression: BinaryExpression) -> 'QueryFromRequestParameters':
        """
        This method applies a sqlalchemy binary expression to the base query

        :param expression: Is the binary expression which is to be applied to the base query.

        :return:           The filtered QueryFromRequestParameters
        """
        self._query = self._query.filter(expression)
        return self

    @property
    def pagination(self) -> Optional[dict]:
        """
        :return: The pagination parameters if they exist
        """
        return self._arguments.get('pagination', None)

    @property
    def filters(self) -> Optional[dict]:
        """
        :return: The filter parameters if they exist
        """
        return self._arguments.get('filter', None)

    @property
    def sorting(self) -> Optional[dict]:
        """
        :return: The sorting parameters if they exist
        """
        return self._arguments.get('sort', None)

    def result(self) -> Tuple:
        """
        Applies all filters to the query and returns the result

        :return: The queried data and the content-range header entry.
        """

        # Apply all filters
        if self.filters is not None:
            for filter_field, filter_value in self.filters.items():
                # Case 1: One filter value and string. We use the contains method for this
                if isinstance(filter_value, str):
                    self._query = self._query.filter(self._column_mapper[filter_field].contains(filter_value))
                # Case 2: One filter value and int/float. We use the is_ method for this
                elif isinstance(filter_value, (int, float, bool)):
                    self._query = self._query.filter(self._column_mapper[filter_field].is_(filter_value))
                # Case 3: Multiple filter values
                else:
                    self._query = self._query.filter(self._column_mapper[filter_field].in_(tuple(filter_value)))

        # Apply sorting
        if self.sorting is not None:
            # Only perform the lowercase operation if the column type is not "types.Integer"
            # If the column to be sorted by is of the type "types.integer", the lowercase function
            # must not be used, otherwise integers are sorted by the scheme
            # "1, 10, 11, 12, ..., 2, 21, 22, ... 3..."
            column = self._column_mapper[self.sorting.get("field")]
            if not isinstance(column.type, types.Integer):
                column = func.lower(column)

            if self.sorting.get("order").lower() == 'asc':
                self._query = self._query.order_by(column.asc())
            else:
                self._query = self._query.order_by(column.desc())

        # Apply the pagination if it exists
        if self.pagination is not None:
            page = self.pagination.get("page")
            per_page = self.pagination.get("perPage")
            self._query = self._query.paginate(page=page, per_page=per_page, error_out=False)
            data = self._query.items
            range_start = (page - 1) * per_page
            range_end = page * per_page - 1
            total_items = self._query.total

        # Perform a standard query
        else:
            data = self._query.all()
            total_items = self._query.count()
            range_start = 0
            range_end = total_items

        # Most data provider expect the API to include a Content-Range header in the response.
        # The value must be the total number of resources in the collection.
        # This allows the client interface to know how many pages of resources there are in total,
        # and build the pagination controls.
        content_range = f'{self._model.__table__.name}: {range_start}-{range_end}/{total_items}'

        return data, content_range

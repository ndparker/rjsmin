# -*- coding: ascii -*-
#
# Copyright 2024 - 2025
# Andr\xe9 Malo or his licensors, as applicable
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Utilities
~~~~~~~~~

"""

import functools as _ft


basestring_ = (
    str
    if str is not bytes
    else basestring  # noqa pylint: disable = undefined-variable
)


def cached(func):
    """
    Caching decorator

    Parameters:
      func (callable):
        The function to cache the result of

    Returns:
        The decorated function
    """
    cache = getattr(_ft, "cache", None)
    if cache is not None:
        return cache(func)

    store = {}

    @_ft.wraps(func)
    def inner(*args, **kwargs):
        """The cache wrapper"""
        key = tuple(list(args) + sorted(kwargs.items()))
        try:
            return store[key]
        except KeyError:
            store[key] = result = func(*args, **kwargs)
            return result

    return inner


def dictmerge(dict1, dict2):
    """
    Merge nested dict2 into dict1

    Parameters:
      dict1 (dict or adict):
        Dict to update

      dict2 (dict or adict):
        Dict to merge

    Returns:
      dict or adict: The updated dict1. If it was an adict, a new adict is
                     returned.
    """
    type1 = type(dict1)
    if isinstance(dict2, adict):
        type1 = adict
    elif type1 not in (dict, adict):
        type1 = adict

    dict1 = dict(dict1.items())

    for key, value in dict2.items():
        if isinstance(value, (dict, adict)):
            value = dictmerge(dict1.get(key, {}), value)
        dict1[key] = value

    return type1(dict1)


class adict(object):
    """attribute dict"""

    # pylint: disable = invalid-name, missing-docstring

    def __init__(self, *args, **kwargs):
        """
        Initialization

        Parameters:
          *args:
            Positional dict args

          **kwargs:
            Keyword dict args
        """
        self.__x__ = dict(*args, **kwargs)

    def __iter__(self):
        """
        Return key iterator

        Returns:
          iterable: New key iterator
        """
        return iter(self.__x__)

    def __getitem__(self, name):
        """
        Get value by subscript

        Parameters:
          name (str):
            The key

        Returns:
          any: The value

        Raises:
          KeyError: Key not found
        """
        return self.__x__[name]

    def __getattr__(self, name):
        """
        Get value for dot notation

        Parameters:
          name (str):
            The key

        Returns:
          any: The value

        Raises:
          AttributeError: Key not found
        """
        if name == "__setstate__":
            raise AttributeError(name)
        try:
            return self.__x__[name]
        except KeyError:
            raise AttributeError(name)  # pylint: disable = raise-missing-from

    def items(self):
        """
        Create key/value iterator

        Returns:
          iterable: New key/value iterator
        """
        return self.__x__.items()

    def get(self, *args, **kwargs):
        """
        Get value with default

        Parameters:
          *args:
            Positional dict.get args

          **kwargs:
            Keyword dict.get args

        Returns:
          any: The value or the default (if the key doesn't exist)
        """
        return self.__x__.get(*args, **kwargs)

# -*- encoding: ascii -*-
"""
Utilities
~~~~~~~~~

"""


class adict:
    """attribute dict"""

    # pylint: disable = invalid-name, missing-docstring

    def __init__(self, *args, **kwargs):
        self.__x__ = dict(*args, **kwargs)

    def __iter__(self):
        return iter(self.__x__)

    def __getitem__(self, name):
        return self.__x__[name]

    def __getattr__(self, name):
        if name == "__setstate__":
            raise AttributeError(name)
        try:
            return self.__x__[name]
        except KeyError:
            raise AttributeError(name) from None

    def items(self):
        return self.__x__.items()

    def get(self, *args, **kwargs):
        return self.__x__.get(*args, **kwargs)

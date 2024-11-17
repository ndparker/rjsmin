# -*- coding: ascii -*-
#
# Copyright 2024
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

# -*- coding: ascii -*-
#
# Copyright 2018 - 2025
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
Shared code for dependency files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging as _logging
import re as _re

from ..._inv import shell as _shell
from .. import _parse
from . import _file_model

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.suggest.dep_file")


class DepFile(object):
    """
    Dependency file container

    Attributes:
      name (str):
        The filename
    """

    @property
    def type(self):
        """
        The dep file type

        :Type: str
        """
        return self._model.type

    def __init__(self, filename, model):
        """
        Initialization

        Parameters:
          filename (str):
            The filename
        """
        self.name = _shell.relative(filename)
        self._fullname = _shell.native(filename)
        self._model = model

    @classmethod
    def by_type(cls, type, filename):  # pylint: disable = redefined-builtin
        """
        Return dep file instance by type and name

        This factory returns the found initialized dep file ``None``.

        Parameters:
          type (str):
            The file type

          filename (str):
            The file name

        Returns:
          DepFile: new instance
        """
        # pylint: disable = used-before-assignment
        # pylint: disable = unnecessary-lambda-assignment
        find_subs = lambda cls: set(cls.__subclasses__()).union(
            s for c in cls.__subclasses__() for s in find_subs(c)
        )
        for sub in find_subs(_file_model.Model):
            if sub.type == type:
                return cls(filename, sub.by_name(filename))
        return None

    def __repr__(self):
        """
        Create debug representation

        Returns:
          str: The repr of the container
        """
        return "%s(%r, %r)" % (
            self.__class__.__name__,
            self.name,
            self._model,
        )

    def __hash__(self):
        """
        Hash function based on the filename

        Returns:
          int: The hash
        """
        return hash(self.name)

    def __eq__(self, other):
        """
        Equality - based on the name

        Returns:
          bool: Is it equal?
        """
        return isinstance(other, self.__class__) and other.name == self.name

    def __ne__(self, other):
        """
        Non-Equality - based on the name

        Returns:
          bool: Is it not equal?
        """
        return not self == other

    def __lt__(self, other):
        """
        Less-than comparision - based on the name

        Returns:
          bool: Is it smaller than other?
        """
        return isinstance(other, self.__class__) and self.name < other.name

    def __contains__(self, name):
        """
        Check if package is referenced

        Parameters:
          name (str):
            The package name to look for

        Returns:
          bool: Is it referenced?
        """
        for _ in self.find(name):
            return True
        return False

    def __str__(self):
        """
        The reconstructed file

        Returns:
          str: The file as string
        """
        return "".join(map(str, self._model.parts))

    def write(self):
        """Write back the file"""
        with open(self._fullname, "wb") as fp:
            fp.write(str(self).encode(self._model.encoding))

    def find(self, name, require_version=None):
        """
        Find requirements for `name`

        Parameters:
          name (str):
            The name to look for

          require_version (bool):
            Require the version to be present? If omitted or ``None``, the
            default is picked from the file model.

        Returns:
          iterable: Iterator over found specs
        """
        if require_version is None:
            require_version = self._model.require_version

        find = _re.compile(
            _parse.regex.full_spec(name, require_version=require_version)
        ).finditer

        for part in self._model.parts:
            if part.is_literal:
                continue
            for match in find(part.content):
                yield match.group("spec")

    def patch(self, patches):
        """
        Patch the file

        Parameters:
          patches (dict):
            The changeset to apply

        Returns:
          ReqFile: A new container instance with possibly patched content
        """
        parts = []
        for part in self._model.parts:
            if not part.is_literal:
                part = part.__class__(
                    part.raw, part.quote, self._patch(part.content, patches)
                )
            parts.append(part)
        return self.__class__(self._fullname, self._model.__class__(parts))

    @staticmethod
    def _patch(string, patches):
        """
        Patch a single string - helper

        Parameters:
          string (str):
            The string to patch

          patches (dict):
            Changeset (``{'changes': {name: {'new': 'spec'}, ...}}``)

        Returns:
          str: The patched string
        """

        def valid(req):
            """Check if it's valid to patch"""
            req = _parse.requirement(str(req))
            if req.marker and not req.marker.evaluate():
                return False
            return True

        result = string
        for name, patchlist in patches["changes"].items():
            for patch in patchlist:
                result = _re.sub(
                    _parse.regex.full_spec(name, require_version=True),
                    lambda m, n=patch["new"]: (
                        "%s%s" % (m.group("space"), n)
                        if valid(m.group("spec"))
                        else m.group(0)
                    ),
                    result,
                )

        return result

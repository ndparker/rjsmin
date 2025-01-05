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
Requirement file container
~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging as _logging
import os as _os
import re as _re

from .. import _parse

logger = _logging.getLogger("deps.inspect.req_file")

REQUIREMENT = "requirement"
CONSTRAINT = "constraint"
EDITABLE = "editable"
INDEX = "index"


def tokens(filenames, base=None):
    """
    Walk over requirement tokens from a list of req files

    Parameters:
      filenames (iterable):
        List of filenames to parse

      base (str):
        Base path. If omitted or ``None``, the CWD is used.

    Returns:
      iterable: List of token objects found
    """
    base = _os.path.normpath(_os.path.abspath(base or _os.getcwd()))
    req_match = _re.compile(r"^(?:-r|--requirement)\s+(\S.*)").match
    con_match = _re.compile(r"^(?:-c|--constraint)\s+(\S+)").match
    edit_match = _re.compile(r"^(?:-e|--editable)\s+(\S.*)").match
    idx_match = _re.compile(r"^(?:-i|--index)\s+(\S+)").match
    name_match = _re.compile(r"^(?:%s)" % (_parse.regex.idre)).match

    stack = FileIterator(base, filenames)
    for line in stack:
        content = line.content.strip()
        if not content or content.startswith("#"):
            continue

        match = req_match(content)
        if match:
            req = match.group(1)
            logger.debug("Found requirement reference %r", req)
            if req.lower().startswith(("http://", "https://")):
                logger.debug("Skipping remote requirement file")
                continue

            if req.lower().startswith("file://"):
                req = req[len("file://") :]
            req = _os.path.normpath(
                _os.path.join(_os.path.dirname(line.file), req)
            )
            stack.push_file(req)
            continue

        match = con_match(content)
        if match:
            con = match.group(1)
            if con.lower().startswith("file://"):
                con = con[len("file://") :]
            if not con.startswith(("http://", "https://")):
                con = _os.path.normpath(
                    _os.path.join(_os.path.dirname(line.file), con)
                )

            logger.debug("Returning constraint file %r", con)
            yield Token.constraint(con.rstrip(), line)
            continue

        match = edit_match(content)
        if match:
            value = match.group(1).rstrip()
            logger.debug("Returning editable install %r", value)
            yield Token.editable(value, line)
            continue

        match = idx_match(content)
        if match:
            value = match.group(1).rstrip()
            logger.debug("Returning index %r", value)
            yield Token.index(value, line)
            continue

        if name_match(content):
            logger.debug("Returning requirement %r", content)
            yield Token.requirement(_parse.requirement(content), line)
            continue

        logger.debug(
            "Ignoring line %s in %s: %r", line.lineno, line.file, content
        )


class Token(object):
    """
    Container for parsed requirement file tokens

    Attributes:
      value (any):
        The token. Type depends on the token type. Typically a string, but
        it's an requirement object for type == REQUIREMENT

      line (Line):
        The line object

      type (str):
        The token type
    """

    # pylint: disable = redefined-builtin
    def __init__(self, value, line, type):
        """
        Initialization

        Parameters:
          value (any):
            The token value

          line (Line):
            The line

          type (str):
            The token type:
            - CONSTRAINT
            - REQUIREMENT
            - EDITABLE
            - INDEX
        """
        self.value = value
        self.line = line
        self.type = type

    def __repr__(self):
        """
        Create string representation

        Returns:
          str: String representation
        """
        return "%s(%r, line=%r, type=%s)" % (
            self.__class__.__name__,
            self.value,
            self.line,
            self.type.upper(),
        )

    @classmethod
    def constraint(cls, value, line):
        """
        Create CONSTRAINT token

        Parameters:
          value (str):
            The token value (constraint file reference)

          line (Line):
            The line

        Returns:
          Token: New Token instance
        """
        return cls(value, line, CONSTRAINT)

    @classmethod
    def requirement(cls, value, line):
        """
        Create REQUIREMENT token

        Parameters:
          value (parsed requirement):
            The token value (the parsed requirement object)

          line (Line):
            The line

        Returns:
          Token: New Token instance
        """
        return cls(value, line, REQUIREMENT)

    @classmethod
    def editable(cls, value, line):
        """
        Create EDITABLE token

        Parameters:
          value (str):
            The token value (editable reference, a folder or a URL)

          line (Line):
            The line

        Returns:
          Token: New Token instance
        """
        return cls(value, line, EDITABLE)

    @classmethod
    def index(cls, value, line):
        """
        Create INDEX token

        Parameters:
          value (str):
            The token value (the index URL)

          line (Line):
            The line

        Returns:
          Token: New Token instance
        """
        return cls(value, line, INDEX)


class FileIterator(object):
    """
    Iterator over file lines

    The file list can be extended while iterating over the lines. The file
    added latest will be processed first.
    """

    def __init__(self, base, filenames=None):
        """
        Initialization

        Parameters:
          base (str):
            The base path if relative file names are given

          filenames (iterable):
            The initial list of file names to iterate over
        """
        self._base = base
        self._stack = []
        self._seen = set()
        if filenames is not None:
            for filename in reversed(list(filenames)):
                self.push_file(filename)

    def push_file(self, filename):
        """
        Add a new file to iterate over

        The file will not be added if it has been seen already.

        Parameters:
          filename (str):
            The file name
        """
        filename = _os.path.normpath(_os.path.join(self._base, filename))
        key = _os.path.relpath(filename, self._base)
        if key in self._seen:
            logger.debug("Skipping file %r (already seen)", key)
            return
        self._seen.add(key)

        if not _os.path.isfile(filename):
            logger.debug("Skipping non-file %r", key)
            return

        logger.debug("Adding %r to the stack", key)
        lines = iter(File(filename))
        self._stack.append(getattr(lines, "__next__", None) or lines.next)

    def __iter__(self):
        """
        Iterate over lines

        Returns:
          iterable: All lines in LIFO (files) / FIFO (lines) order
        """
        while self._stack:
            try:
                yield self._stack[-1]()
            except StopIteration:
                self._stack.pop()


class File(object):
    """
    Requirement or constraints file

    Attributes:
      name (str):
        File name
    """

    def __init__(self, name):
        """
        Initialization

        Parameters:
          name (str):
            File name
        """
        self.name = name
        with open(self.name, "rb") as fp:
            self._lines = [
                Line(name, lineno, line.decode("latin-1"))
                for lineno, line in enumerate(fp, start=1)
            ]

    def __repr__(self):
        """
        Create string representation

        Returns:
          str: String representation
        """
        return "%s(%r)" % (
            self.__class__.__name__,
            self.name,
        )

    def __iter__(self):
        """
        Create line iterator

        Returns:
          iterable: Line iterator
        """
        return iter(self._lines)


class Line(object):
    """
    Line in a file

    Attributes:
      file (str):
        File name

      lineno (int):
        Line number

      content (str):
        The line
    """

    def __init__(self, file, lineno, content):
        """
        Initialization

        Parameters:
          file (str):
            File name

          lineno (int):
            Line number

          content (str):
            The line
        """
        self.file = file
        self.lineno = lineno
        self.content = content

    def __repr__(self):
        """
        Create string representation

        Returns:
          str: String representation
        """
        return "%s(%r, %r, %r)" % (
            self.__class__.__name__,
            self.file,
            self.lineno,
            self.content,
        )

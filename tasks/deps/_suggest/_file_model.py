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

from .. import _parse

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.suggest.file_model")


class Model(object):
    """
    File model base

    Attributes:
      parts (list):
        The file parts (strings vs literals)
    """

    #: The file type
    #:
    #: :Type: str
    type = None

    #: Encoding of the file
    #:
    #: :Type: str
    encoding = "latin-1"

    #: Require a version spec when parsing the file?
    #:
    #: :Type: bool
    require_version = None

    def __init__(self, parts):
        """
        Initialization

        Parameters:
          parts (list):
            The file parts
        """
        self.parts = parts

    @classmethod
    def by_name(cls, filename):
        """
        Construct by filename

        Parameters:
          filename (str):
            The filename

        Returns:
          Model: New container instance
        """
        with open(filename, "rb") as fp:
            return cls(cls._parse_stream(fp))

    @classmethod
    def _parse_stream(cls, fp):
        """
        Parse from binary file stream

        Parameters:
          fp (file):
            Binary file stream

        Returns:
          list: The parts
        """
        raise NotImplementedError()


class ReqFile(Model):
    """Requirement file container"""

    type = "text"
    encoding = "latin-1"
    require_version = False

    @classmethod
    def _parse_stream(cls, fp):
        """
        Parse req file
        """
        parts = []
        for line in fp:
            line = line.decode(cls.encoding)
            xline = line.strip()
            if not xline or xline.startswith("#"):
                parts.append(LiteralPart(line))
            else:
                parts.append(StringPart.from_text(line))

        return parts


class SetupFile(Model):
    """Setup file container"""

    type = "setup"
    encoding = "latin-1"
    require_version = True

    @classmethod
    def _parse_stream(cls, fp):
        """
        Parse setup file
        """
        parts = []
        file_content = fp.read().decode(cls.encoding)

        last = 0
        for match in _parse.find_py_str_or_comment(file_content):
            # comments are just skipped. We look for them anyway, because they
            # might contain valid string patterns (which we will ignore)
            if match.group(2):
                continue

            if match.start() > last:
                parts.append(LiteralPart(file_content[last : match.start()]))
            last = match.end()
            raw = match.start() > 0 and file_content[match.start() - 1] == "r"
            parts.append(StringPart.from_python(raw, match.group(1)))

        if len(file_content) > last:
            parts.append(LiteralPart(file_content[last:]))

        return parts


class TomlFile(Model):
    """
    TOML file container
    """

    type = "toml"
    encoding = "utf-8"
    require_version = True

    @classmethod
    def _parse_stream(cls, fp):
        """
        Parse toml file
        """
        parts = []
        file_content = fp.read().decode(cls.encoding)

        last = 0
        for match in _parse.find_toml_str_or_comment(file_content):
            # comments are just skipped. We look for them anyway, because they
            # might contain valid string patterns (which we will ignore)
            if match.group(2):
                continue

            if match.start() > last:
                parts.append(LiteralPart(file_content[last : match.start()]))
            last = match.end()
            raw = file_content[match.start()] == "'"
            parts.append(StringPart.from_toml(raw, match.group(1)))

        if len(file_content) > last:
            parts.append(LiteralPart(file_content[last:]))

        return parts


class StringPart(object):
    """
    String part (of a dep file)

    Attributes:
      raw (bool):
        Is it a raw string?

      quote (str):
        The quote used

      content (str):
        The string content, escaped quotes stripped if not raw
    """

    #: Is it a literal part?
    #:
    #: :Type: bool
    is_literal = False

    def __init__(self, raw, quote, content):
        """
        Initialization

        :Parameters:
          raw (bool):
            Is it a raw string?

          quote (str):
            The quote used

          content (str):
            The string content, escaped quotes stripped if not raw
        """
        self.raw = raw
        self.quote = quote
        self.content = content

    def __eq__(self, other):
        """
        Return equality

        Returns:
          bool: Is it equal to other?
        """
        if not isinstance(other, self.__class__):
            return False
        return (self.raw, self.quote, self.content) == (
            other.raw,
            other.quote,
            other.content,
        )

    def __ne__(self, other):
        """
        Return non-equality

        Returns:
          bool: Is it not equal to other?
        """
        return not self == other

    def __repr__(self):
        """
        Create repr of this container

        Returns:
          str: Representation of the container
        """
        return "%s(%r, %r, %r)" % (
            self.__class__.__name__,
            self.raw,
            self.quote,
            self.content,
        )

    @classmethod
    def from_python(cls, raw, content):
        """
        Construct string from python-encoded

        Parameters:
          raw (bool):
            Is it a raw string?

          content (str):
            The string content from python, including quotes

        Returns:
          String: New string container
        """
        if content.startswith(('"""', "'''")):
            quote, content = content[:3], content[3:-3]
        else:
            quote, content = content[0], content[1:-1]
        if not raw:
            content = _re.sub(
                r"(?s)\\(.)",
                lambda m: m.group(m.group(1) in "'\""),
                content,
            )
        return cls(raw, quote, content)

    from_toml = from_python

    @classmethod
    def from_text(cls, content):
        """
        Construct string from text

        Parameters:
          content (str):
            The string content from text file

        Returns:
          String: New string container
        """
        return cls(True, "", content)

    def __str__(self):
        """
        Rebuild the string part as close to the original as possible

        Returns:
          str: The string, quoted, quotes escaped if needed
        """
        content = self.content
        if not self.raw:
            content = content.replace(self.quote, "\\%s" % (self.quote,))
        return "%s%s%s" % (self.quote, content, self.quote)


class LiteralPart(object):
    """
    Literal part (of a dep file)

    Attributes:
      content (str):
        The part content
    """

    #: Is it a literal part?
    #:
    #: :Type: bool
    is_literal = True

    def __init__(self, content):
        """
        Initialization

        Parameters:
          content (str):
            The part content
        """
        self.content = content

    def __eq__(self, other):
        """
        Return equality

        Returns:
          bool: Is it equal to other?
        """
        if not isinstance(other, self.__class__):
            return False
        return self.content == other.content

    def __ne__(self, other):
        """
        Return non-equality

        Returns:
          bool: Is it not equal to other?
        """
        return not self == other

    def __repr__(self):
        """
        Create repr of this container

        Returns:
          str: Representation of the container
        """
        return "%s(%r)" % (self.__class__.__name__, self.content)

    def __str__(self):
        """
        Rebuild the part as string

        Returns:
          str: The part as string
        """
        return self.content

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
Regular expressions
~~~~~~~~~~~~~~~~~~~

:See: https://www.python.org/dev/peps/pep-0508/
"""
import functools as _ft
import re as _re

# pylint: disable = import-outside-toplevel


class regex(object):
    """Collection of regexes"""

    wsp = r"[^\S\r\n]"
    idre = r"([a-zA-Z\d]+(?:[._-]+[a-zA-Z\d]+)*)"
    extra = r"""(?: \[
        %(wsp)s* %(idre)s+ %(wsp)s*
        (?:,%(wsp)s* %(idre)s %(wsp)s*)*
    \] )""" % dict(
        idre=idre, wsp=wsp
    )

    version_cmp = r"(?:===|[<!=>~]=|[<>])"
    version_str = r"[a-zA-Z0-9_.*+!-]+"
    version_release = r"""(?x)(?:
        ([vV]? (?:[0-9]+!)?)
        ([0-9]+(?:\.[0-9]+)*)
    )"""
    version1 = r"(?: %(cmp)s %(wsp)s* %(version)s )" % dict(
        cmp=version_cmp, wsp=wsp, version=version_str
    )
    version = r"""(?:
        %(version1)s %(wsp)s*
        (?:, %(wsp)s* %(version1)s %(wsp)s* )*
    )""" % dict(
        version1=version1, wsp=wsp
    )

    marker = r"""(?:
        (?: ; %(wsp)s*
            (?:
                [a-zA-Z0-9"'<>=~!().{}_*#\\:,/?[\]`@$%%^&+|-]+
                %(wsp)s*
            )+
        )+
    )""" % dict(
        wsp=wsp
    )

    # the # character is enclosed in a character class, so it can be used
    # with re.X
    line_comment = r"(?:[#][^\r\n]*)"

    py_str_double = r'(?:"[^"\\\r\n]*(?:\\(?:[^\r\n]|\r?\n|\r)[^"\\\r\n]*)*")'
    py_mstr_double = r'(?:"""[^"\\]*(?:(?:\\.|""?[^"])[^"\\]*)*""")'
    py_str_single = r"(?:'[^'\\\r\n]*(?:\\(?:[^\r\n]|\r?\n|\r)[^'\\\r\n]*)*')"
    py_mstr_single = r"(?:'''[^'\\]*(?:(?:\\.|''?[^'])[^'\\]*)*''')"

    toml_str_double = py_str_double
    toml_mstr_double = (
        r'(?:"""[^"\\]*(?:(?:\\.|""(?!"""")|"(?!"""""))[^"\\]*)*""")'
    )
    toml_str_single = r"(?:'[^'\r\n]*(?:[^'\r\n]*)*')"
    toml_mstr_single = r"(?:'''[^']*(?:''?[^'][^']*)*''')"

    @classmethod
    def full_spec(cls, name=None, require_version=False):
        """
        Full version spec regex

        Parameters:
          name (str):
            The package name to match against. If omitted or ``None`` all
            valid names are matched

          require_version (bool):
            Require the version to be present?

        Returns:
          str: The regex
        """
        return r"""(?xm)
            (?P<space> %(wsp)s* )
            (?P<spec>
                (?P<name>    %(name)s                                   )
                (?P<extra>   (?: %(wsp)s* %(extra)s )   ?               )
                (?P<version> (?: %(wsp)s* %(version)s ) %(opt_version)s )
                (?P<marker>  (?: %(wsp)s* %(marker)s )  ?               )
            )
        """ % dict(
            wsp=cls.wsp,
            name=cls.idre if name is None else name_as_regex(name),
            extra=cls.extra,
            version=cls.version,
            opt_version="" if require_version else "?",
            marker=cls.marker,
        )


def name_as_regex(name):
    """
    Transform package name into a regex

    Letters will be matched case insensitively and interpunction chars will be
    matched as a sequence.

    >>> name_as_regex("foo-b4r")
    '(?<![a-zA-Z0-9_.-])[fF][oO][oO][_.-]+[bB]4[rR](?![a-zA-Z0-9_.-])'

    Parameters:
     name (str):
        The name to transform

    Returns:
      str: The name as regex
    """
    # pylint: disable = unnecessary-lambda-assignment

    # escape control characters
    name = _re.sub(r"([^a-zA-Z0-9_.-])", r"\\\1", name)

    # replace interpunction sequences with matches of interpunction sequences
    name = _re.sub(r"[_.-]+", "[_.-]+", name)

    # match all letters CI
    ci_match = lambda m: "[%s%s]" % (m.group(1).lower(), m.group(1).upper())
    name = _re.sub(r"([a-zA-Z])", ci_match, name)

    # make sure we're matching the full name
    name = r"(?<![a-zA-Z0-9_.-])%s(?![a-zA-Z0-9_.-])" % (name,)

    return name


# group(1) is the match, group(2) the comment (if it is a comment match)
find_py_str_or_comment = _re.compile(
    r"""(?s) (
          (%(line_comment)s)
        | %(py_mstr_double)s
        | %(py_mstr_single)s
        | %(py_str_double)s
        | %(py_str_single)s
    ) """
    % vars(regex),
    _re.X,
).finditer

find_toml_str_or_comment = _re.compile(
    r"""(?s) (
          (%(line_comment)s)
        | %(toml_mstr_double)s
        | %(toml_mstr_single)s
        | %(toml_str_double)s
        | %(toml_str_single)s
    ) """
    % vars(regex),
    _re.X,
).finditer


safe_extra_sub = _ft.partial(_re.compile(r"[^A-Za-z0-9.-]+").sub, "_")
name_clean_sub = _ft.partial(_re.compile(r"[-_.]+").sub, "-")


def safe_extra(value):
    """
    Convert string to safe extra name

    Parameters:
      value (str):
        The string to sanitize

    Returns:
      str: The safe extra
    """
    return safe_extra_sub(value).lower()


def normalize(name):
    """
    Normalize package name

    Parameters:
      name (str):
        The name to normalize

    Returns:
      str: The normalized name
    """
    return name_clean_sub(name).lower()


def _make_req_parse():
    """
    Pick requirement parser

    Returns:
      callable: Parser call
    """
    try:
        import packaging.requirements
    except ImportError:
        import pkg_resources
    else:
        return packaging.requirements.Requirement
    return pkg_resources.Requirement.parse


requirement = _make_req_parse()


def _make_ver_parse():
    """
    Pick version parser

    Returns:
      callable: Parser call
    """
    try:
        import packaging.version
    except ImportError:
        import pkg_resources
    else:
        return packaging.version.Version
    return pkg_resources.parse_version


version = _make_ver_parse()

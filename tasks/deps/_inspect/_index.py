# -*- coding: ascii -*-
#
# Copyright 2018 - 2026
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
Inspect package versions in index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import json as _json
import logging as _logging

import setuptools as _  # noqa

try:
    from packaging import requirements as _requirements
    from packaging import specifiers as _specifiers
    from packaging import version as _pversion
except ImportError:
    from setuptools._vendor.packaging import requirements as _requirements  # type: ignore
    from setuptools._vendor.packaging import specifiers as _specifiers  # type: ignore
    from setuptools._vendor.packaging import version as _pversion  # type: ignore

try:
    from setuptools import package_index as _pkg_index  # type: ignore
except ImportError:
    _pkg_index = None

try:
    import pkg_resources as _pkg_resources
except ImportError:
    _pkg_resources = None


import invoke as _invoke

from ... import pypi as _pypi
from ..._inv import tasks as _tasks
from .. import _parse

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.inspect.index")


class _Distribution(object):
    """Simple distribution container"""

    def __init__(self, project_name, version):
        self.project_name = project_name
        self.version = version

    def __repr__(self):
        return "%s(%r, %r)" % (
            self.__class__.__name__,
            self.project_name,
            self.version,
        )


def _copy_req(req):
    """
    Copy a requirement

    Works with both ``packaging.requirements.Requirement`` and
    ``pkg_resources``-style requirements.

    Parameters:
      req (Requirement):
        The requirement to copy

    Returns:
      Requirement: A fresh copy
    """
    if isinstance(req, _requirements.Requirement):
        return _requirements.Requirement(str(req))
    return req.parse(str(req))


def _set_specifier(req, spec_str, prereleases=False):
    """
    Set a new specifier on a requirement

    Works with both ``packaging.requirements.Requirement`` and
    ``pkg_resources``-style requirements.

    Parameters:
      req (Requirement):
        The requirement to update (mutated in place)

      spec_str (str):
        The new specifier string

      prereleases (bool):
        Allow pre-releases?
    """
    if isinstance(req, _requirements.Requirement):
        req.specifier = _specifiers.SpecifierSet(
            spec_str, prereleases=prereleases
        )
    else:
        # pylint: disable-next = unnecessary-dunder-call
        req.specifier.__init__(spec_str, prereleases=prereleases)


class PipIndex(object):
    """Query the index using pip"""

    _is_available = None

    def __init__(self):
        self._ctx = _tasks.new_context()
        self._cache = set()
        self._versions = {}  # normalize(name) -> list of version strings

    @classmethod
    def is_available(cls):
        """Is the pip index available?"""
        if cls._is_available is not None:
            return cls._is_available

        ctx = _tasks.new_context()
        try:
            ctx.run(
                ctx.c(
                    "pip index -i %s versions --json pip",
                    _pypi.index_url(ctx),
                ),
                hide=True,
                echo=False,
            )
        except _invoke.UnexpectedExit:
            cls._is_available = False
        else:
            cls._is_available = True

        return cls._is_available

    def _fetch(self, req):
        """
        Fetch package versions from the index if not already cached

        Parameters:
          req (Requirement):
            The requirement whose package versions to fetch

        Returns:
          str: Normalized package name (cache key)
        """
        key = _parse.normalize(req.name)
        if key in self._cache:
            return key

        ctx = self._ctx
        index_info = _json.loads(
            ctx.run(
                ctx.c(
                    [
                        "pip",
                        "index",
                        "-i",
                        _pypi.index_url(ctx),
                        "versions",
                        "--json",
                        req.name,
                    ]
                ),
                hide=True,
            ).stdout.strip()
        )
        self._versions[key] = index_info.get("versions", [])
        self._cache.add(key)
        return key

    def best_match(self, req):
        """
        Find the best matching distribution for a requirement

        Parameters:
          req (packaging.requirements.Requirement):
            The requirement to match against

        Returns:
          _Distribution: Best matching distribution, or ``None``
        """
        key = self._fetch(req)

        versions = []
        for ver_str in self._versions.get(key, ()):
            try:
                versions.append(_pversion.Version(ver_str))
            except _pversion.InvalidVersion:
                pass

        matching = list(req.specifier.filter(versions))
        if not matching:
            return None

        return _Distribution(
            project_name=req.name,
            version=str(max(matching)),
        )


class Index(object):
    """Python package index container"""

    def __init__(self):
        """Initialization"""
        self._use_pip = PipIndex.is_available()
        if self._use_pip:
            self._index = PipIndex()
            self._wset = None
        elif _pkg_index is not None:
            self._index = _pkg_index.PackageIndex(search_path=[])
            self._wset = _pkg_resources.WorkingSet([])
        else:
            raise RuntimeError("No index access tool available")

    def lookup(self, req):
        """
        Find the best-fitting requirement in the index

        Parameters:
          req (Requirement):
            The requirement to look up

        Returns:
          Distribution: The found distribution or ``None``
        """
        if self._use_pip:
            dist = self._index.best_match(req)
        else:
            dist = self._index.best_match(req, self._wset)
        logger.debug("Index lookup result of %r: %r", str(req), dist)
        return dist

    def scanner(self, version):
        """
        Create a new package scanner

        Parameters:
          version (str):
            The package version to compare to

        Returns:
          PackageScanner: New package scanner
        """
        return PackageScanner(self, version)


class PackageScanner(object):
    """Container for scanning a single package"""

    def __init__(self, index, package_version):
        """
        Initialization

        Parameters:
          index (Index):
            The index container

          package_version (str):
            The installed package version
        """
        self._index = index
        self._version = package_version and _parse.version(package_version)
        self._result = {}

    def result(self):
        """
        Get the aggregated result

        Returns:
          dict: The result
        """
        final = dict(self._result)
        if (
            final.get("latest") is not None
            and final.get("compatible") is not None
            and final["latest"] == final["compatible"]
        ):
            del final["latest"]

        if (
            final.get("compatible") is not None
            and final.get("unchanged") is not None
            and final["compatible"] == final["unchanged"]
        ):
            del final["compatible"]

        # if (
        #     final.get("unchanged") is not None
        #     and final["unchanged"] == self._version
        # ):
        #     del final["unchanged"]

        return {
            key: str(value)
            for key, value in final.items()
            if value is not None
        }

    def inspect(self, req):
        """
        Lookup requirement versions in index

        The aggregated result can be retrieved by calling ``.result()``

        Parameters:
          req (Requirement):
            The requirement to look up
        """
        # we want a specifically typed copy
        if PipIndex.is_available():
            req = _requirements.Requirement(str(req))
        else:
            req = _pkg_index.Requirement.parse(str(req))

        self._update_field("unchanged", req)
        self._find_compat(req)
        self._find_latest(req)

    def _find_compat(self, req):
        """
        Find compatible version

        Parameters:
          req (Requirement):
            The requirement to look up
        """
        req = _copy_req(req)

        # We turn == into ~=, which finds compatible versions
        # (last digit update)
        specs = []
        for spec in req.specifier:
            operator = spec.operator
            if operator == "==":
                operator = "~="
            specs.append("%s%s" % (operator, spec.version))

        try:
            _set_specifier(req, ",".join(specs), prereleases=False)
        except ValueError:
            logger.debug("Invalid compat %r", ",".join(specs))
            return

        logger.debug("Valid compat %r", str(req))
        self._update_field("compatible", req)

    def _find_latest(self, req):
        """
        Find latest version

        Parameters:
          req (Requirement):
            The requirement to look up
        """
        req = _copy_req(req)

        spec = None if self._version is None else ">=%s" % (self._version,)
        _set_specifier(req, spec or "", prereleases=False)

        correction = self._update_field("latest", req)
        if correction:
            correction = "< %s" % (correction,)
            spec = ", ".join((spec, correction)) if spec else correction
            _set_specifier(req, spec or "", prereleases=False)
            self._update_field("latest", req)

    def _update_field(self, field, req):
        """
        Update version info field

        Parameters:
          field (str):
            The field to update

          req (Requirement):
            The requirement to evaluate
        """
        dist = self._index.lookup(_copy_req(req))
        if dist is None:
            return None

        dist_version = _parse.version(dist.version)
        if dist_version.is_prerelease:
            return dist_version

        if (self._version is None or dist_version >= self._version) and (
            self._result.get(field) is None
            or dist_version > self._result[field]
        ):
            self._result[field] = dist_version

        return None

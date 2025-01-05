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
Inspect package versions in index
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging as _logging

from setuptools import package_index as _pkg_index
import pkg_resources as _pkg_resources

from .. import _parse

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.inspect.index")


class Index(object):
    """Python package index container"""

    def __init__(self):
        """Initialization"""
        self._index = _pkg_index.PackageIndex(search_path=[])
        self._wset = _pkg_resources.WorkingSet([])

    def lookup(self, req):
        """
        Find the best-fitting requirement in the index

        Parameters:
          req (Requirement):
            The requirement to look up

        Returns:
          Distribution: The found distribution or ``None``
        """
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
        req = req.parse(str(req))  # copy

        # We turn == into ~=, which finds compatible versions
        # (last digit update)
        specs = []
        for spec in req.specifier:
            operator = spec.operator
            if operator == "==":
                operator = "~="
            specs.append("%s%s" % (operator, spec.version))

        try:
            # pylint: disable = unnecessary-dunder-call
            req.specifier.__init__(",".join(specs), prereleases=False)
        except _pkg_resources.packaging.specifiers.InvalidSpecifier:
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
        req = req.parse(str(req))  # copy

        spec = None if self._version is None else ">=%s" % (self._version,)
        # pylint: disable = unnecessary-dunder-call
        req.specifier.__init__(spec or "", prereleases=False)

        correction = self._update_field("latest", req)
        if correction:
            correction = "< %s" % (correction,)
            spec = ", ".join((spec, correction)) if spec else correction
            req.specifier.__init__(spec or "", prereleases=False)
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
        dist = self._index.lookup(req.parse(str(req)))
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

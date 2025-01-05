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
Inspect current dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import collections as _collections
import json as _json
import logging as _logging
import os as _os
import re as _re

from .. import _parse
from . import _index
from . import _req_file

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.inspect")


def inspect_dependencies(ctx, config, verbose=True, debug=False):
    """
    Inspect dependencies

    Parameters:
      config (adict):
        deps config

      verbose (bool):
        Verbose mode? Default: true

      debug (bool):
        Debug mode? Default: false

    Returns:
      dict: package -> info mapping
    """
    logger.setLevel("DEBUG" if debug else ("INFO" if verbose else "WARN"))

    requirements, _ = _scan_toplevel(ctx, config.toplevel)
    index = _index.Index()

    return {
        name: _inspect_package(index, name, version, places)
        for (name, version), places in requirements.items()
    }


def _scan_toplevel(ctx, req_files):
    """
    Find toplevel packages

    Parameters:
      req_files (list):
        Requirement file names

    Returns:
      tuple: {(normname, installed-version) -> [{line, requirement}]},
             [constraint]
    """
    installed = _find_installed(ctx)

    req = _collections.defaultdict(list)
    con = []

    for item in _req_file.tokens(req_files, base=ctx.shell.root):
        if item.type == _req_file.REQUIREMENT:
            name = _parse.normalize(item.value.name)
            version = installed.get(name, {}).get("version")
            key = (name, version)
            logger.debug("Parsed %r -> %r", item.line.content.strip(), key)
            req[key].append(dict(line=item.line, requirement=item.value))
            continue

        if item.type == _req_file.EDITABLE:
            for parsed, extras in _find_editable_deps(ctx, installed, item):
                name = _parse.normalize(parsed.name)
                version = installed.get(name, {}).get("version")
                key = (name, version)
                logger.debug("Found editable dependency %r", key)
                req[key].append(
                    dict(line=None, requirement=parsed, extras=extras)
                )
            continue

        if item.type == _req_file.CONSTRAINT:
            con.append(item.value)
            continue

    return dict(req), con


def _inspect_package(index, name, version, places):
    """
    Inspect a single package (in multiple locations)

    Parameters:
      index (PackageIndex):
        package index connector

      wset (WorkingSet):
        Working set to use

      name (str):
        The (normalized) package name

      version (str):
        Installed version (or ``None``)

      places (list):
        Places where the requirement was found
    """
    logger.info("Inspecting %s (%s)", name, version)

    scanner = index.scanner(version)
    locations = [
        _inspect_place(scanner, place)
        for place in places
        if _place_evaluates(place)
    ]
    return dict(
        installed=version,
        locations=locations,
        updates=scanner.result() or None,
    )


def _inspect_place(scanner, place):
    """
    Inspect a single place

    Parameters:
      index (PackageIndex):
        package index connector

      wset (WorkingSet):
        Working set to use

      place (dict):
        The place to inspect

      version (Version):
        parsed installed version

      version_info (dict):
        Index version info. Modified in-place.

    Returns:
      dict: The fully inspected place description
    """
    result = dict(requirement=place["requirement"])
    if place["line"]:
        result["file"] = dict(
            name=place["line"].file,
            line=place["line"].lineno,
            content=place["line"].content,
        )
        logger.debug("Adding location %r", result["file"])

    scanner.inspect(place["requirement"])
    return result


def _place_evaluates(place):
    """
    Does a place evaluate in the current environment?

    Parameters:
      place (dict):
        The place to inspect

    Returns:
      bool: The the place's requirement evaluate in the current environment?
    """
    if not place["requirement"].marker:
        return True

    if not place.get("extras"):
        if place["requirement"].marker.evaluate({}):
            return True
    else:
        for extra in place["extras"]:
            env = dict(extra=_parse.safe_extra(extra))
            if place["requirement"].marker.evaluate(env):
                return True

    logger.debug(
        "Ignoring %r because it doesn't evaluate", str(place["requirement"])
    )
    return False


def _find_editable_deps(ctx, installed, spec):
    """
    Find direct dependencies for editable installation

    Parameters:
      installed (dict):
        Installed packages

      spec (Token):
        The editable dep file token

    Returns:
      iterable: List of (requirement, needed-extras) tuples
    """
    pkg_name = _find_editable(ctx, installed, spec)
    if pkg_name:
        parts = spec.value.split("[", 1)
        parts[0] = pkg_name
        extras = sorted(_parse.requirement("[".join(parts)).extras)
        logger.debug("Extras for editable installation: %r", extras)

        try:
            try:
                from importlib import metadata as _metadata
            except ImportError:
                import importlib_metadata as _metadata
        except ImportError:
            import pkg_resources as _pkg_resources

            dist = _pkg_resources.working_set.by_key[pkg_name]
            for item in dist.requires(extras):
                yield item, extras
        else:
            for item in _metadata.requires(pkg_name) or ():
                parsed = _parse.requirement(item)
                yield parsed, extras


def _find_editable(ctx, installed, spec):
    """
    Find editable package installation

    Parameters:
      installed (dict):
        Installed packages

      spec (Token):
        The editable dep file token

    Returns:
      str: The normalized name
    """
    local_path = spec.value.split("[", 1)[0].strip()
    path = _os.path.normpath(
        _os.path.join(_os.path.dirname(spec.line.file), local_path)
    )
    if not _os.path.isdir(path):
        logger.debug("%r does not point to a path -> skipping", spec.value)
        return None

    info = None
    for normname, info in installed.items():
        if "editable" not in info:
            continue

        installed_path = _os.path.normpath(info["editable"])
        if installed_path == path:
            logger.debug(
                "Editable installation of %r found at %r", spec.value, path
            )
            return normname

        logger.debug(
            "Skipping editable %r (path does not match)", info["name"]
        )

    logger.debug("Editable %r not found", spec.value)
    return None


def _find_installed(ctx):
    """
    Find installed packages

    Returns:
      dict: norm-name (str) -> {name: str, version: str[, editable: str]}
    """
    found = _json.loads(
        ctx.run(
            ctx.c("pip list --local --format json"),
            echo=False,
            hide=True,
        ).stdout
    )
    name_match = _re.compile(r"^(?:%s)$" % (_parse.regex.idre,)).match

    result = {}
    for pkg in found:
        assert name_match(pkg["name"])
        item = dict(name=pkg["name"], version=pkg["version"])
        if "editable_project_location" in pkg:
            item["editable"] = pkg["editable_project_location"]
        result[_parse.normalize(pkg["name"])] = item

    return result

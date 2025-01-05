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
Propose updates to current dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import collections as _collections
import itertools as _it
import logging as _logging
import os as _os

from .. import _inspect
from .. import _parse
from . import _dep_file
from . import _latest_file
from . import _requirement

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.suggest")


def suggest_updates(ctx, config, upgrade=False, verbose=True, debug=False):
    """
    Inspect dependencies

    Parameters:
      config (adict):
        The deps config

      upgrade (bool):
        Consider upgrades?

      verbose (bool):
        Verbose mode? Default: true

      debug (bool):
        Debug mode? Default: false

    Returns:
      dict: {"latest": dict, "replace": dict}
    """
    # pylint: disable = too-many-locals

    logger.setLevel("DEBUG" if debug else ("INFO" if verbose else "WARN"))

    changes = _collections.defaultdict(list)
    candidates = {
        key: val
        for key, val in _inspect.inspect_dependencies(
            ctx,
            config,
            verbose=verbose,
            debug=debug,
        ).items()
        if val["updates"]
    }
    if not candidates:
        logger.debug("No dependencies found to update")
        return changes

    latest = {}
    not_latest = set(_parse.normalize(item) for item in config.no_latest)
    for info in _with_locations(ctx, candidates).values():
        for loc, want_upgrade, compat in _updatable(
            config, upgrade, info["locations"]
        ):
            oreq = str(loc["requirement"])
            req, version = _replace(loc, info, want_upgrade, compat)
            preq = _parse.requirement(req)

            if compat and _parse.normalize(preq.name) not in not_latest:
                lreq, lversion = _replace(
                    loc, info, want_upgrade, False, latest=True
                )
                plreq = _parse.requirement(lreq)
                key = _parse.normalize(plreq.name)

                if str(plreq) == str(preq):
                    not_latest.add(key)
                elif key not in not_latest:
                    latest[key] = dict(
                        new=lreq,
                        new_version=lversion,
                    )

            if str(preq) == oreq:
                logger.debug("Unchanged requirement: %r", req)
                continue

            changes[loc["file"]].append(
                dict(
                    new_version=version,
                    new=req,
                    old=loc["content"],
                )
            )

    # pylint: disable = unnecessary-lambda-assignment
    as_key = lambda x: _parse.normalize(_parse.requirement(x).name)
    group_key = lambda x: as_key(x["old"])

    return dict(
        latest=_suggest_latest(config, latest, not_latest),
        replace={
            file: dict(
                changes={
                    name: list(group)
                    for name, group in _it.groupby(
                        sorted(changelist, key=group_key), key=group_key
                    )
                }
            )
            for file, changelist in changes.items()
        },
    )


def _suggest_latest(config, latest, not_latest):
    """
    Suggest latest deps for packages

    Parameters:
      config (adict):
        The deps config

      latest (dict):
        Package -> version info

     not_latest (set):
        Set of packages not to be added

    Returns:
      dict: {add: [str], remove: [str]}
    """
    return (
        _latest_file.LatestFile(
            config.latest.file,
            config.latest.pattern,
            config.latest.prefix,
            config.latest.suffix,
            latest,
            not_latest,
        )
        if config.compat
        else None
    )


def _replace(loc, info, upgrade, compat, latest=False):
    """
    Find replacement for a single requirement

    Parameters:
      loc (dict):
        Location

      info (dict):
        Package update info

      upgrade (bool):
        Try upgrading to the latest version?

      compat (bool):
        Ensure compatible changes? (``~=``)

      latest (bool):
        The target is the list of "latest" requirements (e.g. in
        development.txt)

    Returns:
      tuple: new requirement string and new version (extracted)
             (``(str, str)``)
    """
    req, version = _requirement.replace(
        loc["content"],
        info["updates"],
        upgrade=upgrade,
        compat=compat,
        latest=latest,
    )
    logger.debug(
        "upgrade: %r, compat: %r, latest: %r, req: %s, v: %r",
        upgrade,
        compat,
        latest,
        req,
        version,
    )
    return req, version


def _updatable(config, want_upgrade, locations):
    """
    Find and classify updatable locations

    Parameters:
      config (adict):
        The deps config

      want_upgrade (bool):
        Upgrade requested?

      locations (iterable):
        Locations to consider

    Returns:
      iterable: of (location, upgrade possible, compat required)
    """
    no_compat = set(_parse.normalize(item) for item in config.no_compat)
    no_upgrade = set(_parse.normalize(item) for item in config.no_upgrade)

    for loc in locations:
        if (
            loc["requirement"].marker
            and not loc["requirement"].marker.evaluate()
        ):
            logger.debug("Skipping %r, because it doesn't evaluate", loc)
            continue

        if loc["file"].name in config.keep_as_is:
            logger.debug("Skipping %r (keeping as-is)", loc)
            continue

        want_no_upgrade = (
            _parse.normalize(loc["requirement"].name) in no_upgrade
        )
        upgrade = False if want_no_upgrade else want_upgrade

        if not want_no_upgrade and loc["file"].name in config.upgrade:
            compat = False
            upgrade = True
        elif _parse.normalize(loc["requirement"].name) in no_compat:
            compat = False
        else:
            compat = loc["file"].type != "text" and config.compat

        yield loc, upgrade, compat


def _with_locations(ctx, candidates):
    """
    Setup candidate locations

    Parameters:
      candidates (dict):
        The candidates to prepare

    Returns:
      dict: candidates again
    """
    extra = []

    with ctx.shell.root_dir():
        if _os.path.isfile("setup.py"):
            setups = ["setup.py"]
            if _os.path.isdir("setups"):
                for name in sorted(_os.listdir("setups")):
                    if name.startswith(".") or not name.endswith(".py"):
                        continue
                    setups.append("setups/%s" % (name,))
            extra.extend(
                _dep_file.DepFile.by_type("setup", name) for name in setups
            )

        if _os.path.isfile("pyproject.toml"):
            tomls = ["pyproject.toml"]
            if _os.path.isdir("setups"):
                for name in sorted(_os.listdir("setups")):
                    if name.startswith(".") or not name.endswith(".toml"):
                        continue
                    setups.append("setups/%s" % (name,))
            extra.extend(
                _dep_file.DepFile.by_type("toml", name) for name in tomls
            )

    logger.debug("Extra locations found: %r", extra)

    for name, info in candidates.items():
        info["locations"] = [
            dict(
                file=_dep_file.DepFile.by_type("text", item["file"]["name"]),
                content=item["file"]["content"].strip(),
                requirement=item["requirement"],
            )
            for item in info["locations"]
            if item.get("file")
        ] + [
            dict(
                file=depfile,
                content=req,
                requirement=_parse.requirement(req),
            )
            for depfile in extra
            for req in depfile.find(name)
        ]

    return candidates

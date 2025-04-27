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
import logging as _logging

from . import _parse
from . import _suggest

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.patch")


def patch_updates(ctx, config, upgrade=False, verbose=True, debug=False):
    """
    Patch requirement files for dependency updates

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
      dict: Changelog (``{bucket -> {name -> new version}}``)
    """
    logger.setLevel("DEBUG" if debug else ("INFO" if verbose else "WARN"))

    changes = _suggest.suggest_updates(
        ctx, config, upgrade=upgrade, verbose=verbose, debug=debug
    )
    replace, latest = changes["replace"], changes["latest"]
    if latest and not latest.as_patch_info():
        latest = None
    if not replace and not latest:
        logger.info("Nothing to do.")
        return {}

    changelog = _collections.defaultdict(
        lambda: _collections.defaultdict(dict)
    )
    boilerplate = set(_parse.normalize(item) for item in config.boilerplate)

    for file, change in sorted(replace.items()):
        logger.info("Patching %s...", file.name)
        file.patch(change).write()

        for name, update in change["changes"].items():
            bucket = (
                "boilerplate"
                if name in boilerplate or file.type == "text"
                else "update"
            )
            changelog[bucket][name] = sorted(
                set(item["new_version"] for item in update)
            )

    if latest:
        # The file might have been modified, so reload
        error = latest.load()
        if error:
            ctx.fail(error)

        latest.write()
        changelog["support"] = latest.as_changed()
        for name in changelog["support"]:
            changelog["update"].pop(name, None)

    return {key: dict(value) for key, value in changelog.items() if value}

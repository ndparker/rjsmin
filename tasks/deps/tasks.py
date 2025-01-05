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
Dependency Management Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import json as _json
import os as _os
import sys as _sys

import invoke as _invoke

from .._inv import tasks as _tasks
from .._inv import util as _util

# pylint: disable = import-outside-toplevel

NAMESPACE = "deps"


def _default_config(ctx):
    """
    Set default config

    Returns:
      adict: ctx.deps after defaults being applied
    """
    if getattr(_default_config, "applied", None):
        return ctx.deps

    ctx.deps = _util.dictmerge(
        _util.adict(
            toplevel=[
                "development.txt",
                "tests/requirements.txt",
            ],
            upgrade=[
                "checkout-requirements.txt",
            ],
            keep_as_is=[
                "compat-requirements.txt",
            ],
            no_compat=["setuptools", "pip", "build"],
            no_upgrade=[],
            no_latest=[],
            boilerplate=["setuptools", "pip", "build"],
            compat=True,
            latest=_util.adict(
                file="development.txt",
                pattern=r"(?=^-e\s+\.)",
                prefix="# Latest dependencies",
                suffix="",
            ),
        ),
        ctx.get("deps", {}),
    )
    _default_config.applied = True
    return ctx.deps


@_invoke.task()
def old(ctx):
    """List outdated python packages"""
    with ctx.shell.root_dir():
        ctx.run("pip list -o", echo=True)


@_invoke.task()
def package(ctx, upgrade=False):
    """
    Update python dependencies, excluding development (``-e .``)

    Parameters:
      upgrade (bool):
        Run pip install with ``-U`` flag?
    """
    cmd = ["pip", "install"]
    if upgrade:
        cmd += ["-U"]
    cmd += ["-e", "."]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_invoke.task(default=True)
def dev(ctx, upgrade=False):
    """
    Update python dependencies, including development (``-r development.txt``)

    Parameters:
      upgrade (bool):
        Run pip install with ``-U`` flag?
    """
    cmd = ["pip", "install"]
    if upgrade:
        cmd += ["-U"]
    cmd += ["-r", "development.txt"]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_invoke.task()
def reset(ctx, upgrade=False):
    """
    Reset your virtual env

    This command uninstalls everything except editable installs and reinstalls
    from scratch (``-r development.txt``)

    Parameters:
      upgrade (bool):
        Run pip install with ``-U`` flag?
    """
    cmd = [ctx.which("bash"), "-il", "%s/reset.sh"]
    if upgrade:
        cmd += ["-u"]
    cmd += ["."]
    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(cmd, ctx.shell.native(_os.path.dirname(__file__))),
            pty=True,
        )


@_invoke.task()
def inspect(ctx, deps=False, verbose=False, debug=False):
    """
    Inspect current dependencies and print to stdout

    Parameters:
      deps (bool):
        run ``inv deps`` before?

      verbose (bool):
        Verbose mode? Default: true

      debug (bool):
        Debug mode? Default: false
    """
    if deps:
        _tasks.execute(ctx, "deps.dev")

    from . import _inspect

    _sys.stdout.write(
        _json.dumps(
            _inspect.inspect_dependencies(
                ctx,
                _default_config(ctx),
                verbose=verbose,
                debug=debug,
            ),
            indent=4,
            default=str,
        )
        + "\n"
    )


@_invoke.task()
def check(ctx, upgrade=False, deps=False, verbose=True, debug=False):
    """
    Suggest dependency changes (basically dry run for `inv deps.patch`)

    Parameters:
      deps (bool):
        run ``inv deps`` before?

      upgrade (bool):
        Consider upgrades? They might be incompatible with your code.
        Default: false

      verbose (bool):
        Verbose mode? Default: true

      debug (bool):
        Debug mode? Default: false
    """
    if deps:
        _tasks.execute(ctx, "deps.dev")

    from . import _suggest

    result = _suggest.suggest_updates(
        ctx,
        _default_config(ctx),
        upgrade=upgrade,
        verbose=verbose,
        debug=debug,
    )

    result["replace"] = {
        file.name: dict(type=file.type, **info)
        for file, info in result["replace"].items()
    }
    result["latest"] = result["latest"] and result["latest"].as_patch_info()
    _sys.stdout.write(
        _json.dumps(
            result,
            indent=4,
            default=str,
        )
        + "\n"
    )


@_invoke.task()
def patch(ctx, deps=False, upgrade=False, verbose=True, debug=False):
    """
    Find dependency updates and patch the files

    Parameters:
      deps (bool):
        run ``inv.deps`` before?

      upgrade (bool):
        Consider upgrades? They might be incompatible with your code.
        Default: false

      verbose (bool):
        Verbose mode? Default: true

      debug (bool):
        Debug mode? Default: false
    """
    if deps:
        _tasks.execute(ctx, "deps.dev")

    from . import _patch

    _sys.stdout.write(
        _json.dumps(
            _patch.patch_updates(
                ctx,
                _default_config(ctx),
                upgrade=upgrade,
                verbose=verbose,
                debug=debug,
            ),
            indent=4,
            default=str,
        )
        + "\n"
    )

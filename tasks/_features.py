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
Check for enabled features
~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os as _os

from ._inv import shell as _shell
from ._inv import util as _util


@_util.cached
def black(_):
    """
    Check if the black formatter is enabled

    Returns:
      bool: Black formatter enabled?
    """
    return _shell.frompath("black") is not None


@_util.cached
def pylint(ctx):
    """
    Check if the pylint checker is enabled

    Returns:
      bool: pylint checker enabled?
    """
    if ctx.get("package") and _shell.frompath("pylint") is not None:
        return _os.path.exists(_shell.native("pylintrc"))
    return False


@_util.cached
def flake8(ctx):
    """
    Check if the flake8 checker is enabled

    Returns:
      bool: flake8 checker enabled?
    """
    if ctx.get("package") and _shell.frompath("flake8") is not None:
        return _os.path.exists(_shell.native(".flake8"))
    return False


@_util.cached
def python_package(ctx):
    """
    Check if the python package is configured

    Returns:
      bool: python package configured?
    """
    return bool(ctx.get("package"))


@_util.cached
def python_tests(ctx):
    """
    Check if the python tests are possible

    Returns:
      bool: python tests enabled?
    """
    if ctx.get("package"):
        return _os.path.exists(_shell.native("tests"))
    return False


@_util.cached
def tox(_):
    """
    Check if tox is installed

    Returns:
      bool: tox installed?
    """
    return _shell.frompath("tox") is not None


@_util.cached
def tox_tests(ctx):
    """
    Check if tox tests are possible

    Returns:
      bool: tox tests enabled?
    """
    return tox(ctx) and python_tests(ctx)


@_util.cached
def sphinx(_):
    """
    Check if sphinx is installed

    Returns:
      bool: Sphinx installed?
    """
    return _shell.frompath("sphinx-build") is not None


@_util.cached
def terraform(ctx):
    """
    Check if terraform is enabled

    Returns:
      bool: is terraform enabled?
    """
    if _shell.frompath("terraform") is not None:
        path = ctx.paths.get("terraform")
        return path and _os.path.exists(_shell.native(path))
    return False


@_util.cached
def sam(ctx):
    """
    Check if sam is enabled

    Returns:
      bool: is sam enabled?
    """
    if _shell.frompath("sam") is not None:
        path = ctx.get("cloudformation", {}).get("template")
        return path and _os.path.exists(_shell.native(path))
    return False

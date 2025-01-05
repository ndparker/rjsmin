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
def black():
    """
    Check if the black formatter is enabled

    Returns:
      bool: Black formatter enabled?
    """
    return _shell.frompath("black") is not None


@_util.cached
def pylint():
    """
    Check if the pylint checker is enabled

    Returns:
      bool: pylint checker enabled?
    """
    if _shell.frompath("pylint") is not None:
        return _os.path.exists(_shell.native("pylintrc"))
    return False


@_util.cached
def flake8():
    """
    Check if the flake8 checker is enabled

    Returns:
      bool: flake8 checker enabled?
    """
    if _shell.frompath("flake8") is not None:
        return _os.path.exists(_shell.native(".flake8"))
    return False

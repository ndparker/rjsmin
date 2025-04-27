# -*- coding: ascii -*-
#
# Copyright 2019 - 2025
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
Meta information
~~~~~~~~~~~~~~~~

"""

from .._inv import shell as _shell

# pylint: disable = import-outside-toplevel


def find_meta():
    """
    Find package meta data

    Returns:
      dict: Package metadata
    """
    # pylint: disable = import-error, no-name-in-module
    from build import util as _build_util

    if find_meta.found is None:
        find_meta.found = _build_util.project_wheel_metadata(
            _shell.native(".")
        )

    return find_meta.found


find_meta.found = None

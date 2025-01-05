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
Setup invoke namespace
~~~~~~~~~~~~~~~~~~~~~~

"""

import logging as _logging
import sys as _sys

from . import _default_settings
from . import shell as _shell
from . import tasks as _tasks
from . import util as _util

# pylint: disable = import-outside-toplevel


def setup():
    """
    Create invoke task namespace

    Returns:
      invoke.Collection: The main namespace
    """
    _logging.basicConfig(format="%(message)s")
    _logging.root.setLevel("ERROR")

    try:
        from .. import _settings
    except ImportError:
        settings = {}
    else:
        settings = _settings.settings

    env = {
        key: _util.adict(value) if isinstance(value, dict) else value
        for key, value in _util.dictmerge(
            _default_settings.default_settings(), settings
        ).items()
    }
    _sys.path.insert(0, _shell.root)

    return _tasks.setup_tasks(_util.adict(env))

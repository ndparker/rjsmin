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
Setup invoke namespace
~~~~~~~~~~~~~~~~~~~~~~

"""

import importlib as _importlib
import logging as _logging
import os as _os
import sys as _sys

from . import _default_settings
from . import shell as _shell
from . import tasks as _tasks
from . import util as _util


def setup(local="tasks", settings="tasks._settings"):
    """
    Create invoke task namespace

    Parameters:
      local (str):
        The package to scan for local tasks. Default: tasks

      settings (str):
        The local module containing the settings. Default: tasks._settings

    Returns:
      invoke.Collection: The main namespace
    """
    _logging.basicConfig(format="%(message)s")
    _logging.root.setLevel("ERROR")

    _set_root()

    try:
        settings = _import(settings).settings
    except (ImportError, AttributeError):
        settings = {}

    env = {
        key: _util.adict(value) if isinstance(value, dict) else value
        for key, value in _util.dictmerge(
            _default_settings.default_settings(), settings
        ).items()
    }

    return _tasks.setup_tasks(_import(local), _util.adict(env))


def _import(module):
    """
    Import a module

    Parameters:
      module (str):
        fully qualified module name

    Returns:
      module: The imported module

    Raises:
      - ImportError: module could not be imported
    """
    parts = module.rsplit(".", 1)
    if len(parts) > 1:
        return _importlib.import_module("." + parts[1], parts[0])
    return _importlib.import_module(module)


def _set_root():
    """Setup root directory based on tasks import"""
    # tasks is hardcoded here, because that's what ``inv`` is looking for.
    try:
        tasks = _sys.modules["tasks"]
    except KeyError:
        tasks = _importlib.import_module("tasks")

    tasks_path = getattr(tasks, "__path__", None)
    if tasks_path:
        _shell.root = _os.path.normpath(
            _os.path.join(_os.path.abspath(tasks_path[0]), _os.path.pardir)
        )
    else:
        _shell.root = _os.path.dirname(_os.path.abspath(tasks.__file__))

    if _shell.root in _sys.path:
        if _shell.root != _sys.path[0]:
            _sys.path.remove(_shell.root)
    if _shell.root not in _sys.path:
        _sys.path.insert(0, _shell.root)

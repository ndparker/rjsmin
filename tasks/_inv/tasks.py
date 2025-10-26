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
Task management
~~~~~~~~~~~~~~~

"""

__all__ = [
    "builtin",
    "by_name",
    "execute",
    "exists",
    "new_context",
    "optional",
    "package",
    "task_paths",
]

import collections as _collections
import importlib as _importlib
import os as _os
import re as _re

import invoke as _invoke

from . import _default_settings
from . import shell as _shell
from . import util as _util

_META = {
    "loaded": False,
    "settings": None,
    "paths": {key: () for key in ("builtin", "local")},
    "pkg": {},
}
_TASKS = {key: _invoke.Collection() for key in (None, "builtin", "local")}


def exists(name, location=None):
    """
    Check if a task exists

    Parameters:
      name (str):
        The fully qualified task name

      location (str):
        The task location (builtin, local). If omitted or ``None``, the
        merged task list is looked up

    Returns:
      bool: Does the task exist?
    """
    return name in _TASKS[location]


def by_name(name, location=None):
    """
    Find task by name

    Parameters:
      name (str):
        The fully qualified task name

      location (str):
        The task location (builtin, local). If omitted or ``None``, the
        merged task list is looked up

    Returns:
      invoke.Task: The task

    Raises:
      KeyError: Task not found
    """
    return _TASKS[location][name]


def package(location):
    """
    Find task package name

    Parameters:
        The package location to look up (builtin or local)

    Returns:
      str: The task package name
    """
    return _META["pkg"][location]


def task_paths(*location):
    """
    Find list of task package paths

    Parameters:
      *location:
        The package locations to look up (builtin or local)

    Yields:
      tuple: location, path
    """
    for loc in location:
        for item in _META["paths"][loc]:
            yield (loc, item)


def _execute_task(*args, **kwargs):  # pylint: disable = invalid-name
    """
    _execute_task(location, ctx, name, **kwargs)

    Execute a task like invoke does (including pre + post).

    All arguments have to be given via kwargs.

    Parameters:
      *args:
        List of (task-name, kwargs) tuples. If there's no kwargs for a task,
        the task-name only is sufficient. If there's only one task-name given,
        kwargs is applied to that task. Otherwise kwargs must be empty.

      **kwargs:
        Arguments if a single task is given

    Returns:
      dict: A dict mapping task objects to their return values (as returned
            from ``invoke.Exceutor().execute()``)
    """
    location, ctx, tasks = args[0], args[1], list(args[2:])
    if len(tasks) == 1 and isinstance(tasks[0], _util.basestring_):
        tasks = [(tasks[0], kwargs)]
    elif kwargs:
        raise AssertionError("Multiple tasks cannot share the same kwargs")

    for idx, task in enumerate(tasks):
        if isinstance(task, _util.basestring_):
            tasks[idx] = (task, {})

    return _invoke.Executor(_TASKS[location], ctx.config).execute(*tasks)


def execute(*args, **kwargs):  # pylint: disable = invalid-name
    """
    execute(ctx, name, **kwargs)

    Execute a task like invoke does (including pre + post).

    All arguments have to be given via kwargs.

    Parameters:
      *args:
        List of (task-name, kwargs) tuples. If there's no kwargs for a task,
        the task-name only is sufficient. If there's only one task-name given,
        kwargs is applied to that task. Otherwise kwargs must be empty.

      **kwargs:
        Arguments if a single task is given

    Returns:
      dict: A dict mapping task objects to their return values (as returned
            from ``invoke.Exceutor().execute()``)
    """
    return _execute_task(None, *args, **kwargs)


def builtin(*args, **kwargs):  # pylint: disable = invalid-name
    """
    builtin(ctx, name, **kwargs)

    Execute a builtin task like invoke does (including pre + post).

    All arguments have to be given via kwargs.

    Parameters:
      *args:
        List of (task-name, kwargs) tuples. If there's no kwargs for a task,
        the task-name only is sufficient. If there's only one task-name given,
        kwargs is applied to that task. Otherwise kwargs must be empty.

      **kwargs:
        Arguments if a single task is given

    Returns:
      dict: A dict mapping task objects to their return values (as returned
            from ``invoke.Exceutor().execute()``)
    """
    return _execute_task("builtin", *args, **kwargs)


def new_context():
    """
    Create a new context

    Typically only needed if a function is run "independent" from invoke.

    Returns:
      invoke.Context: The new context
    """
    config = _invoke.Config()
    collection_config = _TASKS[None].configuration()
    config.load_collection(collection_config)
    config.load_shell_env()
    return _invoke.context.Context(config)


def optional(collection, featureflag=None):
    """
    Decorator for optional task

    Parameters:
      collection (list):
        Collection to append the task name to if the task is enabled. Can be
        ``None`` if no collection is desired.

      featureflag (callable):
        Feature flag function. If it's not None, it's called without
        arguments. The return value is treated as a bool. If true, the task
        will be returned by the decorator and the task name will be added to
        the collection. Otherwise ``None`` will be returned.

        If featureflag is ``None``, the collection will be checked as a bool.
        If true the task will be returned, ``None`` otherwise.

    Returns:
      callable: inner function accepting the task and taking the decision.
    """

    def inner(func):
        """
        Inner proxy, taking the return decision

        Parameters:
          func (Task):
            The optional task

        Returns:
          callable: The task or ``None``
        """
        if featureflag is None:
            if collection:
                return func

        else:
            settings = _META["settings"]
            if settings is None:
                settings = _util.adict(_default_settings.default_settings())

            if featureflag(settings):
                if collection is not None:
                    collection.append(func.name)
                return func

        return None

    return inner


def setup_tasks(local, env):
    """
    Find available tasks (cached)

    Parameters:
      env (dict-like):
        The settings

    Returns:
      invoke.Collection: The tasks
    """
    # pylint: disable = too-many-locals
    # pylint: disable = too-many-branches

    if _META["loaded"]:
        return _TASKS[None]
    _META["settings"] = env

    torepair, default_tasks = [], _collections.defaultdict(list)
    locs = _collections.defaultdict(lambda: _collections.defaultdict(dict))
    pkg_paths = _collections.defaultdict(list)

    for pkg, path, location, modules in _task_modules(local):
        assert location in _TASKS
        pkg_paths[location].append(path)
        _META["pkg"][location] = pkg

        for module in modules:
            name = getattr(module, "NAMESPACE", None)
            if not name:
                name = module.__name__[len(pkg) + 1 :]  # noqa

            default_task = None
            for item in vars(module).values():
                if not isinstance(item, _invoke.Task):
                    continue

                if item.is_default:
                    default_task = item

                torepair.append((name, item))
                locs[None][name][item.name] = item
                locs[location][name][item.name] = item

            if default_task is not None:
                default_tasks[name].append(default_task)

    # If there's more than one default per namespace: last one wins
    for tasks in default_tasks.values():
        for task in tasks[:-1]:
            task.is_default = False

    _META["paths"].update(
        (key, tuple(value)) for key, value in pkg_paths.items()
    )
    for location, spaces in locs.items():
        collection = _invoke.Collection(
            **{
                name: _invoke.Collection(*tasks.values())
                for name, tasks in spaces.items()
            }
        )
        collection.configure(env)
        _TASKS[location] = collection

    # pre and post can be passed as string - map them here
    for name, task in torepair:
        for attr in ("pre", "post"):
            res = []
            for dep in getattr(task, attr):
                if not isinstance(dep, _util.basestring_):
                    res.append(dep)
                    continue

                if "." in dep:
                    depspace, dep = dep.rsplit(".", 1)
                else:
                    depspace = name
                res.append(_TASKS[None].collections[depspace][dep])
            setattr(task, attr, res)

    _META["loaded"] = True
    return _TASKS[None]


def _task_modules(local):
    """
    Find task modules to apply - in order

    Parameters:
      local (module):
        Local task package

    Yields:
      tuple: package name, path, location, list of modules
    """
    pkg = __name__.rsplit(".", 2)[0]
    if pkg != local.__name__:
        path = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
        yield (pkg, path, "builtin", list(_find_modules(path, pkg)))

    pkg = local.__name__
    for path in reversed(local.__path__):
        yield pkg, path, "local", list(_find_modules(path, pkg))


def _find_modules(path, pkg):
    """
    Find modules with tasks

    Parameters:
      path (str):
        Path to scan recursively

      pkg (str):
        Package name the path represents

    Returns:
      iterable: Modules found
    """
    init = "__init__.py"

    for filename in _find_python_files(path):
        dirname, basename = _os.path.split(filename)

        # import module/package and yield if there are any tasks
        modname = filename[:-3] if basename != init else dirname
        modname = ".".join(_shell.pathparts(modname))
        qname = "%s.%s" % (pkg, modname)

        module = _importlib.import_module(qname)
        for item in vars(module).values():
            if isinstance(item, _invoke.Task):
                yield module
                break


def _find_python_files(base):
    """
    Find python files in path

    Parameters:
      base (str):
        The path to scan recursively

    Yields:
      valid python file, relative to base (reachable via import)
    """
    is_valid_file = _re.compile(r"^[a-zA-Z_]+[a-zA-Z0-9_]*\.py$").match
    is_valid_dir = _re.compile(r"^[a-zA-Z_]+[a-zA-Z0-9_]*$").match
    init = "__init__.py"

    for dirpath, dirnames, filenames in _os.walk(_shell.native(base)):
        dirnames[:] = sorted(
            item
            for item in dirnames
            if (
                is_valid_dir(item)
                and _os.path.exists(_os.path.join(dirpath, item, init))
            )
        )
        filenames = sorted(item for item in filenames if is_valid_file(item))
        for name in filenames:
            dest = _os.path.relpath(_os.path.join(dirpath, name), base)

            # Skip root __init__.py
            if dest != init:
                yield "/".join(_shell.pathparts(dest))

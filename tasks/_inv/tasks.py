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
Task management
~~~~~~~~~~~~~~~

"""
__all__ = ["by_name", "execute", "exists", "new_context"]

import collections as _collections
import importlib as _importlib
import os as _os
import re as _re

import invoke as _invoke

from . import shell as _shell
from . import util as _util

_TASKS = None
_SETTINGS = None


def exists(name):
    """
    Check if a task exists

    Parameters:
      name (str):
        The fully qualified task name

    Returns:
      bool: Does the task exist?
    """
    assert _TASKS is not None

    return name in _TASKS


def by_name(name):
    """
    Find task by name

    Parameters:
      name (str):
        The fully qualified task name

    Returns:
      invoke.Task: The task

    Raises:
      KeyError: Task not found
    """
    assert _TASKS is not None

    return _TASKS[name]


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
    assert _TASKS is not None

    ctx, tasks = args[0], list(args[1:])
    if len(tasks) == 1 and isinstance(tasks[0], _util.basestring_):
        tasks = [(tasks[0], kwargs)]
    elif kwargs:
        raise AssertionError("Multiple tasks cannot share the same kwargs")

    for idx, task in enumerate(tasks):
        if isinstance(task, _util.basestring_):
            tasks[idx] = (task, {})

    return _invoke.Executor(_TASKS, ctx.config).execute(*tasks)


def new_context():
    """
    Create a new context

    Typically only needed if a function is run "independent" from invoke.

    Returns:
      invoke.Context: The new context
    """
    assert _TASKS is not None

    config = _invoke.Config()
    collection_config = _TASKS.configuration()
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

        elif featureflag(_SETTINGS):
            if collection is not None:
                collection.append(func.name)
            return func

        return None

    return inner


def setup_tasks(env):
    """
    Find available tasks (cached)

    Parameters:
      env (dict-like):
        The settings

    Returns:
      invoke.Collection: The tasks
    """
    global _SETTINGS, _TASKS  # pylint: disable = global-statement
    if _TASKS is not None:
        return _TASKS
    _SETTINGS = env

    path = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    pkg = _os.path.basename(path)
    torepair, space = [], _collections.defaultdict(dict)

    for module in _find_modules():
        name = getattr(module, "NAMESPACE", None)
        if not name:
            name = module.__name__[len(pkg) + 1 :]  # noqa

        for item in vars(module).values():
            if not isinstance(item, _invoke.Task):
                continue

            torepair.append((name, item))
            space[name][item.name] = item

    result = _invoke.Collection(
        **{
            name: _invoke.Collection(*tasks.values())
            for name, tasks in space.items()
        }
    )
    result.configure(env)

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
                res.append(space[depspace][dep])
            setattr(task, attr, res)

    _TASKS = result
    return result


def _find_modules():
    """
    Find modules with tasks

    Returns:
      iterable: Modules found
    """
    path, prune = _os.path.split(_os.path.dirname(_os.path.abspath(__file__)))
    pkg = _os.path.basename(path)
    pkg_path = pkg + "/"

    is_valid_file = _re.compile(r"^[a-zA-Z_]+[a-zA-Z0-9_]*\.py$").match
    is_valid_dir = _re.compile(r"^[a-zA-Z_]+[a-zA-Z0-9_]*$").match
    init = "__init__.py"

    for filename in _shell.files(path, "[!.]*.py", prune=[prune]):
        assert filename.startswith(pkg_path)
        filename = filename[len(pkg_path) :]  # noqa
        dirname, basename = _os.path.split(filename)
        odirname = dirname

        # Skip root __init__.py or non-id names
        if filename == init or not is_valid_file(basename):
            continue

        # Check all sub-path parts if any
        while dirname:
            if not is_valid_dir(_os.path.basename(dirname)):
                break
            dirname = _os.path.dirname(dirname)
            if not _os.path.exists(_os.path.join(path, dirname, init)):
                break

        # import module/package and yield if there are any tasks
        else:
            modname = filename[:-3] if basename != init else odirname
            modname = ".".join(_shell.pathparts(modname))
            qname = "%s.%s" % (pkg, modname)

            module = _importlib.import_module(qname)
            for item in vars(module).values():
                if isinstance(item, _invoke.Task):
                    yield module
                    break

# -*- coding: ascii -*-
u"""
:Copyright:

 Copyright 2014 - 2024
 Andr\xe9 Malo or his licensors, as applicable

:License:

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.

================
 Test Utilities
================

Test utilities.
"""
__author__ = u"Andr\xe9 Malo"

import contextlib as _contextlib
import sys as _sys
import types as _types

from pytest import skip  # noqa pylint: disable = unused-import

try:
    import mock
except ImportError:
    from unittest import mock

try:
    reload  # pylint: disable = used-before-assignment
except NameError:
    # pylint: disable = redefined-builtin
    try:
        from importlib import reload
    except ImportError:
        from imp import reload  # noqa pylint: disable = deprecated-module

_unset = type("_unset", (object,), {})()  # pylint: disable=invalid-name


# pylint: disable = useless-object-inheritance


class Bunch(object):
    """Bunch object"""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@_contextlib.contextmanager
def patched_import(what, how=_unset):
    """
    Context manager to mock an import statement temporarily

    :Parameters:
      `what` : ``str``
        Name of the module to mock

      `how` : any
        How should it be replaced? If omitted or `unset`, a new MagicMock
        instance is created. The result is yielded as context.
    """
    # basically stolen from opensource.perlig.de/tdi/

    class_types = (type,)
    if str is bytes:
        # pylint: disable = no-member
        class_types += (_types.ClassType,)

    # pylint: disable = unnecessary-lambda-assignment
    _is_exc = lambda obj: isinstance(obj, BaseException) or (
        isinstance(obj, (type, class_types))
        and issubclass(obj, BaseException)
    )

    class FinderLoader(object):
        """Finder / Loader for meta path"""

        def __init__(self, fullname, module):
            self.module = module
            self.name = fullname
            extra = "%s." % fullname
            for key in list(_sys.modules):
                if key.startswith(extra):
                    del _sys.modules[key]
            if fullname in _sys.modules:
                del _sys.modules[fullname]

        def find_spec(self, name, path=None, target=None):
            """Find spec (Python 3.10+)"""
            # pylint: disable = unused-argument
            if name != self.name:
                return None

            from importlib import util

            return util.spec_from_loader(name, self)

        def find_module(self, fullname, path=None):
            """Find the module"""
            # pylint: disable = unused-argument
            if fullname == self.name:
                return self
            return None

        def load_module(self, fullname):
            """Load the module"""
            if _is_exc(self.module):
                raise self.module
            _sys.modules[fullname] = self.module
            return self.module

        def create_module(self, spec):
            """Create module"""
            if _is_exc(self.module):
                raise self.module
            return self.module

        def exec_module(self, module):
            """Execute module"""

    realmodules = _sys.modules.copy()
    try:
        obj = FinderLoader(what, mock.MagicMock() if how is _unset else how)
        realpath = _sys.meta_path[:]
        try:
            _sys.meta_path[:] = [obj] + realpath
            old, parts = _unset, what.rsplit(".", 1)
            if len(parts) == 2:
                parent, base = parts[0], parts[1]
                if parent in _sys.modules:
                    parent = _sys.modules[parent]
                    if hasattr(parent, base):
                        old = getattr(parent, base)
                        setattr(parent, base, obj.module)
            try:
                yield obj.module
            finally:
                if old is not _unset:
                    setattr(parent, base, old)
        finally:
            _sys.meta_path[:] = realpath
    finally:
        _sys.modules.clear()
        _sys.modules.update(realmodules)


def uni(value):
    """
    Create unicode from raw string with unicode escapes

    :Parameters:
      `value` : ``str``
        String, which encodes to ascii and decodes as unicode_escape

    :Return: The decoded string
    :Rtype: ``unicode``
    """
    return value.encode('ascii').decode('unicode_escape')


class badstr(object):  # pylint: disable = invalid-name
    """bad string"""

    def __str__(self):
        raise RuntimeError("yo")


badstr = badstr()


class badbytes(object):  # pylint: disable = invalid-name
    """bad bytes"""

    def __bytes__(self):
        raise RuntimeError("yoyo")

    if str is bytes:
        __str__ = __bytes__


badbytes = badbytes()


class badbool(object):  # pylint: disable = invalid-name
    """bad bool"""

    def __bool__(self):
        raise RuntimeError("yoyo")

    if str is bytes:
        __nonzero__ = __bool__


badbool = badbool()


class baditer(object):  # pylint: disable = invalid-name
    """bad iter"""

    def __init__(self, *what):
        self._what = iter(what)

    def __iter__(self):
        return self

    def __next__(self):
        for item in self._what:
            if isinstance(item, Exception):
                raise item
            return item

    next = __next__

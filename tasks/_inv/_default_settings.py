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
Default settings
~~~~~~~~~~~~~~~~

"""

import sys as _sys

import invoke as _invoke

from . import shell as _shell
from . import util as _util

# pylint: disable = import-outside-toplevel


def fail(msg):
    """
    Exit with message

    Parameters:
      msg (str):
        The fail message

    Raises:
      invoke.Exit: Always raised
    """
    _sys.stderr.write("Error: %s\n" % (msg,))
    raise _invoke.Exit(code=1)


def which(executable):
    """
    Find executable - or fail

    Parameters:
      executable (str):
        The executable to look out for

    Returns:
      str: The full path

    Raises:
      invoke.Exit: If the executable was not found
    """
    found = _shell.frompath(executable)
    if not found:
        fail("%s not found" % (executable,))
    return found


def find_user():
    """
    Find system user

    Returns:
      str: The user's login name or ``None``
    """
    import getpass as _getpass

    try:
        return _getpass.getuser()
    except Exception:  # pylint: disable = broad-exception-caught
        return None


def default_settings():
    """
    Create default settings

    Returns:
      dict: Default settings
    """
    return dict(
        test=_util.adict(ignore=[]),
        shell=_util.adict(
            (key, value)
            for key, value in vars(_shell).items()
            if not key.startswith("_")
        ),
        c=_shell.command,
        q=lambda x: _shell.command("%s", x),
        s=_shell.split_command,
        fail=fail,
        which=which,
        user=find_user(),
        doc=_util.adict(
            userdoc="docs/userdoc",
            website=_util.adict(
                source="docs/website",
                target="dist/website",
            ),
            sphinx=_util.adict(
                want_apidoc=True,
                build="docs/_userdoc/_build",
                source="docs/_userdoc",
            ),
        ),
        pypi=_util.adict(
            # repository='https://test.pypi.org/legacy/',
            repository="https://upload.pypi.org/legacy/",
            username="__token__",
        ),
        paths=_util.adict(),
    )

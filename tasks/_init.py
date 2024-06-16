# -*- encoding: ascii -*-
"""
Setup invoke namespace
~~~~~~~~~~~~~~~~~~~~~~

"""

import os as _os
import sys as _sys

import invoke as _invoke

from . import _shell
from ._util import adict

try:
    from . import _settings
except ImportError:
    _settings = None


class Modules:
    """
    Submodules container

    All modules containing tasks need to be here.
    """

    # pylint: disable = import-outside-toplevel

    from . import (
        benchmark,
        build,
        check,
        clean,
        compile,
        deps,
        doc,
        format,
        test,
        upload,
    )


def fail(msg):
    """Exit with message"""
    _sys.stderr.write("Error: %s\n" % (msg,))
    raise _invoke.Exit(1)


def which(executable):
    """Find executable - or fail"""
    found = _shell.frompath(executable)
    if not found:
        fail("%s not found" % (executable,))
    return found


def namespace():
    """Create invoke task namespace"""
    settings = {} if _settings is None else _settings.settings

    env = dict(
        test=adict(ignore=[]),
        shell=adict(
            (key, value)
            for key, value in vars(_shell).items()
            if not key.startswith("_")
        ),
        c=_shell.command,
        q=lambda x: _shell.command("%s", x),
        fail=fail,
        which=which,
        doc=adict(
            userdoc="docs/userdoc",
            website=adict(
                source="docs/website",
                target="dist/website",
            ),
            sphinx=adict(
                build='docs/_userdoc/_build',
                source='docs/_userdoc',
            ),
        ),
        pypi=adict(
            # repository='https://test.pypi.org/legacy/',
            repository='https://upload.pypi.org/legacy/',
            username='__token__',
        ),
    )
    env.update(settings)

    _sys.path.insert(
        0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
    )

    result = _invoke.Collection(
        *[
            value
            for key, value in vars(Modules).items()
            if not key.startswith("__")
        ]
    )
    result.configure(adict(env))
    return result

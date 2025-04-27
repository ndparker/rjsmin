# -*- coding: ascii -*-
#
# Copyright 2007 - 2025
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
Build Tasks
~~~~~~~~~~~

"""

import os as _os

try:
    import build as _build
except ImportError:
    _build = None

import invoke as _invoke

from .._inv import tasks as _tasks
from . import _pkg_dir

# pylint: disable = import-outside-toplevel

NAMESPACE = "build"


@_invoke.task(default=True)
def source(ctx):
    """Build source package"""
    if source.avoid_rerun:
        return

    if _tasks.exists("doc.doc"):
        _tasks.execute(ctx, "doc.doc")

    with ctx.shell.root_dir():
        if not _os.path.isdir("setups"):
            _build_sdist(ctx)
            source.avoid_rerun = True
            return

    _source_multi(ctx)
    source.avoid_rerun = True


source.avoid_rerun = False


def _source_multi(ctx):
    """Build multiple source packages"""
    with ctx.shell.root_dir():
        ctx.shell.mkdir_p("dist")

        # Collect names
        names = sorted(
            set(
                name.rsplit(".", 1)[0]
                for name in _os.listdir("setups")
                if not name.startswith(".")
                and name.endswith((".py", ".toml"))
            )
        )

        # Build each package from a copy
        for name in names:
            with _pkg_dir.sdist(ctx, name) as pkg_root:
                _build_sdist(ctx)
                for archive in _os.listdir("dist"):
                    ctx.shell.cp(
                        _os.path.join(pkg_root, "dist", archive),
                        _os.path.join(ctx.shell.root, "dist", archive),
                    )


def _build_sdist(ctx):
    """Build single sdist in the CWD"""
    if ctx.get("wheels", {}).get("build") == "universal":
        with open("setup.cfg", "wb") as fp:
            fp.write(b"[bdist_wheel]\n")
            fp.write(b"universal = 1\n")

    if _build is None:
        ctx.run("python setup.py sdist")
    else:
        ctx.run("python -m build --sdist")

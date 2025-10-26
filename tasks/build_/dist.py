# -*- coding: ascii -*-
#
# Copyright 2007 - 2026
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

import invoke as _invoke

from . import _dist
from . import _release
from . import _version

NAMESPACE = "build"


@_invoke.task("doc.doc")
def dist(ctx):
    """Build distribution"""
    fakeroot = ctx.shell.frompath("fakeroot")
    with ctx.shell.root_dir():
        ctx.shell.rm_rf("build", "dist")
        ctx.run(
            ctx.c("%s python setup.py sdist --formats tar,zip", fakeroot),
            echo=True,
        )

        files = list(ctx.shell.files("dist", "*.zip"))
        digestname = files[0][:-3] + "digests"
        for name in ctx.shell.files("dist", "*.tar"):
            files.append(_dist.compress(ctx, name, "gzip", ".gz"))
            files.append(_dist.compress(ctx, name, "bzip2", ".bz2"))
            files.append(_dist.compress(ctx, name, "xz", ".xz"))
            ctx.shell.rm(name)
        files = [name for name in files if name]

        _dist.digest(ctx, files, digestname)
        _dist.copy_changes(ctx)


@_invoke.task()
def version(ctx):
    """Version"""
    with ctx.shell.root_dir():
        _version.update(ctx)


@_invoke.task("doc.doc")
def release(ctx):
    """Release"""
    with ctx.shell.root_dir():
        _release.check_committed(ctx)
        version(ctx)
        _release.add_tag(ctx)

    # _doc.doc(ctx)  # dependencies are not called, hence put as regular
    # dep here
    dist(ctx)

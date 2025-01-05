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
Documentation Tasks
~~~~~~~~~~~~~~~~~~~

"""

import os as _os

import invoke as _invoke

from .. import _features
from .._inv import tasks as _tasks
from . import _sphinx

NAMESPACE = "doc"


@_tasks.optional(None, _features.sphinx)
@_invoke.task()
def userdoc(ctx):
    """Create userdocs"""
    if _tasks.exists("compile.compile"):
        _tasks.execute(ctx, "compile.compile")

    _sphinx.run(
        ctx, ctx.doc.sphinx.build, ctx.doc.sphinx.source, ctx.doc.userdoc
    )


@_tasks.optional(None, _features.sphinx)
@_invoke.task(userdoc, default=True)
def doc(ctx):  # pylint: disable = unused-argument
    """Create docs"""


@_tasks.optional(None, _features.sphinx)
@_invoke.task()
def website(ctx):
    """Create website"""
    ctx.shell.rm_rf(ctx.doc.website.source)
    ctx.shell.cp_r(
        ctx.doc.sphinx.source, _os.path.join(ctx.doc.website.source, "src")
    )
    ctx.shell.rm_rf(ctx.doc.website.target)
    ctx.shell.mkdir_p(ctx.doc.website.target)

    dlfile = _os.path.join(
        ctx.doc.website.source, "src", "website_download.txt"
    )
    with open(dlfile, "rb") as fp:
        download = fp.read().decode("latin-1")

    ixfile = _os.path.join(ctx.doc.website.source, "src", "index.txt")
    with open(ixfile, "rb") as fp:
        index = fp.read().decode("latin-1").splitlines(True)

    with open(ixfile, "wb") as fp:
        for line in index:
            if line.startswith(".. placeholder: Download"):
                line = download
            fp.write(line.encode("latin-1"))

    _sphinx.run(
        ctx,
        ctx.shell.native(_os.path.join(ctx.doc.website.source, "build")),
        ctx.shell.native(_os.path.join(ctx.doc.website.source, "src")),
        ctx.shell.native(ctx.doc.website.target),
    )
    ctx.shell.rm(_os.path.join(ctx.doc.website.target, ".buildinfo"))

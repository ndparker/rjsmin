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
Cleanup tasks
~~~~~~~~~~~~~

"""

import invoke as _invoke

from ._inv import tasks as _tasks


@_invoke.task()
def py(ctx):
    """Wipe *.py[co] files"""
    ctx.shell.rm_rf(ctx.shell.glob("**/__pycache__/", "**/*.py[co]"))


@_invoke.task(py)
def dist(ctx):
    """Wipe all"""
    _tasks.execute(ctx, "clean.clean", so=True, cache=True)


@_invoke.task(py, default=True)
def clean(ctx, so=False, cache=False):
    """
    Wipe *.py[co] files and test leftovers

    Parameters:
      so (bool):
        Clean *.so files, too? Default: false

      cache (bool):
        Clean various cache files and directories, too? Default: false
    """
    ctx.shell.rm(ctx.shell.files(".", ".coverage*"))
    path = ctx.paths.get("terraform")
    if path:
        gpath = ctx.shell.glob_escape(path.rstrip("/")) + "/**/"
        ctx.shell.rm_rf(ctx.shell.glob(gpath + "*.auto.tfvars.json"))
        ctx.shell.rm_rf(ctx.shell.glob(gpath + "*.tf.json"))

    ctx.shell.rm_rf(
        "gcov.out",
        "setup.cfg",
        "docs/coverage/",
        "docs/gcov/",
        "build/",
        "dist/",
        "wheel/dist/",
        ctx.doc.userdoc,
        ctx.doc.sphinx.build,
        ctx.doc.website.source,
        ctx.doc.website.target,
    )
    more = ctx.get("clean", {}).get("default", [])
    for glob in more:
        ctx.shell.rm_rf(ctx.shell.glob(glob))

    if cache:
        _tasks.execute(ctx, "clean.cache")
    if so:
        _tasks.execute(ctx, "clean.so")


@_invoke.task(name="cache")
def cacheclean(ctx):
    """Wipe Cache files"""
    path = ctx.paths.get("terraform")
    if path:
        gpath = ctx.shell.glob_escape(path.rstrip("/")) + "/**/"
        ctx.shell.rm_rf(ctx.shell.glob(gpath + ".terraform/"))
        ctx.shell.rm_rf(ctx.shell.glob(gpath + ".terraform.lock.hcl"))

    ctx.shell.rm_rf(
        ".tox/",
        ".cache/",
        ".pytest_cache/",
        "tests/.cache/",
        "tests/.pytest_cache/",
        ".mypy_cache/",
    )
    more = ctx.get("clean", {}).get("cache", [])
    for glob in more:
        ctx.shell.rm_rf(ctx.shell.glob(glob))


@_invoke.task(name="so")
def soclean(ctx):
    """Wipe *.so files"""
    ctx.shell.rm(ctx.shell.glob("**/*.pyd", "**/*.so"))

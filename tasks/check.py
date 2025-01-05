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
Run code checkers
~~~~~~~~~~~~~~~~~

"""

import os as _os

import invoke as _invoke

from . import _features
from ._inv import tasks as _tasks

_CHECKERS = []
_CHECKERS_TF = []
_CHECKERS_SAM = []


@_tasks.optional(_CHECKERS, _features.pylint)
@_invoke.task("clean.py")
def lint(ctx):
    """Run pylint"""
    cmd = [ctx.which("pylint")] + ctx.s("--rcfile pylintrc") + [ctx.package]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_tasks.optional(_CHECKERS, _features.flake8)
@_invoke.task("clean.py")
def flake8(ctx):
    """Run flake8"""
    if _os.path.exists(ctx.shell.native(ctx.package + ".py")):
        candidate = ctx.package + ".py"
    else:
        candidate = ctx.package

    cmd = [ctx.which("flake8"), candidate]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_tasks.optional(_CHECKERS, _features.black)
@_invoke.task("clean.py")
def black(ctx):
    """Run black"""
    cmd = [ctx.which("black")] + ctx.s("--check --config pyproject.toml .")

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_tasks.optional(_CHECKERS_TF, _features.terraform)
@_invoke.task()
def tf_fmt(ctx):
    """Run terraform fmt -check"""
    base_cmd = [ctx.which("terraform"), "-chdir=" + ctx.paths.terraform]
    with ctx.shell.root_dir():
        ctx.run(ctx.c(base_cmd + ctx.s("fmt -recursive -check")), echo=True)


@_tasks.optional(_CHECKERS_TF, _features.terraform)
@_invoke.task()
def tf_validate(ctx):
    """Run terraform validate"""
    base_cmd = [ctx.which("terraform"), "-chdir=" + ctx.paths.terraform]
    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(base_cmd + ctx.s("init -backend=false")),
            hide=True,
            echo=True,
        )
        ctx.run(ctx.c(base_cmd + ctx.s("validate")), echo=True)


@_tasks.optional(_CHECKERS_SAM, _features.sam)
@_invoke.task()
def sam_validate(ctx):
    """Run sam validate"""
    cmd = (
        [ctx.which("sam")]
        + ctx.s("validate --lint -t")
        + [ctx.cloudformation.template]
    )
    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


# Collections of checks
# =====================


@_tasks.optional(_CHECKERS_TF)
@_invoke.task(name="tf")
def terraform(ctx):
    """Run terraform checks"""
    _tasks.execute(ctx, *["check." + checker for checker in _CHECKERS_TF])


@_tasks.optional(_CHECKERS_SAM)
@_invoke.task()
def sam(ctx):
    """Run sam checks"""
    _tasks.execute(ctx, *["check." + checker for checker in _CHECKERS_SAM])


_CHECKERS += _CHECKERS_TF
_CHECKERS += _CHECKERS_SAM


@_tasks.optional(_CHECKERS)
@_invoke.task(name="all", default=True)
def all_(ctx):
    """Run all checkers"""
    _tasks.execute(ctx, *["check." + checker for checker in _CHECKERS])

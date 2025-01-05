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
Run code formatters
~~~~~~~~~~~~~~~~~~~

"""

import invoke as _invoke

from . import _features
from ._inv import tasks as _tasks

_FORMATTERS = []


@_tasks.optional(_FORMATTERS, _features.black)
@_invoke.task()
def black(ctx, diff=False):
    """
    Format python code using Black formatter

    Parameters:
      diff (bool):
        Just emit a diff instead of changing files inline? Default: false
    """
    cmd = [ctx.which("black")]
    if diff:
        cmd += ctx.s("--diff --color")
    cmd += ctx.s("--config pyproject.toml .")

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_tasks.optional(_FORMATTERS, _features.terraform)
@_invoke.task(name="tf")
def terraform(ctx):
    """Format terraform code"""
    base_cmd = [ctx.which("terraform"), "-chdir=" + ctx.paths.terraform]
    with ctx.shell.root_dir():
        ctx.run(ctx.c(base_cmd + ctx.s("fmt -recursive")), echo=True)


@_tasks.optional(_FORMATTERS)
@_invoke.task(name="all", default=True)
def all_(ctx):
    """Run all formatters"""
    _tasks.execute(ctx, *["format." + formatter for formatter in _FORMATTERS])

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
Dependency Management Tasks
~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import os as _os

import invoke as _invoke

NAMESPACE = "deps"


@_invoke.task()
def old(ctx):
    """List outdated python packages"""
    with ctx.shell.root_dir():
        ctx.run("pip list -o", echo=True)


@_invoke.task()
def package(ctx, upgrade=False):
    """
    Update python dependencies, excluding development (``-e .``)

    Parameters:
      upgrade (bool):
        Run pip install with ``-U`` flag?
    """
    cmd = ["pip", "install"]
    if upgrade:
        cmd += ["-U"]
    cmd += ["-e", "."]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_invoke.task(default=True)
def dev(ctx, upgrade=False):
    """
    Update python dependencies, including development (``-r development.txt``)

    Parameters:
      upgrade (bool):
        Run pip install with ``-U`` flag?
    """
    cmd = ["pip", "install"]
    if upgrade:
        cmd += ["-U"]
    cmd += ["-r", "development.txt"]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_invoke.task()
def reset(ctx, upgrade=False):
    """
    Reset your virtual env

    This command uninstalls everything except editable installs and reinstalls
    from scratch (``-r development.txt``)

    Parameters:
      upgrade (bool):
        Run pip install with ``-U`` flag?
    """
    cmd = [ctx.which("bash"), "-il", "%s/reset.sh"]
    if upgrade:
        cmd += ["-u"]
    cmd += ["."]
    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(cmd, ctx.shell.native(_os.path.dirname(__file__))),
            pty=True,
        )

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
Release code
~~~~~~~~~~~~

"""

import re as _re


def check_committed(ctx):
    """Check if everything is committed"""
    git = ctx.shell.frompath("git")
    lines = ctx.run(
        ctx.c("%s branch --color=never", git), env=dict(LC_ALL="C"), hide=True
    ).stdout.splitlines()
    for line in lines:
        if line.startswith("*"):
            branch = line.split(None, 1)[1]
            break
    else:
        ctx.fail("Could not determine current branch.")

    if branch != "master":
        rex = _re.compile(r"^\d+(?:\.\d+)*\.[xX]$").match
        match = rex(branch)
        if not match:
            ctx.fail("Not in master or release branch.")

    lines = ctx.run(
        ctx.c("%s status --porcelain", git), env=dict(LC_ALL="C"), hide=True
    ).stdout
    if lines:
        ctx.fail("Uncommitted changes!")


def add_tag(ctx):
    """Add release tag"""
    version = ctx.run("python setup.py --version", hide=True).stdout.strip()
    git = ctx.shell.frompath("git")

    ctx.run(
        ctx.c(
            """
        %s tag -a -m "Release version %s" -- %s
    """,
            git,
            version,
            version,
        ),
        echo=True,
    )

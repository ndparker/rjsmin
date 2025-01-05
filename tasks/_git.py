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
Git commands
~~~~~~~~~~~~

"""


def current_branch(ctx):
    """
    Find the current branch

    Returns:
      str: The current branch or None
    """
    return (
        command(
            ctx, ctx.s("branch --color=never --show-current"), hide=True
        ).stdout.strip()
        or None
    )


def command(ctx, cmd, **kwargs):
    """
    Run git command

    Parameters:
      cmd (list):
        The command to run

      **kwargs:
        Extra arguments for ctx.run()

    Returns:
      The run result
    """
    env = dict(LC_ALL="C")
    cmd = [ctx.which("git")] + cmd
    with ctx.shell.root_dir():
        return ctx.run(ctx.c(cmd), env=env, **kwargs)

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
Upload packages
~~~~~~~~~~~~~~~

"""

import invoke as _invoke


@_invoke.task(default=True)
def source(ctx):
    """Upload source package"""
    files = list(ctx.shell.files("dist", "*.tar.gz"))
    if len(files) != 1:
        ctx.fail("Not exactly one tarball found")

    cmd = "twine upload --repository-url %s --username %s %s"
    args = [ctx.pypi.repository, ctx.pypi.username, files[0]]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd, *args), echo=True)


@_invoke.task()
def wheels(ctx):
    """Upload wheels"""
    files = list(ctx.shell.files("wheel/dist", "*.whl"))
    if not files:
        ctx.fail("No wheel found")

    cmd = (
        ctx.s("twine upload --repository-url")
        + [ctx.pypi.repository, "--username", ctx.pypi.username]
        + files
    )
    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)

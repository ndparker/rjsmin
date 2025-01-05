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
Doc Tasks
~~~~~~~~~

"""

import os as _os


def run(ctx, build, source, target):
    """
    Run sphinx

    Parameters:
      build (str):
        Build directory

      source (str):
        Source directory

      target (str):
        Target directory
    """
    want_apidoc = ctx.doc.sphinx.want_apidoc
    if want_apidoc:
        apidoc = ctx.which("sphinx-apidoc")
    sphinx = ctx.which("sphinx-build")

    with ctx.shell.root_dir():
        if want_apidoc:
            cmd = (
                [apidoc]
                + ctx.s("-f --private -stxt -e -o")
                + ["%s/apidoc" % (source,), ctx.package]
            )
            ctx.run(
                ctx.c(cmd),
                env=dict(
                    _os.environ,
                    SPHINX_APIDOC_OPTIONS=",".join(
                        ["members", "undoc-members", "special-members"]
                    ),
                ),
                echo=True,
            )

        cmd = (
            [sphinx]
            + ctx.s("-a -d")
            + [_os.path.join(build, "doctrees")]
            + ctx.s("-b html")
            + [source, target]
        )
        ctx.run(ctx.c(cmd), echo=True)

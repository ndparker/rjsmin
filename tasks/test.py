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
Test suite tasks
~~~~~~~~~~~~~~~~

"""

import invoke as _invoke

from . import _features
from ._inv import tasks as _tasks


@_tasks.optional(None, _features.python_tests)
@_invoke.task()
def local(
    ctx,
    new_first=False,
    failed_first=False,
    keep_going=False,
    capture=False,
    coverage=False,
    coverage_report=True,
    only=None,
):
    """
    Run the unit test suite using py.test

    Parameters:
      new_first (bool):
        Run tests from new files first. Default: false

      failed_first (bool):
        Run all tests, but run the last failures first. Default: false

      keep_going (bool):
        Keep going after a failure? Default: false

      capture (bool):
        Capture output? Default: false

      coverage (bool):
        Measure test coverage? Default: false

      coverage_report (bool):
        Emit coverage report? Only relevant if coverage is enabled.
        Default: true

      only (str):
        Filter expression for tests to run
    """
    # pylint: disable = too-many-positional-arguments

    cmd = [ctx.which("py.test")] + ctx.s(
        "-vv --color=yes --doctest-modules --doctest-ignore-import-errors"
    )
    if new_first:
        cmd += ["--nf"]
    if failed_first:
        cmd += ["--ff"]
    if not keep_going:
        cmd += ["--exitfirst"]
    if not capture:
        cmd += ["-s"]
    if coverage:
        cmd += ["--no-cov-on-fail", "--cov", ctx.package]
        if coverage_report:
            cmd += ["--cov-report=html", "--cov-report=term"]
        else:
            cmd += ["--cov-report="]
    if only:
        cmd += ["-k", only]

    for ignored in ctx.test.ignore:
        cmd += ["--ignore", ignored]

    cmd += ["tests"]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)


@_tasks.optional(None, _features.tox_tests)
@_invoke.task(default=True)
def tox(ctx, rebuild=False, env=None, hashseed=None):
    """
    Run the test suite using tox

    Parameters:
      rebuild (bool):
        Rebuild tox environment(s)? Default: false

      env (str):
        A single test environment to run. All environments are run otherwise.

      hashseed (str):
        The hashseed to use. Only specify as a debugging measure.
    """
    cmd = [ctx.which("tox")]
    if rebuild:
        cmd += ["-r"]
    if env is not None:
        cmd += ["-e", env]
    if hashseed is not None:
        cmd += ["--hashseed", hashseed]

    with ctx.shell.root_dir():
        ctx.run(ctx.c(cmd), echo=True)

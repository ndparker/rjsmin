# -*- encoding: ascii -*-
"""
Test suite tasks
~~~~~~~~~~~~~~~~

"""

import os as _os

import invoke as _invoke


@_invoke.task()
def local(ctx):
    """Run the unit test suite using py.test"""
    with ctx.shell.root_dir():
        command = r"""
            %s -c test.ini -vv -s
            --doctest-modules
            --color=yes
            --exitfirst
        """
        args = [ctx.which("py.test")]

        for ignored in ctx.test.ignore:
            command += " --ignore %s"
            args.append(ignored)

        command += " %s"
        args.append("tests")

        ctx.run(ctx.c(command, *args), echo=True)


@_invoke.task(default=True)
def tox(ctx, rebuild=False, env=None):
    """Run the test suite using tox"""
    command = r""" %s -c test.ini """
    args = [ctx.which("tox")]
    if rebuild:
        command += " -r"
    if env is not None:
        command += " -e %s"
        args.append(env)

    with ctx.shell.root_dir():
        ctx.run(ctx.c(command, *args), echo=True)

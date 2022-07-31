# -*- encoding: ascii -*-
"""
Checking tasks
~~~~~~~~~~~~~~

"""

import invoke as _invoke

from . import clean as _clean


@_invoke.task(_clean.py)
def lint(ctx):
    """ Run pylint """
    pylint = ctx.shell.frompath('pylint')
    if pylint is None:
        raise RuntimeError("pylint not found")

    with ctx.shell.root_dir():
        ctx.run(ctx.c(
            r''' %(pylint)s --rcfile pylintrc %(package)s ''',
            pylint=pylint,
            package=ctx.package
        ), echo=True)


@_invoke.task(_clean.py)
def flake8(ctx):
    """ Run flake8 """
    exe = ctx.shell.frompath('flake8')
    if exe is None:
        raise RuntimeError("flake8 not found")

    with ctx.shell.root_dir():
        ctx.run(ctx.c(
            r''' %(flake8)s %(package)s.py ''',
            flake8=exe,
            package=ctx.package
        ), echo=True)


@_invoke.task(lint, flake8, default=True)
def all(ctx):  # pylint: disable = redefined-builtin, unused-argument
    """ Run all """

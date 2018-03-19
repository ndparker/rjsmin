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
    flake8 = ctx.shell.frompath('flake8')
    if flake8 is None:
        raise RuntimeError("flake8 not found")

    with ctx.shell.root_dir():
        ctx.run(ctx.c(
            r''' %(flake8)s %(package)s ''',
            flake8=flake8,
            package=ctx.package
        ), echo=True)


@_invoke.task(lint, flake8, default=True)
def all(ctx):
    """ Run all """

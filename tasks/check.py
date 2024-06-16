# -*- encoding: ascii -*-
"""
Checking tasks
~~~~~~~~~~~~~~

"""

import invoke as _invoke

from . import clean as _clean


@_invoke.task(_clean.py)
def lint(ctx):
    """Run pylint"""
    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(
                "%(pylint)s --rcfile pylintrc %(package)s",
                pylint=ctx.which("pylint"),
                package=ctx.package,
            ),
            echo=True,
        )


@_invoke.task(_clean.py)
def flake8(ctx):
    """Run flake8"""
    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(
                "%(flake8)s %(package)s.py",
                flake8=ctx.which("flake8"),
                package=ctx.package,
            ),
            echo=True,
        )


@_invoke.task(_clean.py)
def black(ctx):
    """Run black"""
    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(
                "%(black)s --check --config black.toml .",
                black=ctx.which("black"),
            ),
            echo=True,
        )


@_invoke.task(lint, flake8, black, default=True)
def all(ctx):  # pylint: disable = redefined-builtin, unused-argument
    """Run all"""

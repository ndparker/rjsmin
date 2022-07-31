# -*- encoding: ascii -*-
"""
Dependencies
~~~~~~~~~~~~

"""

import os as _os

import invoke as _invoke


@_invoke.task()
def old(ctx):
    """ List outdated python packages """
    with ctx.shell.root_dir():
        ctx.run('pip list -o', echo=True)


@_invoke.task()
def package(ctx, upgrade=False):
    """ Update python dependencies, excluding development """
    with ctx.shell.root_dir():
        ctx.run('pip install %s-e .' % ('-U ' if upgrade else '',), echo=True)


@_invoke.task(default=True)
def dev(ctx, upgrade=False):
    """ Update python dependencies, including development """
    with ctx.shell.root_dir():
        ctx.run('pip install %s-r development.txt'
                % ('-U ' if upgrade else '',), echo=True)


@_invoke.task()
def reset(ctx, python=False, upgrade=False):
    """ Reset your virtual env """
    cmd = "bash -il %s/reset.sh"
    if python:
        cmd += ' -p'
    if upgrade:
        cmd += ' -u'
    cmd += ' %s'
    with ctx.shell.root_dir():
        pwd = _os.getcwd()
        ctx.run(ctx.c(cmd, ctx.shell.native(_os.path.dirname(__file__)), pwd),
                pty=True)

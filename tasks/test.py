# -*- encoding: ascii -*-
"""
Test suite tasks
~~~~~~~~~~~~~~~~

"""

import invoke as _invoke


@_invoke.task()
def local(ctx):
    """ Run the test suite using py.test """
    tester = ctx.shell.frompath('py.test')
    if tester is None:
        raise RuntimeError("py.test not found")

    with ctx.shell.root_dir():
        command = r'''
            %s -c test.ini -vv -s
            --doctest-modules
            --color=yes
            --exitfirst
        '''
        args = [tester]

        for ignored in ctx.test.ignore:
            command += ' --ignore %s'
            args.append(ignored)

        command += ' %s'
        args.append('tests')

        ctx.run(ctx.c(command, *args), echo=True)


@_invoke.task(default=True)
def tox(ctx, rebuild=False, env=None):
    """ Run the test suite using tox """
    tox = ctx.shell.frompath('tox')  # pylint: disable = redefined-outer-name
    if tox is None:
        raise RuntimeError("tox not found")

    command = r''' %s -c test.ini '''
    args = [tox]
    if rebuild:
        command += ' -r'
    if env is not None:
        command += ' -e %s'
        args.append(env)

    with ctx.shell.root_dir():
        ctx.run(ctx.c(command, *args), echo=True)

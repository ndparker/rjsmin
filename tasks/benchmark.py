# -*- encoding: ascii -*-
"""
Benchmarks
~~~~~~~~~~

"""

import invoke as _invoke


@_invoke.task(default=True)
def tox(ctx, rebuild=False, env=None):
    """
    Run the benchmarks using tox

    :Parameters:
      `rebuild` : ``bool``
        Rebuild the tox environments?

      `env` : ``str``
        Run this one environment only.
    """
    tox = ctx.shell.frompath("tox")  # pylint: disable = redefined-outer-name
    if tox is None:
        raise RuntimeError("tox not found")

    command = r""" %s -c bench/tox.ini """
    args = [tox]
    if rebuild:
        command += " -r"
    if env is not None:
        command += " -e %s"
        args.append(env)

    with ctx.shell.root_dir():
        ctx.run(ctx.c(command, *args), echo=True)

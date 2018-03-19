# -*- encoding: ascii -*-
"""
Compile tasks
~~~~~~~~~~~~~

"""

import invoke as _invoke


@_invoke.task(default=True)
def compile(ctx):  # pylint: disable = redefined-builtin
    """ Compile the package """
    with ctx.shell.root_dir():
        ctx.run('pip install -e .')

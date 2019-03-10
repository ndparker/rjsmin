# -*- encoding: ascii -*-
"""
Compile tasks
~~~~~~~~~~~~~

"""

import os as _os

import invoke as _invoke


@_invoke.task(default=True)
def compile(ctx):  # pylint: disable = redefined-builtin
    """ Compile the package """
    with ctx.shell.root_dir():
        ctx.run('pip install -e .',
                env=dict(_os.environ, SETUP_CEXT_REQUIRED="1"))

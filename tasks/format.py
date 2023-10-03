# -*- encoding: ascii -*-
"""
Running code formatters
~~~~~~~~~~~~~~~~~~~~~~~

"""

import invoke as _invoke


@_invoke.task(default=True)
def black(ctx, diff=False):
    """Format python code using Black formatter"""
    exe = ctx.shell.frompath('black')
    if exe is None:
        raise RuntimeError("black not found")

    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(
                '%%s %s --config black.toml .'
                % ('--diff --color' if diff else '',),
                exe,
            ),
            echo=True,
        )

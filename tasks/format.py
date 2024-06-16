# -*- encoding: ascii -*-
"""
Running code formatters
~~~~~~~~~~~~~~~~~~~~~~~

"""

import invoke as _invoke


@_invoke.task()
def black(ctx, diff=False):
    """Format python code using Black formatter"""
    with ctx.shell.root_dir():
        ctx.run(
            ctx.c(
                (
                    "%%(black)s %(diff)s --config black.toml ."
                    % dict(
                        diff="--diff --color" if diff else "",
                    )
                ),
                black=ctx.which("black"),
            ),
            echo=True,
        )


@_invoke.task(black, name="all", default=True)
def all_(ctx):
    """Run all"""

# -*- encoding: ascii -*-
"""
Uploading
~~~~~~~~~

"""

import invoke as _invoke


@_invoke.task(default=True)
def source(ctx):
    """ Upload source package """
    with ctx.shell.root_dir():
        files = list(ctx.shell.files('dist', '*.tar.gz'))
        if len(files) != 1:
            ctx.fail("Not exactly one tarball found")

        ctx.run(ctx.c('''
            twine upload
            --repository-url %s
            --username %s
            %s
        ''', ctx.pypi.repository, ctx.pypi.username, files[0]), echo=True)

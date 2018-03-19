# -*- encoding: ascii -*-
"""
Build Tasks
~~~~~~~~~~~

"""

import invoke as _invoke

from . import doc as _doc
from . import _dist
from . import _release
from . import _version


@_invoke.task(_doc.doc, default=True)
def source(ctx):
    """ Build source package """
    with ctx.shell.root_dir():
        ctx.run('python setup.py sdist')


@_invoke.task(_doc.doc)
def dist(ctx):
    """ Build distribution """
    fakeroot = ctx.shell.frompath('fakeroot')
    with ctx.shell.root_dir():
        ctx.shell.rm_rf('build', 'dist')
        ctx.run(ctx.c('%s python setup.py sdist --formats tar,zip', fakeroot),
                echo=True)

        files = list(ctx.shell.files('dist', '*.zip'))
        digestname = files[0][:-3] + 'digests'
        for name in ctx.shell.files('dist', '*.tar'):
            files.append(_dist.compress(ctx, name, 'gzip', '.gz'))
            files.append(_dist.compress(ctx, name, 'bzip2', '.bz2'))
            files.append(_dist.compress(ctx, name, 'xz', '.xz'))
            ctx.shell.rm(name)
        files = [name for name in files if name]

        _dist.digest(ctx, files, digestname)
        _dist.copy_changes(ctx)


@_invoke.task()
def version(ctx):
    """ Version """
    with ctx.shell.root_dir():
        _version.update(ctx)


@_invoke.task(_doc.doc)
def release(ctx):
    """ Release """
    with ctx.shell.root_dir():
        _release.check_committed(ctx)
        version(ctx)
        _release.add_tag(ctx)

    # _doc.doc(ctx)  # dependencies are not called, hence put as regular
    # dep here
    dist(ctx)

# -*- encoding: ascii -*-
"""
Build Tasks
~~~~~~~~~~~

"""
from __future__ import print_function

import os as _os
import platform as _platform
import re as _re

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


@_invoke.task()
def wheels(ctx, arches=None):
    """
    Build wheels

    Parameters:
      arches (str):
        Space separated list of architectures. If not supplied it defaults to
        the current machine type. Except if the current machine type is
        "x86_64", then if defaults to "x86_64 i686 aarch64" (using
        binfmt_misc in combination with multiarch/qemu-user-static for the
        latter).
    """
    # pylint: disable = too-many-branches

    path = 'wheel/dist'

    machine = _platform.machine()
    if arches is None:
        if machine == 'x86_64':
            arches = "x86_64 i686 aarch64"
        else:
            arches = machine
    arches = arches.split()
    for arch in arches:
        if machine == arch:
            continue
        if machine == 'x86_64' and arch == 'i686':
            continue
        ctx.run(ctx.c('''
            docker run --rm --privileged multiarch/qemu-user-static
            --reset -p yes
        '''), echo=True, pty=True)
        break

    with ctx.shell.root_dir():
        ctx.shell.rm_rf(path)
        pythons = "36 37 38 39 310"

        for arch in arches:
            if arch in ("x86_64", "i686"):
                ctx.run(
                    ctx.c('''
                        docker run --rm -it -v%s/wheel:/io
                        quay.io/pypa/manylinux1_%s:latest
                    ''' + (arch == "i686" and "linux32" or "") + '''
                        /io/build.sh %s %s
                    ''', _os.getcwd(), arch, ctx.package, "27"),
                    echo=True, pty=True,
                )
            ctx.run(
                ctx.c('''
                    docker run --rm -it -v%s/wheel:/io
                    quay.io/pypa/manylinux_2_24_%s:latest
                    ''' + (arch == "i686" and "linux32" or "") + '''
                    /io/build.sh %s %s
                ''', _os.getcwd(), arch, ctx.package, pythons),
                echo=True, pty=True,
            )

        # strip file names
        multi_sub = _re.compile(r'(?:[.-]manylinux[^.]+)+').sub
        tomove = []
        for name in _os.listdir(path):
            if not name.endswith('.whl'):
                continue
            pick = _best_manylinux(name)
            if pick:
                tomove.append((
                    name, multi_sub((lambda _, p=pick: '-' + p), name)
                ))
        for old, new in tomove:
            if old == new:
                continue

            print("%s -> %s" % (old, new))
            _os.rename(_os.path.join(path, old), _os.path.join(path, new))


def _best_manylinux(name):
    """ Find best manylinux variant produced by auditwheel """
    tag_list_search = _re.compile(r'(?:[.-]manylinux[^.]+)+').search

    tags = tag_list_search(name)
    if not tags:
        return None
    sortable = []
    for tag in tags.group(0).strip('-.').split('.'):
        assert tag.startswith('manylinux')
        ver = tag[len('manylinux'):]
        if ver.startswith(("1_", "2010_", "2014_")):
            sortable.append(((1, int(ver.split('_')[0])), tag))
            continue
        assert ver.startswith('_')
        ver = tuple(map(int, ver[1:].split('_')[:2]))
        assert ver[0] > 1
        sortable.append((ver, tag))
    if not sortable:
        return None

    return min(sortable)[-1]


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

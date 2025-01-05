# -*- encoding: ascii -*-
"""
Build Tasks
~~~~~~~~~~~

"""
from __future__ import print_function

import itertools as _it
import os as _os
import platform as _platform
import re as _re

import invoke as _invoke

from . import _dist
from . import _release
from . import _version

# pylint: disable = import-outside-toplevel

NAMESPACE = "build"


@_invoke.task("doc.doc", default=True)
def source(ctx):
    """Build source package"""
    with ctx.shell.root_dir():
        if ctx.get("wheels", {}).get("build") == "universal":
            with open("setup.cfg", "wb") as fp:
                fp.write(b"[bdist_wheel]\n")
                fp.write(b"universal = 1\n")

        try:
            import build  # noqa pylint: disable = unused-import
        except ImportError:
            ctx.run("python setup.py sdist")
        else:
            ctx.run("python -m build --sdist")


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
    # pylint: disable = unused-argument

    if ctx.wheels.build == "binary":
        return _build_binary(ctx, arches=arches)

    assert not arches
    assert ctx.wheels.build == "universal"
    return _build_universal(ctx)


def _build_universal(ctx):
    """Build universal wheel"""
    with ctx.shell.root_dir():
        ctx.shell.rm_rf("wheel/dist")

        for package in ctx.shell.files(
            "dist/", "%s-*.tar.gz" % (ctx.package,)
        ):
            ctx.run(
                ctx.c(
                    """
                pip wheel --no-binary :all: --no-cache -w wheel/dist %s
            """,
                    package,
                ),
                pty=True,
            )


def _build_binary(ctx, arches=None):
    """
    Build binary wheels

    Parameters:
      arches (str):
        Space separated list of architectures. If not supplied it defaults to
        the current machine type. Except if the current machine type is
        "x86_64", then if defaults to "x86_64 i686 aarch64" (using
        binfmt_misc in combination with multiarch/qemu-user-static for the
        latter).
    """
    # pylint: disable = too-many-branches, too-many-locals

    path = "wheel/dist"

    machine = _platform.machine()
    if arches is None:
        if machine == "x86_64":
            arches = "x86_64 i686 aarch64"
        else:
            arches = machine
    arches = arches.split()
    for arch in arches:
        if machine == arch:
            continue
        if machine == "x86_64":
            if arch == "i686":
                continue

            ctx.run(
                ctx.c(
                    """
                docker run --rm --privileged multiarch/qemu-user-static
                --reset -p yes
            """
                ),
                echo=True,
                pty=True,
            )
            break

    with ctx.shell.root_dir():
        # pylint: disable = too-many-nested-blocks
        ctx.shell.rm_rf(path)
        for package in ctx.shell.files(
            "dist/", "%s-*.tar.gz" % (ctx.package,)
        ):
            ppath = "/io/%s" % (_os.path.basename(package))

            ctx.shell.cp(package, ctx.shell.native("wheel/"))
            try:
                for arch in arches:
                    spec = ctx.wheels.specs[arch]
                    prefix = "linux32" if arch == "i686" else ""
                    for libc in ("manylinux", "musllinux"):
                        groups = sorted(
                            (
                                (tup[0], tup[1][libc])
                                for tup in spec.items()
                                if libc in tup[1]
                            ),
                            key=lambda x, libc=libc: (x[1], x[0]),
                        )
                        for v, group in _it.groupby(
                            groups, key=lambda x: x[1]
                        ):
                            pythons = " ".join(
                                sorted(item[0] for item in group)
                            )
                            if "_" in v:
                                v = "_" + v
                            ctx.run(
                                ctx.c(
                                    (
                                        """
                                        docker run --rm -it -v%s/wheel:/io
                                        quay.io/pypa/%s%s_%s:latest
                                    """
                                        + prefix
                                        + """
                                        /io/build.sh %s %s %s
                                    """
                                    ),
                                    _os.getcwd(),
                                    libc,
                                    v,
                                    arch,
                                    libc,
                                    ppath,
                                    pythons,
                                ),
                                echo=True,
                                pty=True,
                            )
            finally:
                _os.unlink(
                    ctx.shell.native(
                        "wheel/%s" % (_os.path.basename(package),)
                    )
                )

        # strip file names
        multi_sub = _re.compile(r"(?:[.-]manylinux[^.]+)+").sub
        tomove = []
        for name in _os.listdir(path):
            if not name.endswith(".whl"):
                continue
            if "manylinux" not in name:
                continue

            pick = _best_manylinux(name)
            if pick:
                tomove.append(
                    (name, multi_sub((lambda _, p=pick: "-" + p), name))
                )
        for old, new in tomove:
            if old == new:
                continue

            print("%s -> %s" % (old, new))
            _os.rename(_os.path.join(path, old), _os.path.join(path, new))


def _best_manylinux(name):
    """Find best manylinux variant produced by auditwheel"""
    tag_list_search = _re.compile(r"(?:[.-]manylinux[^.]+)+").search

    tags = tag_list_search(name)
    if not tags:
        return None
    sortable = []
    for tag in tags.group(0).strip("-.").split("."):
        assert tag.startswith("manylinux")
        ver = tag[len("manylinux") :]
        if ver.startswith(("1_", "2010_", "2014_")):
            sortable.append(((1, int(ver.split("_")[0])), tag))
            continue
        assert ver.startswith("_")
        ver = tuple(map(int, ver[1:].split("_")[:2]))
        assert ver[0] > 1
        sortable.append((ver, tag))
    if not sortable:
        return None

    return min(sortable)[-1]


@_invoke.task("doc.doc")
def dist(ctx):
    """Build distribution"""
    fakeroot = ctx.shell.frompath("fakeroot")
    with ctx.shell.root_dir():
        ctx.shell.rm_rf("build", "dist")
        ctx.run(
            ctx.c("%s python setup.py sdist --formats tar,zip", fakeroot),
            echo=True,
        )

        files = list(ctx.shell.files("dist", "*.zip"))
        digestname = files[0][:-3] + "digests"
        for name in ctx.shell.files("dist", "*.tar"):
            files.append(_dist.compress(ctx, name, "gzip", ".gz"))
            files.append(_dist.compress(ctx, name, "bzip2", ".bz2"))
            files.append(_dist.compress(ctx, name, "xz", ".xz"))
            ctx.shell.rm(name)
        files = [name for name in files if name]

        _dist.digest(ctx, files, digestname)
        _dist.copy_changes(ctx)


@_invoke.task()
def version(ctx):
    """Version"""
    with ctx.shell.root_dir():
        _version.update(ctx)


@_invoke.task("doc.doc")
def release(ctx):
    """Release"""
    with ctx.shell.root_dir():
        _release.check_committed(ctx)
        version(ctx)
        _release.add_tag(ctx)

    # _doc.doc(ctx)  # dependencies are not called, hence put as regular
    # dep here
    dist(ctx)

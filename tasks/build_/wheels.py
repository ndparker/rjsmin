# -*- coding: ascii -*-
#
# Copyright 2007 - 2026
# Andr\xe9 Malo or his licensors, as applicable
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

from .. import features as _features
from .._inv import tasks as _tasks
from . import _container

NAMESPACE = "build"


@_tasks.optional(None, _features.python_wheels)
@_invoke.task()
def wheels(ctx, arches=None, pythons=None):
    """
    Build wheels

    Parameters:
      arches (str):
        Space separated list of architectures. If not supplied it defaults to
        the current machine type. Except if the current machine type is
        "x86_64", then if defaults to "x86_64 i686 aarch64" (using
        binfmt_misc in combination with multiarch/qemu-user-static for the
        latter).

      pythons (str):
        Space separated list of pythons (36 37 etc). If omitted, all possible
        python versions will be built. Only relevant for binary builds.
    """
    if ctx.wheels.build == "binary":
        return _build_binary(ctx, arches=arches, pythons=pythons)

    assert not arches
    assert ctx.wheels.build in ("universal", "simple")
    return _build_universal(ctx)


def _build_universal(ctx):
    """Build universal / simple wheel"""
    path = ".bdist"

    with ctx.shell.root_dir():
        ctx.shell.rm_rf(path)

        cmd = ctx.s("pip wheel --no-binary :all: --no-cache --no-deps -w")
        cmd += [path]

        for package in ctx.shell.files(
            "dist/", "%s[-_]*.tar.gz" % (ctx.package,)
        ):
            ctx.run(ctx.c(cmd + [package]), echo=True)
            _finalize_bdist(ctx, path)


def _build_binary(ctx, arches=None, pythons=None):
    """
    Build binary wheels

    Parameters:
      arches (str):
        Space separated list of architectures. If not supplied it defaults to
        the current machine type. Except if the current machine type is
        "x86_64", then if defaults to "x86_64 i686 aarch64" (using
        binfmt_misc in combination with multiarch/qemu-user-static for the
        latter).

      pythons (str):
        Space separated list of pythons (36 37 etc). If omitted, all possible
        python versions will be built. Only relevant for binary builds.
    """
    path = ".bdist"
    arches = _ensure_arches(ctx, arches)
    build_sh = _os.path.join(_os.path.dirname(__file__), "wheel.sh")
    wanted_pythons = set(pythons.split()) if pythons else None

    with ctx.shell.root_dir():
        ctx.shell.rm_rf(path)
        ctx.shell.mkdir_p(path)

        for package in ctx.shell.files(
            "dist/", "%s-*.tar.gz" % (ctx.package,)
        ):
            for image, cmd, libc, py in _pypa_containers(ctx, arches):
                pythons = (
                    py
                    if wanted_pythons is None
                    else (set(py) & wanted_pythons)
                )
                if not pythons:
                    continue

                name = "wheel-%s" % (_os.path.basename(package),)
                cmd += [
                    "/io/build.sh",
                    libc,
                    "/io/pkg.tar.gz",
                    " ".join(sorted(pythons)),
                ]

                with _container.Container(ctx, name, image) as container:
                    container.execute(ctx.s("mkdir /io"))
                    container.cp_in(package, "/io/pkg.tar.gz")
                    container.cp_in(build_sh, "/io/build.sh")
                    container.execute(ctx.s("chmod +x /io/build.sh"))
                    container.execute(cmd)
                    container.cp_out("/io/dist/.", path)

                _finalize_bdist(ctx, path)


def _finalize_bdist(ctx, path):
    """
    Finalize wheel names, move files to dist/

    Parameters:
      path (str):
        wheel path
    """
    # collapse file names
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
        _os.rename(_os.path.join(path, old), _os.path.join(path, new))

    if path == "dist":
        return

    # Move to dist/
    for name in _os.listdir(path):
        old = "%s/%s" % (path, name)
        new = "dist/%s" % (name,)
        print("%s -> %s" % (old, new))
        _os.rename(ctx.shell.native(old), ctx.shell.native(new))


def _pypa_containers(ctx, arches):
    """
    Create a list of containers to execute

    Parameters:
      arches (list):
        List of arches to apply

    Yields:
      tuple: image, command prefix, libc, python list
    """
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
            for v, group in _it.groupby(groups, key=lambda x: x[1]):
                if "_" in v:
                    v = "_" + v
                if ":" in v:
                    v, tag = v.split(":", 1)
                else:
                    tag = "latest"

                yield (
                    "quay.io/pypa/%s%s_%s:%s" % (libc, v, arch, tag),
                    [prefix] if prefix else [],
                    libc,
                    sorted(item[0] for item in group),
                )


def _ensure_arches(ctx, arches):
    """
    Install multiarch qemu

    Parameters:
      arches (str):
        The desired architectures

    Returns:
      list: The split architecture strings
    """
    machine = _platform.machine()
    system = _platform.system()
    if arches is None:
        if machine == "x86_64":
            arches = "x86_64 i686 aarch64"
        else:
            arches = machine
    arches = arches.split()

    if system == "Linux":
        for arch in arches:
            if machine == arch:
                continue
            if machine == "x86_64":
                if arch == "i686":
                    continue

                ctx.run(
                    ctx.c(
                        _container.DockerCommand(ctx).run(
                            "multiarch/qemu-user-static",
                            command=["--reset", "-p", "yes"],
                            remove=True,
                            privileged=True,
                        )
                    ),
                    echo=True,
                )

                break

    return arches


def _best_manylinux(name):
    """
    Find best manylinux variant produced by auditwheel

    Parameters:
      name (str):
        filename (basename) of the package

    Returns:
      str: The best version, or ``None`` if it couldn't be determined
    """
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

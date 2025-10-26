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

import contextlib as _contextlib
import os as _os
import tempfile as _tempfile

from ..util import package as _package


@_contextlib.contextmanager
def sdist(ctx, name):
    """
    Create temporary package directory as a context

    Parameters:
      name (str):
        The sub-package name

    Returns:
      The directory name
    """
    dotsdist = ".sdist"
    try:
        with ctx.shell.root_dir():
            ctx.shell.mkdir_p(dotsdist)
            directory = _tempfile.mkdtemp(dir=dotsdist)

            # cp target cannot exist before
            target = _os.path.join(directory, "x")
            ctx.shell.cp_r(".", target, ignore=_ignore(ctx))

            ext_map = {
                ".py": "setup.py",
                ".toml": "pyproject.toml",
                ".MANIFEST": "MANIFEST.in",
            }
            for ext, dest in ext_map.items():
                dest = _os.path.join(target, dest)
                ctx.shell.rm(dest)

                src = _os.path.join(target, "setups", name + ext)
                if _os.path.isfile(src):
                    with open(src, "rb") as fp:
                        content = fp.read().decode("latin-1")
                    if "$BASE" in content or "$VERSION" in content:
                        meta = _package.find_meta()
                        content = content.replace(
                            "$VERSION", meta["Version"]
                        ).replace("$BASE", meta["Name"])
                        with open(dest, "wb") as fp:
                            fp.write(content.encode("latin-1"))
                    else:
                        ctx.shell.cp(src, dest)
            if not _os.path.isfile(_os.path.join(target, "MANIFEST.in")):
                with open(_os.path.join(target, "MANIFEST.in"), "wb"):
                    pass
            ctx.shell.rm_rf(_os.path.join(target, "setups"))

            _os.chdir(target)
            yield target
    finally:
        ctx.shell.rm_rf(dotsdist)


def _ignore(ctx):
    """
    Make ignore function (as expected by shutil.copytree)

    Returns:
      callable: The copytree ignore callback function
    """
    # Config option to add more files/directories to ignore
    extra = ctx.get("setup_ignore")

    # Collect all checked-in files, those are good.
    with ctx.shell.root_dir():
        files = set(
            _os.path.normpath(item)
            for item in ctx.run("git ls-files -z", hide=True).stdout.split(
                "\0"
            )
        )
    for item in list(files):
        dirname = _os.path.dirname(item)
        if dirname:
            files.add(dirname)

    root = []
    extra = set(_os.path.normpath(item) for item in extra or ())

    def ignorable(node, children):
        """
        Ignore function as called by shutil.copytree

        Parameters:
          node (str):
            The directory

          children (list):
            The directory entries

        Returns:
          list: The entries to ignore
        """
        if not root:
            root.append(node)
        node = node[len(root[0]) + 1 :]

        # Collect entries to ignore
        result = []
        for item in children:
            path = _os.path.normpath(
                _os.path.join(node, item) if node else item
            )

            # explicit ignores takes precedence
            if path in extra:
                result.append(item)

            # If it looks weird, check back with the git list
            elif item.startswith(".") or item.endswith(".egg-info"):
                if path not in files:
                    result.append(item)

        return result

    return ignorable

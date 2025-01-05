# -*- coding: ascii -*-
#
# Copyright 2018 - 2025
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
Model for req file containing latest versions of dependencies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging as _logging
import re as _re

from ..._inv import shell as _shell
from .. import _parse

# pylint: disable = import-outside-toplevel

logger = _logging.getLogger("deps.suggest.latest_file")


class LatestFile(object):
    """
    Dependency file container

    Attributes:
      name (str):
        The filename
    """

    # pylint: disable = too-many-instance-attributes

    def __init__(self, filename, pattern, prefix, suffix, latest, not_latest):
        """
        Initialization

        Parameters:
          filename (str):
            The filename

          pattern (str):
            Pattern to find the place where to insert the latest deps

          prefix (str):
            Prefix line for the latest deps

          suffix (str):
            Suffix line for the latest deps

          latest (dict):
            normname -> update-info

          not_latest (set):
            Not in latest (possibly anymore)
        """
        # pylint: disable = too-many-positional-arguments

        self.name = _shell.relative(filename)
        self._fullname = _shell.native(filename)
        self._pattern = pattern
        self._prefix, self._suffix = prefix, suffix
        self._add, self._remove = [], []
        self._pre, self._post = None, None
        self._latest, self._not_latest = latest, not_latest
        error = self.load()
        if error:
            logger.debug("%s", error)

    def __repr__(self):
        """
        Create debug representation

        Returns:
          str: The repr of the container
        """
        return "%s(%r, %r, %r, %r, %r, %r)" % (
            self.__class__.__name__,
            self.name,
            self._pattern,
            self._prefix,
            self._suffix,
            self._latest,
            self._not_latest,
        )

    def __str__(self):
        """
        The reconstructed file

        Returns:
          str: The file as string
        """
        pre = "".join(self._pre) + "\n"
        add = "".join(self._add)
        prefix = (
            self._prefix + "\n" if add and self._prefix is not None else ""
        )
        suffix = (
            self._suffix + "\n" if add and self._suffix is not None else ""
        )
        return pre + prefix + add + suffix + self._post

    def as_patch_info(self):
        """
        Create jsonable patch information

        Returns:
          dict: {"add": [], "remove": []} or None
        """
        if set(self._add) == set(self._remove):
            return None
        return dict(add=list(self._add), remove=list(self._remove))

    def as_changed(self):
        """
        Create jsonable patch information

        Returns:
          dict: Name -> new version
        """
        patched = self.as_patch_info()
        if not patched:
            return {}

        removed = {}
        changed = {}
        for line in patched["remove"]:
            req = _parse.requirement(line)
            ops = set(spec.operator for spec in req.specifier)
            versions = [spec.version for spec in req.specifier]
            if ops in ({"=="}, {"~="}):
                removed[_parse.normalize(req.name)] = versions[0]

        for line in patched["add"]:
            req = _parse.requirement(line)
            ops = set(spec.operator for spec in req.specifier)
            versions = [spec.version for spec in req.specifier]
            if ops in ({"=="}, {"~="}):
                name = _parse.normalize(req.name)
                if removed.get(name) != versions[0]:
                    changed[name] = versions[0]

        return changed

    def load(self):
        """
        (Re-)load the file

        Returns:
          str: Error message if any. ``None`` if it was successful.
        """
        try:
            with open(self._fullname, "rb") as fp:
                content = fp.read().decode("latin-1")
        except IOError as e:
            return "Could not read file %r: %s" % (self._fullname, e)

        search = _re.compile("(%s)" % (self._pattern,), _re.M).search
        found = search(content)
        if not found:
            return "Pattern %r not found in %r" % (self._pattern, self.name)

        cut = ""
        pre = content[: found.start(1)]
        post = content[found.start(1) :]
        while pre and not pre.endswith("\n"):
            cut += pre[-1]
            pre = pre[:-1]
        self._pre = pre.splitlines(True)
        self._post = "".join(reversed(cut)) + post

        # Find lines to remove and lines to add
        add = []
        for item in sorted(self._latest.values(), key=lambda x: x["new"]):
            add.append(item["new"].rstrip() + "\n")
        self._add, self._remove = add, self._remove_previous()

        return None

    def _remove_previous(self):
        """
        Remove previous "latest" dependencies from pre

        Returns:
          list: The removed dependencies
        """
        # pylint: disable = too-many-branches

        pre = self._pre
        prefix, suffix = self._prefix or "", self._suffix
        is_req = _re.compile(_parse.regex.full_spec()).match
        remove = []

        while pre:
            # skip empty lines
            if not pre[-1].strip():
                pre.pop()
                continue

            # skip suffix
            if suffix is not None and pre[-1].strip() == suffix.strip():
                pre.pop()
                continue

            # if we hit the prefix, we're done.
            if prefix and pre[-1].strip() == prefix.strip():
                pre.pop()
                break

            # we hit otherwise a line, which does not look like a requirement
            if not is_req(pre[-1]):
                if not prefix:
                    break

                # Scan upwards and look out for the prefix line, skip until
                # then
                idx = 0
                for idx, line in enumerate(reversed(pre), start=1):
                    if line.strip() == prefix.strip():
                        break
                else:
                    break
                for _ in range(idx):
                    pre.pop()
                break

            # Finally we've hit something parsable
            # stop if it's not in our list, except if there's a prefix to be
            # found, then continue scanning
            key = _parse.normalize(_parse.requirement(pre[-1]).name)
            if key not in self._latest and key not in self._not_latest:
                for line in reversed(pre):
                    if line.strip() == prefix.strip():
                        break
                else:
                    break

            remove.append(pre.pop())

        # skip any empty lines
        while pre and not pre[-1].strip():
            pre.pop()
        return remove

    def write(self):
        """Write back the file"""
        # Try to assemble the file before opening it for writing
        result = str(self).encode("latin-1")

        with open(self._fullname, "wb") as fp:
            fp.write(result)

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
Requirement manipulation
~~~~~~~~~~~~~~~~~~~~~~~~

"""

import logging as _logging
import re as _re

from .. import _parse

logger = _logging.getLogger("deps.suggest.requirement")


_spec_sub = _re.compile(
    r"""(?x)
        ( (?:[^=]==|[<~]=|<) %(wsp)s* ) ( %(version_str)s )
    """
    % vars(_parse.regex)
).sub


def replace(original, updates, upgrade=False, compat=True, latest=False):
    """
    Find replacement for a single requirement

    Parameters:
      original:
        Original requirement

      updates (dict):
        Available updates for the dependency

      upgrade (bool):
        Try upgrading to the latest version? Default: False

      compat (bool):
        Ensure compatible changes? (``~=``) Default: true

      latest (bool):
        The target is the list of "latest" requirements (e.g. in
        development.txt)

    Returns:
      tuple: new requirement string and new version (extracted)
             (``(str, str)``)
    """
    desired_version = None
    if upgrade:
        desired_version = (
            updates.get("latest")
            or updates.get("compatible")
            or updates.get("unchanged")
        )
    elif not compat:
        desired_version = updates.get("compatible") or updates.get(
            "unchanged"
        )
    if not desired_version:
        return original, None

    version = _parse.version(desired_version)
    if compat:
        replacement = _replace_compat(original, version, upgrade)
    elif latest:
        replacement = _replace_latest(original, version)
    elif upgrade:
        replacement = _replace_upgrade(original, version)
    else:
        replacement = original

    req = _parse.requirement(replacement)
    for spec in req.specifier:
        if spec.operator == "~=" and compat:
            continue
        if spec.operator == "==" and (latest or (compat and not upgrade)):
            continue
        if spec.operator not in ("==", "~=", "<=", "<"):
            continue
        if _parse.version(spec.version) >= version:
            continue

        new_version = plus_1(version) if spec.operator == "<" else version
        replacement = _spec_sub(
            lambda m, n=new_version: "%s%s"
            % (m.group(1), digits(m.group(2), n)),
            replacement,
        )

    return replacement, desired_version


def _replace_compat(requirement, version, upgrade):
    """
    Replace with compat request

    Parameters:
      requirement (str):
        Requirement to manipulate

      version (Version):
        Desired version

      upgrade (bool):
        Is an upgrade requested?

    Returns:
      str: The possibly changed requirement
    """
    req = _parse.requirement(str(requirement))
    ops = set(spec.operator for spec in req.specifier)
    vers = [spec.version for spec in req.specifier]

    if ops == {"~="} and plus_1(digits(vers[0], version)) != plus_1(vers[0]):
        return _spec_sub(
            lambda m: ">= %s, < %s"
            % (
                vers[0],
                digits(vers[0], plus_1(digits(vers[0], version))),
            ),
            requirement,
        )

    if not upgrade:
        return requirement

    if ops == {"=="} and plus_1(version) != plus_1(vers[0]):
        return _spec_sub(
            lambda m: "%s >= %s, <= %s"
            % (
                m.group(1)[0] if m.group(1)[0] not in "=<~> \t" else "",
                vers[0],
                digits(vers[0], version),
            ),
            requirement,
        )

    return _replace_upgrade(requirement, version)


def _replace_upgrade(requirement, version):
    """
    Replace with upgrade request

    Parameters:
      requirement (str):
        Requirement to manipulate

       version (Version):
        Desired version

    Returns:
      str: The possibly changed requirement
    """
    req = _parse.requirement(str(requirement))
    ops = set(spec.operator for spec in req.specifier)

    if ops not in ({">=", "<"}, {">=", "<="}):
        return requirement

    lt_ver = [
        spec.version for spec in req.specifier if spec.operator in ("<", "<=")
    ][0]
    if _parse.version(lt_ver) > version:
        return requirement

    return _spec_sub(
        lambda m: "%s%s"
        % (
            m.group(1),
            digits(
                lt_ver,
                (version if "<=" in ops else plus_1(digits(lt_ver, version))),
            ),
        ),
        requirement,
    )


def _replace_latest(requirement, version):
    """
    Set version to latest

    Parameters:
      requirement (str):
        Requirement to manipulate

       version (Version):
        Desired version

    Returns:
      str: The possibly changed requirement
    """
    req = _parse.requirement(str(requirement))
    ops = set(spec.operator for spec in req.specifier)

    if ops not in ({">=", "<"}, {">=", "<="}):
        return requirement

    return _re.sub(
        _parse.regex.full_spec(req.name),
        lambda m: "%s%s ~= %s%s%s"
        % (
            m.group("name"),
            m.group("extra"),
            digits(m.group("version"), version),
            m.group("version")[len(m.group("version").rstrip()) :],
            m.group("marker"),
        ),
        requirement,
    )


def digits(ref_version, target_version):
    """
    Ensure significant number of version number items

    Parameters:
      ref_version (str):
        Reference version

      target_version (str):
        The version to adjust

    Returns:
      str: target version with possibly adjusted number of digits
    """
    release_match = _re.compile(_parse.regex.version_release).search

    ref_release = release_match(str(ref_version))
    if not ref_release:
        return target_version

    target_release = release_match(str(target_version))
    if not target_release:
        return target_version

    no_digits = len(ref_release.group(2).split("."))
    return "%s%s" % (
        target_release.group(1),
        ".".join(
            (target_release.group(2).split(".") + (["0"] * no_digits))[
                :no_digits
            ]
        ),
    )


def plus_1(version, which=-2):
    """
    Increase version number, so the < operator can be applied

    Parameters:
      version (Version or str):
        The version to increase

      which (int):
        Which version index to change. If it's outside the range of the
        versions, -1 is applied. Default: -2

    Returns:
      str: Increased version as a string
    """
    # group(1) is optional "epoch", group(2) the actual numbered version items
    # group(1) will be passed through, group(2) will be manipulated
    release = _re.match(_parse.regex.version_release, str(version))
    assert release, repr(str(version))

    numbers = [int(item) for item in release.group(2).split(".")]
    index = len(numbers) + which if which < 0 else which
    if not 0 <= index < len(numbers):
        index = len(numbers) - 1

    numbers[index] += 1
    return "%s%s" % (
        release.group(1),
        ".".join(map(str, numbers[: index + 1])),
    )

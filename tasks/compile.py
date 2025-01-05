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
Compile tasks
~~~~~~~~~~~~~

"""

import os as _os

import invoke as _invoke

from . import _features
from ._inv import tasks as _tasks


@_tasks.optional(None, _features.python_package)
@_invoke.task(default=True)
def compile(ctx):  # pylint: disable = redefined-builtin
    """Compile the package"""
    with ctx.shell.root_dir():
        ctx.run(
            "pip install -e .", env=dict(_os.environ, SETUP_CEXT_REQUIRED="1")
        )

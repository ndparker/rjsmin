#!/usr/bin/env python
# -*- coding: ascii -*-
#
# Copyright 2011
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

import re as _re

TPL = r"""
static const unsigned short rjsmin_charmask[128] = {
    @@mask@@
};
""".strip() + "\n"

def _make_charmask():
    dull = r'[^\047"/\000-\040]'
    pre_regex = r'[(,=:\[!&|?{};\r\n]'
    regex_dull = r'[^/\\\[\r\n]'
    regex_cc_dull = r'[^\\\]\r\n]'

    newline = r'[\r\n]'

    id_literal = r'[^\000-#%-,./:-@\[-^`{-~-]'
    id_literal_open = r'[^\000-\040"#%-\047)*,./:-@\\-^`|-~]'
    id_literal_close = r'[^\000-!#%&(*,./:-@\[\\^`{|~]'

    string_dull = r'[^\047"\\\r\n]'

    space = r'[\000-\011\013\014\016-\040]'

    charmask = []
    for x in range(8):
        maskline = []
        for y in range(16):
            c, mask = chr(x*16 + y), 0
            if _re.match(dull, c):
                mask |= 1
            if _re.match(pre_regex, c):
                mask |= 2
            if _re.match(regex_dull, c):
                mask |= 4
            if _re.match(regex_cc_dull, c):
                mask |= 8
            if _re.match(id_literal, c):
                mask |= 16
            if _re.match(id_literal_open, c):
                mask |= 32
            if _re.match(id_literal_close, c):
                mask |= 64
            if _re.match(string_dull, c):
                mask |= 128
            if _re.match(space, c):
                mask |= 256

            if mask < 10:
                mask = '  ' + str(mask)
            elif mask < 100:
                mask = ' ' + str(mask)
            maskline.append(str(mask))
            if y == 7:
                charmask.append(', '.join(maskline))
                maskline = []
        charmask.append(', '.join(maskline))
    return TPL.replace('@@mask@@', ',\n    '.join(charmask))

print _make_charmask()

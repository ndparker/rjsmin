#!/usr/bin/env python
from __future__ import print_function

import sys

a = sys.argv[1]

while len(a) > 62:
    b, a = a[:62], a[62:]
    while b.endswith('\\'):
        b = b[:-1]
        a = '\\' + a
    print("r'%s'" % (b,))
print("r'%s'" % (a,))

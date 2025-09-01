# Simple beta key generator for quick testing (legacy-friendly)
# Works on Python 2.7 and Python 3.x
from __future__ import print_function
import os
import binascii
import sys
import random

def make_simple_key(prefix='OLD', length=16):
    r = os.urandom(length)
    return "%s-%s" % (prefix, binascii.hexlify(r).decode('ascii') if hasattr(binascii, 'hexlify') else r.encode('hex'))

if __name__ == '__main__':
    prefix = 'OLD'
    if len(sys.argv) > 1:
        prefix = sys.argv[1]
    key = make_simple_key(prefix=prefix, length=8)  # 8 bytes -> 16 hex chars
    print(key)
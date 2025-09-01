# -*- coding: utf-8 -*-
"""
Scan files for non-ASCII characters and print line numbers and byte positions.
Usage:
  python find_non_ascii.py main.py engine.py utils.py
"""
from __future__ import print_function
import sys
import os

def scan_file(path):
    try:
        with open(path, 'rb') as f:
            data = f.read()
    except Exception as e:
        print("Cannot open", path, ":", e)
        return
    for i, line in enumerate(data.splitlines(), 1):
        for j, ch in enumerate(line):
            if ch > 127:
                print("{file}:{line}:{col}: byte 0x{b:02x}".format(file=path, line=i, col=j+1, b=ch))
                # show the offending snippet
                try:
                    snippet = line.decode('utf-8', errors='replace')
                except Exception:
                    snippet = repr(line)
                print("  >", snippet)
                break

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python find_non_ascii.py file1.py [file2.py ...]")
        sys.exit(1)
    for p in sys.argv[1:]:
        if os.path.exists(p):
            scan_file(p)
        else:
            print("Not found:", p)
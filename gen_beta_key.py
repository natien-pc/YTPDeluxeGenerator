# -*- coding: utf-8 -*-
# HMAC-signed offline beta key generator (works with Python 2.7 and Python 3.x)
from __future__ import print_function
import hmac
import hashlib
import time
import os
import binascii
import sys
import argparse

def make_signed_key(secret, user='anon', expires_unix=0, rand_bytes=8):
    """
    secret: shared secret string (keep private)
    user: short user id or label
    expires_unix: 0 for never, otherwise Unix timestamp
    rand_bytes: randomness size
    returns key string: BETA|USER|EXP|RANDHEX|HMACHEX
    """
    rand = os.urandom(rand_bytes)
    randhex = binascii.hexlify(rand).decode('ascii')
    payload = "|".join([str(user), str(int(expires_unix)), randhex])
    mac = hmac.new(secret.encode('utf-8'), payload.encode('utf-8'), hashlib.sha256).hexdigest()
    key = "BETA|%s|%s|%s|%s" % (user, int(expires_unix), randhex, mac)
    return key

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate HMAC-signed beta keys (legacy-friendly).")
    parser.add_argument('--secret', required=True, help='Shared secret (keep private)')
    parser.add_argument('--user', default='anon', help='User or label')
    parser.add_argument('--days', type=int, default=0, help='Days until expiry (0 = never expire)')
    parser.add_argument('--out', default=None, help='Write key to file (e.g. beta_key.txt)')
    args = parser.parse_args()

    expiry = 0
    if args.days and args.days > 0:
        expiry = int(time.time()) + args.days * 24 * 3600

    key = make_signed_key(args.secret, user=args.user, expires_unix=expiry)
    if args.out:
        with open(args.out, 'w') as f:
            f.write(key + '\n')
        print("Wrote key to", args.out)
    else:
        print(key)
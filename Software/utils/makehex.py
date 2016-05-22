#!/usr/bin/env python3
#
# This is free and unencumbered software released into the public domain.
#
# Anyone is free to copy, modify, publish, use, compile, sell, or
# distribute this software, either in source code form or as a compiled
# binary, for any purpose, commercial or non-commercial, and by any
# means.

from sys import argv

binfile = argv[1]
nwords = int(argv[2])
start_address = int(argv[3], 16)
word_line = int(argv[4])

with open(binfile, "rb") as f:
    bindata = f.read()

assert word_line % 4 == 0

assert start_address < 4*nwords
assert start_address % 4 == 0

assert len(bindata) < 4*nwords
assert len(bindata) % 4 == 0

for i in range(start_address//(4 * word_line)):
    print("00000000" * word_line)

for i in range((nwords - start_address//4)//word_line):
    line = ""
    for k in range(word_line):
        index = i * word_line + k
        if index < len(bindata)//4:
            w = bindata[4*index : 4*index+4]
            line = ("%02x%02x%02x%02x" % (w[3], w[2], w[1], w[0])) + line
        else:
            line = "00000000" + line
    print(line)
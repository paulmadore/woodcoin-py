#!/usr/bin/env python
#
# Read raw block on stdin, print human-readable on stdout
#

import struct
import sys

from BCDataStream import *
from deserialize import *

headerBytes = 0xd9b4bef9
testnetHeaderBytes = 0x0709110b

def main():
    blockdata = sys.stdin.read()

    h = struct.unpack_from('<I', blockdata, 0)[0]
    if h == headerBytes or h == testnetHeaderBytes:
        blockdata = blockdata[8:]

    vds = BCDataStream()
    vds.write(blockdata)

    block = parse_Block(vds)
    print deserialize_Block(block)

if __name__ == '__main__':
    main()

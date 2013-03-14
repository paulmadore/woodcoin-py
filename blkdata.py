#!/usr/bin/env python
#
# Code for dumping data in a raw blk000*.dat file
#

import hashlib
import logging
import struct
import sys

from BCDataStream import *
from deserialize import *

headerBytes = 0xd9b4bef9
testnetHeaderBytes = 0x0709110b

MAX_BLOCK_SIZE=1000000

def scan_for_blocks(testnet, blockdata):
    position = 0

    if testnet: msgheader = testnetHeaderBytes
    else: msgheader = headerBytes

    # 91 is smallest possible block size:
    #  = 4 byte msgheader + 4 byte size + 80 byte + 1 byte tx size + min-2-byte-coinbase
    while position+91 < len(blockdata):
        h = struct.unpack_from('<I', blockdata, position)[0]
        if h != msgheader:
            position += 1
            continue
        start = position
        position += 4
        blocksize = struct.unpack_from('<I', blockdata, position)[0]
        if blocksize < 80 or blocksize > MAX_BLOCK_SIZE:
            raise Exception("Bad blocksize: %d"%(blocksize,))
        position += 4
        blockcontents = blockdata[start:position+blocksize] # includes msgheader and size
        vds = BCDataStream()
        vds.write(blockdata[position:position+blocksize])
        block = parse_Block(vds)
        yield (blockcontents, block)
        position += blocksize

def height_from_coinbase(txn):
    coinbase = txn['txIn'][0]
    ssig = coinbase['scriptSig']
    nbytes = ord(ssig[0])
    height = 0
    for i in range(0,nbytes):
        height += ord(ssig[1+i])<<(8*i)
    return height

def main():
    import optparse
    parser = optparse.OptionParser(usage="%prog [options] [blk00NNN.dat]")
    parser.add_option("--heights", action="store_true", dest="print_heights", default=False,
                    help="Print height,hash contained in block.version=2 coinbase transactions")
    parser.add_option("--hashes", action="store_true", dest="print_hashes", default=False,
                      help="Print block hashes contained in the file")
    parser.add_option("--extract", action="store", dest="extract", default=None,
                      help="Extract block(s) to stdout, given block height or hash")
    parser.add_option("--testnet", action="store_true", dest="testnet", default=False,
                      help="Parse tesnet3 blk.dat file")

    (options, args) = parser.parse_args()

    if len(args) == 1:
        blockdata = open(args[0], "rb").read()
    else:
        blockdata = sys.stdin.read()

    for (rawblock, block) in scan_for_blocks(options.testnet, blockdata):
        # Note: rawblock includes 8-byte msgheader+size
        # block header is bytes 8-88
        height = None
        if block['version'] > 1:
            height = height_from_coinbase(block['transactions'][0])
        binaryhash = hashlib.sha256(hashlib.sha256(rawblock[8:88]).digest()).digest()
        hexhash = binaryhash[::-1].encode('hex_codec')

        if options.extract is not None:
            if options.extract == height or options.extract == hexhash:
                sys.stdout.write(rawblock)
        elif options.print_heights and height is not None:
            print("%d,%s"%(height,hexhash))
        elif options.print_hashes:
            print(hexhash)


if __name__ == '__main__':
    main()

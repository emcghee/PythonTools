from argparse import ArgumentParser
from binascii import hexlify

from Crypto.Hash import MD4

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('hash')

    return parser.parse_args()

def main(args):
    inputHash = args.hash
    hash = MD4.new(inputHash.encode('utf-16le')).digest()
    print('aad3b435b51404eeaad3b435b51404ee:' + hexlify(hash).decode())

if __name__ == '__main__':
    args = parseArguments()
    main(args)

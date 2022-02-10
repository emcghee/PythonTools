from argparse import ArgumentParser
from secrets import token_bytes
from base64 import b64encode


def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('length', type=int, help='The length of key to generate.')

    return parser.parse_args()


def main(args):
    length = args.length

    rawBytes = token_bytes(length)
    encoded = b64encode(rawBytes)
    base64String = encoded.decode()

    print(base64String)


if __name__ == '__main__':
    args = parseArguments()
    main(args)

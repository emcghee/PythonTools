from argparse import ArgumentParser
from base64 import b64encode, encode

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('text')

    return parser.parse_args()

def main(args):
    text = args.text

    encoded = b64encode(text.encode())

    print(encoded.decode())

if __name__ == '__main__':
    args = parseArguments()
    main(args)

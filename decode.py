from argparse import ArgumentParser
from base64 import b64decode

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('text')

    return parser.parse_args()

def main(args):
    text = args.text

    decoded = b64decode(text.encode())

    print(decoded.decode())

if __name__ == '__main__':
    args = parseArguments()
    main(args)

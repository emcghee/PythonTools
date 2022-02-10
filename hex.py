from argparse import ArgumentParser
from os.path import exists
from sys import stdout

def parseArguments():
    parser = ArgumentParser()
    parser.add_argument('file', help='The file to hexify or unhexify.')
    parser.add_argument('--unhex', action='store_true', help='Convert from hex to bytes.')

    return parser.parse_args()

def main(args):
    file = args.file
    unhex = args.unhex

    if not exists(file):
        print(f"[-] Could not find '{file}'")
        return

    if unhex:
        with open(file, 'rt') as readFile:
            hex = readFile.read()
        
        stdout.buffer.write(bytes.fromhex(hex))

    else:
        with open(file, 'rb') as readFile:
            raw = readFile.read()

        hex = raw.hex()
        print(hex)

if __name__ == "__main__":
    args = parseArguments()
    main(args)

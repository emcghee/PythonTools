import pyperclip
from argparse import ArgumentParser
from sys import stdin

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('inputFile', nargs='?')

    return parser.parse_args()

def main(args):
    inputFile = args.inputFile
    if not inputFile:
        for line in stdin:
            content = line.strip()

    else:
        with open(inputFile, 'rt') as readFile:
            content = readFile.read()

    pyperclip.copy(content)

if __name__ == '__main__':
    args = parseArguments()
    main(args)

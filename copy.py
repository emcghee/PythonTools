import pyperclip
from argparse import ArgumentParser

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('inputFile')

    return parser.parse_args()

def main(args):
    inputFile = args.inputFile

    with open(inputFile, 'rt') as readFile:
        content = readFile.read()

    pyperclip.copy(content)

if __name__ == '__main__':
    args = parseArguments()
    main(args)

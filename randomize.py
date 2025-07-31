from argparse import ArgumentParser
from random import shuffle

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('filename')

    return parser.parse_args()

def main(args):
    filename = args.filename
    with open(filename, 'rt') as readFile:
        contents = readFile.readlines()

    shuffle(contents)

    print(''.join(contents))

if __name__ == '__main__':
    args = parseArguments()
    main(args)

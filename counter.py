from collections import Counter
from json import dumps
from argparse import ArgumentParser

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('file')
    parser.add_argument('--delimeter', default=':')
    parser.add_argument('--field', type=int, default=2)

    return parser.parse_args()

def prettyPrint(dictionary):
    print(dumps(dictionary, sort_keys=True, indent=4))

def main(args):
    filename = args.file
    delimeter = args.delimeter
    field = args.field

    with open(filename, 'rt') as readFile:
        lines = readFile.readlines()

    counter = Counter()

    for line in lines:
        line = line.strip()
        lineSplit = line.split(delimeter)
        theHash = lineSplit[field-1]
        counter[theHash] += 1

    common = counter.most_common(5)
    for thing in common:
        print(thing)

if __name__ == '__main__':
    args = parseArguments()
    main(args)

from argparse import ArgumentParser
from os.path import splitext
from shutil import copy
from os import rename
from subprocess import run

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('input', help='The file to append null byte(s) to')
    parser.add_argument('--bytes', default=1, type=int, help='The amount of null bytes to append')
    parser.add_argument('--count', default=1, type=int, help='The amount of files to produce')
    parser.add_argument('--output', default=None, help='The file to output')

    return parser.parse_args()

def main(args):
    input = args.input
    bytes = args.bytes
    count = args.count
    output = args.output

    filename, extension = splitext(input)

    if output is None:
        output = filename + '_nulled_'

    tempFile = 'temp' + extension
    copy(input, tempFile)
    for i in range(count):
        command =  f"truncate -s +{bytes} {tempFile}"
        run(command.split(' '))
        outputFile = output + str(i) + extension
        rename(tempFile, outputFile)

        if i + 1 < count:
            copy(outputFile, tempFile)

if __name__ == '__main__':
    args = parseArguments()
    main(args)

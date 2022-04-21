import pyperclip
from argparse import ArgumentParser

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('outputFile')

    return parser.parse_args()

def main(args):
    outputFile = args.outputFile

    content = pyperclip.paste()

    with open(outputFile, 'wt') as writeFile:
        writeFile.write(content)

if __name__ == '__main__':
    args = parseArguments()
    main(args)

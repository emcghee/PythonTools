from argparse import ArgumentParser
from base64 import b64encode, b64decode

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('inputFile')
    parser.add_argument('-d', '-D', '--decode', action='store_true', help='Base64 decode the input.')
    parser.add_argument('-o', '-O', '--output', help='The file to write the output to.')

    return parser.parse_args()

def main(args):
    inputFile = args.inputFile
    decode = args.decode
    output = args.output

    with open(inputFile, 'rb') as readFile:
        content = readFile.read()

    if decode:
        b64output = b64decode(content)
    else:
        b64output = b64encode(content)
   
    writeOutput(b64output, output)
        

def writeOutput(content, output):
    if output:
        with open(output, 'wb') as writeFile:
            writeFile.write(content)
    else:
        try:
            contentString = content.decode()
            print(contentString)
        except UnicodeDecodeError:
            print(f"UnicodeDecodeError: Output can not decode to a string (send it to a file with --output).")

if __name__ == '__main__':
    args = parseArguments()
    main(args)

from argparse import ArgumentParser
from pathlib import PureWindowsPath, PurePosixPath
from sys import stdin, argv
from subprocess import Popen, PIPE

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('path', nargs='+')
    parser.add_argument('--absolute', action='store_true', help='Convert relative to absolute path')
    
    return parser.parse_args()

def convertPath(args):
    # Detect if path is native or linux
    # native = 'C:\\Users\\Attack\\Documents\\Github\\PythonTools'
    # native2 = '~\\Documents\\Github\\PythonTools'
    # native3 = 'Documents\\Github\\PythonTools'
    # linux = '/c/Users/Attack/Documents/Github/PythonTools'
    # linux2 = '~/Documents/Github/PythonTools'
    # linux3 = 'Documents/Github/PythonTools'

    path = ' '.join(args.path)

    if not path:
        for line in stdin:
            path = line.strip()

    converted = str()
    # homePath = str(Path.home())

    if '/' in path:
        purePath = PurePosixPath(path)
        partsList = list(purePath.parts)
        if len(partsList):
            root = partsList[0]
            if root == '/':
                if len(partsList) > 1:
                    next = partsList[1]
                    capitalized = next.upper()
                    converted = '\\'.join([capitalized + ':'] + partsList[2:])
                    print(converted)
            else:
                converted = '\\'.join(partsList)
                print(converted)

    else:
        purePath = PureWindowsPath(path)
        partsList = list(purePath.parts)
        if len(partsList):
            root = partsList[0]
            if ':\\' in root:
                drive = root[0]
                lowerized = drive.lower()
                converted = '/'.join(['', lowerized] + partsList[1:])
                print(converted)
            else:
                converted = '/'.join(partsList)
                print(converted)

    import pyperclip
    pyperclip.copy(converted)

def pwd():
    process = Popen('powershell.exe -c pwd', shell=True, stdout=PIPE)
    process.wait()
    stdout = process.stdout.read().decode()
    stdoutSplit = stdout.split('----')
    path = stdoutSplit[-1].strip()
    if ' ' in path:
        print(f'"{path}"')
    else:
        print(path)

    purePath = PureWindowsPath(path)
    partsList = list(purePath.parts)
    if len(partsList):
        root = partsList[0]
        if ':\\' in root:
            drive = root[0]
            lowerized = drive.lower()
            converted = '/'.join(['', lowerized] + partsList[1:])
        else:
            converted = '/'.join(partsList)
        
        if ' ' in converted:
            print(f'"{converted}"')
        else:
            print(converted)

if __name__ == '__main__':
    # args = parseArguments()
    # main(args)
    if len(argv) == 1 or not argv[1]:
        pwd()
    else:
        args = parseArguments()
        convertPath(args)

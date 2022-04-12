from argparse import ArgumentParser
import hashlib

BUFSIZE = 64 * 1024

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('filename', nargs='+')
    parser.add_argument('--md5', action='store_true')
    parser.add_argument('--sha1', action='store_true')
    parser.add_argument('--sha256', action='store_true')

    return parser.parse_args()

def main(args):
    filename = args.filename
    md5 = args.md5
    sha1 = args.sha1
    sha256 = args.sha256

    if not (md5 or sha1 or sha256):
        md5 = True
        sha1 = True
        sha256 = True

    for file in filename:
        md5digest = hashlib.md5()
        sha1digest = hashlib.sha1()
        sha256digest = hashlib.sha256()

        with open(file, 'rb') as readFile:
            while True:
                data = readFile.read(BUFSIZE)
                if not data:
                    break

                if md5:
                    md5digest.update(data)

                if sha1:
                    sha1digest.update(data)

                if sha256:
                    sha256digest.update(data)

        print(f"\n========== {file} ==========")
        if md5:
            print(f"MD5: {md5digest.hexdigest()}")
        
        if sha1:
            print(f"SHA1: {sha1digest.hexdigest()}")

        if sha256:
            print(f"SHA256: {sha256digest.hexdigest()}")

if __name__ == '__main__':
    args = parseArguments()
    main(args)

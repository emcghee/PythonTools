from argparse import ArgumentParser


def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('string', help='The string to check the length of.')

    return parser.parse_args()


def main(args):
    string = args.string
    length = len(string)
    print(length)


if __name__ == "__main__":
    args = parseArguments()
    main(args)

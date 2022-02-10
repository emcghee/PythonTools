import random
import string
import argparse


def generateRandomString(args: argparse.Namespace):
	available = str()
	if args.lowercase:
		available += string.ascii_lowercase
	
	if args.uppercase:
		available += string.ascii_uppercase

	if args.symbols:
		available += string.punctuation

	if args.numbers:
		available += string.digits

	if len(available) == 0:
		print("At least one of -l, -u, -s, or -n is required.")
		return

	length = args.length
	out = str()
	for i in range(length):
		out += random.choice(available)

	print(out)


def parseArguments() -> argparse.Namespace:
	parser = argparse.ArgumentParser()
	parser.add_argument('length', type=int, help='The length of the random string to generate.')
	parser.add_argument('-l', dest='lowercase', action='store_true', help='Include lowercase letters.')
	parser.add_argument('-u', dest='uppercase', action='store_true', help='Include uppercase letters.')
	parser.add_argument('-s', dest='symbols', action='store_true', help='Include symbols.')
	parser.add_argument('-n', dest='numbers', action='store_true', help='Include numbers.')

	args = parser.parse_args()
	return args


def main():
	args = parseArguments()
	generateRandomString(args)


if __name__ == '__main__':
	main()

import argparse
import base64

# Set up argument parser
parser = argparse.ArgumentParser(description='Decode base64 to hexadecimal.')
parser.add_argument('value', type=str, help='The base64 string to decode.')

# Parse the command line arguments
args = parser.parse_args()

# Use the supplied base64 value
base64_str = args.value
base64_bytes = base64_str.encode('utf-8')
hex_bytes = base64.b64decode(base64_bytes)
hex_str = hex_bytes.hex().upper()

print(hex_str)

from base64 import b64decode, b64encode
from argparse import ArgumentParser
from os.path import exists
# import binascii
from itertools import cycle

# from Crypto.Cipher import AES
# from Crypto.Util.Padding import pad, unpad

# def string_to_bytes(string: str, encoding="utf-8") -> bytes:
# 	return str.encode(string, encoding)


# def bytes_to_string(input_bytes: bytes, encoding="utf-8") -> str:
# 	return input_bytes.decode(encoding)


# def encrypt(key: bytes, plaintext: bytes, iv: bytes = None) -> bytes:
#     padded = pad(plaintext, AES.block_size)

#     cipher = AES.new(key, AES.MODE_CBC, iv=iv)
#     iv = cipher.iv
#     ciphertext = cipher.encrypt(padded)
#     return ciphertext + iv


# def decrypt(key: bytes, ciphertext: bytes, iv: bytes = None) -> bytes:
#     if iv is None:
#         ciphertext, iv = split_cipher_iv(ciphertext)
    
#     cipher = AES.new(key, AES.MODE_CBC, iv=iv)
#     plaintext = cipher.decrypt(ciphertext)
#     data = unpad(plaintext, AES.block_size)

#     return data


# def split_cipher_iv(blob: bytes) -> tuple:
#     ciphertext = blob[:-16]
#     iv = blob[-16:]

#     return ciphertext, iv


def xor(plaintext, key):
    return bytes(bytearray(a^b for a, b in zip(plaintext, cycle(key))))


def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('-b', dest='base64input', action='store_true', help='Read as base64 bytes.')
    parser.add_argument('-B', dest='base64output', action='store_true', help='Write as base64 bytes.')
    parser.add_argument('-f', dest='file', action='store_true', help='Read the input from a file.')
    parser.add_argument('-o', dest='output', metavar='output', help='A file to output to.')
    parser.add_argument('key', help='The key to xor with. Base64 string.')
    parser.add_argument('plaintext', help='The input to xor or the filename containing the input if -f is used.')

    return parser


def main(parser):
    args = parser.parse_args()
    base64Input = args.base64input
    base64Output = args.base64output
    file = args.file
    output = args.output
    key = b64decode(args.key)
    print(f"Key: {key.decode()}")
    plaintext = args.plaintext

    if file and not exists(plaintext):
        print(f"[-] File '{plaintext}' does not exist.")
        return
    elif file:
        with open(plaintext, "rb") as readFile:
            payload = readFile.read()
    else:
        payload = plaintext.encode()

    if base64Input:
        payload = b64decode(payload)
        
    encoded = xor(payload, key)
    if base64Output:
        encoded = b64encode(encoded)

    if output:
        with open(output, "wb") as writeFile:
            writeFile.write(encoded)

    else:
        print(encoded)


if __name__ == "__main__":
    parser = parseArguments()
    main(parser)

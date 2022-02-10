from base64 import b64decode, b64encode
from argparse import ArgumentParser
from os.path import exists
import binascii

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

def string_to_bytes(string: str, encoding="utf-8") -> bytes:
	return str.encode(string, encoding)


def bytes_to_string(input_bytes: bytes, encoding="utf-8") -> str:
	return input_bytes.decode(encoding)


def encrypt(key: bytes, plaintext: bytes, iv: bytes = None) -> bytes:
    padded = pad(plaintext, AES.block_size)

    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    iv = cipher.iv
    ciphertext = cipher.encrypt(padded)
    return ciphertext + iv


def decrypt(key: bytes, ciphertext: bytes, iv: bytes = None) -> bytes:
    if iv is None:
        ciphertext, iv = split_cipher_iv(ciphertext)
    
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = cipher.decrypt(ciphertext)
    data = unpad(plaintext, AES.block_size)

    return data


def split_cipher_iv(blob: bytes) -> tuple:
    ciphertext = blob[:-16]
    iv = blob[-16:]

    return ciphertext, iv


def parseArguments():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='subparser')
    encrypt = subparsers.add_parser('encrypt')
    decrypt = subparsers.add_parser('decrypt')

    encrypt.add_argument('-b', dest='base64', action='store_true', help='Output the encrypted bytes as base64.')
    encrypt.add_argument('-f', dest='file', action='store_true', help='Read the plaintext from a file.')
    encrypt.add_argument('-i', dest='iv', metavar='iv', help='The iv to encrypt the payload with. This gets appended to the end of the ciphertext.')  
    encrypt.add_argument('-o', dest='output', metavar='output', help='A file to output the encrypted bytes to.')
    encrypt.add_argument('key', help='The key to encrypt the payload with. Base64 string.')
    encrypt.add_argument('plaintext', help='The plaintext to encrypt or the filename containing the plaintext if -f is used.')

    decrypt.add_argument('-B', dest='base64', action='store_true', help='Input the encrypted bytes as raw bytes (not base64).')
    decrypt.add_argument('-f', dest='file', action='store_true', help='Read the ciphertext from a file.')
    decrypt.add_argument('-i', dest='iv', metavar='iv', help='The iv to decrypt the payload with. If not set this gets extracted from the end of the ciphertext.')    
    decrypt.add_argument('-o', dest='output', metavar='output', help='A file to output the decrypted bytes to.')  
    decrypt.add_argument('key', help='The key to decrypt the payload with. Base64 string.')
    decrypt.add_argument('ciphertext', help='The ciphertext to decrypt or the filename containing the ciphertext if -f is used.')

    return parser


def main(parser):
    args = parser.parse_args()
    if hasattr(args, 'subparser'):
        subparser = getattr(args, 'subparser')
        if subparser == 'encrypt':
            base64 = args.base64
            iv = b64decode(args.iv) if args.iv else None
            key = b64decode(args.key)
            output = args.output
            plaintext = args.plaintext
            file = args.file

            if file and not exists(plaintext):
                print(f"[-] File '{plaintext}' does not exist.")
                return
            elif file:
                with open(plaintext, "rb") as readFile:
                    payload = readFile.read()
            else:
                payload = plaintext.encode()

            encrypted = encrypt(key, payload, iv=iv)

            if base64:
                encrypted = b64encode(encrypted)

            if output:
                with open(output, "wb") as writeFile:
                    writeFile.write(encrypted)

            else:
                print(encrypted)
            
        elif subparser == 'decrypt':
            # Key is base64
            # IV is base64 if included
            # Read from file or take base64 encrypted
            base64 = args.base64
            iv = b64decode(args.iv) if args.iv else None
            key = b64decode(args.key)
            output = args.output
            ciphertext = args.ciphertext
            file = args.file

            if file and not exists(ciphertext):
                print(f"[-] File '{ciphertext}' does not exist.")
                return
            elif file:
                with open(ciphertext, "rb") as readFile:
                    payload = readFile.read()
            else:
                payload = ciphertext

            if not base64:
                try:
                    payload = b64decode(payload)
                except binascii.Error:
                    print(f"[-] Read ciphertext was not base64'd despite no -B flag.")
                    return

            decrypted = decrypt(key, payload, iv=iv)

            if output:
                with open(output, "wb") as writeFile:
                    writeFile.write(decrypted)

            else:
                print(decrypted)
        else:
            parser.print_help()


if __name__ == "__main__":
    parser = parseArguments()
    main(parser)

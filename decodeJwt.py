import base64
import json

def base64url_decode(input_str):
    # Add required padding
    rem = len(input_str) % 4
    if rem > 0:
        input_str += '=' * (4 - rem)
    return base64.urlsafe_b64decode(input_str)

def decode_jwt(jwt):
    header_b64, payload_b64, signature_b64 = jwt.split('.')
    header = json.loads(base64url_decode(header_b64))
    payload = json.loads(base64url_decode(payload_b64))
    return header, payload

from argparse import ArgumentParser

def parseArguments():
    parser = ArgumentParser()

    parser.add_argument('jwt', help='The JWT to decode')
    parser.add_argument('--signature', help='The signature used to sign the JWT which will be validated')

    return parser.parse_args()

def main(args):
    jwt = args.jwt
    signature = args.signature

    if signature:
        raise NotImplementedError("--signature <SIGNATURE> is not implemented yet.")
    
    header, payload = decode_jwt(jwt)
    print("Header:", json.dumps(header, indent=2))
    print("Payload:", json.dumps(payload, indent=2))

if __name__ == '__main__':
    args = parseArguments()
    main(args)

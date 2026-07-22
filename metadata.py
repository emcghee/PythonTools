from argparse import ArgumentParser
import os
from datetime import datetime, timezone

import pefile

STRING_FIELDS = [
    'CompanyName',
    'FileDescription',
    'FileVersion',
    'InternalName',
    'LegalCopyright',
    'LegalTrademarks',
    'OriginalFilename',
    'ProductName',
    'ProductVersion',
    'Comments',
    'PrivateBuild',
    'SpecialBuild',
]

MACHINE_MAP = {
    0x014c: 'x86 (i386)',
    0x0200: 'IA64',
    0x8664: 'x64 (AMD64)',
    0xaa64: 'ARM64',
    0x01c0: 'ARM',
    0x01c4: 'ARMNT',
}

SUBSYSTEM_MAP = {
    1: 'Native',
    2: 'Windows GUI',
    3: 'Windows CUI (console)',
    5: 'OS/2 CUI',
    7: 'POSIX CUI',
    9: 'Windows CE GUI',
    10: 'EFI application',
    11: 'EFI boot service driver',
    12: 'EFI runtime driver',
    13: 'EFI ROM',
    14: 'Xbox',
    16: 'Windows boot application',
}

def parseArguments():
    parser = ArgumentParser(description='Dump version/metadata info from PE executables.')
    parser.add_argument('filename', nargs='+', help='one or more executable paths')
    return parser.parse_args()

def decode(value):
    if isinstance(value, bytes):
        try:
            return value.decode('utf-8').strip('\x00').strip()
        except UnicodeDecodeError:
            return value.decode('latin-1', errors='replace').strip('\x00').strip()
    return str(value).strip('\x00').strip()

def collectStrings(pe):
    strings = {}
    if not hasattr(pe, 'FileInfo'):
        return strings

    for entries in pe.FileInfo:
        for entry in entries:
            if not hasattr(entry, 'StringTable'):
                continue
            for table in entry.StringTable:
                for key, value in table.entries.items():
                    strings[decode(key)] = decode(value)
    return strings

def formatFixedVersion(ms, ls):
    return f"{(ms >> 16) & 0xffff}.{ms & 0xffff}.{(ls >> 16) & 0xffff}.{ls & 0xffff}"

def main(args):
    for file in args.filename:
        print(f"\n========== {file} ==========")

        if not os.path.isfile(file):
            print(f"  [!] not a file")
            continue

        size = os.path.getsize(file)
        print(f"File size:        {size} bytes")

        try:
            pe = pefile.PE(file, fast_load=False)
        except pefile.PEFormatError as e:
            print(f"  [!] not a PE file: {e}")
            continue

        machine = pe.FILE_HEADER.Machine
        print(f"Architecture:     {MACHINE_MAP.get(machine, f'unknown (0x{machine:04x})')}")

        if hasattr(pe, 'OPTIONAL_HEADER'):
            subsys = pe.OPTIONAL_HEADER.Subsystem
            print(f"Subsystem:        {SUBSYSTEM_MAP.get(subsys, f'unknown ({subsys})')}")

        timestamp = pe.FILE_HEADER.TimeDateStamp
        if timestamp:
            compiled = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            print(f"Compile time:     {compiled.isoformat()} (0x{timestamp:08x})")

        try:
            print(f"Imphash:          {pe.get_imphash()}")
        except Exception:
            pass

        if hasattr(pe, 'VS_FIXEDFILEINFO') and pe.VS_FIXEDFILEINFO:
            ffi = pe.VS_FIXEDFILEINFO[0]
            print(f"Fixed FileVer:    {formatFixedVersion(ffi.FileVersionMS, ffi.FileVersionLS)}")
            print(f"Fixed ProductVer: {formatFixedVersion(ffi.ProductVersionMS, ffi.ProductVersionLS)}")

        strings = collectStrings(pe)
        if not strings:
            print("\nNo VS_VERSION_INFO string table present.")
            pe.close()
            continue

        print()
        for field in STRING_FIELDS:
            if field in strings:
                print(f"{field + ':':<18}{strings[field]}")

        extras = {k: v for k, v in strings.items() if k not in STRING_FIELDS}
        for k, v in extras.items():
            print(f"{k + ':':<18}{v}")

        pe.close()

if __name__ == '__main__':
    args = parseArguments()
    main(args)

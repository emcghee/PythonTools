#!/usr/bin/env python3
"""Redact domain/user/host identifiers from PrivescCheck (or PrivKit) BOF output.

Auto-detects identifying values from anchor lines that PrivescCheck always
emits in a known location:

    Hostname     : VM-151                    -> <HOSTNAME>
    FQDN         : VM-151.SCPMCS.net          -> <FQDN>
    DNS Domain   : SCPMCS.net                 -> <DNS_DOMAIN>
    Domain       : SCPMCS                     -> <DOMAIN>
    Name      : SCPMCS\\ekirsch                -> <DOMAIN>\\<USER1>
    User : SCPMCS\\admin.cnihells              -> <DOMAIN>\\<USER2>
    Home : C:\\Users\\ekirsch                   -> C:\\Users\\<USER1>
    S-1-5-21-2699877148-465998499-3477157127  -> <DOMAIN_SID>
    10.59.57.66                                -> <IPv4_1>

Each value gets a stable token so cross-references survive (the same
username always maps to the same <USERN>). Built-in account names
(SYSTEM, NETWORK SERVICE, INTERACTIVE, etc.) and well-known SIDs are
left untouched.

Usage:
    python3 sanitizePrivesccheck.py input.txt              # writes input_sanitized.txt
    python3 sanitizePrivesccheck.py input.txt -o out.txt   # explicit output path
    python3 sanitizePrivesccheck.py input.txt --stdout     # write to stdout instead
    python3 sanitizePrivesccheck.py input.txt --show-mapping
    python3 sanitizePrivesccheck.py input.txt --extra Tanium,SecureLogin
"""

import argparse
import re
import sys
from pathlib import Path


BUILTIN_KEEP = {
    "SYSTEM", "LOCAL SERVICE", "NETWORK SERVICE",
    "INTERACTIVE", "REMOTE INTERACTIVE LOGON",
    "Administrator", "Administrators", "Users", "Everyone",
    "Authenticated Users", "This Organization", "LOCAL",
    "Domain Users", "Domain Admins", "Domain Computers",
    "Domain Controllers", "Enterprise Admins", "Schema Admins",
    "Remote Desktop Users", "Power Users", "Backup Operators",
    "Print Operators", "Account Operators", "Server Operators",
    "Pre-Windows 2000 Compatible Access", "Replicator",
    "Network Configuration Operators", "Performance Log Users",
    "Performance Monitor Users", "Distributed COM Users",
    "Group Policy Creator Owners", "Read-only Domain Controllers",
    "Cloneable Domain Controllers", "Protected Users",
    "Cert Publishers", "DnsAdmins", "DnsUpdateProxy",
    "Mandatory Label",
}

WELL_KNOWN_SIDS = (
    "S-1-0", "S-1-1", "S-1-2", "S-1-3",
    "S-1-5-1", "S-1-5-2", "S-1-5-3", "S-1-5-4", "S-1-5-6",
    "S-1-5-7", "S-1-5-8", "S-1-5-9", "S-1-5-10", "S-1-5-11",
    "S-1-5-12", "S-1-5-13", "S-1-5-14", "S-1-5-15", "S-1-5-17",
    "S-1-5-18", "S-1-5-19", "S-1-5-20",
    "S-1-5-32",          # BUILTIN
    "S-1-5-5-0",         # LogonSessionId parent (the session ID itself is redacted separately)
    "S-1-15",            # AppContainer SIDs
    "S-1-16",            # Integrity labels
    "S-1-18",            # Authentication authority asserted identity
)


def is_well_known_sid(sid):
    # Match exact prefix or prefix followed by a dash so 'S-1-5-2' doesn't swallow 'S-1-5-21-...'.
    return any(sid == p or sid.startswith(p + "-") for p in WELL_KNOWN_SIDS)


# Tight IPv4 regex - each octet 0-255, no adjacent digits/dots
IPV4_RE = re.compile(
    r"(?<![\d.])"
    r"((?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\."
    r"(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\."
    r"(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)\."
    r"(?:25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d))"
    r"(?![\d.])"
)

IPV4_SKIP = {"0.0.0.0", "127.0.0.1", "255.255.255.255"}

IPV6_RE = re.compile(
    r"(?<![\w:])"
    r"(?:[0-9a-fA-F]{1,4}:){2,7}[0-9a-fA-F]{1,4}"
    r"(?![\w:])"
)

IPV6_SKIP = {
    "0000:0000:0000:0000:0000:0000:0000:0000",
    "0000:0000:0000:0000:0000:0000:0000:0001",
}

MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}[-:]){5}[0-9A-Fa-f]{2}\b")


def extract_identifiers(text):
    """First pass: walk the output and build a {literal -> token} map."""
    mapping = {}
    user_counter = [0]
    user_map = {}

    def user_token(uname):
        if uname not in user_map:
            user_counter[0] += 1
            user_map[uname] = f"<USER{user_counter[0]}>"
        return user_map[uname]

    # Use setdefault on all host/domain assignments so the FIRST classifier wins.
    # Reason: HARDENING - Default Local Administrator emits 'Domain : <hostname>'
    # (the local-SAM 'domain' of the Administrator account = the computer name).
    # The Hostname pass must claim that value first, otherwise the later
    # NetBIOS Domain pass would relabel the hostname as <DOMAIN>.

    # Hostname (MISC - System Information)
    for m in re.finditer(r"^\s*Hostname\s*:\s*(\S+)", text, re.MULTILINE):
        mapping.setdefault(m.group(1), "<HOSTNAME>")

    # FQDN — also derive DNS domain from it
    for m in re.finditer(r"^\s*FQDN\s*:\s*(\S+)", text, re.MULTILINE):
        fqdn = m.group(1)
        mapping.setdefault(fqdn, "<FQDN>")
        if "." in fqdn:
            host_part, dns_dom = fqdn.split(".", 1)
            mapping.setdefault(host_part, "<HOSTNAME>")
            if dns_dom:
                mapping.setdefault(dns_dom, "<DNS_DOMAIN>")

    # DNS Domain (explicit field)
    for m in re.finditer(r"^\s*DNS Domain\s*:\s*(\S+)", text, re.MULTILINE):
        mapping.setdefault(m.group(1), "<DNS_DOMAIN>")

    # NetBIOS Domain (MISC - Machine Role / HARDENING - Default Local Administrator)
    for m in re.finditer(r"^\s*Domain\s*:\s*(\S+)", text, re.MULTILINE):
        mapping.setdefault(m.group(1), "<DOMAIN>")

    # USER - Identity (Name : DOMAIN\user)
    for m in re.finditer(r"^\s*Name\s*:\s*([\w-]+)\\([\w.\-]+)", text, re.MULTILINE):
        domain, user = m.group(1), m.group(2)
        if domain not in BUILTIN_KEEP:
            mapping.setdefault(domain, "<DOMAIN>")
        if user not in BUILTIN_KEEP:
            mapping[user] = user_token(user)

    # MISC - User Home Profiles (User : DOMAIN\user)
    for m in re.finditer(r"^\s*User\s*:\s*([\w-]+)\\([\w.\-]+)", text, re.MULTILINE):
        domain, user = m.group(1), m.group(2)
        if domain not in BUILTIN_KEEP:
            mapping.setdefault(domain, "<DOMAIN>")
        if user not in BUILTIN_KEEP:
            mapping[user] = user_token(user)

    # USER - Groups (table rows: DOMAIN\group   SID)
    for m in re.finditer(r"^\s+([\w-]+)\\[\w.\- ]+?\s+S-1-", text, re.MULTILINE):
        domain = m.group(1)
        if domain not in BUILTIN_KEEP:
            mapping.setdefault(domain, "<DOMAIN>")

    # Local Administrators (table rows: [User]/[Group] DOMAIN\name)
    for m in re.finditer(
        r"^\s*\[(User|Group)\]\s+([\w-]+)\\[\w.\- ]+", text, re.MULTILINE
    ):
        domain = m.group(2)
        if domain not in BUILTIN_KEEP:
            mapping.setdefault(domain, "<DOMAIN>")

    # Home paths: C:\Users\username
    for m in re.finditer(
        r"[A-Za-z]:[\\/]Users[\\/]([\w.\-]+)", text
    ):
        user = m.group(1)
        if user not in BUILTIN_KEEP and user.lower() not in {"public", "default", "all users"}:
            mapping[user] = user_token(user)

    # Domain SID prefix (S-1-5-21-X-Y-Z, before any trailing -RID)
    for m in re.finditer(r"\bS-1-5-21-\d+-\d+-\d+", text):
        prefix = m.group(0)
        if not is_well_known_sid(prefix):
            mapping[prefix] = "<DOMAIN_SID>"

    # Logon session IDs (S-1-5-5-0-NNNN)
    for m in re.finditer(r"\bS-1-5-5-0-\d+", text):
        mapping[m.group(0)] = "<LOGON_SESSION>"

    # IPv4 addresses
    ipv4_counter = [0]
    ipv4_map = {}
    for m in IPV4_RE.finditer(text):
        ip = m.group(1)
        if ip in IPV4_SKIP:
            continue
        if ip not in ipv4_map:
            ipv4_counter[0] += 1
            ipv4_map[ip] = f"<IPv4_{ipv4_counter[0]}>"
        mapping[ip] = ipv4_map[ip]

    # IPv6 addresses
    ipv6_counter = [0]
    ipv6_map = {}
    for m in IPV6_RE.finditer(text):
        ip = m.group(0)
        if ip in IPV6_SKIP:
            continue
        if ip not in ipv6_map:
            ipv6_counter[0] += 1
            ipv6_map[ip] = f"<IPv6_{ipv6_counter[0]}>"
        mapping[ip] = ipv6_map[ip]

    # MAC addresses
    mac_counter = [0]
    mac_map = {}
    for m in MAC_RE.finditer(text):
        mac = m.group(0).upper()
        if mac in {"FF-FF-FF-FF-FF-FF", "00-00-00-00-00-00",
                   "FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00"}:
            continue
        # Skip if it looks like a version string by accident (no real test possible
        # since MAC chars are hex-only; rare false positive risk)
        if mac not in mac_map:
            mac_counter[0] += 1
            mac_map[mac] = f"<MAC_{mac_counter[0]}>"
        # Replace both original case forms
        mapping[m.group(0)] = mac_map[mac]

    return mapping


def sanitize(text, mapping, extra=()):
    """Apply mapping (longest-key first) to text. `extra` is an iterable of
    plain literals to redact with <CUSTOM>."""
    full = dict(mapping)
    for term in extra:
        if term:
            full[term] = "<CUSTOM>"

    for key in sorted(full.keys(), key=len, reverse=True):
        text = text.replace(key, full[key])
    return text


def main():
    parser = argparse.ArgumentParser(
        description="Sanitize PrivescCheck/PrivKit output of host-specific identifiers."
    )
    parser.add_argument("input", help="Input file (raw PrivescCheck/PrivKit output)")
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: <INPUT>_sanitized<.ext>)",
    )
    parser.add_argument(
        "--stdout", action="store_true",
        help="Write to stdout instead of a file",
    )
    parser.add_argument(
        "--show-mapping", action="store_true",
        help="Print the identifier->token mapping to stderr",
    )
    parser.add_argument(
        "--extra",
        default="",
        help="Comma-separated extra strings to redact as <CUSTOM>",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    text = input_path.read_text(encoding="utf-8", errors="replace")
    mapping = extract_identifiers(text)

    extra = [t.strip() for t in args.extra.split(",") if t.strip()]
    sanitized = sanitize(text, mapping, extra)

    if args.show_mapping:
        print("Identifier mapping (longest-first):", file=sys.stderr)
        for k in sorted(mapping.keys(), key=len, reverse=True):
            print(f"  {k!r} -> {mapping[k]}", file=sys.stderr)
        if extra:
            print("Extra redactions:", file=sys.stderr)
            for t in extra:
                print(f"  {t!r} -> <CUSTOM>", file=sys.stderr)
        print("", file=sys.stderr)

    if args.stdout:
        sys.stdout.write(sanitized)
        return

    if args.output:
        out_path = Path(args.output)
    else:
        out_path = input_path.with_name(
            f"{input_path.stem}_sanitized{input_path.suffix}"
        )

    out_path.write_text(sanitized, encoding="utf-8")
    print(f"Wrote {len(sanitized):,} bytes to {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""ProxyChains Manager Script"""

import os
import sys
import re
import subprocess
from pathlib import Path


def find_config():
    """Locate the proxychains config, following proxychains4's own lookup order."""
    env_path = os.environ.get('PROXYCHAINS_CONF_FILE')
    candidates = []
    if env_path:
        candidates.append(Path(env_path))
    candidates.extend([
        Path.cwd() / 'proxychains.conf',
        Path.home() / '.proxychains' / 'proxychains.conf',
        Path('/etc/proxychains.conf'),
        Path('/etc/proxychains4.conf'),
        Path('/usr/local/etc/proxychains.conf'),
        Path('/opt/homebrew/etc/proxychains.conf'),
    ])
    for p in candidates:
        if p.is_file():
            return str(p)
    print("Error: could not find proxychains config in any standard location:", file=sys.stderr)
    for p in candidates:
        print(f"  {p}", file=sys.stderr)
    sys.exit(1)


CONFIG = find_config()

PROXY_TYPES = {'socks4', 'socks5', 'http', 'https'}


def needs_sudo(path):
    """Return True if we can't write the file as the current user."""
    return not os.access(path, os.W_OK)


def show_help():
    """Display help information"""
    print("Usage: proxymanager [option] [args]")
    print()
    print("Options:")
    print("  add <proxy>     Add new proxy and comment out old ones")
    print("  swap <target>   Swap active proxy (uncomment target, comment others)")
    print("  clear           Clear all proxies (comment them all out)")
    print("  remove          Remove all proxy lines completely (DELETE)")
    print("  list            List current proxies with line numbers")
    print("  restore         Restore all proxies (uncomment all)")
    print()
    print("Add examples:")
    print("  proxymanager add 127.0.0.1 1080               (defaults to socks5)")
    print("  proxymanager add 127.0.0.1:1080               (colon format)")
    print("  proxymanager add socks5 127.0.0.1 1080        (explicit type)")
    print("  proxymanager add socks4 127.0.0.1:1080        (type + colon format)")
    print("  proxymanager add 127.0.0.1 1080 mytunnel      (with comment)")
    print("  proxymanager add socks5 127.0.0.1:1080 corp   (type + colon + comment)")
    print()
    print("Swap examples:")
    print("  proxymanager swap 2                           (by list number)")
    print("  proxymanager swap 10.10.10.10 9050            (by IP and port)")
    print("  proxymanager swap 10.10.10.10:9050            (by IP:port)")
    print("  proxymanager swap mytunnel                    (by comment)")


def read_config():
    """Read configuration file (using sudo only when needed)."""
    try:
        if os.access(CONFIG, os.R_OK):
            with open(CONFIG, 'r') as f:
                return f.read().splitlines()
        result = subprocess.run(
            ['sudo', 'cat', CONFIG],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.splitlines()
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"Error reading config {CONFIG}: {e}", file=sys.stderr)
        sys.exit(1)


def write_config(lines):
    """Write configuration file (using sudo only when needed)."""
    content = '\n'.join(lines) + '\n'
    try:
        if not needs_sudo(CONFIG):
            with open(CONFIG, 'w') as f:
                f.write(content)
            return
        process = subprocess.Popen(
            ['sudo', 'tee', CONFIG],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            text=True
        )
        process.communicate(input=content)
        if process.returncode != 0:
            raise Exception(f"tee command failed with code {process.returncode}")
    except Exception as e:
        print(f"Error writing config {CONFIG}: {e}", file=sys.stderr)
        sys.exit(1)


def find_proxylist_section(lines):
    """Find the start and end indices of [ProxyList] section"""
    start_idx = None
    end_idx = None

    for i, line in enumerate(lines):
        if line.strip() == '[ProxyList]':
            start_idx = i
        elif start_idx is not None and line.strip().startswith('['):
            end_idx = i
            break

    if start_idx is not None and end_idx is None:
        end_idx = len(lines)

    return start_idx, end_idx


def parse_add_args(args):
    """
    Parse add command arguments. Returns (proxy_type, ip, port, comment).
    Supports:
      IP PORT [COMMENT]
      IP:PORT [COMMENT]
      TYPE IP PORT [COMMENT]
      TYPE IP:PORT [COMMENT]
    """
    if not args:
        return None, None, None, None

    proxy_type = 'socks5'
    comment = None

    # Check if first arg is a proxy type keyword
    if args[0].lower() in PROXY_TYPES:
        proxy_type = args[0].lower()
        args = args[1:]

    if not args:
        return None, None, None, None

    # Check for IP:PORT colon format in first arg
    if ':' in args[0]:
        ip, port = args[0].split(':', 1)
        if len(args) > 1:
            comment = ' '.join(args[1:])
    else:
        ip = args[0]
        if len(args) < 2:
            return None, None, None, None
        port = args[1]
        if len(args) > 2:
            comment = ' '.join(args[2:])

    return proxy_type, ip, port, comment


def get_proxy_entries(lines, start_idx, end_idx):
    """
    Return list of (list_num, file_line_idx, line_content) for all proxy lines.
    list_num is 1-based index for user display/swap reference.
    """
    proxy_pattern = re.compile(r'^#*(socks|http)', re.IGNORECASE)
    entries = []
    num = 1
    for i in range(start_idx + 1, end_idx):
        if proxy_pattern.match(lines[i].strip()):
            entries.append((num, i, lines[i]))
            num += 1
    return entries


def add_proxy(args):
    """Add new proxy and comment out old ones"""
    proxy_type, ip, port, comment = parse_add_args(args)

    if not ip or not port:
        print("Error: Need at least IP and port")
        print("Example: proxymanager add 127.0.0.1 1080")
        print("Example: proxymanager add 127.0.0.1:1080 mytunnel")
        print("Example: proxymanager add socks5 127.0.0.1 1080")
        sys.exit(1)

    new_proxy = f"{proxy_type} {ip} {port}"
    if comment:
        new_proxy += f" # {comment}"

    lines = read_config()
    start_idx, end_idx = find_proxylist_section(lines)

    if start_idx is None:
        print("Error: [ProxyList] section not found in config", file=sys.stderr)
        sys.exit(1)

    # Comment out all existing active proxies in [ProxyList] section
    active_pattern = re.compile(r'^(socks|http)', re.IGNORECASE)
    for i in range(start_idx + 1, end_idx):
        if active_pattern.match(lines[i].strip()):
            lines[i] = '#' + lines[i]

    # Add new proxy after [ProxyList] line
    lines.insert(start_idx + 1, new_proxy)

    write_config(lines)

    print(f"[+] Added new proxy: {new_proxy}")
    print("[+] Old proxies commented out")
    list_proxies()


def swap_proxy(args):
    """
    Swap active proxy. Uncomments the target, comments out all others.
    Target can be: list number, IP PORT pair, IP:PORT, or comment text.
    """
    if not args:
        print("Error: swap requires a target (list number, IP PORT, or comment)")
        print("Example: proxymanager swap 2")
        print("Example: proxymanager swap 10.10.10.10 9050")
        print("Example: proxymanager swap mytunnel")
        sys.exit(1)

    lines = read_config()
    start_idx, end_idx = find_proxylist_section(lines)

    if start_idx is None:
        print("Error: [ProxyList] section not found in config", file=sys.stderr)
        sys.exit(1)

    entries = get_proxy_entries(lines, start_idx, end_idx)

    if not entries:
        print("Error: No proxies found in config")
        sys.exit(1)

    target_idx = None  # file line index of the target proxy

    def match_ip_port(ip_arg, port_arg):
        """Find file line index for a proxy matching ip:port."""
        for _, file_idx, line_content in entries:
            # Strip leading comment marker(s) then parse fields
            stripped = line_content.strip().lstrip('#').strip()
            parts = stripped.split()
            # parts: [type, ip, port, ...]
            if len(parts) >= 3 and parts[1] == ip_arg and parts[2] == port_arg:
                return file_idx
        return None

    def match_comment(search_text):
        """Find file line index for a proxy whose inline comment contains search_text."""
        search_lower = search_text.lower()
        for _, file_idx, line_content in entries:
            stripped = line_content.strip().lstrip('#').strip()
            if '#' in stripped:
                inline_comment = stripped.split('#', 1)[1].strip().lower()
                if search_lower in inline_comment:
                    return file_idx
        return None

    # Match by list number (single purely-numeric arg)
    if len(args) == 1 and args[0].isdigit():
        num = int(args[0])
        for entry_num, file_idx, _ in entries:
            if entry_num == num:
                target_idx = file_idx
                break
        if target_idx is None:
            print(f"Error: No proxy with list number {num}")
            sys.exit(1)

    # Match by IP:PORT colon format (single arg containing ':')
    elif len(args) == 1 and ':' in args[0]:
        ip_arg, port_arg = args[0].split(':', 1)
        target_idx = match_ip_port(ip_arg, port_arg)
        if target_idx is None:
            # Fall back to comment match
            target_idx = match_comment(args[0])
        if target_idx is None:
            print(f"Error: No proxy found matching '{args[0]}'")
            sys.exit(1)

    # Match by IP PORT (two args)
    elif len(args) >= 2:
        target_idx = match_ip_port(args[0], args[1])
        if target_idx is None:
            print(f"Error: No proxy found matching {args[0]} {args[1]}")
            sys.exit(1)

    # Match by comment text (single non-numeric arg)
    else:
        target_idx = match_comment(args[0])
        if target_idx is None:
            print(f"Error: No proxy found with comment matching '{args[0]}'")
            sys.exit(1)

    # Uncomment target, comment out all others
    active_pattern = re.compile(r'^(socks|http)', re.IGNORECASE)
    for entry_num, file_idx, line_content in entries:
        stripped = line_content.strip()
        if file_idx == target_idx:
            # Uncomment: strip leading whitespace and one leading '#'
            if stripped.startswith('#'):
                lines[file_idx] = stripped[1:]
        else:
            # Comment out if currently active
            if active_pattern.match(stripped):
                lines[file_idx] = '#' + lines[file_idx]

    write_config(lines)

    print(f"[+] Swapped active proxy to: {lines[target_idx].strip()}")
    list_proxies()


def clear_proxies():
    """Comment out all proxies"""
    lines = read_config()
    start_idx, end_idx = find_proxylist_section(lines)

    if start_idx is None:
        print("Error: [ProxyList] section not found in config", file=sys.stderr)
        sys.exit(1)

    active_pattern = re.compile(r'^(socks|http)', re.IGNORECASE)
    for i in range(start_idx + 1, end_idx):
        if active_pattern.match(lines[i].strip()):
            lines[i] = '#' + lines[i]

    write_config(lines)

    print("[+] All proxies commented out")
    list_proxies()


def remove_proxies():
    """Actually DELETE all proxy lines (commented and uncommented)"""
    lines = read_config()
    start_idx, end_idx = find_proxylist_section(lines)

    if start_idx is None:
        print("Error: [ProxyList] section not found in config", file=sys.stderr)
        sys.exit(1)

    proxy_pattern = re.compile(r'^#*(socks|http)', re.IGNORECASE)
    new_lines = []
    for i, line in enumerate(lines):
        if start_idx < i < end_idx:
            if not proxy_pattern.match(line.strip()):
                new_lines.append(line)
        else:
            new_lines.append(line)

    write_config(new_lines)

    print("[+] All proxy lines deleted")
    list_proxies()


def list_proxies():
    """List current proxies with list numbers"""
    lines = read_config()
    start_idx, end_idx = find_proxylist_section(lines)

    print()
    print(f"Current ProxyList configuration: ({CONFIG})")
    print("================================")

    if start_idx is None:
        print("(No ProxyList section found)")
        return

    entries = get_proxy_entries(lines, start_idx, end_idx)

    if not entries:
        print("(No proxies configured)")
    else:
        for num, _, line_content in entries:
            stripped = line_content.strip()
            status = "active  " if not stripped.startswith('#') else "inactive"
            print(f"[{num}] ({status}) {stripped}")


def restore_proxies():
    """Uncomment all proxies"""
    lines = read_config()
    start_idx, end_idx = find_proxylist_section(lines)

    if start_idx is None:
        print("Error: [ProxyList] section not found in config", file=sys.stderr)
        sys.exit(1)

    commented_pattern = re.compile(r'^#(socks|http)', re.IGNORECASE)
    for i in range(start_idx + 1, end_idx):
        if commented_pattern.match(lines[i].strip()):
            lines[i] = lines[i].strip()[1:]  # strip leading '#'

    write_config(lines)

    print("[+] All proxies restored (uncommented)")
    list_proxies()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        show_help()
        return

    command = sys.argv[1]

    if command == 'add':
        add_proxy(sys.argv[2:])
    elif command == 'swap':
        swap_proxy(sys.argv[2:])
    elif command == 'clear':
        clear_proxies()
    elif command == 'remove':
        remove_proxies()
    elif command == 'list':
        list_proxies()
    elif command == 'restore':
        restore_proxies()
    else:
        show_help()


if __name__ == '__main__':
    main()

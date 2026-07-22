# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A flat collection of single-purpose Python CLI utilities used in red-team / offensive-security workflows (encoding, hashing, Kerberos ticket handling, NTLM, proxychains config, infra status, session logging, output sanitization, etc.). Each file is an independent script — there is no package, no shared library module, and no import graph between scripts.

## Running scripts

Scripts are invoked directly with `python <name>.py` and rely on shell aliases for ergonomics. `aliases.txt` is the source of truth for the public names — when adding a new script that users will invoke regularly, add an alias line using the `<PATH>` placeholder so it matches the existing pattern (the user substitutes `<PATH>` in their shell rc). The `pc` alias for `proxychains.py` is hard-coded to a Linux VM share path and is intentionally separate from the rest.

## Adding a new script

Follow the prevailing pattern — deviation creates inconsistency since these scripts are read and copy-pasted as templates:

- `parseArguments()` builds and returns an `argparse.ArgumentParser` (or its parsed `Namespace`); `main(args)` does the work; `if __name__ == '__main__':` wires them together.
- Subcommand-style scripts (see `aes.py`) return the parser itself from `parseArguments()` so `main(parser)` can call `parser.print_help()` when no subcommand is given.
- Scripts are platform-agnostic by default; when a script must branch on OS, dispatch at the bottom (`if sys.platform == "win32":`) and keep the per-platform implementations as separate top-level functions (see `logsession.py`).

## Dependencies

Dependency tracking is incomplete and historically loose:

- `requirements.txt` / `Pipfile` list only `pyperclip`. Real third-party imports in the tree include `pycryptodome` (`from Crypto...` in `aes.py`, `ntlm.py`), `tabulate` (`status.py`), `impacket` (`ticketConvert.py`, `getst_wrap.py`), and `pywinpty` (Windows path of `logsession.py`).
- When adding a script with a new dependency, install it ad-hoc rather than assuming the lockfile reflects reality. Don't "fix" the lockfile to match — that's a separate cleanup the user hasn't asked for.

## Non-obvious script behavior

- **`status.py`** parses `tailscale status` output and groups hosts by hostname prefix tied to red-team infra roles: `cs-`/`cs2n1-` = Cobalt Strike, `gp-` = GoPhish, `nh-` = Nighthawk, `pwn-` = PwnDrop, `redir-` = redirector, `s1-` = Stage1. Adding a new infra type means adding both the CLI flag and the prefix match.
- **`proxychains.py`** mutates the system `proxychains.conf` (searches a fixed candidate list including `/etc`, `/opt/homebrew/etc`, etc.) and shells out to `sudo` only when the current user lacks write access. Operations target the `[ProxyList]` section specifically — preserve that section boundary when editing.
- **`ticketConvert.py`** auto-detects kirbi vs ccache by magic byte and shells out to a sibling `describeTicket.py` (Impacket script, not in this repo) after conversion.
- **`getst_wrap.py`** is an Impacket `getST.py` automation wrapper — it expects `getST.py` on `PATH` and writes/cleans up `.ccache`/`.kirbi` files in the cwd.
- **`logsession.py`** runs an interactive shell under a PTY and tees output to a log file; the Unix path uses `pty`+`select`, the Windows path uses `pywinpty`+threads. If `logfile` already exists, it auto-suffixes `-1`, `-2`, etc. rather than appending or overwriting.
- **`sanitizePrivesccheck.py`** redacts identifiers from PrivescCheck/PrivKit BOF output using stable token mappings (same username → same `<USERN>` across the file) and preserves well-known SIDs and built-in account names.

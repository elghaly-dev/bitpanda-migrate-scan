#!/usr/bin/env python3
"""bitpanda-migrate-scan: find legacy Bitpanda API usage in a source tree.

Single file, Python 3 standard library only. No network access.
Files are only read as text. Files whose name starts with ".env" are never
opened. Secrets are never printed: a suspected key is reported as
file:line plus the first 8 hex characters of its sha256.

Author: Wyndham Heaven (elghaly). License: ISC.
"""
import argparse
import hashlib
import json
import os
import re
import sys

__version__ = "0.1.0"

LEGACY_HOST = "api.bitpanda.com"
NEW_BASE = "https://api.public.bitpanda.com"

# (legacy path, [new endpoints], scope hint). Longest legacy path wins.
# Source: https://docs.public.bitpanda.com/migrating-from-the-legacy-api
MAPPING = [
    ("/wallets/transactions", ["GET /v1/operations"], "Transaction"),
    ("/fiatwallets/transactions", ["GET /v1/operations"], "Transaction"),
    ("/assets/transactions/commodity", ["GET /v1/operations"], "Transaction"),
    ("/asset-wallets", ["GET /v1/portfolio"], "Balances"),
    ("/fiatwallets", ["GET /v1/portfolio"], "Balances"),
    ("/wallets", ["GET /v1/portfolio"], "Balances"),
    ("/trades", ["GET /v1/operations"], "Transaction"),
    (
        "/ticker",
        ["GET /v1/assets", "GET /v1/currencies", "GET /v1/tickers/{assetId}"],
        "Trade (Read) - UNVERIFIED per endpoint",
    ),
]

EXTS = {
    ".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".gs", ".py", ".yaml",
    ".yml", ".json", ".sh", ".bash", ".ps1", ".rb", ".php", ".go", ".java",
    ".kt", ".cs", ".rs", ".toml", ".ini", ".cfg", ".txt", ".md", ".ipynb",
    ".html", ".vue",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "dist", "build", ".tox"}
MAX_BYTES = 2 * 1024 * 1024

URL_RE = re.compile(
    r"(?<![\w.-])api\.bitpanda\.com(?::\d+)?(?P<path>/[A-Za-z0-9_\-/{}$.]*)?"
)
KEY_RE = re.compile(
    r"""(?ix)
    (?:api[_-]?key|apikey|x-api-key|bitpanda[_-]?(?:key|token|secret)|secret|token)
    ["']?\s*[:=]\s*["'](?P<val>[A-Za-z0-9_\-+/=]{20,})["']
    """
)
PLACEHOLDER_RE = re.compile(r"(?i)(your|example|placeholder|changeme|xxxx|<|\$\{|process\.env|getenv|\*{3,})")

REMINDER = """\
Reminder - when you move to the new API:
  * Create a NEW read-only API key in your Bitpanda account
    (https://app.bitpanda.com/my-account/apikey). Grant only the Balances and
    Transaction scopes. Do not grant Trade (Write) or Earn (Write).
    If you migrate /ticker calls you also need Trade (Read) - UNVERIFIED which
    scope each market-data endpoint checks.
  * Turn on the IP allow list for the key and set an expiry (maximum 1 year).
  * Send the key in the x-api-key header; load it from an environment
    variable or secret manager, never from source code.
  * Legacy API access ends 31 January 2027.
"""


def lookup(path):
    """Return (legacy_prefix, new_endpoints, scope) for a legacy path or None."""
    if path is None:
        return None
    p = path.rstrip("/.")
    if p.startswith("/v1"):
        p = p[3:]
    for legacy, new, scope in MAPPING:
        if p == legacy or p.startswith(legacy + "/") or p.startswith(legacy + "$") or p.startswith(legacy + "{"):
            return legacy, new, scope
    return None


def fingerprint(value):
    return hashlib.sha256(value.encode("utf-8", "replace")).hexdigest()[:8]


def scan_text(text, name="<text>"):
    """Yield hit dicts for one file's text. Never includes raw source lines."""
    for lineno, line in enumerate(text.splitlines(), 1):
        for m in URL_RE.finditer(line):
            path = m.group("path")
            found = lookup(path)
            hit = {"file": name, "line": lineno, "kind": "legacy-endpoint",
                   "found": LEGACY_HOST + (path or "")}
            if found:
                hit["new"] = found[1]
                hit["scope"] = found[2]
            elif path and re.fullmatch(r"/v1/?", path):
                hit["note"] = "Legacy base URL. Check each call built from it."
            else:
                hit["note"] = "Legacy host, no mapping in the migration guide. Review by hand."
            yield hit
        for m in KEY_RE.finditer(line):
            val = m.group("val")
            if PLACEHOLDER_RE.search(val):
                continue
            yield {"file": name, "line": lineno, "kind": "possible-key",
                   "fingerprint": fingerprint(val)}


def iter_files(root):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        for fn in sorted(filenames):
            if fn.startswith(".env"):
                continue
            if os.path.splitext(fn)[1].lower() in EXTS:
                yield os.path.join(dirpath, fn)


def scan_path(root):
    hits = []
    for path in iter_files(root):
        try:
            if os.path.getsize(path) > MAX_BYTES:
                continue
            with open(path, "rb") as fh:
                raw = fh.read()
        except OSError:
            continue
        if b"\0" in raw:
            continue
        rel = os.path.relpath(path, root) if os.path.isdir(root) else path
        hits.extend(scan_text(raw.decode("utf-8", "replace"), rel))
    return hits


def render(hits):
    out = []
    for h in hits:
        loc = "%s:%d" % (h["file"], h["line"])
        if h["kind"] == "possible-key":
            out.append("%s  possible API key in source (sha256:%s). Value not shown. "
                       "Rotate it and move it out of the code." % (loc, h["fingerprint"]))
        elif "new" in h:
            out.append("%s  %s\n    -> %s %s  [scope: %s]" % (
                loc, h["found"], NEW_BASE, "  or  ".join(h["new"]), h["scope"]))
        else:
            out.append("%s  %s\n    -> %s" % (loc, h["found"], h["note"]))
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Find legacy Bitpanda API usage (offline).")
    ap.add_argument("path", help="directory or file to scan")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--exit-zero", action="store_true", help="always exit 0")
    ap.add_argument("--version", action="version", version=__version__)
    args = ap.parse_args(argv)
    if not os.path.exists(args.path):
        print("path not found: %s" % args.path, file=sys.stderr)
        return 2
    hits = scan_path(args.path)
    if args.json:
        print(json.dumps(hits, indent=2))
    else:
        if hits:
            print(render(hits))
            n = sum(1 for h in hits if h["kind"] == "legacy-endpoint")
            print("\n%d legacy endpoint hit(s), %d possible key(s)." % (
                n, len(hits) - n))
            print(REMINDER)
        else:
            print("No legacy Bitpanda API usage found.")
    return 0 if (args.exit_zero or not hits) else 1


if __name__ == "__main__":
    sys.exit(main())

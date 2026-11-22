# bitpanda-migrate-scan

An open-source, offline scanner that finds code still calling the legacy Bitpanda API
(`api.bitpanda.com/v1`) and prints the matching endpoint of the new Bitpanda Public API
(`api.public.bitpanda.com`).

Bitpanda's migration guide says the legacy API is available only until **31 January 2027**.

Author: Wyndham Heaven (elghaly). Licence: ISC. Not affiliated with Bitpanda.

## What it does

* One file, Python 3, standard library only (`bitpanda_migrate_scan.py`).
* Makes no network calls.
* Walks a directory and reads `.js .ts .gs (Apps Script) .py .yaml/.yml (Home Assistant) .json` and
  other text files. Files whose names start with `.env` are never opened.
* Prints `file:line`, the legacy endpoint found, the suggested new endpoint and the scope it needs.
* Never prints source lines. If something looks like an API key, it prints only `file:line` and the
  first 8 characters of its sha256, so you can tell keys apart without exposing them.
* Ends with a reminder: create a read-only key (Balances and Transaction scopes only, no Trade or Earn
  write), turn on the IP allow list, and set an expiry.

## Use

```
python3 bitpanda_migrate_scan.py path/to/project
python3 bitpanda_migrate_scan.py path/to/project --json
```

Exit code: 0 nothing found, 1 hits found, 2 bad path. `--exit-zero` always returns 0.

Example output:

```
sample.gs:3  api.bitpanda.com/v1/wallets
    -> https://api.public.bitpanda.com GET /v1/portfolio  [scope: Balances]
sample.py:4  possible API key in source (sha256:d41b649d). Value not shown. Rotate it and move it out of the code.
```

## Mapping

See [MAPPING.md](MAPPING.md) for the table, sources, and how the `/v1` prefix question was resolved.
Short version: the hosted docs and the live gateway use `/v1`; the GitHub `openapi.yaml` omits it and
looks out of date.

## Limits

* It matches the literal host `api.bitpanda.com`. Code that builds the host from config or an
  environment variable is not found; search for your own variable names too.
* The new responses are shaped differently (unified portfolio and operations). The scanner points to
  the new endpoint; you still update your parsing code.
* Per-endpoint scope requirements are UNVERIFIED (not in the published OpenAPI document).
* This tool never asks for or uses a Bitpanda key. Test the new endpoints yourself with a key you create.

## Tests

```
python3 -m unittest discover -s tests -v
```

Fixtures in `tests/fixtures` are known-answer samples (Apps Script, Home Assistant YAML, Python).
CI runs them on Python 3.9 and 3.12.

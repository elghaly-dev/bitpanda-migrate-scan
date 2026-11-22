# Legacy to new endpoint mapping

Legacy base: `https://api.bitpanda.com/v1` (available until 31 January 2027).
New base: `https://api.public.bitpanda.com`, with a `/v1` path prefix (see "The /v1 prefix" below).

| Legacy endpoint | New endpoint | Scope (from the key-generation docs) | Source |
| --- | --- | --- | --- |
| `GET /v1/wallets` | `GET /v1/portfolio` | Balances | [Migration guide][guide] |
| `GET /v1/fiatwallets` | `GET /v1/portfolio` | Balances | [Migration guide][guide] |
| `GET /v1/asset-wallets` | `GET /v1/portfolio` | Balances | [Migration guide][guide] |
| `GET /v1/trades` | `GET /v1/operations` | Transaction | [Migration guide][guide] |
| `GET /v1/wallets/transactions` | `GET /v1/operations` | Transaction | [Migration guide][guide] |
| `GET /v1/fiatwallets/transactions` | `GET /v1/operations` | Transaction | [Migration guide][guide] |
| `GET /v1/assets/transactions/commodity` | `GET /v1/operations` | Transaction | [Migration guide][guide] |
| `GET /v1/ticker` | `GET /v1/assets`, `GET /v1/currencies`, `GET /v1/tickers/{assetId}` | Trade (Read) (UNVERIFIED per endpoint) | [Migration guide][guide] |

Endpoints with no legacy equivalent: `GET /v1/portfolio-history`, `POST /v1/quotes`,
`POST /v1/quotes/{id}/accept`, `GET /v1/earn/configs`, `POST /v1/earn/actions/{action}`.

Notes:

* The unified `/v1/portfolio` and `/v1/operations` responses have a different shape from the
  separate wallet and transaction responses. Moving the URL is not enough; update your data model.
* Scopes: Balances = balances and portfolio data; Transaction = historical operations;
  Trade (Read) = market data, assets, currencies. Per-endpoint scope requirements are not
  published in the OpenAPI document, so the endpoint-to-scope column follows the scope descriptions
  and is UNVERIFIED until tested with a real key.
* Keys: maximum validity 1 year, optional IP allow list, header `x-api-key` ([API key generation][keys]).
* The scanner only maps the rows above. Any other `api.bitpanda.com` path is reported as "review by hand".

## The /v1 prefix

The migration guide lists new paths with `/v1`. The README and `docs/openapi.yaml` in
`bitpanda-labs/bitpanda-public-api` list them without it (for example `/portfolio/holdings`,
`/rfq/quotes`, `/earn/stake`). Checked on 2026-11-22:

* Hosted docs pages (docs.public.bitpanda.com) define paths as `/v1/portfolio`, `/v1/operations`,
  `/v1/quotes`, `/v1/assets`, `/v1/currencies`, `/v1/tickers/{assetId}`, `/v1/portfolio-history`.
* GitHub `docs/openapi.yaml` (commit 83e1203) has server `https://api.public.bitpanda.com` and no `/v1`
  in any path, and uses different names for some paths (`/portfolio/holdings`, `/portfolio/history`,
  `/rfq/quotes`, `/earn/stake`). Its changelog is empty, so it appears out of date compared to the hosted docs.
* Unauthenticated probe of the live host (no key sent): `/v1/portfolio`, `/v1/operations`, `/v1/assets` and
  `/v1/portfolio/holdings` answer 401; the same paths without `/v1` answer 404. So the live gateway serves
  under `/v1`. A 401 is also returned for unknown `/v1/...` paths, so this proves the prefix, not the
  exact path names after it.
* Conclusion: use `/v1/...` and the path names from the hosted docs. Whether `/v1/portfolio` or
  `/v1/portfolio/holdings` answers for an authenticated key is UNVERIFIED (no key was used).

[guide]: https://docs.public.bitpanda.com/migrating-from-the-legacy-api
[keys]: https://docs.public.bitpanda.com/api-key-generation

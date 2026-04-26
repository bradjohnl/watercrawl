# SearXNG Search Backend

This fork adds a [SearXNG](https://github.com/searxng/searxng) search backend as an alternative to the upstream Google Custom Search Engine (CSE) backend. Use it when you want a self-hosted, key-free, privacy-respecting search source for WaterCrawl's `/search` API.

## How it works

`SearXNGSearchScrapper` (`backend/spider/spiders/searxng_search.py`) is a Scrapy spider that queries a SearXNG JSON endpoint instead of Google CSE. It is a drop-in replacement selected at runtime via the `SCRAPY_SEARCH_BACKEND` environment variable, so the rest of WaterCrawl (search request lifecycle, advanced crawling, result enrichment) is unchanged.

## Prerequisites

A running SearXNG instance reachable from the WaterCrawl `app` and `celery` containers, with the **JSON output format enabled**. By default SearXNG only enables HTML output.

In your SearXNG `settings.yml` under `search:`:

```yaml
search:
  formats:
    - html
    - json
```

If SearXNG runs on the Docker host and WaterCrawl runs in containers on the default bridge network, the host is reachable as `172.17.0.1`. On other setups (Docker Desktop, custom networks), use the appropriate hostname (`host.docker.internal`, the SearXNG service name on a shared compose network, etc.).

## Configuration

Set these in `docker/.env` (or your environment):

| Variable | Default | Description |
| --- | --- | --- |
| `SCRAPY_SEARCH_BACKEND` | `GoogleCustomSearchScrapper` | Set to `SearXNGSearchScrapper` to activate this backend. |
| `SCRAPY_SEARXNG_URL` | `http://172.17.0.1:4000` | Base URL of the SearXNG instance (no trailing path; the spider appends `/search`). |
| `SCRAPY_SEARXNG_SEARCH_PAGE_LIMIT` | `3` | Max pages of SearXNG results to paginate through per query. |

Then restart the stack:

```sh
docker compose up -d --build
```

## Verifying

1. Issue a search via the WaterCrawl API (or UI).
2. Watch celery logs: `docker compose logs -f celery`. You should see `Starting SearXNG search for query: ...`.
3. Confirm SearXNG receives the request: it should show `/search?q=...&format=json&pageno=1` in its access log.

## Behavior notes

- **Time range** filters from WaterCrawl (`h1`, `d1`, `w1`, `m1`, `y1`) are mapped to SearXNG's coarser ranges (`day`, `week`, `month`, `year`). SearXNG has no "last hour", so `h1` maps to `day`.
- **Language** is forwarded as the SearXNG `language` query parameter when set.
- **Pagination** stops at whichever comes first: `SCRAPY_SEARXNG_SEARCH_PAGE_LIMIT`, the WaterCrawl `result_limit`, or an empty result page.
- **Result enrichment** (advanced crawling of each result URL) works identically to the Google backend: this spider inherits from `SearchScrapper` and calls `append_result` + `advanced_search`.

## Switching back to Google

Unset (or set to default) `SCRAPY_SEARCH_BACKEND` and restart. The change is per-process; no migrations needed.

## Troubleshooting

- **`Connection refused` / spider hangs**: WaterCrawl can't reach SearXNG. Verify the URL from inside the celery container: `docker compose exec celery curl -fsS "$SCRAPY_SEARXNG_URL/search?q=test&format=json"`.
- **`format=json` returns HTML or 403**: SearXNG `settings.yml` is missing the `json` format under `search.formats`. Add it and restart SearXNG.
- **Empty results**: Try the same query directly against SearXNG. Check that SearXNG has at least one engine enabled that returns results for your query and language.

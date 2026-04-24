from typing import Iterable

from scrapy import Request

from spider.spiders.google_search import SearchScrapper
from spider import settings


class SearXNGSearchScrapper(SearchScrapper):
    """Search spider using a self-hosted SearXNG instance."""

    name = "SearXNGSearchScrapper"
    allowed_domains = []

    # SearXNG time range mapping (WaterCrawl -> SearXNG format)
    TIME_RANGE_MAP = {
        "h1": "day",     # Last hour -> day (SearXNG minimum)
        "d1": "day",
        "w1": "week",
        "m1": "month",
        "y1": "year",
    }

    def make_url(self, page=1):
        base_url = settings.SEARXNG_URL.rstrip("/")
        params = {
            "q": self.helpers.search_query,
            "format": "json",
            "pageno": str(page),
        }

        if self.helpers.language:
            params["language"] = self.helpers.language

        if self.helpers.time_range:
            mapped = self.TIME_RANGE_MAP.get(
                self.helpers.time_range[0], None
            )
            if mapped:
                params["time_range"] = mapped

        query_string = "&".join(
            f"{key}={value}" for key, value in params.items() if value
        )
        return f"{base_url}/search?{query_string}"

    def start_requests(self) -> Iterable[Request]:
        self.pubsub_service.send_feed(
            f"Starting SearXNG search for query: {self.helpers.search_query}",
            feed_type="info",
        )
        yield Request(
            url=self.make_url(),
            callback=self.parse_json,
            errback=self.search_error,
            meta={"skip_playwright": True, "page": 1},
        )

    def parse_json(self, response):
        data = response.json()
        results = data.get("results", [])

        for item in results:
            url = item.get("url", "")
            title = item.get("title", "")
            description = item.get("content", "")

            if not url:
                continue

            if self.append_result(
                url=url,
                title=title,
                description=description,
            ):
                yield from self.advanced_search(
                    url=url,
                    title=title,
                    description=description,
                )

            if len(self.results) >= self.search_service.search_request.result_limit:
                return

        # Paginate if more results needed
        current_page = response.meta.get("page", 1)
        max_pages = getattr(settings, "SEARXNG_SEARCH_PAGE_LIMIT", 3)

        if (
            results
            and len(self.results) < self.search_service.search_request.result_limit
            and current_page < max_pages
        ):
            next_page = current_page + 1
            self.pubsub_service.send_feed(
                f"Fetching SearXNG page {next_page}", feed_type="info"
            )
            yield Request(
                url=self.make_url(page=next_page),
                callback=self.parse_json,
                errback=self.search_error,
                meta={"skip_playwright": True, "page": next_page},
            )

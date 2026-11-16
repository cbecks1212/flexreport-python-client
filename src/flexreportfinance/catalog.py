from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from ._client import FlexreportClient


class _Route(NamedTuple):
    method: str
    send: str  # "json": parameters is the JSON body; "query": parameters go in the query string; "body": the body is parameters[body_key] on its own
    body_key: str | None = None


ENDPOINT_METHOD_MAPPER: dict[str, _Route] = {
    # earnings_endpoints.py
    "/get-earnings-topics": _Route("POST", "query"),
    "/summarize-earnings-transcript": _Route("POST", "json"),
    "/summarize-stock-news": _Route("POST", "query"),
    "/list-upcoming-earnings-announcements": _Route("POST", "json"),
    "/predict-earnings-announcement-move": _Route("POST", "json"),
    "/earnings-season-cohort": _Route("POST", "json"),
    "/earnings-history": _Route("POST", "json"),
    "/get-realtime-events": _Route("POST", "json"),
    "/transcript-guidance": _Route("POST", "json"),
    "/transcript-analysis": _Route("POST", "json"),
    # financial_endpoints.py
    "/list-financial-items": _Route("GET", "query"),
    "/list-financial-ratios": _Route("GET", "query"),
    "/list-as-reported-items": _Route("GET", "query"),
    "/list-revenue-segments": _Route("GET", "query"),
    "/list-tickers": _Route("GET", "query"),
    "/get-fiscal-quarter": _Route("GET", "query"),
    "/get-sectors": _Route("GET", "query"),
    "/get-sub-industries": _Route("GET", "query"),
    "/list-realtime-event-options": _Route("GET", "query"),
    "/list-institutional-investor-types": _Route("GET", "query"),
    "/list-countries": _Route("GET", "query"),
    "/list-symbols-with-names": _Route("GET", "query"),
    "/list-marketcap-options": _Route("GET", "query"),
    "/get-company-snapshot": _Route("GET", "query"),
    "/situate-company": _Route("GET", "query"),
    "/situate-market": _Route("GET", "query"),
    "/company-financials": _Route("POST", "json"),
    # insider_trading.py
    "/insider-transactions": _Route("POST", "json"),
    "/insider-activity-summary": _Route("POST", "json"),
    # institutional_ownership.py
    "/13f-position-change": _Route("POST", "json"),
    "/13f-position-by-manager-type": _Route("POST", "json"),
    "/13f-cik-allocation": _Route("POST", "json"),
    "/list-institutional-managers": _Route("GET", "query"),
    # ir_endpoints.py
    "/ir-document-analysis": _Route("POST", "json"),
    "/ir-document": _Route("POST", "json"),
    "/ir-content": _Route("POST", "json"),
    "/ir-documents-season": _Route("POST", "json"),
    # price_endpoints.py
    "/get-aftermarket-data": _Route("POST", "json"),
    "/get-stock-performance-ytd": _Route("GET", "query"),
    "/get-intraday-stock-performance": _Route("POST", "body", "symbols"),
    "/get-intraday-data": _Route("GET", "query"),
    "/detect-intraday-outlier-jumps": _Route("GET", "query"),
    "/list-technical-indicators": _Route("GET", "query"),
    "/list-intraday-chart-options": _Route("GET", "query"),
    "/technical-indicator-endpoint": _Route("GET", "query"),
    "/is-market-open": _Route("GET", "query"),
}

DATA_ENDPOINT_DESCRIPTIONS: dict[str, dict[str, Any]] = {
    # Earnings
    "/get-earnings-topics": {
        "description": "Returns the most mentioned topics across earnings calls for a given year and quarter.",
        "sample_parameters": {"year": 2026, "quarter": 3},
    },
    "/summarize-earnings-transcript": {
        "description": "Returns a summary of a company's earnings call transcript for a given year and quarter.",
        "sample_parameters": {"ticker": "AAPL", "year": 2026, "quarter": 3},
    },
    "/summarize-stock-news": {
        "description": "Returns a summary of recent news about a company.",
        "sample_parameters": {"ticker": "AAPL"},
    },
    "/list-upcoming-earnings-announcements": {
        "description": "Lists earnings announcements scheduled between two dates, optionally filtered by symbol, industry, sector or market cap.",
        "sample_parameters": {"start_date": "2026-11-16", "end_date": "2026-11-20", "sector": ["Technology"]},
    },
    "/predict-earnings-announcement-move": {
        "description": "Predicts the size of a stock's move on its next earnings report, alongside its average past earnings reaction.",
        "sample_parameters": {"symbols": ["AAPL", "MSFT"]},
    },
    "/earnings-season-cohort": {
        "description": "Returns each covered company's latest result this earnings season, with actual vs estimated EPS and revenue and whether it beat, missed or came in line.",
        "sample_parameters": {"sector": "Technology", "sp_index": True, "limit": 50},
    },
    "/earnings-history": {
        "description": "Returns a company's reported quarters, newest first, with adjusted EPS and revenue vs estimates, the surprise and the next scheduled report.",
        "sample_parameters": {"symbol": "AAPL", "limit": 8},
    },
    "/get-realtime-events": {
        "description": "Returns the latest realtime events of one type, such as EPS updates, gainers, losers or transcript updates.",
        "sample_parameters": {"event_type": "eps_update", "tickers": ["AAPL"]},
    },
    "/transcript-guidance": {
        "description": "Returns how a company's guidance changed on each earnings call (raised, in line, revised down or not provided), newest first.",
        "sample_parameters": {"symbol": "AAPL", "limit": 4},
    },
    "/transcript-analysis": {
        "description": "Returns a call-over-call analysis of a company's earnings transcripts: what each call added, removed, strengthened or weakened, with source links.",
        "sample_parameters": {"symbol": "AAPL", "limit": 1},
    },
    # Financials and lookups
    "/list-financial-items": {
        "description": "Lists the standardized EDGAR financial line items available.",
        "sample_parameters": {},
    },
    "/list-financial-ratios": {
        "description": "Lists the EDGAR financial ratios available.",
        "sample_parameters": {},
    },
    "/list-as-reported-items": {
        "description": "Lists the XBRL concepts a company tags in its own 10-Q and 10-K filings.",
        "sample_parameters": {"ticker": "AAPL"},
    },
    "/list-revenue-segments": {
        "description": "Lists a company's revenue segments as tagged in its filings.",
        "sample_parameters": {"ticker": "AAPL"},
    },
    "/list-tickers": {
        "description": "Lists every ticker Flexreport Finance covers, with its company or index name.",
        "sample_parameters": {},
    },
    "/get-fiscal-quarter": {
        "description": "Returns the most recent fiscal quarter companies will report on.",
        "sample_parameters": {},
    },
    "/get-sectors": {
        "description": "Lists all company sectors.",
        "sample_parameters": {},
    },
    "/get-sub-industries": {
        "description": "Lists the sub-industries within one or more sectors.",
        "sample_parameters": {"sector": ["Technology", "Energy"]},
    },
    "/list-realtime-event-options": {
        "description": "Lists the realtime event types, each with its family, a description and related follow-up endpoints.",
        "sample_parameters": {},
    },
    "/list-institutional-investor-types": {
        "description": "Lists the institutional investor types used to group 13F ownership.",
        "sample_parameters": {},
    },
    "/list-countries": {
        "description": "Lists the countries Flexreport Finance covers.",
        "sample_parameters": {},
    },
    "/list-symbols-with-names": {
        "description": "Returns every covered symbol paired with its company name.",
        "sample_parameters": {},
    },
    "/list-marketcap-options": {
        "description": "Lists the market-cap categories used as filters.",
        "sample_parameters": {},
    },
    "/get-company-snapshot": {
        "description": "Returns a company snapshot covering its investment thesis, price performance, analyst ratings and targets, financials, ownership and recent news.",
        "sample_parameters": {"symbol": "AAPL"},
    },
    "/situate-company": {
        "description": "Summarizes the recent events that matter for a company and points to the endpoints that go deeper on each.",
        "sample_parameters": {"symbol": "AAPL", "window_days": 14},
    },
    "/situate-market": {
        "description": "Returns the realtime event types relevant to a market question, in reading order, with the tickers each currently covers.",
        "sample_parameters": {"question": "Which companies beat earnings this week?"},
    },
    "/company-financials": {
        "description": "Returns a company's standardized or as-reported EDGAR financials, 8-K financial tables or year-over-year changes.",
        "sample_parameters": {"symbol": "AAPL", "financial_type": "edgar_quarterly_financials", "limit": 5, "line_items": ["revenue", "netIncome"]},
    },
    # Insider trading
    "/insider-transactions": {
        "description": "Returns a company's Form 4 transactions by senior insiders over the last 6 months, newest first, with footnotes and SEC links.",
        "sample_parameters": {"symbol": "AAPL", "side": ["BUY", "SELL"], "role": ["ceo"], "limit": 50},
    },
    "/insider-activity-summary": {
        "description": "Returns a company's quarterly insider buying and selling totals and each senior insider's net activity over the last 6 months.",
        "sample_parameters": {"symbol": "AAPL", "limit": 8},
    },
    # Institutional ownership (13F)
    "/13f-position-change": {
        "description": "Returns a 13F filer's positions by CIK, marked as new, closed, increased, decreased or unchanged.",
        "sample_parameters": {"cik": "0001067983", "position_filter": ["NEW", "CLOSED"]},
    },
    "/13f-position-by-manager-type": {
        "description": "Returns a stock's institutional ownership aggregated by manager type over recent quarters.",
        "sample_parameters": {"symbol": "AAPL", "manager_type": ["Hedge Fund"], "limit": 4},
    },
    "/13f-cik-allocation": {
        "description": "Returns a 13F filer's portfolio weights by sector or industry over recent quarters.",
        "sample_parameters": {"cik": "0001067983", "group_by": "sector", "limit": 4},
    },
    "/list-institutional-managers": {
        "description": "Searches institutional managers by name, CIK or manager type.",
        "sample_parameters": {"q": "berkshire", "limit": 10},
    },
    # Investor relations
    "/ir-document-analysis": {
        "description": "Returns an analyst's read of a company's most recent investor-relations decks, with links to the pages it cites.",
        "sample_parameters": {"symbol": "AAPL", "limit": 5},
    },
    "/ir-document": {
        "description": "Returns a company's investor-relations documents, newest first.",
        "sample_parameters": {"symbol": "AAPL", "limit": 10},
    },
    "/ir-content": {
        "description": "Returns the extracted text of one investor-relations document, page by page.",
        "sample_parameters": {"url": "<document_url from /ir-document>"},
    },
    "/ir-documents-season": {
        "description": "Returns investor-relations documents published this earnings season across companies, filterable by symbol, sector, index, country or market cap.",
        "sample_parameters": {"sector": "Technology", "limit": 50},
    },
    # Prices
    "/get-aftermarket-data": {
        "description": "Returns after-hours 15-minute price bars for a list of stocks within a datetime range.",
        "sample_parameters": {"symbols": ["AAPL"], "start_datetime": "2026-11-13T16:00:00", "end_datetime": "2026-11-13T20:00:00"},
    },
    "/get-stock-performance-ytd": {
        "description": "Returns a stock's year-to-date performance.",
        "sample_parameters": {"symbol": "AAPL"},
    },
    "/get-intraday-stock-performance": {
        "description": "Returns each stock's latest price and percent change from the previous close.",
        "sample_parameters": {"symbols": ["AAPL", "MSFT"]},
    },
    "/get-intraday-data": {
        "description": "Returns a stock's intraday price bars for one day at 1-minute to 4-hour frequency.",
        "sample_parameters": {"symbol": "AAPL", "frequency": "five_minute", "date": "2026-11-13"},
    },
    "/detect-intraday-outlier-jumps": {
        "description": "Flags the minutes in a stock's intraday trading where the move is an outlier relative to its daily volatility.",
        "sample_parameters": {"symbol": "AAPL", "zscore_threshold": 2.0},
    },
    "/list-technical-indicators": {
        "description": "Lists the technical indicators available.",
        "sample_parameters": {},
    },
    "/list-intraday-chart-options": {
        "description": "Lists the supported intraday frequencies.",
        "sample_parameters": {},
    },
    "/technical-indicator-endpoint": {
        "description": "Returns a technical indicator's history for a stock over a date range.",
        "sample_parameters": {"symbol": "AAPL", "indicator": "rsi", "start_date": "2026-10-01", "end_date": "2026-10-31"},
    },
    "/is-market-open": {
        "description": "Returns whether the market is open for an exchange.",
        "sample_parameters": {"exchange": "NYSE"},
    },
}

LOOKUP_ENDPOINTS = sorted(e for e, r in ENDPOINT_METHOD_MAPPER.items() if e.startswith("/list") and r.method == "GET")


class Catalog:
    """Public reference data; these endpoints need no login."""

    def __init__(self, client: "FlexreportClient"):
        self._client = client

    def symbols(self) -> Any:
        return self._client._json("GET", "/list-tickers", auth=None)

    def topics(self) -> Any:
        return self._client._json("GET", "/list-realtime-event-options", auth=None)

    @staticmethod
    def endpoints() -> list[str]:
        """Every endpoint path client.data.get_data() accepts, sorted."""
        return sorted(ENDPOINT_METHOD_MAPPER)

    def list_data_endpoints(self):
        return DATA_ENDPOINT_DESCRIPTIONS

    def data_endpoint_parameters(self, endpoint: str, **params: Any) -> Any:
        """Valid values for data-endpoint parameters, from a /list-* lookup, e.g. "/list-countries".

        /list-as-reported-items and /list-revenue-segments need ticker="AAPL".
        """
        endpoint = "/" + endpoint.strip().lstrip("/")
        if endpoint not in LOOKUP_ENDPOINTS:
            raise ValueError(f"{endpoint!r} is not a lookup endpoint; choose one of {LOOKUP_ENDPOINTS}")
        return self._client._json("GET", endpoint, params=params, auth=None)

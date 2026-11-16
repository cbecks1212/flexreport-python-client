from typing import TYPE_CHECKING, Any

from .data import ENDPOINT_METHOD_MAPPER

if TYPE_CHECKING:
    from ._client import FlexreportClient

DATA_ENDPOINT_DESCRIPTIONS = {
    # Earnings
    "/get-earnings-topics": "Returns the most mentioned topics across earnings calls for a given year and quarter.",
    "/summarize-earnings-transcript": "Returns a summary of a company's earnings call transcript for a given year and quarter.",
    "/summarize-stock-news": "Returns a summary of recent news about a company.",
    "/list-upcoming-earnings-announcements": "Lists earnings announcements scheduled between two dates, optionally filtered by symbol, industry, sector or market cap.",
    "/predict-earnings-announcement-move": "Predicts the size of a stock's move on its next earnings report, alongside its average past earnings reaction.",
    "/earnings-season-cohort": "Returns each covered company's latest result this earnings season, with actual vs estimated EPS and revenue and whether it beat, missed or came in line.",
    "/earnings-history": "Returns a company's reported quarters, newest first, with adjusted EPS and revenue vs estimates, the surprise and the next scheduled report.",
    "/get-realtime-events": "Returns the latest realtime events of one type, such as EPS updates, gainers, losers or transcript updates.",
    "/transcript-guidance": "Returns how a company's guidance changed on each earnings call (raised, in line, revised down or not provided), newest first.",
    "/transcript-analysis": "Returns a call-over-call analysis of a company's earnings transcripts: what each call added, removed, strengthened or weakened, with source links.",
    # Financials and lookups
    "/list-financial-items": "Lists the standardized EDGAR financial line items available.",
    "/list-financial-ratios": "Lists the EDGAR financial ratios available.",
    "/list-as-reported-items": "Lists the XBRL concepts a company tags in its own 10-Q and 10-K filings.",
    "/list-revenue-segments": "Lists a company's revenue segments as tagged in its filings.",
    "/list-tickers": "Lists every ticker Flexreport Finance covers, with its company or index name.",
    "/get-fiscal-quarter": "Returns the most recent fiscal quarter companies will report on.",
    "/get-sectors": "Lists all company sectors.",
    "/get-sub-industries": "Lists the sub-industries within one or more sectors.",
    "/list-realtime-event-options": "Lists the realtime event types, each with its family, a description and related follow-up endpoints.",
    "/list-institutional-investor-types": "Lists the institutional investor types used to group 13F ownership.",
    "/list-countries": "Lists the countries Flexreport Finance covers.",
    "/list-symbols-with-names": "Returns every covered symbol paired with its company name.",
    "/list-marketcap-options": "Lists the market-cap categories used as filters.",
    "/get-company-snapshot": "Returns a company snapshot covering its investment thesis, price performance, analyst ratings and targets, financials, ownership and recent news.",
    "/situate-company": "Summarizes the recent events that matter for a company and points to the endpoints that go deeper on each.",
    "/situate-market": "Returns the realtime event types relevant to a market question, in reading order, with the tickers each currently covers.",
    "/company-financials": "Returns a company's standardized or as-reported EDGAR financials, 8-K financial tables or year-over-year changes.",
    # Insider trading
    "/insider-transactions": "Returns a company's Form 4 transactions by senior insiders over the last 6 months, newest first, with footnotes and SEC links.",
    "/insider-activity-summary": "Returns a company's quarterly insider buying and selling totals and each senior insider's net activity over the last 6 months.",
    # Institutional ownership (13F)
    "/13f-position-change": "Returns a 13F filer's positions by CIK, marked as new, closed, increased, decreased or unchanged.",
    "/13f-position-by-manager-type": "Returns a stock's institutional ownership aggregated by manager type over recent quarters.",
    "/13f-cik-allocation": "Returns a 13F filer's portfolio weights by sector or industry over recent quarters.",
    "/list-institutional-managers": "Searches institutional managers by name, CIK or manager type.",
    # Investor relations
    "/ir-document-analysis": "Returns an analyst's read of a company's most recent investor-relations decks, with links to the pages it cites.",
    "/ir-document": "Returns a company's investor-relations documents, newest first.",
    "/ir-content": "Returns the extracted text of one investor-relations document, page by page.",
    "/ir-documents-season": "Returns investor-relations documents published this earnings season across companies, filterable by symbol, sector, index, country or market cap.",
    # Prices
    "/get-aftermarket-data": "Returns after-hours 15-minute price bars for a list of stocks within a datetime range.",
    "/get-stock-performance-ytd": "Returns a stock's year-to-date performance.",
    "/get-intraday-stock-performance": "Returns each stock's latest price and percent change from the previous close.",
    "/get-intraday-data": "Returns a stock's intraday price bars for one day at 1-minute to 4-hour frequency.",
    "/detect-intraday-outlier-jumps": "Flags the minutes in a stock's intraday trading where the move is an outlier relative to its daily volatility.",
    "/list-technical-indicators": "Lists the technical indicators available.",
    "/list-intraday-chart-options": "Lists the supported intraday frequencies.",
    "/technical-indicator-endpoint": "Returns a technical indicator's history for a stock over a date range.",
    "/is-market-open": "Returns whether the market is open for an exchange.",
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

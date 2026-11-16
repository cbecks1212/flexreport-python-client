import json
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

# These answer with {"task_id", "status"}; get_data polls them to completion when wait=True.
TASK_ENDPOINTS = {"/get-earnings-topics", "/summarize-earnings-transcript", "/summarize-stock-news"}


class Data:
    def __init__(self, client: "FlexreportClient"):
        self._client = client

    @staticmethod
    def endpoints() -> list[str]:
        return sorted(ENDPOINT_METHOD_MAPPER)

    def get_data(self, endpoint: str, parameters: dict | None = None, *, wait: bool = True, max_wait: float = 900, poll_every: float = 3.0, progress: bool = True, timeout: float | None = None) -> Any:
        """Call a data endpoint by path, e.g. get_data("/earnings-history", {"symbol": "AAPL"}).

        parameters are sent where the endpoint expects them (JSON body or query string).
        For /get-intraday-stock-performance pass {"symbols": [...]}.
        """
        endpoint = "/" + endpoint.strip().lstrip("/")
        route = ENDPOINT_METHOD_MAPPER.get(endpoint)
        if route is None:
            raise ValueError(f"Unknown endpoint {endpoint!r}; see Data.endpoints() for the supported ones")

        parameters = {k: v for k, v in (parameters or {}).items() if v is not None}
        kwargs: dict[str, Any] = {}
        if timeout is not None:
            kwargs["timeout"] = timeout

        if route.send == "query":
            kwargs["params"] = parameters
        elif route.send == "json":
            kwargs["json"] = parameters
        else:
            if route.body_key not in parameters:
                raise ValueError(f"{endpoint} needs parameters={{{route.body_key!r}: ...}}")
            kwargs["json"] = parameters[route.body_key]

        result = self._client._json(route.method, endpoint, **kwargs)

        if wait and endpoint in TASK_ENDPOINTS and isinstance(result, dict) and "task_id" in result:
            return self._client._wait_for_task(result["task_id"], endpoint.lstrip("/"), max_wait, poll_every, progress)
        return result

    def trace_data(
        self,
        *,
        relation: str | None = None,
        keys: list[dict] | str | None = None,
        column: str | None = None,
        t: str | None = None,
        prompt: str | None = None,
        values: dict | str | None = None,
        max_documents: int = 50,
        resolve_passages: bool = False,
        claim: str | None = None,
        ticker: str | None = None,
        document_type: str = "8-K",
        on_date: str | None = None,
        accession: str | None = None,
    ) -> Any:
        """Resolve numbers in a result back to their source documents (GET /trace-sources).

        Three ways in:
          - relation + keys: the grain values of the rows you hold, e.g.
            relation="...", keys=[{"symbol": "SNOW", "cik": "0001273087", "date": "2026-06-30"}]
          - t: a trace_token from a result's sources block (or the original query token)
          - claim + ticker: locate a sentence or figure inside a filing (document_type 8-K, 10-Q or 10-K)
        """
        if not ((relation and keys) or t or (claim and ticker)):
            raise ValueError("pass relation and keys, or t, or claim and ticker")
        if document_type not in {"8-K", "10-Q", "10-K"}:
            raise ValueError("document_type must be 8-K, 10-Q or 10-K")

        params = {
            "relation": relation,
            "keys": keys if keys is None or isinstance(keys, str) else json.dumps(keys),
            "column": column,
            "t": t,
            "prompt": prompt,
            "values": values if values is None or isinstance(values, str) else json.dumps(values),
            "max_documents": max_documents,
            "resolve_passages": str(resolve_passages).lower(),
            "claim": claim,
            "ticker": ticker,
            "document_type": document_type,
            "on_date": on_date,
            "accession": accession,
        }
        return self._client._json("GET", "/trace-sources", params={k: v for k, v in params.items() if v is not None}, timeout=120)

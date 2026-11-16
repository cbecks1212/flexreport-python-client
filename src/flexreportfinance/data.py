import json
from typing import TYPE_CHECKING, Any

from .catalog import ENDPOINT_METHOD_MAPPER

if TYPE_CHECKING:
    from ._client import FlexreportClient

# These answer with {"task_id", "status"}; get_data polls them to completion when wait=True.
TASK_ENDPOINTS = {"/get-earnings-topics", "/summarize-earnings-transcript", "/summarize-stock-news"}


class Data:
    def __init__(self, client: "FlexreportClient"):
        self._client = client

    def get_data(self, endpoint: str, parameters: dict | None = None, *, wait: bool = True, max_wait: float = 900, poll_every: float = 3.0, progress: bool = True, timeout: float | None = None) -> Any:
        """Call a data endpoint by path, e.g. get_data("/earnings-history", {"symbol": "AAPL"}).

        parameters are sent where the endpoint expects them (JSON body or query string).
        For /get-intraday-stock-performance pass {"symbols": [...]}.
        """
        endpoint = "/" + endpoint.strip().lstrip("/")
        route = ENDPOINT_METHOD_MAPPER.get(endpoint)
        if route is None:
            raise ValueError(f"Unknown endpoint {endpoint!r}; see client.catalog.endpoints() for the supported ones")

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

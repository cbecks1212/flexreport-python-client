import json
from urllib.parse import parse_qs

import httpx
import pytest

from flexreportfinance import FlexreportClient
from flexreportfinance.data import ENDPOINT_METHOD_MAPPER, Data


def test_client_exposes_data(api):
    assert isinstance(api.data, Data)


def test_json_endpoint_sends_body(api):
    api.data.get_data("/earnings-history", {"symbol": "AAPL", "limit": 4})
    req = api.requests[-1]
    assert req.method == "POST"
    assert req.url.path == "/earnings-history"
    assert json.loads(req.content) == {"symbol": "AAPL", "limit": 4}
    assert req.headers["Authorization"] == "Bearer tok"


def test_query_endpoint_sends_params_and_repeats_lists(api):
    api.data.get_data("/get-sub-industries", {"sector": ["Energy", "Utilities"]})
    req = api.requests[-1]
    assert req.method == "GET"
    assert parse_qs(req.url.query.decode()) == {"sector": ["Energy", "Utilities"]}
    assert req.content == b""


def test_post_with_query_params(api):
    api.data.get_data("/summarize-stock-news", {"ticker": "AAPL"}, wait=False)
    req = api.requests[-1]
    assert req.method == "POST"
    assert parse_qs(req.url.query.decode()) == {"ticker": ["AAPL"]}


def test_bare_body_endpoint_sends_the_list(api):
    api.data.get_data("/get-intraday-stock-performance", {"symbols": ["AAPL", "MSFT"]})
    assert json.loads(api.requests[-1].content) == ["AAPL", "MSFT"]


def test_bare_body_endpoint_requires_its_key(api):
    with pytest.raises(ValueError, match="symbols"):
        api.data.get_data("/get-intraday-stock-performance", {"tickers": ["AAPL"]})
    assert api.requests == []


def test_none_values_are_dropped(api):
    api.data.get_data("/earnings-season-cohort", {"sector": None, "limit": 3})
    assert json.loads(api.requests[-1].content) == {"limit": 3}


def test_leading_slash_and_whitespace_optional(api):
    api.data.get_data(" earnings-history ", {"symbol": "AAPL"})
    assert api.requests[-1].url.path == "/earnings-history"


def test_parameters_optional(api):
    api.data.get_data("/list-countries")
    assert api.requests[-1].url.query == b""


def test_unknown_endpoint_raises(api):
    with pytest.raises(ValueError, match="Unknown endpoint"):
        api.data.get_data("/not-an-endpoint")
    assert api.requests == []


@pytest.mark.parametrize("endpoint", ["/onboard-symbol", "/generate-earnings-season-deep-dive", "/get-transcript-updates"])
def test_excluded_endpoints_are_not_routed(endpoint):
    assert endpoint not in ENDPOINT_METHOD_MAPPER


def test_task_endpoint_waits_for_result(api):
    out = api.data.get_data("/get-earnings-topics", {"year": 2026, "quarter": 3}, progress=False)
    assert out == {"task_id": "t-1", "status": "SUCCESS", "result": {"topics": ["ai"]}}


def test_task_endpoint_no_wait_returns_task_id(api):
    out = api.data.get_data("/get-earnings-topics", {"year": 2026, "quarter": 3}, wait=False)
    assert out == {"task_id": "t-1", "status": "PENDING"}


def test_http_error_propagates():
    def handler(request):
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(422, json={"detail": "bad"})

    client = FlexreportClient("user", "pass")
    client._http = httpx.Client(base_url="https://api.test", transport=httpx.MockTransport(handler), auth=client._http.auth)
    with pytest.raises(httpx.HTTPStatusError):
        client.data.get_data("/earnings-history", {"symbol": "AAPL"})


def test_endpoints_lists_mapper():
    assert Data.endpoints() == sorted(ENDPOINT_METHOD_MAPPER)


def test_trace_data_serializes_keys(api):
    api.data.trace_data(relation="edgar_quarterly_financials", keys=[{"symbol": "SNOW", "date": "2026-06-30"}])
    req = api.requests[-1]
    assert req.method == "GET" and req.url.path == "/trace-sources"
    q = parse_qs(req.url.query.decode())
    assert json.loads(q["keys"][0]) == [{"symbol": "SNOW", "date": "2026-06-30"}]
    assert q["resolve_passages"] == ["false"]
    assert q["max_documents"] == ["50"]


def test_trace_data_passes_string_keys_through(api):
    api.data.trace_data(relation="r", keys='[{"symbol":"SNOW"}]', values={"q": 1})
    q = parse_qs(api.requests[-1].url.query.decode())
    assert q["keys"] == ['[{"symbol":"SNOW"}]']
    assert json.loads(q["values"][0]) == {"q": 1}


def test_trace_data_token_and_pinpoint_forms(api):
    api.data.trace_data(t="abc")
    assert parse_qs(api.requests[-1].url.query.decode())["t"] == ["abc"]
    api.data.trace_data(claim="revenue grew 12%", ticker="AAPL", document_type="10-Q", resolve_passages=True)
    q = parse_qs(api.requests[-1].url.query.decode())
    assert q["claim"] == ["revenue grew 12%"] and q["document_type"] == ["10-Q"] and q["resolve_passages"] == ["true"]


@pytest.mark.parametrize("kwargs", [{}, {"relation": "r"}, {"keys": [{"a": 1}]}, {"claim": "x"}])
def test_trace_data_requires_a_complete_form(api, kwargs):
    with pytest.raises(ValueError, match="relation and keys"):
        api.data.trace_data(**kwargs)
    assert api.requests == []


def test_trace_data_rejects_bad_document_type(api):
    with pytest.raises(ValueError, match="document_type"):
        api.data.trace_data(claim="x", ticker="AAPL", document_type="S-1")

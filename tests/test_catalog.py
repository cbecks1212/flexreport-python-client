from urllib.parse import parse_qs

import pytest

from flexreportfinance.catalog import DATA_ENDPOINT_DESCRIPTIONS, LOOKUP_ENDPOINTS
from flexreportfinance.data import ENDPOINT_METHOD_MAPPER


def test_every_endpoint_has_a_description():
    assert set(DATA_ENDPOINT_DESCRIPTIONS) == set(ENDPOINT_METHOD_MAPPER)
    assert all(d.endswith(".") and d.count(". ") == 0 for d in DATA_ENDPOINT_DESCRIPTIONS.values())


def test_list_data_endpoints(api):
    assert api.catalog.list_data_endpoints() == DATA_ENDPOINT_DESCRIPTIONS


def test_lookup_endpoints_are_the_get_list_routes():
    assert LOOKUP_ENDPOINTS == sorted(LOOKUP_ENDPOINTS)
    assert "/list-countries" in LOOKUP_ENDPOINTS
    assert "/list-as-reported-items" in LOOKUP_ENDPOINTS
    assert all(e.startswith("/list") and ENDPOINT_METHOD_MAPPER[e].method == "GET" for e in LOOKUP_ENDPOINTS)
    assert "/list-upcoming-earnings-announcements" not in LOOKUP_ENDPOINTS  # POST


def test_data_endpoint_parameters_calls_lookup_without_login(api):
    assert api.catalog.data_endpoint_parameters("/list-countries") == {"ok": True}
    req = api.requests[-1]
    assert req.method == "GET"
    assert req.url.path == "/list-countries"
    assert req.url.query == b""
    assert "Authorization" not in req.headers


def test_data_endpoint_parameters_passes_params(api):
    api.catalog.data_endpoint_parameters("/list-as-reported-items", ticker="AAPL")
    assert parse_qs(api.requests[-1].url.query.decode()) == {"ticker": ["AAPL"]}

    api.catalog.data_endpoint_parameters("/list-institutional-managers", q="berkshire", limit=5)
    assert parse_qs(api.requests[-1].url.query.decode()) == {"q": ["berkshire"], "limit": ["5"]}


def test_data_endpoint_parameters_slash_optional(api):
    api.catalog.data_endpoint_parameters(" list-countries ")
    assert api.requests[-1].url.path == "/list-countries"


@pytest.mark.parametrize("endpoint", [
    "/list-upcoming-earnings-announcements",  # POST in the data mapper
    "/list-available-reports",                # POST, belongs to Reports
    "/list-nonsense",                         # starts with /list but doesn't exist
    "/earnings-history",                      # a data endpoint, not a lookup
])
def test_data_endpoint_parameters_rejects_non_lookups(api, endpoint):
    with pytest.raises(ValueError, match="not a lookup endpoint"):
        api.catalog.data_endpoint_parameters(endpoint)
    assert api.requests == []

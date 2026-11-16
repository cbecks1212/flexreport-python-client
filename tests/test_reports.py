from contextlib import contextmanager

import httpx
import pytest

from flexreportfinance import FlexreportClient

PDF = b"%PDF-1.7 fake report"


class _BreaksMidway(httpx.SyncByteStream):
    def __iter__(self):
        yield b"%PDF-1.7 partial"
        raise httpx.ReadError("connection reset")


def _s3(request: httpx.Request) -> httpx.Response:
    name = request.url.path.rsplit("/", 1)[-1]
    if name == "forbidden.pdf":
        return httpx.Response(403, content=b"<Error><Code>AccessDenied</Code></Error>")
    if name == "midway.pdf":
        return httpx.Response(200, stream=_BreaksMidway())
    if name == "unreachable.pdf":
        raise httpx.ConnectError("no route to host", request=request)
    return httpx.Response(200, content=PDF + name.encode())


def _row(symbol, file=None, stale=False):
    return {"symbol": symbol, "url": f"https://s3.test/reports/{file or symbol}.pdf",
            "stale": stale, "generated_at": "2026-11-15T12:00:00+00:00"}


@pytest.fixture
def reports(monkeypatch):
    """Returns (make_client, s3_requests). make_client(rows) builds a client whose API serves those cached rows."""
    s3_requests = []

    def s3_handler(request):
        s3_requests.append(request)
        return _s3(request)

    @contextmanager
    def fake_stream(method, url, **kwargs):
        with httpx.Client(transport=httpx.MockTransport(s3_handler)) as http:
            with http.stream(method, url, **kwargs) as response:
                yield response

    monkeypatch.setattr(httpx, "stream", fake_stream)
    clients = []

    def make_client(rows):
        def api(request):
            if request.url.path == "/token":
                return httpx.Response(200, json={"access_token": "tok"})
            assert request.url.path == "/get-cached-reports"
            return httpx.Response(200, json={"result": rows, "missing": [], "rendering": {}})

        client = FlexreportClient("user", "pass")
        client._http = httpx.Client(base_url="https://api.test", transport=httpx.MockTransport(api), auth=client._http.auth)
        clients.append(client)
        return client

    yield make_client, s3_requests
    for client in clients:
        client.close()


def test_saves_each_pdf_and_returns_paths(reports, tmp_path):
    make_client, s3_requests = reports
    client = make_client([_row("AAPL"), _row("MSFT")])
    out_dir = tmp_path / "new" / "dir"

    saved = client.reports.download(["AAPL", "MSFT"], str(out_dir))

    assert saved == [str(out_dir / "AAPL.pdf"), str(out_dir / "MSFT.pdf")]
    assert (out_dir / "AAPL.pdf").read_bytes() == PDF + b"AAPL.pdf"
    assert (out_dir / "MSFT.pdf").read_bytes() == PDF + b"MSFT.pdf"
    assert all("Authorization" not in r.headers for r in s3_requests)  # API token never sent to S3


def test_stale_report_downloaded_by_default(reports, tmp_path, capsys):
    make_client, _ = reports
    client = make_client([_row("AAPL", stale=True)])

    assert client.reports.download(["AAPL"], str(tmp_path)) == [str(tmp_path / "AAPL.pdf")]
    assert "STALE, GENERATED 2026-11-15T12:00:00+00:00" in capsys.readouterr().out


def test_skip_stale(reports, tmp_path):
    make_client, s3_requests = reports
    client = make_client([_row("AAPL", stale=True), _row("MSFT")])

    assert client.reports.download(["AAPL", "MSFT"], str(tmp_path), skip_stale=True) == [str(tmp_path / "MSFT.pdf")]
    assert not (tmp_path / "AAPL.pdf").exists()
    assert [r.url.path for r in s3_requests] == ["/reports/MSFT.pdf"]


def test_unknown_staleness_is_not_skipped(reports, tmp_path):
    make_client, _ = reports
    client = make_client([{**_row("AAPL"), "stale": None}])

    assert client.reports.download(["AAPL"], str(tmp_path), skip_stale=True) == [str(tmp_path / "AAPL.pdf")]


@pytest.mark.parametrize("file", ["forbidden", "midway", "unreachable"])
def test_failed_download_leaves_no_file_and_loop_continues(reports, tmp_path, capsys, file):
    make_client, _ = reports
    client = make_client([_row("BAD", file=file), _row("MSFT")])

    saved = client.reports.download(["BAD", "MSFT"], str(tmp_path))

    assert saved == [str(tmp_path / "MSFT.pdf")]
    assert not (tmp_path / "BAD.pdf").exists()
    assert "ERROR DOWNLOADING BAD'S REPORT" in capsys.readouterr().out


def test_forbidden_reports_status(reports, tmp_path, capsys):
    make_client, _ = reports
    client = make_client([_row("BAD", file="forbidden")])

    assert client.reports.download(["BAD"], str(tmp_path)) == []
    assert "HTTP 403" in capsys.readouterr().out


def test_no_cached_reports_raises(reports, tmp_path):
    make_client, _ = reports
    client = make_client([])

    with pytest.raises(ValueError, match="NO REPORTS TO DOWNLOAD"):
        client.reports.download(["ZZZZ"], str(tmp_path))

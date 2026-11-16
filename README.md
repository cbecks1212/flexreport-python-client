# Flexreport Finance

Python client for the Flexreport Finance REST API. A username and password are required to use the client. If you do not have those, you can create a free account from Python (see below) or at https://app.flexreportfinapi.com/register-api. For more information, please visit https://app.flexreportfinapi.com/ and https://app.flexreportfinapi.com/api-docs.

## Quick Install

```bash
pip install flexreportfinance
```

## Creating an account

You can sign up without leaving your notebook. Your email is your username.

```python
from getpass import getpass
import flexreportfinance as frf

print(frf.register("you@example.com", getpass("Password: ")))
```

You'll get an email with a link to confirm your account. Click it before using the client; logins are rejected until the account is confirmed.

If you'd rather sign up in the browser, the form at https://app.flexreportfinapi.com/register-api does the same thing.

## Resetting your password

Request a reset and you'll get an email with a link. The link looks like `https://app.flexreportfinapi.com/reset-password?token=<token>`. Copy the token from it and pass it to `reset_password()`:

```python
from getpass import getpass
import flexreportfinance as frf

frf.request_reset_password("you@example.com")

# after the email arrives
frf.reset_password("<token>", getpass("New password: "))
```

The token expires, so don't sit on it. Alternatively, just click the link in the email and set a new password on the website.

## Quick example of real-time streaming

```python
from flexreportfinance import FlexreportClient

with FlexreportClient("username", "password") as client:
    for event_id, event in client.events.stream(symbols=["AAPL"]):
        print(event_id, event)
```

`stream()` keeps the connection open and yields events as they arrive, so the loop runs until you break out of it. Live updates are not published on weekends.

## Streaming with a saved subscription

A subscription saves a topics/symbols filter on the server and remembers its position: each time you stream it, it resumes after the last event the previous stream delivered, so a consumer that disconnects misses nothing. Valid topics are listed by `client.catalog.topics()`.

Create it once and keep the id. There is no endpoint to list subscriptions, and creation is limited to 30 per hour.

```python
from flexreportfinance import FlexreportClient

with FlexreportClient("username", "password") as client:
    sub = client.events.create_subscription(topics=["eps_update"], symbols=["AAPL", "MSFT"])
    print("subscription id:", sub["subscription_id"])
```

Stream it, now or in any later session:

```python
with FlexreportClient("username", "password") as client:
    for event_id, event in client.events.stream_with_subscription("<subscription id>"):
        print(event_id, event)
```

Delete it when you no longer need it (an open stream on it ends shortly after):

```python
with FlexreportClient("username", "password") as client:
    client.events.delete_subscription("<subscription id>")
```

## Querying data

In addition to streaming real-time events, `client.data.get_data()` calls any of the API's data endpoints by path to supplement real-time events with timeseries data: earnings, financials, insider trading, 13F institutional ownership, investor-relations documents and prices. Pass the endpoint's parameters as a dict; the client sends them where that endpoint expects them (JSON body or query string). Each endpoint's parameters are listed at https://app.flexreportfinapi.com/api-docs. Or see Finding endpoints and parameter values below to quickly lookup values with the Flexreport Client.

```python
from flexreportfinance import FlexreportClient

with FlexreportClient("username", "password") as client:
    history = client.data.get_data("/earnings-history", {"symbol": "AAPL", "limit": 4})
    insiders = client.data.get_data("/insider-transactions", {"symbol": "AAPL", "role": ["ceo"]})
    snapshot = client.data.get_data("/get-company-snapshot", {"symbol": "AAPL"})
    bars = client.data.get_data("/get-intraday-data", {"symbol": "AAPL", "frequency": "five_minute"})
```


### Finding endpoints and parameter values

`client.catalog.list_data_endpoints()` returns every supported path with a one-sentence description of what it returns:

```python
for endpoint, description in client.catalog.list_data_endpoints().items():
    print(f"{endpoint}: {description}")
```

`client.catalog.data_endpoint_parameters()` fetches the valid values for a parameter from one of the `/list-*` lookup endpoints, such as countries, market-cap categories, financial line items or intraday frequencies. Pass any parameters the lookup takes as keyword arguments:

```python
countries = client.catalog.data_endpoint_parameters("/list-countries")
line_items = client.catalog.data_endpoint_parameters("/list-as-reported-items", ticker="AAPL")
managers = client.catalog.data_endpoint_parameters("/list-institutional-managers", q="berkshire")
```

`/list-as-reported-items` and `/list-revenue-segments` require `ticker`. Any other endpoint raises `ValueError`; `flexreportfinance.catalog.LOOKUP_ENDPOINTS` lists the accepted ones.

### Calling endpoints that take a bare list or run as tasks

`/get-intraday-stock-performance` takes only a list of symbols. Pass it under `symbols`:

```python
moves = client.data.get_data("/get-intraday-stock-performance", {"symbols": ["AAPL", "MSFT"]})
```

`/get-earnings-topics`, `/summarize-earnings-transcript` and `/summarize-stock-news` run as background tasks on the server. `get_data()` waits for them (up to `max_wait` seconds, 15 minutes by default) and returns `{"task_id", "status", "result"}`. Pass `wait=False` to get the task id back straight away.

### Tracing numbers to their sources

`client.data.trace_data()` maps figures back to the documents they came from: the filing, section or transcript passage. There are three ways to call it:

```python
# 1. The rows you hold: the relation they came from plus each row's key values,
#    both given in a result's sources block
client.data.trace_data(relation="<relation>", keys=[{"symbol": "SNOW", "cik": "0001273087", "date": "2026-06-30"}])

# 2. A trace token from a result's sources block
client.data.trace_data(t="<trace_token>")

# 3. A sentence or figure to find inside a filing (8-K, 10-Q or 10-K)
client.data.trace_data(claim="Revenue grew 12% year over year", ticker="AAPL", document_type="10-Q", resolve_passages=True)
```

`resolve_passages=True` also returns the text behind each citation.

## Quick example of downloading the latest research for AAPL

```python
from flexreportfinance import FlexreportClient

file_directory_to_save = "SPECIFY YOUR DIRECTORY TO SAVE FILES TO"

with FlexreportClient("username", "password") as client:
    saved = client.reports.download(["AAPL"], file_directory_to_save)

print(saved)  # ['<your directory>/AAPL.pdf']
```

`download()` saves each report as `SYMBOL.pdf`, creating the directory if needed, and returns the paths it saved. A symbol that fails to download is reported and skipped, so the rest still download.

A report is stale when the company has had an event since the PDF was generated. Stale reports are still downloaded and flagged in the output; pass `skip_stale=True` to leave them out.

## Alternatively, you can control the download logic yourself

`client.reports.get()` looks up the latest report for each symbol without downloading anything. It returns a dict with:

- `cached`: one entry per report found, with the `symbol`, a `url` for the PDF, `generated_at`, `age_hours` and `stale`. The `url` is a presigned link, valid for about 6 hours, that needs no login, so you can fetch it with any HTTP client.
- `missing`: the symbols that have no report.

```python
import httpx
from flexreportfinance import FlexreportClient

with FlexreportClient("username", "password") as client:
    report_data = client.reports.get(["AAPL", "MSFT"])

for report in report_data["cached"]:
    print(report["symbol"], report["generated_at"], "stale" if report["stale"] else "current")

# Fetch one PDF yourself: save it, upload it elsewhere, or keep the bytes in memory
aapl = next(r for r in report_data["cached"] if r["symbol"] == "AAPL")
pdf_bytes = httpx.get(aapl["url"]).content
```

### Downloading all of the latest reports from today

`client.reports.available()` lists the reports published on a date. Pass its symbols to `get()` and download each one:

```python
from datetime import date
from pathlib import Path

import httpx
from flexreportfinance import FlexreportClient

today = date.today().isoformat()  # YYYY-MM-DD
out_dir = Path("reports")
out_dir.mkdir(exist_ok=True)

with FlexreportClient("username", "password") as client:
    report_plans = client.reports.available(report_date=today)
    symbols = list(dict.fromkeys(plan["symbol"] for plan in report_plans))
    if not symbols:
        raise SystemExit(f"No reports for {today} (none are published on weekends).")
    report_data = client.reports.get(symbols=symbols)

for report in report_data["cached"]:
    if report["stale"]:
        print(f"{report['symbol']}: report predates the latest event (generated {report['generated_at']})")
    response = httpx.get(report["url"])
    response.raise_for_status()
    file_path = out_dir / f"{report['symbol']}.pdf"
    file_path.write_bytes(response.content)
    print(f"{report['symbol']} -> saved to {file_path}")

if report_data["missing"]:
    print("No report for:", report_data["missing"])
```

## Using your own PDF template

A saved template puts your research in your own format (masthead, colours, layout) and is applied automatically to every PDF the API renders for you. Each account has one template. You describe the template you want in plain English, and `template_type` is one of:

- `"bespoke"`: your design replaces the standard report layout.
- `"add_on"`: your design restyles one section of the standard layout. `anchor` is required and names the section, e.g. `"technical"`, `"financials"` or `"ownership"`.

Drafting and saving each run as a background task on the server. The client polls until the task finishes (up to `max_wait` seconds, 15 minutes by default) and returns `{"task_id", "status", "result"}`. `status` is `"SUCCESS"`, `"FAILURE"`, or `"TIMEOUT"` if `max_wait` ran out first.

### 1. Draft and preview

Drafting turns your request into several treatments, renders each one as preview images, and stores nothing. Drafts expire after 24 hours.

```python
from flexreportfinance import FlexreportClient

template = "I'd like a modern, sleek equity research template."

with FlexreportClient("username", "password") as client:
    draft = client.reports.draft_template(template, "bespoke")

result = draft["result"]
print("draft id:", result["draft_id"])
for variant in result["variants"]:
    print(variant["variant_id"], variant["name"], "-", variant["rationale"])
    for url in variant["preview_urls"]:
        print("   ", url)
```

### 2. Save the variant you picked

Passing `draft_id` and `variant_id` saves exactly the treatment you previewed; the request, `template_type` and `anchor` come from the draft, so you don't pass them again. Saving replaces any template already on the account.

```python
with FlexreportClient("username", "password") as client:
    saved = client.reports.save_template(draft_id="<draft id>", variant_id="<variant id>")
    print(saved["status"], saved["result"])
```

To save without previewing, pass `template` and `template_type` (and `anchor` for an `add_on`) instead of `draft_id` and `variant_id`.

### Viewing, changing and deleting

```python
with FlexreportClient("username", "password") as client:
    print(client.reports.get_template())

    # Change only the fields you pass; the rest keep their saved values.
    client.reports.update_template(template_type="add_on", anchor="financials")

    # With no arguments, recompiles the saved template as stored.
    client.reports.update_template()

    # Go back to the standard layouts.
    client.reports.delete_template()
```

The client logs in on the first authenticated call and logs in again if the token expires.

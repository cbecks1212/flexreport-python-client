# Flexreport Finance

Python client for the Flexreport Finance REST API. A username and password are required to use the client. If you do not have those, please create a free account at https://app.flexreportfinapi.com/register-api. For more information, please visit https://app.flexreportfinapi.com/ and https://app.flexreportfinapi.com/api-docs.

## Quick Install

```bash
pip install flexreportfinance
```

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

## Quick example of downloading the latest research for AAPL

```python
import base64
from flexreportfinance import FlexreportClient

with FlexreportClient("username", "password") as client:
    report_data = client.reports.get(symbols=["AAPL"])

for symbol, report in report_data["rendered"].items():
    file_path = f"{symbol}_report.pdf"
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(report["result"]["pdf"]))
    print(f"{report['result']['headline']} -> saved to {file_path}")
```

## Downloading all of the latest reports from today

```python
import base64
from datetime import date
from flexreportfinance import FlexreportClient

today = date.today().isoformat()  # YYYY-MM-DD
with FlexreportClient("username", "password") as client:
    report_plans = client.reports.available(report_date=today)
    symbols = list(dict.fromkeys(plan["symbol"] for plan in report_plans))
    if not symbols:
        raise SystemExit(f"No reports for {today} (none are published on weekends).")
    report_data = client.reports.get(symbols=symbols)

for symbol, report in report_data["rendered"].items():
    file_path = f"{symbol}_report.pdf"
    with open(file_path, "wb") as f:
        f.write(base64.b64decode(report["result"]["pdf"]))
    print(f"{report['result']['headline']} -> saved to {file_path}")
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

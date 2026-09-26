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

The client logs in on the first authenticated call and logs in again if the token expires.

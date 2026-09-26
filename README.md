# flexreportfinance

Python client for the Flexreport Finance REST API.

```python
from flexreportfinance import FlexreportClient

with FlexreportClient("username", "password") as client:
    symbols = client.catalog.symbols()
    topics = client.catalog.topics()

    plans = client.reports.available(event_types=None)
    reports = client.reports.get(["AAPL", "MSFT"])

    for event_id, event in client.events.stream(symbols=["AAPL"]):
        print(event_id, event)
```

The client logs in on the first authenticated call and logs in again if the token expires.

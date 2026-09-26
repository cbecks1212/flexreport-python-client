from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._client import FlexreportClient


class Catalog:
    """Public reference data; these endpoints need no login."""

    def __init__(self, client: "FlexreportClient"):
        self._client = client

    def symbols(self) -> Any:
        return self._client._json("GET", "/list-tickers", auth=None)

    def topics(self) -> Any:
        return self._client._json("GET", "/list-realtime-event-options", auth=None)

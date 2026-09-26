import json
from collections.abc import Iterator
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from ._client import FlexreportClient


class Events:
    def __init__(self, client: "FlexreportClient"):
        self._client = client

    def stream(
        self,
        topics: list[str] | None = None,
        symbols: list[str] | None = None,
        last_event_id: str | None = None,
        read_timeout: float = 30,
    ) -> Iterator[tuple[str | None, dict]]:
        """Yield (event_id, event) from the server-sent event stream.

        Pass the last event_id you saw as last_event_id to resume after a disconnect.
        """
        params = {k: v for k, v in {"topics": topics, "symbols": symbols}.items() if v is not None}
        headers = {"Last-Event-ID": last_event_id} if last_event_id else {}

        with self._client._http.stream(
            "GET", "/events", params=params, headers=headers, timeout=httpx.Timeout(10, read=read_timeout)
        ) as resp:
            resp.raise_for_status()
            frame: dict[str, str] = {}

            for line in resp.iter_lines():
                if line:
                    if line.startswith(":"):
                        continue
                    key, _, value = line.partition(":")
                    value = value.removeprefix(" ")
                    frame[key] = f"{frame[key]}\n{value}" if key == "data" and key in frame else value
                    continue
                if frame.get("event") == "event" and "data" in frame:
                    yield frame.get("id"), json.loads(frame["data"])
                frame = {}

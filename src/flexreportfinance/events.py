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
        """Yield (event_id, event) for events matching topics/symbols, starting now.

        Pass the last event_id you saw as last_event_id to resume after a disconnect.
        """
        params = {k: v for k, v in {"topics": topics, "symbols": symbols}.items() if v is not None}
        yield from self._stream_frames("/events", params, last_event_id, read_timeout)

    def stream_with_subscription(
        self,
        subscription_id: str,
        last_event_id: str | None = None,
        read_timeout: float = 30,
    ) -> Iterator[tuple[str | None, dict]]:
        """Yield (event_id, event) for a subscription from create_subscription().

        Resumes after the last event the previous stream on this subscription delivered;
        pass last_event_id to start from a different position instead.
        """
        yield from self._stream_frames(f"/event-subscription/{subscription_id}", {}, last_event_id, read_timeout)

    def create_subscription(self, topics: list[str] | None = None, symbols: list[str] | None = None) -> dict:
        return self._client._json("POST", "/register-subscription", json={"topics": topics, "symbols": symbols})

    def delete_subscription(self, subscription_id: str) -> dict:
        return self._client._json("DELETE", f"/event-subscription/{subscription_id}")

    def _stream_frames(
        self, path: str, params: dict, last_event_id: str | None, read_timeout: float
    ) -> Iterator[tuple[str | None, dict]]:
        headers = {"Last-Event-ID": last_event_id} if last_event_id else {}

        with self._client._http.stream(
            "GET", path, params=params, headers=headers, timeout=httpx.Timeout(10, read=read_timeout)
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

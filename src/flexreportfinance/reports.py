import time
from typing import TYPE_CHECKING, Any

from tqdm.auto import tqdm

if TYPE_CHECKING:
    from ._client import FlexreportClient

TERMINAL = {"SUCCESS", "FAILURE", "REVOKED"}


class Reports:
    def __init__(self, client: "FlexreportClient"):
        self._client = client

    def available(self, event_types: list[str] | None = None) -> Any:
        return self._client._json("POST", "/list-available-reports", json={"event_types": event_types}, timeout=60)

    def get(self, symbols: list[str], *, max_wait: float = 900, poll_every: float = 3.0, progress: bool = True) -> dict:
        if not symbols:
            raise ValueError("symbols must not be empty")

        data = self._client._json("POST", "/get-cached-reports", json=symbols, timeout=900)
        cached = data.get("result", [])
        missing = data.get("missing", [])
        rendering = data.get("rendering", {})  # {ticker: {"task_id", "status", "symbol"}}

        total = len(cached) + len(missing) + len(rendering)
        rendered, failed = {}, {}
        with tqdm(total=total, desc="Reports", unit="sym", disable=not progress) as pbar:
            pbar.update(len(cached) + len(missing))

            pending = {t: v["task_id"] for t, v in rendering.items()}
            deadline = time.monotonic() + max_wait

            while pending and time.monotonic() < deadline:
                for ticker, task_id in list(pending.items()):
                    body = self._client._json("GET", "/task-status", params={"task_id": task_id})
                    status = body.get("status")

                    if status in TERMINAL:
                        (rendered if status == "SUCCESS" else failed)[ticker] = body
                        del pending[ticker]
                        pbar.update(1)
                    else:
                        pbar.set_postfix_str(f"{ticker}: {status}")

                if pending:
                    time.sleep(poll_every)

            if pending:
                if progress:
                    tqdm.write(f"Timed out waiting on: {sorted(pending)}")
                failed.update({t: {"status": "TIMEOUT", "task_id": tid} for t, tid in pending.items()})

        return {"cached": cached, "rendered": rendered, "missing": missing, "failed": failed}

import time
from typing import TYPE_CHECKING, Any

from tqdm.auto import tqdm

if TYPE_CHECKING:
    from ._client import FlexreportClient

TERMINAL = {"SUCCESS", "FAILURE", "REVOKED"}


class Reports:
    def __init__(self, client: "FlexreportClient"):
        self._client = client

    def available(self, report_date: str, event_types: list[str] | None = None) -> Any:
        return self._client._json("POST", "/list-available-reports", json={"event_types": event_types, "report_date": report_date}, timeout=60)

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

    def draft_template(self, template: str, template_type: str, *, template_format: str = "html", anchor: str | None = None, max_wait: float = 900, poll_every: float = 3.0, progress: bool = True) -> dict:
        """Render previews of templates proposed from a plain-English request, without saving anything.

        The result carries the draft_id and per-variant preview URLs; pass the draft_id
        and the chosen variant_id to save_template() to store exactly what was previewed.
        """
        data = self._client._json("POST", "/draft-user-template", json={"template": template, "template_type": template_type, "template_format": template_format, "anchor": anchor})
        return self._client._wait_for_task(data["task_id"], "Template draft", max_wait, poll_every, progress)

    def save_template(self, template: str, template_type: str, *, template_format: str = "html", anchor: str | None = None, draft_id: str | None = None, variant_id: str | int | None = None, max_wait: float = 900, poll_every: float = 3.0, progress: bool = True) -> dict:
        """Save (or overwrite) the account's template. With draft_id and variant_id, the previewed variant is saved as-is."""
        data = self._client._json("POST", "/save-user-template", json={"template": template, "template_type": template_type, "template_format": template_format, "anchor": anchor, "draft_id": draft_id, "variant_id": variant_id})
        return self._client._wait_for_task(data["task_id"], "Template save", max_wait, poll_every, progress)

    def update_template(self, template: str | None = None, template_type: str | None = None, *, template_format: str | None = None, anchor: str | None = None, draft_id: str | None = None, variant_id: str | int | None = None, max_wait: float = 900, poll_every: float = 3.0, progress: bool = True) -> dict:
        """Change the saved template; omitted fields keep their stored values. With no arguments, recompiles the stored template."""
        fields = {"template": template, "template_type": template_type, "template_format": template_format, "anchor": anchor, "draft_id": draft_id, "variant_id": variant_id}
        data = self._client._json("PUT", "/update-user-template", json={k: v for k, v in fields.items() if v is not None})
        return {"changed": data.get("changed", []), **self._client._wait_for_task(data["task_id"], "Template update", max_wait, poll_every, progress)}

    def get_template(self) -> dict:
        return self._client._json("GET", "/get-user-template")

    def delete_template(self) -> dict:
        return self._client._json("DELETE", "/delete-user-template")

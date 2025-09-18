"""
post_plaintext_blast_httpx.py

Sends plaintext messages of the form:
  <timestamp> <WEBHOOK_SECRET> <MESSAGE>

Concurrently to a URL with a maximum of N simultaneous requests.
No retries, no backoff — just send.

Edit the constants at the top of this file.
"""

import asyncio
from datetime import datetime, timezone
import sys
import httpx
import traceback

# -------------------------
# Configure these constants
# -------------------------
URL = "https://grangemail.com/api/v1/trading-view-webhook"  # Destination URL
WEBHOOK_SECRET = "2qND5DJYk0aLoWVGhO2YYuBrurHxQW0B"

URL = "http://localhost/api/v1/trading-view-webhook"
WEBHOOK_SECRET = "Rr80D8vLT1hi7rsZFWSBahEruTUOr6ZL"
MESSAGE = "LSE_DLY:BYIT DOWN 400 20 15.531 13.978 13.163 12.697 12.427 12.27 12.186 12.15 12.149"

TOTAL_REQUESTS = 200  # How many requests to send in total
CONCURRENCY = 20  # How many at the same time
# -------------------------

CONTENT_TYPE = "text/plain; charset=utf-8"
TIMEOUT_SECONDS = 50  # per-request timeout


def now_formatted_with_offset():
    """Return timestamp like: 2025-09-16T08:00:00+0100 (no colon in offset)."""
    dt = datetime.now(timezone.utc).astimezone()
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


async def post_once(client: httpx.AsyncClient, url: str, payload: str):
    """Post payload once and return (status, text)."""
    resp = await client.post(
        url, content=payload.encode("utf-8"), headers={"Content-Type": CONTENT_TYPE}
    )
    return resp.is_success, resp.status_code, resp.text


async def worker(
    task_id: int,
    url: str,
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    results: list,
):
    """Construct timestamped payload and POST it."""
    async with sem:
        timestamp = now_formatted_with_offset()
        payload = f"{timestamp} {WEBHOOK_SECRET} {MESSAGE}"
        try:
            is_success, status, text = await post_once(client, url, payload)
            if is_success:
                results.append((True, status, text))
                print(f"[ok] task#{task_id} -> {status}")
            else:
                # Treat non-2xx as errors; print response snippet to stderr
                results.append((False, status, text))
                snippet = (text or "").strip().replace("\n", " ")[:500]
                print(
                    f"[err] task#{task_id} -> HTTP {status} - {snippet}",
                    file=sys.stderr,
                )
        except Exception as e:
            results.append((False, None, str(e)))
            print(f"[err] task#{task_id} -> Exception: {e!r}", file=sys.stderr)
            # Print stack trace to stderr for debugging
            traceback.print_exc()


async def run_all():
    sem = asyncio.Semaphore(CONCURRENCY)
    results = []

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        tasks = [
            asyncio.create_task(worker(i + 1, URL, sem, client, results))
            for i in range(TOTAL_REQUESTS)
        ]
        await asyncio.gather(*tasks)

    # Summarize
    success_count = sum(1 for r in results if r[0])
    fail_count = len(results) - success_count
    print("\n--- Summary ---")
    print(f"Total attempts : {len(results)}")
    print(f"Successes      : {success_count}")
    print(f"Failures       : {fail_count}")


def main():
    print(f"Sending {TOTAL_REQUESTS} POST(s) to {URL} with concurrency={CONCURRENCY}")
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

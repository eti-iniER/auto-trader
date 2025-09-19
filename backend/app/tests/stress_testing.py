"""Asynchronous plaintext webhook stress test.

Sends lines like: "<timestamp> <WEBHOOK_SECRET> <MESSAGE>" to a URL with bounded concurrency.
"""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import sys
import traceback
from typing import Optional, Tuple, List

import httpx


# Defaults (can be overridden via CLI)
# DEFAULT_URL = "https://grangemail.com/api/v1/trading-view-webhook"
# DEFAULT_WEBHOOK_SECRET = "2qND5DJYk0aLoWVGhO2YYuBrurHxQW0B"

DEFAULT_URL = "http://localhost/api/v1/trading-view-webhook"
DEFAULT_WEBHOOK_SECRET = "Rr80D8vLT1hi7rsZFWSBahEruTUOr6ZL"
DEFAULT_MESSAGE = "LSE_DLY:BYIT DOWN 400 20 15.531 13.978 13.163 12.697 12.427 12.27 12.186 12.15 12.149"
DEFAULT_TOTAL_REQUESTS = 60
DEFAULT_CONCURRENCY = 20
DEFAULT_CONTENT_TYPE = "text/plain; charset=utf-8"
DEFAULT_TIMEOUT_SECONDS = 50


Result = Tuple[bool, Optional[int], str]


def iso_now_local_no_colon_offset() -> str:
    """Timestamp like 2025-09-16T08:00:00+0100 (offset without colon)."""
    dt = datetime.now(timezone.utc).astimezone()
    return dt.strftime("%Y-%m-%dT%H:%M:%S%z")


async def post_once(client: httpx.AsyncClient, url: str, payload: str) -> Result:
    resp = await client.post(url, content=payload.encode("utf-8"))
    return resp.is_success, resp.status_code, resp.text


async def worker(
    task_id: int,
    url: str,
    sem: asyncio.Semaphore,
    client: httpx.AsyncClient,
    results: List[Result],
    secret: str,
    message: str,
) -> None:
    async with sem:
        timestamp = iso_now_local_no_colon_offset()
        payload = f"{timestamp} {secret} {message}"
        try:
            is_success, status, text = await post_once(client, url, payload)
            if is_success:
                results.append((True, status, text))
                print(f"[ok] task#{task_id} -> {status}")
            else:
                results.append((False, status, text))
                snippet = (text or "").strip().replace("\n", " ")[:500]
                print(
                    f"[err] task#{task_id} -> HTTP {status} - {snippet}",
                    file=sys.stderr,
                )
        except Exception as e:  # noqa: BLE001
            results.append((False, None, str(e)))
            print(f"[err] task#{task_id} -> Exception: {e!r}", file=sys.stderr)
            traceback.print_exc()


async def run_all(
    *,
    url: str,
    total_requests: int,
    concurrency: int,
    timeout_seconds: int,
    content_type: str,
    secret: str,
    message: str,
) -> None:
    sem = asyncio.Semaphore(concurrency)
    results: List[Result] = []

    async with httpx.AsyncClient(
        timeout=timeout_seconds, headers={"Content-Type": content_type}
    ) as client:
        tasks = [
            asyncio.create_task(
                worker(i + 1, url, sem, client, results, secret, message)
            )
            for i in range(total_requests)
        ]
        await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r[0])
    fail_count = len(results) - success_count
    print("\n--- Summary ---")
    print(f"Total attempts : {len(results)}")
    print(f"Successes      : {success_count}")
    print(f"Failures       : {fail_count}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Async plaintext webhook stress test")
    parser.add_argument("--url", default=DEFAULT_URL, help="Destination URL")
    parser.add_argument(
        "--secret", default=DEFAULT_WEBHOOK_SECRET, help="Webhook secret"
    )
    parser.add_argument("--message", default=DEFAULT_MESSAGE, help="Message body")
    parser.add_argument(
        "--total",
        type=int,
        default=DEFAULT_TOTAL_REQUESTS,
        help="Total requests to send",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=DEFAULT_CONCURRENCY,
        help="Max concurrent requests",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-request timeout in seconds",
    )
    parser.add_argument(
        "--content-type",
        default=DEFAULT_CONTENT_TYPE,
        help="Content-Type header value",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(
        f"Sending {args.total} POST(s) to {args.url} with concurrency={args.concurrency}"
    )
    try:
        asyncio.run(
            run_all(
                url=args.url,
                total_requests=args.total,
                concurrency=args.concurrency,
                timeout_seconds=args.timeout,
                content_type=args.__dict__["content_type"],
                secret=args.secret,
                message=args.message,
            )
        )
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

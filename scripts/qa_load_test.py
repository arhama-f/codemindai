#!/usr/bin/env python3
"""Automated QA/load-testing bots for CodeMind AI.

Spins up N concurrent synthetic clients that drive the real HTTP API through
the full core product loop (register -> org -> connect mock GitHub -> add
repo -> index -> ask -> analyze -> dismiss finding), to surface concurrency
bugs (race conditions, DB deadlocks, arq queue contention) before real users
do. This is a synthetic load test, NOT a source of user validation or social
proof -- all created data is clearly labeled as such (qa-bot-*@codemind-qa.example.com
emails, "QA Bot Org N" org names) and lives in the local dev database.

Usage:
    python scripts/qa_load_test.py --bots 10
    python scripts/qa_load_test.py --base-url http://localhost:8010 --bots 25 --timeout 90

Requires the API + worker to already be running (native `uvicorn`/`arq` per
docs/setup.md, or `docker compose --profile full up -d --build`), alongside
Postgres/Redis. Targets the local dev DB ("codemind"), not the test DB --
repeated runs accumulate rows there; `docker compose down -v` resets it if
you want a clean slate (not run automatically by this script).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
import uuid
from dataclasses import dataclass, field

import httpx

STEPS = [
    "register",
    "create_org",
    "connect_github",
    "list_repositories",
    "add_repository",
    "index",
    "ask",
    "analyze",
    "dismiss_finding",
]


@dataclass
class BotResult:
    bot_id: int
    ok: bool = True
    error: str | None = None
    failed_step: str | None = None
    step_seconds: dict[str, float] = field(default_factory=dict)


async def _poll_job(client: httpx.AsyncClient, base_url: str, org_id: str, job_id: str, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = await client.get(f"{base_url}/api/organizations/{org_id}/jobs/{job_id}")
        response.raise_for_status()
        status = response.json()["status"]
        if status == "completed":
            return
        if status == "failed":
            raise RuntimeError(f"job {job_id} failed")
        await asyncio.sleep(1)
    raise TimeoutError(f"job {job_id} did not complete within {timeout}s (last status poll pending)")


async def run_bot(bot_id: int, base_url: str, run_id: str, timeout: float) -> BotResult:
    result = BotResult(bot_id=bot_id)
    email = f"qa-bot-{bot_id}-{run_id}@codemind-qa.example.com"

    async with httpx.AsyncClient(timeout=30) as client:
        current_step = "register"
        try:
            step_start = time.monotonic()
            response = await client.post(
                f"{base_url}/api/auth/register",
                json={"email": email, "password": "qa-bot-password-1", "full_name": f"QA Bot {bot_id}"},
            )
            response.raise_for_status()
            result.step_seconds["register"] = time.monotonic() - step_start

            current_step = "create_org"
            step_start = time.monotonic()
            response = await client.post(
                f"{base_url}/api/organizations", json={"name": f"QA Bot Org {bot_id} ({run_id})"}
            )
            response.raise_for_status()
            org_id = response.json()["id"]
            result.step_seconds["create_org"] = time.monotonic() - step_start

            current_step = "connect_github"
            step_start = time.monotonic()
            response = await client.post(f"{base_url}/api/organizations/{org_id}/github/connect")
            response.raise_for_status()
            result.step_seconds["connect_github"] = time.monotonic() - step_start

            current_step = "list_repositories"
            step_start = time.monotonic()
            response = await client.get(f"{base_url}/api/organizations/{org_id}/github/repositories")
            response.raise_for_status()
            repos = response.json()
            if not repos:
                raise RuntimeError("no repositories returned from mock GitHub connect")
            external_repo_id = repos[0]["external_repo_id"]
            result.step_seconds["list_repositories"] = time.monotonic() - step_start

            current_step = "add_repository"
            step_start = time.monotonic()
            response = await client.post(
                f"{base_url}/api/organizations/{org_id}/repositories",
                json={"external_repo_id": external_repo_id},
            )
            response.raise_for_status()
            repo_id = response.json()["id"]
            result.step_seconds["add_repository"] = time.monotonic() - step_start

            current_step = "index"
            step_start = time.monotonic()
            response = await client.post(
                f"{base_url}/api/organizations/{org_id}/repositories/{repo_id}/index"
            )
            response.raise_for_status()
            job_id = response.json()["job_id"]
            await _poll_job(client, base_url, org_id, job_id, timeout)
            result.step_seconds["index"] = time.monotonic() - step_start

            current_step = "ask"
            step_start = time.monotonic()
            response = await client.post(
                f"{base_url}/api/organizations/{org_id}/repositories/{repo_id}/ask",
                json={"question": "Where is the divide function and could it fail?"},
            )
            response.raise_for_status()
            result.step_seconds["ask"] = time.monotonic() - step_start

            current_step = "analyze"
            step_start = time.monotonic()
            response = await client.post(
                f"{base_url}/api/organizations/{org_id}/repositories/{repo_id}/analyses"
            )
            response.raise_for_status()
            job_id = response.json()["job_id"]
            await _poll_job(client, base_url, org_id, job_id, timeout)
            result.step_seconds["analyze"] = time.monotonic() - step_start

            current_step = "dismiss_finding"
            step_start = time.monotonic()
            response = await client.get(
                f"{base_url}/api/organizations/{org_id}/repositories/{repo_id}/findings"
            )
            response.raise_for_status()
            findings = response.json()
            if findings:
                finding_id = findings[0]["id"]
                response = await client.post(
                    f"{base_url}/api/organizations/{org_id}/repositories/{repo_id}/findings/{finding_id}/dismiss",
                    json={"reason": "qa-load-test dismissal"},
                )
                response.raise_for_status()
            result.step_seconds["dismiss_finding"] = time.monotonic() - step_start

        except Exception as exc:  # noqa: BLE001 - report any failure per-bot, don't crash the run
            result.ok = False
            result.failed_step = current_step
            result.error = f"{type(exc).__name__}: {exc}"

    return result


def _print_summary(results: list[BotResult]) -> bool:
    passed = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]

    print(f"\n{'=' * 60}")
    print(f"QA load test: {len(passed)}/{len(results)} bots passed")
    print(f"{'=' * 60}\n")

    if passed:
        print("Latency by step (seconds, over passing bots):")
        for step in STEPS:
            samples = [r.step_seconds[step] for r in passed if step in r.step_seconds]
            if not samples:
                continue
            print(
                f"  {step:<18} min={min(samples):6.2f}  "
                f"avg={sum(samples) / len(samples):6.2f}  max={max(samples):6.2f}"
            )

    if failed:
        print("\nFailures:")
        for r in failed:
            print(f"  bot {r.bot_id}: failed at '{r.failed_step}' -- {r.error}")

    print()
    return not failed


async def main_async(args: argparse.Namespace) -> int:
    run_id = uuid.uuid4().hex[:8]
    print(f"Starting {args.bots} QA bots against {args.base_url} (run_id={run_id})")

    results = await asyncio.gather(
        *(run_bot(i, args.base_url, run_id, args.timeout) for i in range(1, args.bots + 1))
    )

    all_ok = _print_summary(results)
    return 0 if all_ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base-url", default="http://localhost:8010", help="API base URL")
    parser.add_argument("--bots", type=int, default=10, help="number of concurrent bots")
    parser.add_argument(
        "--timeout", type=float, default=60.0, help="seconds to wait for each indexing/analysis job"
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()

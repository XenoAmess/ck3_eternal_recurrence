"""Wait on the existing partial core query before Root's first full snapshot.

This module reuses a held MCP ClientSession. It never launches CK3, creates a
client, reads driver-state files, or requests a complete snapshot.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json


async def wait_for_restored_core_v1(session, expected: dict) -> dict:
    """Observe loading through the registered core tool; qualify nothing else."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + 180.0
    started = datetime.now(timezone.utc).isoformat()
    attempts = []
    while True:
        attempt = {"query": len(attempts) + 1,
                   "started_at_utc": datetime.now(timezone.utc).isoformat(),
                   "tool": "ck3_query_core_frame_v1", "arguments": {}}
        ready = False
        try:
            result = await session.call_tool("ck3_query_core_frame_v1", {})
            raw = result.model_dump(mode="json")
            attempt["result"] = raw
            body = raw.get("structuredContent", raw.get("structured_content"))
            if not isinstance(body, dict):
                for block in raw.get("content", []):
                    if block.get("type") == "text":
                        try:
                            candidate = json.loads(block["text"])
                        except (TypeError, ValueError):
                            continue
                        if isinstance(candidate, dict):
                            body = candidate
                            break
            # NativeDriver already applies the existing exact-build core
            # normalizer. Keep the partial result separate from full readiness.
            ready = (
                not raw.get("isError", raw.get("is_error", False))
                and isinstance(body, dict)
                and body.get("status") == "partial"
                and body.get("complete_snapshot") is False
                and body.get("core_available") is True
                and body.get("application_main_observed") is True
                and body.get("map_ready") is True
                and body.get("has_played_character") is True
                and body.get("played_character_alive") is True
                and body.get("paused") is expected["expected_paused"]
                and body.get("date_raw") == expected["expected_date_raw"]
            )
        except Exception as error:
            attempt["client_error"] = repr(error)
        attempt["ended_at_utc"] = datetime.now(timezone.utc).isoformat()
        attempt["core_ready_for_full_snapshot"] = ready
        attempts.append(attempt)
        remaining = deadline - loop.time()
        if ready or remaining <= 0:
            return {
                "status": ("CORE_READY_FOR_FULL_SNAPSHOT" if ready
                           else "TIMED_OUT_WAITING_FOR_CORE"),
                "started_at_utc": started,
                "ended_at_utc": datetime.now(timezone.utc).isoformat(),
                "core_query_count": len(attempts),
                "full_snapshot_query_count": 0,
                "wait_budget_seconds": 180,
                "poll_interval_seconds": 1,
                "expected_date_raw": expected["expected_date_raw"],
                "expected_paused": expected["expected_paused"],
                "original_character_and_episode_qualified": False,
                "complete_snapshot_qualified": False,
                "attempts": attempts,
            }
        await asyncio.sleep(min(1.0, remaining))

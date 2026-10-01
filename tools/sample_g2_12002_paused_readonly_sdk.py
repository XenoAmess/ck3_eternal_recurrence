"""Sample the eight published nonwar private query domains using MCP stdio.

The default CLI path only reads a runner plan and writes its sampling plan.
The sole live operator can later use --execute-readonly to start the plan's
MCP server. This tool never submits an action or controls the CK3 process.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import Mapping
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import uuid


OBSERVATION_TOOL = "ck3_take_snapshot"
ROOT_TOOL = "ck3_query_campaign_root_context_v1"
READ_FLAGS = frozenset({
    "--private-council-query", "--private-faction-gift-query",
    "--private-active-scheme-sway-query", "--private-realm-law-paused-query",
    "--private-government-runtime-adapter-query", "--private-prisoner-collection-query",
    "--private-activity-feast-queries", "--private-family-obligations-query",
})
DOMAIN_TOOLS = (
    ("government", "ck3_query_government_runtime_adapter_private_v1"),
    ("family", "ck3_query_family_obligations_private_v1"),
    ("prisoner", "ck3_query_player_prisoner_collection_private_v1"),
    ("sway", "ck3_query_active_scheme_sway_target_private_v1"),
    ("law", "ck3_query_realm_law_final_terms_private_v1"),
    ("council", "ck3_query_council_final_gates_private_v1"),
    ("feast", "ck3_query_activity_feast_hosted_post_private_v1"),
    ("gift", "ck3_query_faction_gift_candidate_private_v1"),
)


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_readonly_plan(path: Path) -> dict[str, object]:
    plan = json.loads(path.read_text(encoding="utf-8-sig"))
    argv = plan.get("argv") if isinstance(plan, dict) else None
    if (not isinstance(argv, list) or not argv
            or any(not isinstance(arg, str) or not arg for arg in argv)
            or plan.get("formal_action_permits_enabled") is not False):
        raise ValueError("runner plan must contain argv with formal action permits off")
    private_flags = [arg for arg in argv if arg.startswith("--private-")]
    if set(private_flags) != READ_FLAGS or len(private_flags) != len(READ_FLAGS):
        raise ValueError("runner plan must select exactly the eight nonwar private read flags")
    for flag, expected in (("--driver", "native-headless"), ("--transport", "stdio")):
        try:
            actual = argv[argv.index(flag) + 1]
        except (ValueError, IndexError) as error:
            raise ValueError("runner plan lacks " + flag) from error
        if actual != expected:
            raise ValueError("runner plan requires " + flag + " " + expected)
    return plan


def _packet(result: object) -> dict[str, object]:
    if isinstance(result, Mapping):
        return dict(result)
    dump = getattr(result, "model_dump", None)
    if callable(dump):
        value = dump(mode="json", by_alias=True)
        if isinstance(value, dict):
            return value
    raise ValueError("MCP result cannot be serialized as a packet")


def _payload(packet: Mapping[str, object]) -> dict[str, object] | None:
    value = packet.get("structuredContent", packet.get("structured_content"))
    if isinstance(value, dict):
        return value
    content = packet.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, Mapping) and item.get("type") == "text":
                try:
                    value = json.loads(str(item.get("text", "")))
                except json.JSONDecodeError:
                    continue
                if isinstance(value, dict):
                    return value
    return None


def _frame(snapshot: Mapping[str, object]) -> dict[str, int]:
    actor = snapshot.get("played_character")
    actor_id = actor.get("character_id") if isinstance(actor, Mapping) else None
    revision, date_raw = snapshot.get("revision"), snapshot.get("date_raw")
    if snapshot.get("paused") is not True:
        raise ValueError("snapshot is not paused")
    if snapshot.get("map_ready") is False:
        raise ValueError("snapshot map is not ready")
    if (type(revision) is not int or revision <= 0
            or type(date_raw) is not int or date_raw < 0
            or type(actor_id) is not int or not 0 < actor_id <= 0xFFFFFFFF):
        raise ValueError("snapshot lacks observed revision, actor or date_raw")
    result = {"revision": revision, "actor_character_id": actor_id, "date_raw": date_raw}
    native = snapshot.get("native_revision")
    if type(native) is int and native > 0:
        result["native_revision"] = native
    return result


def _same_actor_date(baseline: Mapping[str, int], frame: Mapping[str, int]) -> bool:
    return all(baseline[key] == frame[key] for key in ("actor_character_id", "date_raw"))


def _tool_names(listed: Mapping[str, object]) -> set[str]:
    tools = listed.get("tools")
    return {tool["name"] for tool in tools if isinstance(tool, Mapping)
            and isinstance(tool.get("name"), str)} if isinstance(tools, list) else set()


def planned_queries(options: argparse.Namespace) -> list[dict[str, object]]:
    queries = []
    for domain, tool in DOMAIN_TOOLS:
        arguments: dict[str, object] = {}
        reason = None
        if domain == "family":
            if options.family_subject_character_id is None or options.family_candidate_character_id is None:
                reason = "explicit_family_subject_and_candidate_ids_required"
            else:
                arguments = {
                    "subject_character_id": options.family_subject_character_id,
                    "candidate_character_id": options.family_candidate_character_id,
                    "request_matrilineal_option": options.family_matrilineal,
                }
                if options.family_break_recipient_character_id is not None:
                    arguments["break_recipient_character_id"] = options.family_break_recipient_character_id
        elif domain == "sway":
            if options.sway_target_character_id is None:
                reason = "explicit_sway_target_id_required"
            else:
                arguments["target_character_id"] = options.sway_target_character_id
        elif domain == "gift":
            arguments["minimum_gold_reserve_raw"] = options.minimum_gold_reserve_raw
        queries.append({"domain": domain, "tool": tool, "arguments": arguments,
                        "skip_reason": reason})
    return queries


async def sample_paused_readonly(
    client: Any, *, artifacts: Path, options: argparse.Namespace,
    transport: str = "stdio-sdk",
) -> dict[str, object]:
    """Sample fixed read tools; a changed paused actor/date ends the batch."""
    artifacts.mkdir(parents=True, exist_ok=True)
    report: dict[str, object] = {
        "schema": "xar.g2.paused-readonly-sample.v1", "executed": True,
        "transport": transport, "observation_tool": OBSERVATION_TOOL,
        "status": "running", "calls": [], "domains": [],
        "formal_action_calls": 0,
    }

    async def call(name: str, arguments: dict[str, object]) -> dict[str, object] | None:
        ordinal = len(report["calls"]) + 1
        path = artifacts / f"{ordinal:03d}-{name}.json"
        record: dict[str, object] = {"tool": name, "arguments": arguments,
                                    "packet_file": path.name}
        try:
            packet = _packet(await client.call_tool(name, arguments))
            _write(path, {"tool": name, "arguments": arguments, "packet": packet})
            if packet.get("isError", packet.get("is_error", False)):
                record["status"] = "error"
                record["error"] = "MCP tool result isError"
                value = None
            else:
                value = _payload(packet)
                record["status"] = "captured" if value is not None else "error"
                if value is None:
                    record["error"] = "MCP result has no object payload"
        except Exception as error:
            record.update({"status": "error", "error_type": type(error).__name__,
                           "error": str(error)})
            _write(path, record)
            value = None
        report["calls"].append(record)
        return value

    try:
        listing = _packet(await client.list_tools())
        _write(artifacts / "tool-discovery.json", listing)
        names = _tool_names(listing)
        if OBSERVATION_TOOL not in names:
            raise ValueError("canonical ck3_take_snapshot tool is unavailable")
        initial = await call(OBSERVATION_TOOL, {})
        if initial is None:
            raise ValueError("initial observed snapshot is unavailable")
        baseline = _frame(initial)
        report["initial_frame"] = baseline

        async def fresh_frame() -> dict[str, int]:
            observed = await call(OBSERVATION_TOOL, {})
            if observed is None:
                raise ValueError("fresh observed snapshot is unavailable")
            frame = _frame(observed)
            if not _same_actor_date(baseline, frame):
                raise ValueError("observed actor or date changed during sample batch")
            return frame

        for query in planned_queries(options):
            domain_record = {"domain": query["domain"], "tool": query["tool"]}
            report["domains"].append(domain_record)
            if query["skip_reason"] is not None:
                domain_record.update({"status": "skipped", "reason": query["skip_reason"]})
                continue
            if query["tool"] not in names:
                domain_record.update({"status": "skipped", "reason": "tool_not_published"})
                continue
            frame = await fresh_frame()
            arguments = {**query["arguments"], "expected_revision": frame["revision"]}
            if query["domain"] == "gift":
                if ROOT_TOOL not in names:
                    domain_record.update({"status": "skipped", "reason": "campaign_root_tool_not_published"})
                    continue
                root_packet = await call(ROOT_TOOL, {"expected_revision": frame["revision"]})
                frame = await fresh_frame()
                root = root_packet.get("campaign_root_context") if isinstance(root_packet, Mapping) else None
                if not isinstance(root, dict) or root_packet.get("status") != "available":
                    domain_record.update({"status": "skipped", "reason": "campaign_root_unavailable"})
                    continue
                government = root.get("government")
                if (root.get("snapshot_revision") != frame.get("native_revision")
                        or root.get("date_raw") != frame["date_raw"]
                        or root.get("player_character_id") != frame["actor_character_id"]):
                    domain_record.update({"status": "skipped", "reason": "campaign_root_frame_mismatch"})
                    continue
                if not isinstance(government, Mapping) or government.get("key") != "feudal_government":
                    domain_record.update({"status": "skipped", "reason": "gift_government_not_supported"})
                    continue
                count = root.get("player_targeting_faction_count")
                if type(count) is not int or count < 0:
                    domain_record.update({"status": "skipped", "reason": "targeting_faction_count_unavailable"})
                    continue
                if count == 0:
                    domain_record.update({"status": "skipped", "reason": "native_targeting_factions_known_empty"})
                    continue
                arguments.update({"expected_revision": frame["revision"], "same_frame_root": root})
            value = await call(query["tool"], arguments)
            domain_record.update({"status": "captured" if value is not None else "error",
                                  "source_frame": frame})
            # Record an independent post-read paused frame too. An unavailable
            # domain query may be followed by other reads only on that same
            # observed actor/date.
            await fresh_frame()
        report["status"] = "sampled_with_query_errors" if any(
            row.get("status") == "error" for row in report["domains"]
        ) else "sampled"
    except Exception as error:
        report.update({"status": "stopped", "stop_error_type": type(error).__name__,
                       "stop_reason": str(error)})
    _write(artifacts / "sample-result.json", report)
    return report


async def execute_stdio_plan(
    plan: Mapping[str, object], *, artifacts: Path, options: argparse.Namespace,
) -> dict[str, object]:
    from mcp import ClientSession, StdioServerParameters, stdio_client

    argv = plan["argv"]
    script = next((Path(arg) for arg in argv[1:] if arg.endswith("mcp_server.py")), None)
    parameters = StdioServerParameters(command=argv[0], args=argv[1:],
                                       cwd=script.parent if script is not None else None)
    with (artifacts / "mcp-server-stderr.log").open("w", encoding="utf-8") as stderr:
        async with stdio_client(parameters, errlog=stderr) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as client:
                initialized = await client.initialize()
                _write(artifacts / "mcp-initialize.json", _packet(initialized))
                return await sample_paused_readonly(client, artifacts=artifacts, options=options)


def _character_id(value: str) -> int:
    parsed = int(value)
    if not 0 < parsed <= 0xFFFFFFFF:
        raise argparse.ArgumentTypeError("character ID must be a full positive uint32")
    return parsed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--plan", type=Path, required=True)
    result.add_argument("--artifacts", type=Path, required=True)
    result.add_argument("--execute-readonly", action="store_true",
                        help="sole live operator: start the plan's MCP stdio server and sample reads")
    result.add_argument("--family-subject-character-id", type=_character_id)
    result.add_argument("--family-candidate-character-id", type=_character_id)
    result.add_argument("--family-break-recipient-character-id", type=_character_id)
    result.add_argument("--family-matrilineal", action="store_true")
    result.add_argument("--sway-target-character-id", type=_character_id)
    result.add_argument("--minimum-gold-reserve-raw", type=int, default=10_000_000)
    return result


def main(argv: list[str] | None = None) -> int:
    options = parser().parse_args(argv)
    if options.minimum_gold_reserve_raw < 0:
        raise ValueError("minimum gold reserve must be nonnegative")
    plan = load_readonly_plan(options.plan)
    run_dir = options.artifacts / (
        "sample-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    )
    run_dir.mkdir(parents=True)
    _write(run_dir / "input-runner-plan.json", plan)
    sampling_plan = {
        "schema": "xar.g2.paused-readonly-sampler-plan.v1",
        "executed": False, "observation_tool": OBSERVATION_TOOL,
        "queries": planned_queries(options), "formal_action_calls": 0,
    }
    _write(run_dir / "sampling-plan.json", sampling_plan)
    if options.execute_readonly:
        try:
            report = asyncio.run(execute_stdio_plan(plan, artifacts=run_dir, options=options))
        except Exception as error:
            report = {"status": "stopped", "executed": True,
                      "stop_error_type": type(error).__name__, "stop_reason": str(error)}
            _write(run_dir / "sample-result.json", report)
        status = report["status"]
    else:
        status = "prepared_files_only"
    print(json.dumps({"status": status, "artifacts": str(run_dir)}, ensure_ascii=False))
    return 1 if status == "stopped" else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Ordinary CK3 campaign policy over an already-owned async MCP client.

No attach, injector, desktop, observer, date-control or episode-rule capability
is imported or invoked. The profile provider owns process/build/Steam/lease
guards. Calendar completion is established from complete plaintext save bytes.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import time
from typing import Any, Protocol


SNAPSHOT = "ck3_take_profile_native_snapshot_v1"
INSPECT = "ck3_query_native_profile_v1"
PAUSE = "ck3_pause_profile_simulation_v1"
PAUSE_CONTROLLER_INSPECT = "ck3_query_clock_pause_profile_v1"
PAUSE_CONTROLLER = "ck3_pause_profile_gameplay_v1"
SIMULATION = "ck3_set_profile_simulation_v1"
QUERY_EVENT = "ck3_query_profile_event_window_v1"
SELECT_EVENT = "ck3_select_profile_event_option_v1"
SAVE = "ck3_save_profile_checkpoint_v1"
TOOLS = {SNAPSHOT, INSPECT, PAUSE, SIMULATION, QUERY_EVENT, SELECT_EVENT, SAVE}
RAW_UNITS_PER_DAY = 24  # Authoritative ck3_native_clock_reader.py clock contract.
_LATE_POSTCONDITIONS = {
    "RuntimeError: native pause/resume postcondition did not materialize",
    "RuntimeError: current native pause postcondition did not materialize",
}
_TRANSIENT_EVENT_PRESENTATION = {
    "event_window_not_materialized", "event_splash_transition_in_progress",
}


class AsyncClient(Protocol):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any: ...


@dataclass(frozen=True)
class CampaignConfig:
    start_date: str
    target_date: str
    baseline_date_raw: int
    save_directory: Path
    evidence_directory: Path
    checkpoint_days: int = 365
    poll_seconds: float = 2.0
    postcondition_timeout_seconds: float = 20.0
    no_progress_timeout_seconds: float = 300.0
    tool_timeout_seconds: float = 90.0
    max_event_chain: int = 64
    speed: int = 5

    def validate(self) -> None:
        if parse_date(self.start_date) >= parse_date(self.target_date):
            raise ValueError("start_date must precede target_date")
        if type(self.baseline_date_raw) is not int or self.baseline_date_raw <= 0:
            raise ValueError("baseline_date_raw must be the frozen positive native start clock")
        if type(self.checkpoint_days) is not int or not 1 <= self.checkpoint_days <= 366:
            raise ValueError("checkpoint_days must be between 1 and 366")
        if type(self.max_event_chain) is not int or not 1 <= self.max_event_chain <= 256:
            raise ValueError("max_event_chain must be between 1 and 256")
        if type(self.speed) is not int or self.speed not in {1, 3, 5}:
            raise ValueError("speed must be an ordinary profile speed: 1, 3 or 5")
        for name in ("poll_seconds", "postcondition_timeout_seconds", "no_progress_timeout_seconds", "tool_timeout_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if not Path(self.save_directory).is_dir():
            raise ValueError("save_directory must already exist")


class CampaignStop(RuntimeError):
    def __init__(self, reason: str, *, rejected: bool = False):
        super().__init__(reason)
        self.rejected = rejected


def parse_date(value: str) -> date:
    if not isinstance(value, str) or re.fullmatch(r"\d+\.\d+\.\d+", value) is None:
        raise ValueError("CK3 date must be year.month.day")
    return date(*(int(part) for part in value.split(".")))


def _brace_depth(prefix: bytes) -> int:
    depth, quoted, escaped, comment = 0, False, False, False
    for value in prefix:
        if comment:
            comment = value not in (10, 13)
        elif quoted:
            if escaped:
                escaped = False
            elif value == 92:
                escaped = True
            elif value == 34:
                quoted = False
        elif value == 35:
            comment = True
        elif value == 34:
            quoted = True
        elif value == 123:
            depth += 1
        elif value == 125:
            depth -= 1
            if depth < 0:
                raise ValueError("save prefix has unmatched closing brace")
    return -1 if quoted or comment else depth


def read_plaintext_save(path: Path) -> tuple[bytes, dict[str, Any]]:
    """Hash every byte, then read an unambiguous top-level body date, not meta_date."""
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or len(raw) != after.st_size:
        raise ValueError("save changed during full-byte read")
    if not raw.startswith(b"SAV0100") or b"\0" in raw:
        raise ValueError("checkpoint is not the supported plaintext SAV0100 format")
    candidates = list(re.finditer(rb"(?m)^date[ \t]*=[ \t]*(\d+\.\d+\.\d+)[ \t]*\r?$", raw))
    body = [m for m in candidates if _brace_depth(raw[:m.start()]) == 0]
    if len(body) != 1:
        raise ValueError("save requires exactly one top-level body date")
    actual_date = body[0].group(1).decode("ascii")
    parse_date(actual_date)
    meta = re.findall(rb"(?m)^[ \t]*meta_date[ \t]*=[ \t]*(\d+\.\d+\.\d+)[ \t]*\r?$", raw)
    if len(meta) > 1 or (meta and parse_date(meta[0].decode("ascii")) != parse_date(actual_date)):
        raise ValueError("save meta_date disagrees with the body date")
    return raw, {"path": str(path.resolve()), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                 "body_date": actual_date, "meta_date": meta[0].decode("ascii") if meta else None,
                 "format": "plaintext-SAV0100", "date_field_offset": body[0].start()}


def choose_option(context: dict[str, Any]) -> dict[str, Any]:
    """Rank only native shown/enabled buttons using explicitly partial indicators."""
    options = context.get("options")
    if not isinstance(options, list):
        raise CampaignStop("event_option_presentation_unavailable")
    ranked = []
    for option in options:
        if not isinstance(option, dict) or option.get("shown") is not True or option.get("enabled") is not True:
            continue
        index = option.get("native_option_index")
        if type(index) is not int or not 0 <= index < 64:
            raise CampaignStop("event_native_option_index_invalid", rejected=True)
        rows = option.get("effect_indicators", {}).get("rows", [])
        if not isinstance(rows, list):
            raise CampaignStop("event_indicator_rows_invalid", rejected=True)
        critical = any(isinstance(row, dict) and row.get("critical") is True for row in rows)
        stress = any(isinstance(row, dict) and row.get("kind") in {"stress", "stress_and_fulfillment"}
                     and row.get("direction") == "increase" for row in rows)
        ranked.append(((critical, stress, index), option))
    if not ranked:
        raise CampaignStop("event_has_no_shown_enabled_option")
    return min(ranked, key=lambda row: row[0])[1]


def _serialized(value: Any) -> Any:
    if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "model_dump"):
        try:
            return value.model_dump(mode="json", by_alias=True)
        except TypeError:
            return value.model_dump()
    raise TypeError("MCP client must return a serialized or public model_dump result")


def _body(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("is_error") is True or raw.get("isError") is True:
        raise CampaignStop("mcp_tool_error", rejected=True)
    value = raw.get("structured_content", raw.get("structuredContent"))
    if value is None:
        texts = [item.get("text") for item in raw.get("content", []) if isinstance(item, dict) and item.get("type") == "text"]
        if len(texts) == 1:
            value = json.loads(texts[0])
    if not isinstance(value, dict):
        raise CampaignStop("mcp_structured_content_unavailable", rejected=True)
    return value


class CampaignPolicy:
    def __init__(self, client: AsyncClient, config: CampaignConfig, *, pause_provider: AsyncClient | None = None):
        config.validate()
        self.client, self.config = client, config
        self.pause_provider = pause_provider
        self.pause_controller_binding = None
        self.native_observation = None
        self.directory = Path(config.evidence_directory).resolve()
        self.directory.mkdir(parents=True, exist_ok=True)
        if any(self.directory.iterdir()):
            raise ValueError("evidence_directory must be new and empty")
        self.sequence = 0
        self.binding = None
        self.native_binding = None
        self.last_raw = config.baseline_date_raw
        self.pending_mail_present = False
        self.last_player = None
        self.last_saved_date = parse_date(config.start_date)
        self.last_save_proof = None

    def record(self, kind: str, value: dict[str, Any]) -> Path:
        self.sequence += 1
        path = self.directory / f"{self.sequence:06d}-{kind}.json"
        with path.open("x", encoding="utf-8") as output:
            json.dump({"schema": "ck3.native-campaign-policy.v1", "at_utc": datetime.now(timezone.utc).isoformat(), **value}, output, ensure_ascii=False, indent=2)
            output.write("\n")
        return path

    async def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if tool not in TOOLS:
            raise CampaignStop("policy_tool_not_allowlisted", rejected=True)
        request = self.record("request", {"tool": tool, "arguments": arguments})
        try:
            result = await asyncio.wait_for(self.client.call_tool(tool, arguments), self.config.tool_timeout_seconds)
            raw = _serialized(result)
            self.record("mcp-receipt", {"request": str(request), "tool": tool, "response": raw})
            body = _body(raw)
        except asyncio.CancelledError:
            self.record("unresolved-request", {"request": str(request), "reason": "cancelled; dispatch is not replayed"})
            raise
        except CampaignStop:
            raise
        except Exception as error:
            self.record("request-error", {"request": str(request), "type": type(error).__name__, "reason": str(error)})
            raise CampaignStop("mcp_request_failed_or_unresolved", rejected=True) from error
        identity = (body.get("session_id"), body.get("profile_sha256"))
        if not all(isinstance(item, str) and item for item in identity):
            raise CampaignStop("mcp_profile_identity_missing", rejected=True)
        if self.binding is None:
            self.binding = identity
        elif self.binding != identity:
            raise CampaignStop("mcp_profile_identity_changed", rejected=True)
        return body

    async def snapshot(self, *, policy_action_readback: bool = False) -> dict[str, Any]:
        receipt = await self.call(SNAPSHOT, {})
        if receipt.get("status") != "native_snapshot_verified":
            raise CampaignStop("native_snapshot_guard_failed", rejected=True)
        frame = receipt.get("snapshot", {})
        if (frame.get("map_ready") is not True or frame.get("episode_projection") != "native_campaign"
                or type(frame.get("revision")) is not int or frame["revision"] < 0
                or type(frame.get("date_raw")) is not int or type(frame.get("paused")) is not bool
                or type(frame.get("speed")) is not int):
            raise CampaignStop("native_campaign_snapshot_invalid", rejected=True)
        if frame["date_raw"] < self.last_raw:
            raise CampaignStop("native_clock_moved_backwards", rejected=True)
        previous_raw = self.last_raw
        self.last_raw = frame["date_raw"]
        diagnostics = frame.get("diagnostics", {})
        hello = diagnostics.get("hello", {})
        native = (diagnostics.get("bridge_pid"), diagnostics.get("connection_generation"),
                  hello.get("expected_ck3_version"), hello.get("expected_ck3_sha256"))
        if type(native[0]) is not int or native[0] <= 0 or not native[2] or not native[3]:
            raise CampaignStop("native_process_build_identity_missing", rejected=True)
        if self.native_binding is None:
            self.native_binding = native
        elif self.native_binding != native:
            raise CampaignStop("native_process_build_identity_changed", rejected=True)
        player = frame.get("played_character")
        if not isinstance(player, dict) or type(player.get("character_id")) is not int or player["character_id"] <= 0 or player.get("alive") is not True:
            raise CampaignStop("player_terminal_or_unavailable")
        if self.last_player is not None and self.last_player != player["character_id"]:
            self.record("native-player-change", {"before": self.last_player, "after": player["character_id"], "date_raw": frame["date_raw"], "meaning": "engine current player changed; no one-life identity or heir inference"})
        self.last_player = player["character_id"]
        if any(frame.get(key) for key in ("blocking_modal", "unknown_modal", "game_over")):
            raise CampaignStop("non_event_modal_requires_root")
        pending_mail = frame.get("pending_character_interaction") is not None
        if pending_mail or self.pending_mail_present:
            self.record("pending-mail-observation", {
                "present": pending_mail, "previously_present": self.pending_mail_present,
                "date_raw": frame["date_raw"], "previous_date_raw": previous_raw,
                "native_clock_advanced": frame["date_raw"] > previous_raw,
                "paused": frame["paused"], "policy_action_readback": policy_action_readback,
                "meaning": "native pending mail presence only; no interaction result inferred",
            })
        self.pending_mail_present = pending_mail
        if pending_mail and frame["paused"] and frame.get("active_event") is None and not policy_action_readback:
            raise CampaignStop("pending_mail_with_unexpected_pause")
        return frame

    async def action(self, tool: str, arguments: dict[str, Any], predicate) -> dict[str, Any]:
        """One dispatch only; any later confirmation uses bounded guarded reads."""
        receipt = await self.call(tool, arguments)
        status = receipt.get("status")
        late = (status == "RED" and receipt.get("reason") in _LATE_POSTCONDITIONS
                and (tool == PAUSE or (tool == SIMULATION and arguments.get("action") in {"pause", "resume"})))
        if status != "native_gameplay_postcondition_verified" and not late:
            raise CampaignStop("native_action_rejected_or_guard_failed", rejected=True)
        deadline = time.monotonic() + self.config.postcondition_timeout_seconds
        while True:
            frame = await self.snapshot(policy_action_readback=True)
            if await predicate(frame, receipt):
                self.record("action-confirmed", {"tool": tool, "original_status": status, "recovered_late_postcondition": late, "revision": frame["revision"], "date_raw": frame["date_raw"]})
                return frame
            if time.monotonic() >= deadline:
                raise CampaignStop("native_action_postcondition_not_observed")
            await asyncio.sleep(self.config.poll_seconds)

    async def pause(self, frame: dict[str, Any]) -> dict[str, Any]:
        if frame["paused"]:
            return frame
        if self.pause_provider is not None:
            receipt = await self.call_pause_controller(PAUSE_CONTROLLER, frame)
            if (receipt.get("status") != "gameplay_pause_verified" or receipt.get("desired_paused") is not True
                    or type(receipt.get("input_dispatch_attempts")) is not int or receipt["input_dispatch_attempts"] not in (0, 1)
                    or receipt.get("clock_after", {}).get("paused") is not True
                    or type(receipt.get("clock_after", {}).get("date_raw")) is not int
                    or receipt["clock_after"]["date_raw"] < frame["date_raw"]):
                raise CampaignStop("pause_controller_rejected_or_unconfirmed", rejected=True)
            deadline = time.monotonic() + self.config.postcondition_timeout_seconds
            while True:
                current = await self.snapshot(policy_action_readback=True)
                if current["paused"] and current["date_raw"] >= receipt["clock_after"]["date_raw"]:
                    self.record("pause-controller-confirmed", {"controller_session_id": receipt["session_id"],
                        "controller_profile_sha256": receipt["profile_sha256"], "controller_receipt_path": receipt.get("receipt_path"),
                        "native_session_id": self.binding[0], "date_raw": current["date_raw"], "revision": current["revision"]})
                    return current
                if time.monotonic() >= deadline:
                    raise CampaignStop("pause_controller_native_readback_not_observed")
                await asyncio.sleep(self.config.poll_seconds)
        async def paused(current, receipt):
            return current["paused"] is True
        return await self.action(PAUSE, {}, paused)

    async def call_pause_controller(self, tool: str, frame: dict[str, Any]) -> dict[str, Any]:
        if tool not in {PAUSE_CONTROLLER_INSPECT, PAUSE_CONTROLLER} or self.pause_provider is None:
            raise CampaignStop("pause_controller_tool_not_allowlisted", rejected=True)
        request = self.record("pause-controller-request", {"tool": tool, "arguments": {}})
        try:
            response = await asyncio.wait_for(self.pause_provider.call_tool(tool, {}), self.config.tool_timeout_seconds)
            raw = _serialized(response)
            self.record("pause-controller-receipt", {"request": str(request), "tool": tool, "response": raw})
            body = _body(raw)
        except CampaignStop:
            raise
        except Exception as error:
            self.record("pause-controller-error", {"request": str(request), "type": type(error).__name__, "reason": str(error)})
            raise CampaignStop("pause_controller_request_failed_or_unresolved", rejected=True) from error
        identity = (body.get("session_id"), body.get("profile_sha256"))
        if (body.get("schema") != "ck3.clock-pause-profile-receipt.v1"
                or not isinstance(identity[0], str) or not identity[0] or identity[0] == self.binding[0]
                or not isinstance(identity[1], str) or not re.fullmatch(r"[0-9a-fA-F]{64}", identity[1])):
            raise CampaignStop("pause_controller_identity_invalid", rejected=True)
        if self.pause_controller_binding is None:
            self.pause_controller_binding = identity
        elif self.pause_controller_binding != identity:
            raise CampaignStop("pause_controller_identity_changed", rejected=True)
        observed = self.native_observation
        target = body.get("target_identity")
        fields = {"pid", "hwnd", "process_create_time", "executable", "executable_sha256", "build_id", "game_version", "userdir"}
        if not isinstance(observed, dict) or not isinstance(target, dict) or set(target) != fields:
            raise CampaignStop("pause_controller_target_identity_missing", rejected=True)
        userdirs = [arg.split("=", 1)[1] for arg in observed.get("command_line", [])
                    if isinstance(arg, str) and arg.startswith("-userdir=")]
        hello = frame["diagnostics"]["hello"]
        if (len(userdirs) != 1 or target["pid"] != frame["diagnostics"]["bridge_pid"]
                or target["game_version"] != hello["expected_ck3_version"]
                or str(target["executable_sha256"]).lower() != str(hello["expected_ck3_sha256"]).lower()
                or any(target[key] != observed.get(key) for key in ("pid", "hwnd", "process_create_time", "build_id"))
                or Path(target["executable"]).resolve() != Path(observed.get("executable", "")).resolve()
                or str(target["executable_sha256"]).lower() != str(observed.get("executable_sha256", "")).lower()
                or Path(target["userdir"]).resolve() != Path(userdirs[0]).resolve()):
            raise CampaignStop("pause_controller_target_does_not_match_native_campaign", rejected=True)
        return body

    async def resume(self, frame: dict[str, Any]) -> dict[str, Any]:
        if frame.get("active_event") is not None:
            raise CampaignStop("resume_with_active_event_forbidden")
        async def running(current, receipt):
            return current["paused"] is False
        return await self.action(SIMULATION, {"action": "resume", "expected_revision": frame["revision"]}, running)

    async def set_speed(self, frame: dict[str, Any]) -> dict[str, Any]:
        if frame["speed"] == self.config.speed:
            return frame
        async def desired_speed(current, receipt):
            return current["speed"] == self.config.speed
        return await self.action(SIMULATION, {"action": f"speed_{self.config.speed}", "expected_revision": frame["revision"]}, desired_speed)

    def checkpoint_source(self) -> Path:
        directory = Path(self.config.save_directory).resolve()
        path = (directory / "xar_checkpoint.ck3").resolve()
        if path.parent != directory:
            raise CampaignStop("checkpoint_path_escaped_save_directory", rejected=True)
        return path

    def archive(self, raw: bytes, proof: dict[str, Any], frame: dict[str, Any]) -> dict[str, Any]:
        directory = self.directory / "checkpoints"
        directory.mkdir(exist_ok=True)
        path = directory / f"{parse_date(proof['body_date']).isoformat()}-{proof['sha256']}.ck3"
        if not path.exists():
            with path.open("xb") as output:
                output.write(raw)
        if hashlib.sha256(path.read_bytes()).hexdigest() != proof["sha256"]:
            raise CampaignStop("immutable_archive_bytes_mismatch", rejected=True)
        return {**proof, "archive_path": str(path), "date_raw_at_save": frame["date_raw"],
                "revision_at_save": frame["revision"], "profile_identity": self.binding,
                "played_character_id": self.last_player, "full_effect_preview_claimed": False}

    async def checkpoint(self, frame: dict[str, Any]) -> dict[str, Any]:
        if not frame["paused"] or frame.get("active_event") is not None:
            raise CampaignStop("checkpoint_requires_paused_event_free_frame")
        source = self.checkpoint_source()
        before = (source.stat().st_size, source.stat().st_mtime_ns) if source.exists() else None
        saved = None
        async def materialized(current, receipt):
            nonlocal saved
            if not current["paused"] or current["date_raw"] != frame["date_raw"]:
                raise CampaignStop("checkpoint_native_date_or_pause_changed", rejected=True)
            if not source.is_file() or (source.stat().st_size, source.stat().st_mtime_ns) == before:
                return False
            try:
                raw, proof = await asyncio.to_thread(read_plaintext_save, source)
            except OSError:
                return False
            except ValueError as error:
                if str(error) == "save changed during full-byte read":
                    return False
                raise CampaignStop(f"checkpoint_body_or_format_invalid: {error}", rejected=True) from error
            actual_date = parse_date(proof["body_date"])
            if actual_date < self.last_saved_date:
                raise CampaignStop("checkpoint_body_date_moved_backwards", rejected=True)
            declared = receipt.get("result", {}).get("checkpoint")
            if not isinstance(declared, dict) or (declared.get("status") != "saved" or Path(declared.get("path", "")).resolve() != source
                    or declared.get("size") != proof["bytes"] or str(declared.get("sha256", "")).lower() != proof["sha256"]
                    or declared.get("date_raw") != frame["date_raw"]):
                raise CampaignStop("checkpoint_declared_bytes_or_native_date_disagree", rejected=True)
            saved = await asyncio.to_thread(self.archive, raw, proof, current)
            self.last_saved_date, self.last_save_proof = actual_date, saved
            return True
        current = await self.action(SAVE, {"expected_revision": frame["revision"]}, materialized)
        self.record("checkpoint-archived", {"checkpoint": saved})
        return current

    async def event_presentation(self, frame: dict[str, Any], instance: int):
        """Wait only for known presentation transients, using guarded reads."""
        deadline = time.monotonic() + self.config.postcondition_timeout_seconds
        while True:
            if frame["paused"] is not True:
                raise CampaignStop("event_presentation_wait_requires_pause")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CampaignStop("event_presentation_timeout")
            try:
                queried = await asyncio.wait_for(self.call(QUERY_EVENT, {
                    "event_instance_id": instance, "expected_revision": frame["revision"],
                }), remaining)
            except TimeoutError as error:
                raise CampaignStop("event_presentation_timeout") from error
            if queried.get("status") != "native_event_query_verified":
                raise CampaignStop("event_query_guard_or_revision_failed", rejected=True)
            context = queried.get("result", {}).get("current_event_window_context", {})
            if (not isinstance(context, dict) or context.get("current_event_instance_id") != instance):
                raise CampaignStop("event_context_unavailable")
            if (context.get("status") == "available"
                    and context.get("readiness", {}).get("option_presentation_ready") is True):
                return frame, context
            reason = context.get("unavailable_reason")
            if context.get("status") != "unavailable" or reason not in _TRANSIENT_EVENT_PRESENTATION:
                raise CampaignStop("event_context_unavailable")
            self.record("event-presentation-wait", {"instance_id": instance,
                "unavailable_reason": reason, "revision": frame["revision"],
                "date_raw": frame["date_raw"], "selection_dispatched": False})
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CampaignStop("event_presentation_timeout")
            await asyncio.sleep(min(self.config.poll_seconds, remaining))
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CampaignStop("event_presentation_timeout")
            try:
                frame = await asyncio.wait_for(self.snapshot(policy_action_readback=True), remaining)
            except TimeoutError as error:
                raise CampaignStop("event_presentation_timeout") from error
            if frame["paused"] is not True:
                raise CampaignStop("event_presentation_wait_requires_pause")
            active = frame.get("active_event")
            current_instance = active.get("instance_id") if isinstance(active, dict) else None
            if current_instance != instance:
                self.record("event-presentation-instance-changed", {"before": instance,
                    "after": current_instance, "revision": frame["revision"],
                    "selection_dispatched": False})
                return frame, None  # The outer event loop binds the new instance.

    async def events(self, frame: dict[str, Any]) -> dict[str, Any]:
        for _ in range(self.config.max_event_chain):
            active = frame.get("active_event")
            if active is None:
                return frame
            instance = active.get("instance_id") if isinstance(active, dict) else None
            if type(instance) is not int or not 1 <= instance <= 2**31 - 1:
                raise CampaignStop("event_instance_invalid", rejected=True)
            frame, context = await self.event_presentation(frame, instance)
            if context is None:
                continue
            option = choose_option(context)
            self.record("event-choice", {"instance_id": instance, "event_definition_key": context.get("event_definition_key"),
                       "native_option_index": option["native_option_index"], "partial_indicators": option.get("effect_indicators"),
                       "complete_effect_preview": False, "localization_used_for_choice": False})
            async def advanced(current, receipt):
                new = current.get("active_event")
                return current["paused"] and (not isinstance(new, dict) or new.get("instance_id") != instance)
            frame = await self.action(SELECT_EVENT, {"option_number": option["native_option_index"]+1,
                                     "event_instance_id": instance, "expected_revision": frame["revision"]}, advanced)
        raise CampaignStop("event_chain_bound_exceeded")

    async def run(self) -> dict[str, Any]:
        self.record("config", {"start_date": self.config.start_date, "target_date": self.config.target_date,
                   "baseline_date_raw": self.config.baseline_date_raw, "save_directory": str(Path(self.config.save_directory).resolve()),
                   "calendar_completion_source": "full plaintext save body date", "raw_units_per_day_for_save_scheduling": RAW_UNITS_PER_DAY})
        try:
            inspected = await self.call(INSPECT, {})
            if inspected.get("status") != "profile_bound" or inspected.get("attached") is not True:
                raise CampaignStop("existing_profile_not_attached", rejected=True)
            self.native_observation = inspected.get("observation")
            frame = await self.snapshot()
            if self.pause_provider is not None:
                controller = await self.call_pause_controller(PAUSE_CONTROLLER_INSPECT, frame)
                if controller.get("status") != "clock_pause_profile_verified":
                    raise CampaignStop("pause_controller_profile_not_verified", rejected=True)
            frame = await self.pause(frame)
            frame = await self.events(frame)
            frame = await self.checkpoint(frame)
            interval = self.config.checkpoint_days * RAW_UNITS_PER_DAY
            next_save = self.config.baseline_date_raw + ((frame["date_raw"]-self.config.baseline_date_raw)//interval+1)*interval
            progress_raw, progress_time = frame["date_raw"], time.monotonic()
            if self.last_saved_date < parse_date(self.config.target_date):
                frame = await self.set_speed(frame)
            while self.last_saved_date < parse_date(self.config.target_date):
                frame = await self.resume(frame)
                progress_raw, progress_time = frame["date_raw"], time.monotonic()
                while True:
                    await asyncio.sleep(self.config.poll_seconds)
                    frame = await self.snapshot()
                    if frame["date_raw"] > progress_raw:
                        progress_raw, progress_time = frame["date_raw"], time.monotonic()
                    if frame["paused"] and frame.get("active_event") is None:
                        raise CampaignStop("unexpected_pause_or_unknown_modal")
                    if frame.get("active_event") is not None or frame["date_raw"] >= next_save:
                        frame = await self.pause(frame)
                        frame = await self.events(frame)
                        if frame["date_raw"] >= next_save:
                            frame = await self.checkpoint(frame)
                            next_save = self.config.baseline_date_raw + ((frame["date_raw"]-self.config.baseline_date_raw)//interval+1)*interval
                        break
                    if time.monotonic()-progress_time >= self.config.no_progress_timeout_seconds:
                        raise CampaignStop("native_clock_no_progress")
            result = {"status": "completed", "start_date": self.config.start_date, "target_date": self.config.target_date,
                      "final_checkpoint": self.last_save_proof, "evidence_directory": str(self.directory)}
        except CampaignStop as error:
            result = {"status": "rejected" if error.rejected else "await_root", "reason": str(error),
                      "last_date_raw": self.last_raw, "last_checkpoint": self.last_save_proof, "evidence_directory": str(self.directory)}
        except asyncio.CancelledError:
            self.record("outcome", {"status": "await_root", "reason": "caller_cancelled; outstanding dispatch must be inspected before any retry"})
            raise
        except Exception as error:
            result = {"status": "rejected", "reason": f"policy_or_file_error: {type(error).__name__}: {error}",
                      "last_date_raw": self.last_raw, "last_checkpoint": self.last_save_proof,
                      "evidence_directory": str(self.directory)}
        self.record("outcome", result)
        return result


async def run(client: AsyncClient, config: CampaignConfig, *, pause_provider: AsyncClient | None = None) -> dict[str, Any]:
    """Use only the caller's existing official/queued MCP client and frozen baseline."""
    return await CampaignPolicy(client, config, pause_provider=pause_provider).run()

"""Future-cold Native32 tool registration. No registration-time IO or query."""
from __future__ import annotations

from typing import Callable, Protocol
import uuid

from observer_journal_runtime_v1 import (
    AllNativeObservedHistoryV1, DriverV1, ensure_existing_owner_v1,
    qualify_native32_binding_v1, read_native32_once_v1, Native32ResultV1,
    parse_native32_result_v1, _obj, _int, _U64)


class ReadonlyDecoratorV1(Protocol):
    def __call__(self, callback: Callable[[], dict[str, object]]) -> object: ...


def register_native32_journal_v1(register_readonly: ReadonlyDecoratorV1, *,
        owner: object, driver: DriverV1, machine_id: str,
        binding_value: object, existing_ensure: Callable[[object], object]
        ) -> Callable[[], dict[str, object]]:
    """Use the original server/owner. The cold producer must forbid extra args.

    The five-field Root command means explicit all-native-observed-history,
    never current protocol attribution. Empty RequestedIds selects nothing.
    """
    if getattr(driver, "_player_heir_candidate_owner_v1", None) is not owner:
        raise ValueError("same original canonical owner required")

    def ck3_observe_native32_time_command_journal_v1() -> dict[str, object]:
        # Missing production facts fail before the legacy issuer or any query.
        binding = qualify_native32_binding_v1(binding_value, machine_id=machine_id)
        ensure_existing_owner_v1(owner, existing_ensure, sdk_root=binding.sdk_root)
        result = read_native32_once_v1(owner, driver, binding_value=binding_value,
            machine_id=machine_id, request_id="n32journal." + uuid.uuid4().hex,
            selection=AllNativeObservedHistoryV1(), timeout_seconds=2.0)
        return {key: item for key, item in result.items()}

    register_readonly(ck3_observe_native32_time_command_journal_v1)
    return ck3_observe_native32_time_command_journal_v1


def validate_native32_mcp_result_v1(value: object, *, actual_game: object,
        binding_value: object, machine_id: str) -> Native32ResultV1:
    """Single canonical MCP envelope; no aliases, ACK or text fallback."""
    envelope = _obj(value, {"meta", "content", "structured_content", "is_error", "result_type"})
    if envelope["is_error"] is not False or envelope["result_type"] != "complete":
        raise ValueError("complete successful canonical MCP result required")
    game = _obj(actual_game)
    if game.get("machine_id") != machine_id:
        raise ValueError("actual Game belongs to another machine")
    pid = _int(game.get("pid"), (1 << 32) - 1, 1)
    birth = _int(game.get("creation_filetime"), _U64, 1)
    binding = qualify_native32_binding_v1(binding_value, machine_id=machine_id)
    result = parse_native32_result_v1(envelope["structured_content"],
        machine_id=machine_id, game_pid=pid, creation_filetime=birth,
        native_dll_sha256=binding.wire["dll"]["sha256"])
    if result["production_result"] != binding.wire["production_result_ref"]:
        raise ValueError("journal result production qualification differs")
    return result

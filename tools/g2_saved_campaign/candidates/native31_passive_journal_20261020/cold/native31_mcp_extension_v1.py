"""Next-cold entry extension; registers one bounded passive observation tool.
The caller must first create the ordinary Source28 server, then supply its
readonly decorator, actual canonical owner, and the same original driver.
Registration performs no native read. Never use this to change an active A13.
"""
from __future__ import annotations
from typing import Callable, Protocol
import uuid
from observer_journal_v1 import DriverV1, read_from_source28_owner_once_v1, result_payload_v1

ReadonlyCallbackV1 = Callable[[], dict[str, object]]
class ReadonlyDecoratorV1(Protocol):
    def __call__(self, callback: ReadonlyCallbackV1) -> object: ...

def register_native31_journal_v1(register_readonly: ReadonlyDecoratorV1, *,
        owner: object, driver: DriverV1, machine_id: str,
        failed_request_ids: tuple[str, ...] = ()) -> ReadonlyCallbackV1:
    """Call with server.tool(annotations=ToolAnnotations(readOnlyHint=True,
    destructiveHint=False, idempotentHint=True, openWorldHint=False)).
    Source28 create_server installs the canonical owner on
    driver._player_heir_candidate_owner_v1. Supply that retained instance.
    Each explicit tool call sends at most one fixed journal query, no retry.
    """
    if getattr(driver, "_player_heir_candidate_owner_v1", None) is not owner:
        raise ValueError("canonical Source28 owner differs")
    def ck3_observe_native31_time_command_journal_v1() -> dict[str, object]:
        """Read the bounded passive time-command journal; grant no drain proof."""
        return result_payload_v1(read_from_source28_owner_once_v1(owner, driver,
            machine_id=machine_id, request_id="n31journal."+uuid.uuid4().hex,
            failed_request_ids=failed_request_ids, timeout_seconds=2.0))
    register_readonly(ck3_observe_native31_time_command_journal_v1)
    return ck3_observe_native31_time_command_journal_v1

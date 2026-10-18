"""Default-off general reform tools, registered by the existing MCP server."""
from __future__ import annotations

from typing import Annotated, Literal
from pydantic import Field
from mcp.types import ToolAnnotations
from mcp.server.mcpserver.exceptions import ToolError
from .driver import BridgeUnavailableError, UnsupportedStepError, PreSubmissionRevisionMismatchError

Revision = Annotated[int, Field(strict=True, gt=0)]
RiteId = Annotated[int, Field(strict=True, ge=0, lt=2**32 - 1)]
Definition = Annotated[str, Field(strict=True, pattern=r"^[a-z0-9_]{1,128}$")]
Identity = Annotated[str, Field(strict=True, pattern=r"^[0-9a-f]{64}$")]
WriteOperation = Literal["open_create_draft", "open_edit_current_rite_draft", "select_core_tenet",
    "select_doctrine", "set_name_field", "prepare_confirmation", "confirm_once"]
NameField = Literal["name", "adjective", "adherent", "adherent_plural", "description"]
Outcome = Literal["create_faith", "create_rite", "edit_rite"]


def _invoke(function, **arguments):
    try:
        return function(**arguments)
    except (BridgeUnavailableError, UnsupportedStepError, PreSubmissionRevisionMismatchError, ValueError) as error:
        raise ToolError(str(error)) from error


def register_tools(server, driver, forbid_unknown):
    if getattr(driver, "allow_private_player_rite_creation_actions", False) is not True:
        return

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False,
        idempotentHint=False, openWorldHint=False))
    def ck3_query_player_rite_creation_action_context_v1(expected_revision: Revision,
            expected_source_rite_id: RiteId) -> dict[str, object]:
        """Read the actual draft, native full Can, price and confirmation phase; no opening or submission."""
        return _invoke(driver.player_rite_creation_action_private_v1, operation="preview",
            expected_revision=expected_revision, expected_source_rite_id=expected_source_rite_id)
    forbid_unknown(server, "ck3_query_player_rite_creation_action_context_v1")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=True,
        idempotentHint=False, openWorldHint=False))
    def ck3_execute_player_rite_creation_action_v1(operation: WriteOperation, expected_revision: Revision,
            expected_source_rite_id: RiteId,
            core_slot_index: Annotated[int, Field(strict=True, ge=0, lt=64)] | None = None,
            tenet_key: Definition | None = None, group_key: Definition | None = None,
            doctrine_key: Definition | None = None, name_field: NameField | None = None,
            text: Annotated[str, Field(strict=True)] | None = None,
            expected_preview_identity: Identity | None = None,
            expected_outcome_kind: Outcome | None = None) -> dict[str, object]:
        """Use finite original reform controls. prepare opens the modal; confirm_once is never retried after unknown."""
        selectors = {key: value for key, value in {
            "core_slot_index": core_slot_index, "tenet_key": tenet_key, "group_key": group_key,
            "doctrine_key": doctrine_key, "name_field": name_field, "text": text,
            "expected_preview_identity": expected_preview_identity,
            "expected_outcome_kind": expected_outcome_kind}.items() if value is not None}
        return _invoke(driver.player_rite_creation_action_private_v1, operation=operation,
            expected_revision=expected_revision, expected_source_rite_id=expected_source_rite_id, **selectors)
    forbid_unknown(server, "ck3_execute_player_rite_creation_action_v1")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False,
        idempotentHint=False, openWorldHint=False))
    def ck3_collect_player_rite_creation_action_result_v1(
            action_request_id: Annotated[str, Field(strict=True, pattern=r"^rite-action-[0-9a-f]{32}$")],
            timeout_seconds: Annotated[float, Field(ge=0, le=30)] = 0.0) -> dict[str, object]:
        """Collect the retained original final-confirm result only; never resend or infer current legality."""
        return _invoke(driver.collect_player_rite_creation_action_result_private_v1,
            action_request_id=action_request_id, timeout_seconds=timeout_seconds)
    forbid_unknown(server, "ck3_collect_player_rite_creation_action_result_v1")

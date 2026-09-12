"""Publication workflow engine with explicit irreversible-call boundaries."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any, Mapping

from .errors import (
    AuthorizationError,
    GateError,
    ProviderResultUnknownError,
    StateConflictError,
    UnsafeRetryError,
)
from .models import (
    EulaState,
    GameSessionState,
    OperationKind,
    PublicationPlan,
    SteamMode,
    WorkflowState,
)
from .providers import WorkshopProvider
from .validation import validate_local_plan
from .wal import OperationStore, OperationView

_PREFLIGHT_RETRY_STATES = {
    WorkflowState.ONLINE_READY,
    WorkflowState.BLOCKED_ACCOUNT_STATE_UNKNOWN,
    WorkflowState.BLOCKED_OTHER_MACHINE_IN_GAME,
    WorkflowState.BLOCKED_WORKSHOP_EULA,
    WorkflowState.BLOCKED_EULA_STATUS_UNKNOWN,
    WorkflowState.BLOCKED_ITEM_NOT_OWNED,
    WorkflowState.BLOCKED_PROVIDER_CAPABILITY,
    WorkflowState.BLOCKED_APP_ID_MISMATCH,
    WorkflowState.BLOCKED_DESCRIPTOR_ID_MISMATCH,
    WorkflowState.BLOCKED_FORBIDDEN_UPSTREAM_ID,
    WorkflowState.BLOCKED_STAGING_MISMATCH,
}


class WorkshopService:
    """Coordinates typed plans, provider gates, WAL, and offline compensation."""

    def __init__(self, store: OperationStore, provider: WorkshopProvider) -> None:
        self.store = store
        self.provider = provider

    def capabilities(self) -> dict[str, Any]:
        return {
            "schema": "ck3.workshop.capabilities.v1",
            "server_version": "0.1.0",
            "consumer_app_ids": [1_158_310],
            "provider": self.provider.capabilities().to_dict(),
            "irreversible_tool": "workshop_submit",
            "operation_resources": [
                "workshop://capabilities",
                "workshop://operations/{operation_id}",
                "workshop://operations/{operation_id}/events",
            ],
            "legal_agreement_url": "https://steamcommunity.com/sharedfiles/workshoplegalagreement",
            "secrets_policy": "Passwords, Steam Guard codes, cookies, API keys and tickets are never accepted.",
        }

    def create_plan(self, raw: Mapping[str, Any]) -> dict[str, Any]:
        plan = PublicationPlan.from_dict(raw)
        return self.store.create(plan).to_dict()

    def begin_online_window(self, operation_id: str) -> dict[str, Any]:
        view = self.store.load(operation_id)
        if view.irreversible_started:
            raise UnsafeRetryError("cannot reopen an online window after an irreversible call")
        if view.state not in {WorkflowState.PLANNED, *_PREFLIGHT_RETRY_STATES}:
            raise StateConflictError(f"cannot begin online window from {view.state.value}")

        try:
            validate_local_plan(view.plan)
        except GateError as error:
            return self._block_and_raise(
                operation_id, error.gate_code, str(error), compensate=False
            )

        before = self.provider.inspect_account()
        if before.game_session is GameSessionState.IN_GAME:
            return self._block_and_raise(
                operation_id,
                "BLOCKED_OTHER_MACHINE_IN_GAME",
                "the Steam account is already in a game; no launch or takeover is allowed",
                compensate=False,
            )
        if before.game_session is GameSessionState.UNKNOWN:
            return self._block_and_raise(
                operation_id,
                "BLOCKED_ACCOUNT_STATE_UNKNOWN",
                "the current account game-session state is unknown",
                compensate=False,
            )

        compensation_required = view.plan.offline_after
        self.store.append(
            operation_id,
            "ONLINE_WINDOW_INTENT",
            {
                "initial_mode": before.steam_mode.value,
                "offline_compensation_required": compensation_required,
            },
        )
        try:
            if before.steam_mode is SteamMode.OFFLINE:
                self.provider.go_online()
            elif before.steam_mode is not SteamMode.ONLINE:
                raise GateError(
                    "BLOCKED_ACCOUNT_STATE_UNKNOWN",
                    "Steam mode is unknown; refusing to infer an online session",
                )
            after = self.provider.inspect_account()
            if after.steam_mode is not SteamMode.ONLINE:
                raise GateError(
                    "BLOCKED_ACCOUNT_STATE_UNKNOWN",
                    "provider did not confirm Steam online after the transition",
                )
            if after.game_session is GameSessionState.IN_GAME:
                raise GateError(
                    "BLOCKED_OTHER_MACHINE_IN_GAME",
                    "the account became in-game; refusing to continue",
                )
            if after.game_session is not GameSessionState.IDLE:
                raise GateError(
                    "BLOCKED_ACCOUNT_STATE_UNKNOWN",
                    "the online account game-session state is unknown",
                )
            return self.store.append(
                operation_id,
                "ONLINE_WINDOW_OPENED",
                {"offline_compensation_required": compensation_required},
            ).to_dict()
        except GateError as error:
            return self._block_and_raise(
                operation_id, error.gate_code, str(error), compensate=True
            )
        except Exception:
            self._compensate_offline(operation_id)
            raise

    def preflight(self, operation_id: str) -> dict[str, Any]:
        view = self.store.load(operation_id)
        if view.irreversible_started:
            raise UnsafeRetryError("preflight cannot alter an operation after an irreversible call")
        if view.state not in _PREFLIGHT_RETRY_STATES:
            raise StateConflictError(
                f"preflight requires an online window; current state is {view.state.value}"
            )
        try:
            local = validate_local_plan(view.plan)
            account = self.provider.inspect_account()
            if account.steam_mode is not SteamMode.ONLINE:
                raise GateError(
                    "BLOCKED_ACCOUNT_STATE_UNKNOWN",
                    "Steam online mode is not currently confirmed",
                )
            if account.game_session is GameSessionState.IN_GAME:
                raise GateError(
                    "BLOCKED_OTHER_MACHINE_IN_GAME",
                    "the account is already in a game on this or another machine",
                )
            if account.game_session is not GameSessionState.IDLE:
                raise GateError(
                    "BLOCKED_ACCOUNT_STATE_UNKNOWN",
                    "the account game-session state is unknown",
                )
            self._validate_provider_capabilities(view.plan)
            eula = self.provider.inspect_eula(view.plan.consumer_app_id)
            if eula is EulaState.NEEDS_ACTION:
                raise GateError(
                    "BLOCKED_WORKSHOP_EULA",
                    "Workshop Legal Agreement requires owner action",
                )
            if eula is not EulaState.CLEAR:
                raise GateError(
                    "BLOCKED_EULA_STATUS_UNKNOWN",
                    "provider cannot prove Workshop Legal Agreement status",
                )
            if (
                view.plan.operation is OperationKind.UPDATE
                and view.plan.target_item_id not in account.owned_item_ids
            ):
                raise GateError(
                    "BLOCKED_ITEM_NOT_OWNED",
                    "the current Steam account does not prove ownership of the target item",
                )
            return self.store.append(
                operation_id,
                "PREFLIGHT_GREEN",
                {
                    "local": local,
                    "account_idle": True,
                    "target_owned": (
                        None
                        if view.plan.operation is OperationKind.CREATE
                        else True
                    ),
                    "eula": eula.value,
                },
            ).to_dict()
        except GateError as error:
            return self._block_and_raise(
                operation_id, error.gate_code, str(error), compensate=True
            )

    def issue_submit_token(
        self,
        operation_id: str,
        expected_plan_sha256: str,
        *,
        ttl_seconds: int = 300,
    ) -> dict[str, Any]:
        view = self.store.load(operation_id)
        if view.state is not WorkflowState.PREFLIGHT_GREEN or view.irreversible_started:
            raise StateConflictError("submit authorization requires a fresh GREEN preflight")
        if not secrets.compare_digest(expected_plan_sha256, view.plan_sha256):
            raise AuthorizationError("expected_plan_sha256 does not match the durable plan")
        if ttl_seconds < 30 or ttl_seconds > 900:
            raise AuthorizationError("submit token ttl_seconds must be between 30 and 900")
        token = secrets.token_urlsafe(32)
        digest = _token_digest(operation_id, token)
        expires = datetime.now(UTC) + timedelta(seconds=ttl_seconds)
        current = self.store.append(
            operation_id,
            "SUBMIT_TOKEN_ISSUED",
            {"token_digest": digest, "expires_at_utc": expires.isoformat()},
        )
        result = current.to_dict()
        result["submit_token"] = token
        result["warning"] = "The plaintext token is returned once and is not persisted."
        return result

    def submit(
        self,
        operation_id: str,
        expected_plan_sha256: str,
        submit_token: str,
    ) -> dict[str, Any]:
        view = self.store.load(operation_id)
        if view.irreversible_started:
            raise UnsafeRetryError(
                f"operation is already past an irreversible boundary ({view.state.value}); automatic retry is forbidden"
            )
        if view.state is not WorkflowState.PREFLIGHT_GREEN:
            raise StateConflictError("workshop_submit requires PREFLIGHT_GREEN")
        self._verify_submit_authorization(view, expected_plan_sha256, submit_token)

        self.store.compare_and_append(
            operation_id, view.event_count, "SUBMIT_TOKEN_CONSUMED", {}
        )
        succeeded = False
        try:
            if view.plan.operation is OperationKind.CREATE:
                item_id = self._create_once(view)
            else:
                assert view.plan.target_item_id is not None
                item_id = view.plan.target_item_id
            self.store.append(
                operation_id,
                "CONTENT_SUBMIT_INTENT",
                {"item_id": item_id},
            )
            try:
                result = self.provider.submit_item_update(view.plan, item_id)
            except Exception as error:
                self.store.append(
                    operation_id,
                    "SUBMIT_RESULT_UNKNOWN",
                    {"message": f"{type(error).__name__}: {error}"},
                )
                raise ProviderResultUnknownError(
                    "SubmitItemUpdate result is unknown; automatic retry is forbidden"
                ) from error
            if result.item_id != item_id:
                message = f"provider returned item {result.item_id}, expected {item_id}"
                self.store.append(operation_id, "REMOTE_MISMATCH", {"message": message})
                raise GateError("REMOTE_MISMATCH", message)
            if result.eula is not EulaState.CLEAR:
                code = (
                    "BLOCKED_WORKSHOP_EULA"
                    if result.eula is EulaState.NEEDS_ACTION
                    else "BLOCKED_EULA_STATUS_UNKNOWN"
                )
                message = "submit callback did not prove Workshop EULA clearance"
                self.store.append(
                    operation_id,
                    "BLOCKED",
                    {"gate_code": code, "message": message},
                )
                raise GateError(code, message)
            self.store.append(operation_id, "REMOTE_COMMITTED", {"item_id": item_id})
            succeeded = True
        finally:
            if view.plan.offline_after:
                self._compensate_offline(operation_id)

        current = self.store.load(operation_id)
        if succeeded and (
            not view.plan.offline_after or current.offline_restored
        ):
            current = self.store.append(operation_id, "COMPLETE", {})
        return current.to_dict()

    def _create_once(self, view: OperationView) -> str:
        self.store.append(view.operation_id, "CREATE_INTENT", {})
        try:
            result = self.provider.create_item(view.plan)
        except Exception as error:
            self.store.append(
                view.operation_id,
                "AMBIGUOUS_CREATE",
                {"message": f"{type(error).__name__}: {error}"},
            )
            raise ProviderResultUnknownError(
                "CreateItem result is ambiguous; automatic Create retry is forbidden"
            ) from error
        if result.item_id in view.plan.effective_forbidden_item_ids:
            self.store.append(
                view.operation_id,
                "AMBIGUOUS_CREATE",
                {"message": f"provider returned forbidden item ID {result.item_id}"},
            )
            raise GateError(
                "BLOCKED_FORBIDDEN_UPSTREAM_ID",
                f"provider returned forbidden item ID {result.item_id}",
            )
        if not result.item_id.isdecimal():
            self.store.append(
                view.operation_id,
                "AMBIGUOUS_CREATE",
                {"message": "provider returned an invalid Workshop item ID"},
            )
            raise ProviderResultUnknownError("CreateItem returned an invalid item ID")
        self.store.append(
            view.operation_id,
            "ITEM_ID_DURABLY_RECORDED",
            {"item_id": result.item_id},
        )
        if result.eula is not EulaState.CLEAR:
            code = (
                "BLOCKED_WORKSHOP_EULA"
                if result.eula is EulaState.NEEDS_ACTION
                else "BLOCKED_EULA_STATUS_UNKNOWN"
            )
            self.store.append(
                view.operation_id,
                "BLOCKED",
                {
                    "gate_code": code,
                    "message": "CreateItem callback did not prove Workshop EULA clearance",
                },
            )
            raise GateError(code, "CreateItem requires Workshop EULA owner action")
        return result.item_id

    def restore_offline(self, operation_id: str) -> dict[str, Any]:
        self.store.load(operation_id)
        self._compensate_offline(operation_id, force=True)
        return self.store.load(operation_id).to_dict()

    def recover_offline_obligations(self) -> dict[str, Any]:
        """Compensate durable online obligations after restart or shutdown."""

        recovered: list[dict[str, Any]] = []
        for view in self.store.iter_views():
            if view.offline_compensation_required:
                self._compensate_offline(view.operation_id)
                current = self.store.load(view.operation_id)
                recovered.append(
                    {
                        "operation_id": view.operation_id,
                        "offline_restored": current.offline_restored,
                        "state": current.state.value,
                    }
                )
        return {
            "schema": "ck3.workshop.offline-recovery.v1",
            "operations": recovered,
        }

    def operation(self, operation_id: str) -> dict[str, Any]:
        return self.store.load(operation_id).to_dict()

    def operation_events(self, operation_id: str) -> dict[str, Any]:
        return {
            "schema": "ck3.workshop.operation-events.v1",
            "operation_id": operation_id,
            "events": [event.to_dict() for event in self.store.events(operation_id)],
        }

    def _validate_provider_capabilities(self, plan: PublicationPlan) -> None:
        capabilities = self.provider.capabilities()
        required = capabilities.create_item if plan.operation is OperationKind.CREATE else capabilities.update_item
        missing: list[str] = []
        if capabilities.read_only or not required:
            missing.append(plan.operation.value)
        if not capabilities.account_state_observable:
            missing.append("account_state")
        if plan.operation is OperationKind.UPDATE and not capabilities.owned_items_observable:
            missing.append("owned_items")
        if not capabilities.legal_status_observable:
            missing.append("eula_status")
        if plan.visibility != "public" and not capabilities.visibility:
            missing.append("visibility")
        if plan.change_note and not capabilities.change_note:
            missing.append("change_note")
        if missing:
            raise GateError(
                "BLOCKED_PROVIDER_CAPABILITY",
                f"provider {capabilities.provider} lacks required capabilities: {', '.join(missing)}",
            )

    def _verify_submit_authorization(
        self,
        view: OperationView,
        expected_plan_sha256: str,
        submit_token: str,
    ) -> None:
        if not secrets.compare_digest(expected_plan_sha256, view.plan_sha256):
            raise AuthorizationError("expected_plan_sha256 does not match the durable plan")
        if view.token_digest is None or view.token_expires_at_utc is None:
            raise AuthorizationError("no one-time submit token is active")
        if view.token_consumed:
            raise AuthorizationError("submit token has already been consumed")
        if datetime.now(UTC) >= datetime.fromisoformat(view.token_expires_at_utc):
            raise AuthorizationError("submit token has expired")
        supplied = _token_digest(view.operation_id, submit_token)
        if not secrets.compare_digest(supplied, view.token_digest):
            raise AuthorizationError("submit token does not match")

    def _block_and_raise(
        self,
        operation_id: str,
        gate_code: str,
        message: str,
        *,
        compensate: bool,
    ) -> dict[str, Any]:
        self.store.append(
            operation_id,
            "BLOCKED",
            {"gate_code": gate_code, "message": message},
        )
        if compensate:
            self._compensate_offline(operation_id)
        raise GateError(gate_code, message)

    def _compensate_offline(self, operation_id: str, *, force: bool = False) -> None:
        view = self.store.load(operation_id)
        if not force and not view.offline_compensation_required:
            return
        try:
            self.provider.restore_offline()
            after = self.provider.inspect_account()
            if after.steam_mode is not SteamMode.OFFLINE:
                raise ProviderResultUnknownError("provider did not confirm Steam offline")
            self.store.append(operation_id, "OFFLINE_RESTORED", {})
        except Exception as error:
            self.store.append(
                operation_id,
                "OFFLINE_RESTORE_FAILED",
                {"message": f"{type(error).__name__}: {error}"},
            )


def _token_digest(operation_id: str, token: str) -> str:
    return hashlib.sha256(f"{operation_id}\0{token}".encode("utf-8")).hexdigest()

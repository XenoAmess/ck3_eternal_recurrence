"""Versioned, serializable domain models for Workshop publication."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping

from .errors import PlanValidationError

SCHEMA_VERSION = "ck3.workshop.operation.v1"
CK3_CONSUMER_APP_ID = 1_158_310
CK3_FORBIDDEN_UPSTREAM_ITEM_IDS = frozenset({"3596580780"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_OPERATION_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_ITEM_ID_RE = re.compile(r"^[1-9][0-9]{5,19}$")


class OperationKind(StrEnum):
    CREATE = "create"
    UPDATE = "update"


class SteamMode(StrEnum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class GameSessionState(StrEnum):
    IDLE = "idle"
    IN_GAME = "in_game"
    UNKNOWN = "unknown"


class EulaState(StrEnum):
    CLEAR = "clear"
    NEEDS_ACTION = "needs_action"
    UNKNOWN = "unknown"


class WorkflowState(StrEnum):
    PLANNED = "PLANNED"
    ONLINE_READY = "ONLINE_READY"
    PREFLIGHT_GREEN = "PREFLIGHT_GREEN"
    SUBMITTING = "SUBMITTING"
    CREATE_CALLED = "CREATE_CALLED"
    ITEM_ID_DURABLY_RECORDED = "ITEM_ID_DURABLY_RECORDED"
    CONTENT_UPDATE_CALLED = "CONTENT_UPDATE_CALLED"
    REMOTE_COMMITTED = "REMOTE_COMMITTED"
    COMPLETE = "COMPLETE"
    BLOCKED_OTHER_MACHINE_IN_GAME = "BLOCKED_OTHER_MACHINE_IN_GAME"
    BLOCKED_ACCOUNT_STATE_UNKNOWN = "BLOCKED_ACCOUNT_STATE_UNKNOWN"
    BLOCKED_WORKSHOP_EULA = "BLOCKED_WORKSHOP_EULA"
    BLOCKED_EULA_STATUS_UNKNOWN = "BLOCKED_EULA_STATUS_UNKNOWN"
    BLOCKED_ITEM_NOT_OWNED = "BLOCKED_ITEM_NOT_OWNED"
    BLOCKED_PROVIDER_CAPABILITY = "BLOCKED_PROVIDER_CAPABILITY"
    BLOCKED_APP_ID_MISMATCH = "BLOCKED_APP_ID_MISMATCH"
    BLOCKED_DESCRIPTOR_ID_MISMATCH = "BLOCKED_DESCRIPTOR_ID_MISMATCH"
    BLOCKED_FORBIDDEN_UPSTREAM_ID = "BLOCKED_FORBIDDEN_UPSTREAM_ID"
    BLOCKED_STAGING_MISMATCH = "BLOCKED_STAGING_MISMATCH"
    AMBIGUOUS_CREATE = "AMBIGUOUS_CREATE"
    SUBMIT_RESULT_UNKNOWN = "SUBMIT_RESULT_UNKNOWN"
    REMOTE_MISMATCH = "REMOTE_MISMATCH"
    CACHE_MISMATCH = "CACHE_MISMATCH"
    OFFLINE_RESTORE_FAILED = "OFFLINE_RESTORE_FAILED"


@dataclass(frozen=True, slots=True)
class PublicationPlan:
    """Immutable publication intent; referenced bytes are hash-bound."""

    operation_id: str
    product_key: str
    operation: OperationKind
    consumer_app_id: int
    staging_dir: str
    staging_manifest: str
    staging_manifest_sha256: str
    outer_descriptor: str
    title: str
    description_path: str
    description_sha256: str
    preview_path: str
    preview_sha256: str
    tags: tuple[str, ...] = ()
    visibility: str = "public"
    change_note: str = ""
    target_item_id: str | None = None
    forbidden_item_ids: tuple[str, ...] = ()
    offline_after: bool = True
    schema: str = field(default=SCHEMA_VERSION, init=False)

    def __post_init__(self) -> None:
        if not _OPERATION_ID_RE.fullmatch(self.operation_id):
            raise PlanValidationError("operation_id must be a portable 1-128 character identifier")
        if not self.product_key.strip():
            raise PlanValidationError("product_key must not be empty")
        if not self.title.strip():
            raise PlanValidationError("title must not be empty")
        for name in ("staging_manifest_sha256", "description_sha256", "preview_sha256"):
            if not _SHA256_RE.fullmatch(getattr(self, name)):
                raise PlanValidationError(f"{name} must be a lowercase SHA-256 digest")
        if self.operation is OperationKind.CREATE and self.target_item_id is not None:
            raise PlanValidationError("create plans must not contain target_item_id")
        if self.operation is OperationKind.UPDATE and not self.target_item_id:
            raise PlanValidationError("update plans require target_item_id")
        item_ids = (*self.forbidden_item_ids,)
        if self.target_item_id is not None:
            item_ids += (self.target_item_id,)
        if any(_ITEM_ID_RE.fullmatch(item_id) is None for item_id in item_ids):
            raise PlanValidationError("Workshop item IDs must be decimal identifiers")
        if self.visibility not in {"public", "friends_only", "private", "unlisted"}:
            raise PlanValidationError("unsupported visibility")
        if self.offline_after is not True:
            raise PlanValidationError("CK3 publication plans must require offline_after=true")

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "PublicationPlan":
        allowed = {
            "schema",
            "operation_id",
            "product_key",
            "operation",
            "consumer_app_id",
            "staging_dir",
            "staging_manifest",
            "staging_manifest_sha256",
            "outer_descriptor",
            "title",
            "description_path",
            "description_sha256",
            "preview_path",
            "preview_sha256",
            "tags",
            "visibility",
            "change_note",
            "target_item_id",
            "forbidden_item_ids",
            "offline_after",
        }
        unknown = set(raw) - allowed
        if unknown:
            raise PlanValidationError(f"unknown plan fields: {', '.join(sorted(unknown))}")
        if raw.get("schema", SCHEMA_VERSION) != SCHEMA_VERSION:
            raise PlanValidationError(f"schema must be {SCHEMA_VERSION}")
        try:
            kwargs = dict(raw)
            kwargs.pop("schema", None)
            kwargs["operation"] = OperationKind(str(kwargs["operation"]))
            kwargs["consumer_app_id"] = int(kwargs["consumer_app_id"])
            kwargs["tags"] = tuple(str(value) for value in kwargs.get("tags", ()))
            kwargs["forbidden_item_ids"] = tuple(
                str(value) for value in kwargs.get("forbidden_item_ids", ())
            )
            if kwargs.get("target_item_id") is not None:
                kwargs["target_item_id"] = str(kwargs["target_item_id"])
            return cls(**kwargs)
        except (KeyError, TypeError, ValueError) as error:
            raise PlanValidationError(f"invalid publication plan: {error}") from error

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["operation"] = self.operation.value
        payload["tags"] = list(self.tags)
        payload["forbidden_item_ids"] = list(self.forbidden_item_ids)
        return payload

    @property
    def sha256(self) -> str:
        encoded = json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @property
    def effective_forbidden_item_ids(self) -> frozenset[str]:
        return CK3_FORBIDDEN_UPSTREAM_ITEM_IDS | frozenset(self.forbidden_item_ids)

    def resolved_paths(self) -> dict[str, Path]:
        return {
            "staging_dir": Path(self.staging_dir).expanduser().resolve(),
            "staging_manifest": Path(self.staging_manifest).expanduser().resolve(),
            "outer_descriptor": Path(self.outer_descriptor).expanduser().resolve(),
            "description_path": Path(self.description_path).expanduser().resolve(),
            "preview_path": Path(self.preview_path).expanduser().resolve(),
        }


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    steam_mode: SteamMode
    game_session: GameSessionState
    owned_item_ids: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class CreateItemResult:
    item_id: str
    eula: EulaState = EulaState.CLEAR


@dataclass(frozen=True, slots=True)
class SubmitItemResult:
    item_id: str
    eula: EulaState = EulaState.CLEAR


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

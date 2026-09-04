#!/usr/bin/env python3
"""Strict checkpoint transaction for the real Workforce M360 route-B cell.

This module is runner plumbing.  It assumes the existing Workforce transition
fixture has already moved the paused session from the received-self subject to
the exact owner and exposed the real ``zg361we.360`` window.  It then freezes
that frame, executes route B, obtains the existing Workforce provider proof,
optionally joins the separately versioned career-HC provider, and restores the
byte-identical checkpoint.

The event-window query cannot expose the numeric cycle/case values carried by
generic saved scopes.  Consequently those values are never guessed at capture
time: the post-action Workforce provider seals them onto the checkpoint, and a
later replay must observe the same values before the restore is considered a
case-identical replay.
"""

from __future__ import annotations

import copy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import shutil
from typing import Callable, Final, Mapping, Protocol

from zhongguo_phase2_workforce_action import (
    M360ActionBinding,
    M360_EVENT_DEFINITION_KEY,
    prove_m360_postcondition,
    submit_m360_route_action,
)


SPAN_ID: Final = "phase2_hc_workforce"
PRODUCER_KEY: Final = "hc-workforce"
ROUTE: Final = "B"
OPTION_NUMBER: Final = 2
NATIVE_OPTION_INDEX: Final = 1
FIXTURE_EVENT: Final = "zga_phase2_workforce.1"
SWITCH_BACK_EVENT: Final = "zga_phase2_workforce.3"
FIXTURE_OUTER: Final = "zga_phase2_workforce_action_fixture.mod"
CAREER_CAPABILITY: Final = (
    "game.command.query-zhongguo-career-hc-workforce-postcondition-v1"
)
READINESS: Final = "static-ready-live-pending"

WORKFORCE_REQUIRED_FACTS: Final = (
    "exact_owner_subject_cycle_case",
    "m360_receipt_state_4_choice_2",
    "route_b_collective_sealed_consumed_settled",
    "three_distinct_cohorts",
    "each_cohort_forced_equals_quota",
    "each_cohort_exception_zero",
    "each_cohort_manager_cost_zero",
    "collective_totals_conserved",
    "three_cycle_history_strictly_ordered",
    "m357_m358_m359_receipts_distinct_per_cycle",
    "m361_charter_gate_ready",
    "m361_evidence_count_3",
    "m361_effective_cycle_is_next_cycle",
)

_SHA256_RE: Final = re.compile(r"[0-9a-fA-F]{64}\Z")
_GIT_SHA_RE: Final = re.compile(r"[0-9a-fA-F]{40}\Z")


class RouteBCheckpointError(RuntimeError):
    """Typed fail-closed error suitable for an evidence sidecar."""

    def __init__(self, reason_code: str, evidence: Mapping[str, object]) -> None:
        self.reason_code = reason_code
        self.evidence = {
            **copy.deepcopy(dict(evidence)),
            "result": "RED",
            "reason_code": reason_code,
        }
        super().__init__(f"hc-workforce route-B checkpoint RED [{reason_code}]")


class RouteBCheckpointService(Protocol):
    def capabilities(self) -> dict[str, object]: ...

    def snapshot(self) -> dict[str, object]: ...

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]: ...

    def select_event_option(
        self,
        option_number: int,
        *,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]: ...

    def query_zhongguo_workforce_collective_snapshot_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]: ...

    def execute_step(
        self, step: str, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def save_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...

    def restore_checkpoint(
        self, *, expected_revision: int | None = None
    ) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class RouteBSubjectSession:
    service: RouteBCheckpointService
    transition_receipt: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class RouteBCaseIdentity:
    owner_character_id: int
    subject_character_id: int
    cycle_serial: int
    case_serial: int


SubjectSessionFactory = Callable[[M360ActionBinding], RouteBSubjectSession]


class CareerHcHook(Protocol):
    def __call__(
        self,
        service: RouteBCheckpointService,
        *,
        expected_revision: int,
        expected_date_raw: int,
        identity: RouteBCaseIdentity,
    ) -> Mapping[str, object]: ...


def _fail(reason_code: str, **evidence: object) -> None:
    raise RouteBCheckpointError(reason_code, evidence)


def _integer(
    value: object, label: str, *, minimum: int = 0, maximum: int = 2**63 - 1
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not minimum <= value <= maximum
    ):
        _fail("integer_binding_invalid", label=label, observed=value)
    return value


def _positive_character(value: object, label: str) -> int:
    return _integer(value, label, minimum=1, maximum=2**31 - 1)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path | None, value: Mapping[str, object]) -> None:
    if path is None:
        return
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    temporary.replace(path)


def _paused_binding(
    snapshot: object, *, label: str, require_event: bool = True
) -> dict[str, object]:
    if not isinstance(snapshot, Mapping):
        _fail("snapshot_not_an_object", label=label, snapshot=snapshot)
    played = snapshot.get("played_character")
    active = snapshot.get("active_event")
    binding = {
        "snapshot_id": snapshot.get("snapshot_id"),
        "revision": snapshot.get("revision"),
        "native_revision": snapshot.get("native_revision"),
        "date_raw": snapshot.get("date_raw"),
        "player_character_id": (
            played.get("character_id") if isinstance(played, Mapping) else None
        ),
        "event_instance_id": (
            active.get("instance_id") if isinstance(active, Mapping) else None
        ),
    }
    valid = (
        snapshot.get("paused") is True
        and snapshot.get("map_ready") is True
        and isinstance(binding["snapshot_id"], str)
        and bool(binding["snapshot_id"])
        and isinstance(binding["revision"], int)
        and not isinstance(binding["revision"], bool)
        and int(binding["revision"]) >= 0
        and isinstance(binding["native_revision"], int)
        and not isinstance(binding["native_revision"], bool)
        and int(binding["native_revision"]) > 0
        and isinstance(binding["date_raw"], int)
        and not isinstance(binding["date_raw"], bool)
        and isinstance(binding["player_character_id"], int)
        and not isinstance(binding["player_character_id"], bool)
        and 1 <= int(binding["player_character_id"]) <= 2**31 - 1
        and (
            not require_event
            or (
                isinstance(binding["event_instance_id"], int)
                and not isinstance(binding["event_instance_id"], bool)
                and int(binding["event_instance_id"]) > 0
            )
        )
    )
    if not valid:
        _fail("paused_event_binding_unavailable", label=label, binding=binding)
    return binding


def _scope_character_id(scope: object, label: str) -> int:
    identity = scope.get("typed_identity") if isinstance(scope, Mapping) else None
    if not (
        isinstance(identity, Mapping)
        and identity.get("status") == "available"
        and identity.get("kind") == "character"
    ):
        _fail("event_character_scope_unavailable", label=label, scope=scope)
    return _positive_character(identity.get("character_id"), label)


def _event_context(
    service: RouteBCheckpointService,
    binding: Mapping[str, object],
    *,
    owner_character_id: int,
    subject_character_id: int,
) -> dict[str, object]:
    response = service.query_current_event_window_context_v1(
        int(binding["event_instance_id"]),
        expected_revision=int(binding["revision"]),
    )
    context = (
        response.get("current_event_window_context")
        if isinstance(response, Mapping)
        else None
    )
    readiness = context.get("readiness") if isinstance(context, Mapping) else None
    if not (
        isinstance(response, Mapping)
        and response.get("status") == "available"
        and isinstance(context, Mapping)
        and context.get("status") == "available"
        and context.get("event_definition_key") == M360_EVENT_DEFINITION_KEY
        and context.get("current_event_instance_id")
        == binding["event_instance_id"]
        and context.get("snapshot_revision") == binding["native_revision"]
        and context.get("date_raw") == binding["date_raw"]
        and isinstance(readiness, Mapping)
        and readiness.get("event_definition_identity_ready") is True
        and readiness.get("root_scope_ready") is True
        and readiness.get("saved_scopes_ready") is True
        and readiness.get("option_presentation_ready") is True
    ):
        _fail("real_m360_event_not_ready", binding=binding, response=response)
    assert isinstance(context, Mapping)
    root = _scope_character_id(context.get("root_scope"), "root_scope")
    saved_rows = context.get("saved_scopes")
    if not isinstance(saved_rows, list):
        _fail("m360_saved_scopes_missing", context=context)
    saved: dict[str, object] = {}
    for row in saved_rows:
        if isinstance(row, Mapping) and isinstance(row.get("name"), str):
            name = str(row["name"])
            if name in saved:
                _fail("m360_saved_scope_duplicated", name=name)
            saved[name] = row.get("scope")
    required = {
        "zg361_we_al_owner",
        "zg361_we_al_subject",
        "zg361_we_al_cycle",
        "zg361_we_al_case",
    }
    if not required <= set(saved):
        _fail("m360_case_scopes_missing", missing=sorted(required - set(saved)))
    owner = _scope_character_id(saved["zg361_we_al_owner"], "saved owner")
    subject = _scope_character_id(saved["zg361_we_al_subject"], "saved subject")
    if (
        root != owner_character_id
        or owner != owner_character_id
        or subject != subject_character_id
        or binding["player_character_id"] != owner_character_id
        or owner == subject
    ):
        _fail(
            "m360_owner_subject_binding_drifted",
            root=root,
            owner=owner,
            subject=subject,
            binding=binding,
        )
    options = context.get("options")
    if not isinstance(options, list):
        _fail("m360_option_surface_drifted", options=options)
    enabled = [
        row.get("native_option_index")
        for row in options
        if isinstance(row, Mapping)
        and row.get("shown") is True
        and row.get("enabled") is True
    ]
    if len(options) != 3 or enabled != [0, 1, 2]:
        _fail("m360_option_surface_drifted", options=options)
    return dict(context)


def bind_current_cumulative_projection(
    bootstrap: Mapping[str, object],
    fixture_install: Mapping[str, object],
    *,
    source_git_commit: str,
) -> dict[str, object]:
    """Bind the actual staged product tree plus the isolated transition fixture."""

    trees = bootstrap.get("tree_sha256")
    manifest = bootstrap.get("manifest")
    enabled = bootstrap.get("enabled_mods")
    product_hash = trees.get("product") if isinstance(trees, Mapping) else None
    manifest_hash = manifest.get("tree_sha256") if isinstance(manifest, Mapping) else None
    projection = manifest.get("projection") if isinstance(manifest, Mapping) else None
    before = fixture_install.get("enabled_mods_before")
    after = fixture_install.get("enabled_mods_after")
    fixture_hash = fixture_install.get("target_tree_sha256")
    fixture_mod = f"mod/{FIXTURE_OUTER}"
    valid = (
        isinstance(source_git_commit, str)
        and _GIT_SHA_RE.fullmatch(source_git_commit) is not None
        and isinstance(product_hash, str)
        and _SHA256_RE.fullmatch(product_hash) is not None
        and manifest_hash == product_hash
        and isinstance(projection, Mapping)
        and projection.get("tree_sha256") == product_hash
        and isinstance(enabled, list)
        and len(enabled) == 1
        and all(isinstance(item, str) for item in enabled)
        and fixture_install.get("result") == "GREEN"
        and fixture_install.get("acceptance_only") is True
        and fixture_install.get("release_included") is False
        and fixture_install.get("promo_included") is False
        and before == enabled
        and after == [*enabled, fixture_mod]
        and isinstance(fixture_hash, str)
        and _SHA256_RE.fullmatch(fixture_hash) is not None
        and fixture_install.get("source_tree_sha256") == fixture_hash
    )
    if not valid:
        _fail(
            "current_cumulative_projection_unbound",
            source_git_commit=source_git_commit,
            bootstrap=bootstrap,
            fixture_install=fixture_install,
        )
    return {
        "schema_version": 1,
        "kind": "zg361_current_cumulative_product_projection",
        "source_git_commit": source_git_commit.lower(),
        "projection_name": projection.get("projection"),
        "projection_mode": projection.get("mode"),
        "product_tree_sha256": product_hash.lower(),
        "product_enabled_mod": enabled[0],
        "transition_fixture_tree_sha256": fixture_hash.lower(),
        "transition_fixture_enabled_mod": fixture_mod,
        "fixture_acceptance_only": True,
    }


def _validate_projection_binding(value: object) -> dict[str, object]:
    projection = dict(value) if isinstance(value, Mapping) else {}
    if not (
        projection.get("schema_version") == 1
        and projection.get("kind")
        == "zg361_current_cumulative_product_projection"
        and isinstance(projection.get("source_git_commit"), str)
        and _GIT_SHA_RE.fullmatch(str(projection["source_git_commit"])) is not None
        and isinstance(projection.get("product_tree_sha256"), str)
        and _SHA256_RE.fullmatch(str(projection["product_tree_sha256"])) is not None
        and isinstance(projection.get("transition_fixture_tree_sha256"), str)
        and _SHA256_RE.fullmatch(
            str(projection["transition_fixture_tree_sha256"])
        )
        is not None
        and projection.get("fixture_acceptance_only") is True
        and projection.get("transition_fixture_enabled_mod")
        == f"mod/{FIXTURE_OUTER}"
    ):
        _fail("projection_binding_invalid", projection=value)
    return projection


def _validate_subject_to_owner_transition(
    value: object, *, owner: int, subject: int, date_raw: int
) -> dict[str, object]:
    receipt = dict(value) if isinstance(value, Mapping) else {}
    post = receipt.get("native_played_character_postcondition")
    valid = (
        receipt.get("result") == "GREEN"
        and receipt.get("expected_event_definition_key") == FIXTURE_EVENT
        and receipt.get("owner_character_id") == owner
        and receipt.get("subject_character_id") == subject
        and receipt.get("expected_player_before") == subject
        and receipt.get("expected_player_after") == owner
        and receipt.get("ack_used_as_identity_postcondition") is False
        and isinstance(post, Mapping)
        and post.get("played_character_id") == owner
        and post.get("date_raw") == date_raw
    )
    if not valid:
        _fail("subject_to_owner_transition_unbound", transition_receipt=value)
    return receipt


def _checkpoint_payload(
    result: object, *, status: str, expected_player: int, expected_date: int
) -> dict[str, object]:
    checkpoint = result.get("checkpoint") if isinstance(result, Mapping) else None
    checkpoint = dict(checkpoint) if isinstance(checkpoint, Mapping) else {}
    valid = (
        isinstance(result, Mapping)
        and result.get("accepted") is True
        and checkpoint.get("status") == status
        and isinstance(checkpoint.get("path"), str)
        and Path(str(checkpoint["path"])).is_absolute()
        and isinstance(checkpoint.get("size"), int)
        and not isinstance(checkpoint.get("size"), bool)
        and int(checkpoint["size"]) > 0
        and isinstance(checkpoint.get("sha256"), str)
        and _SHA256_RE.fullmatch(str(checkpoint["sha256"])) is not None
        and checkpoint.get("date_raw") == expected_date
        and (
            status != "saved"
            or checkpoint.get("episode_character_id") == expected_player
        )
    )
    if not valid:
        _fail(
            "native_checkpoint_receipt_invalid",
            expected_status=status,
            expected_player=expected_player,
            expected_date=expected_date,
            result=result,
        )
    return checkpoint


def freeze_route_b_pre_action_checkpoint(
    service: RouteBCheckpointService,
    *,
    owner_character_id: int,
    subject_character_id: int,
    projection_binding: Mapping[str, object],
    subject_to_owner_transition: Mapping[str, object],
    archive_path: Path,
    evidence_path: Path | None = None,
) -> dict[str, object]:
    """Freeze the real M360 frame before any route option is selected."""

    owner = _positive_character(owner_character_id, "owner_character_id")
    subject = _positive_character(subject_character_id, "subject_character_id")
    if owner == subject:
        raise ValueError("owner and subject must be distinct")
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_pre_action_checkpoint",
        "result": "RED",
        "readiness": READINESS,
        "route": ROUTE,
        "option_number": OPTION_NUMBER,
        "native_option_index": NATIVE_OPTION_INDEX,
        "owner_character_id": owner,
        "subject_character_id": subject,
        "projection_binding": None,
        "subject_to_owner_transition": None,
        "event_binding": None,
        "event_context": None,
        "native_save_receipt": None,
        "checkpoint": None,
        "case_identity": {
            "status": "pending_post_action_workforce_provider",
            "cycle_serial": None,
            "case_serial": None,
        },
        "gameplay_action_executed": False,
        "business_postcondition_claimed": False,
        "failure_reason": None,
    }
    _write_json(evidence_path, evidence)
    try:
        projection = _validate_projection_binding(projection_binding)
        before = _paused_binding(service.snapshot(), label="route-B pre-save")
        if before["player_character_id"] != owner:
            _fail("pre_save_player_is_not_owner", binding=before, owner=owner)
        transition = _validate_subject_to_owner_transition(
            subject_to_owner_transition,
            owner=owner,
            subject=subject,
            date_raw=int(before["date_raw"]),
        )
        context = _event_context(
            service,
            before,
            owner_character_id=owner,
            subject_character_id=subject,
        )
        result = service.save_checkpoint(expected_revision=int(before["revision"]))
        checkpoint = _checkpoint_payload(
            result,
            status="saved",
            expected_player=owner,
            expected_date=int(before["date_raw"]),
        )
        source = Path(str(checkpoint["path"])).resolve()
        destination = Path(archive_path).resolve()
        if not source.is_file():
            _fail("native_checkpoint_file_missing", path=str(source))
        if destination.exists():
            _fail("checkpoint_archive_already_exists", path=str(destination))
        observed_size = source.stat().st_size
        observed_sha = _sha256(source)
        expected_sha = str(checkpoint["sha256"]).lower()
        if observed_size != checkpoint["size"] or observed_sha != expected_sha:
            _fail(
                "native_checkpoint_bytes_drifted",
                path=str(source),
                observed_size=observed_size,
                observed_sha256=observed_sha,
                checkpoint=checkpoint,
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        if (
            destination.stat().st_size != observed_size
            or _sha256(destination) != observed_sha
        ):
            _fail("checkpoint_archive_copy_drifted", path=str(destination))
        after = _paused_binding(service.snapshot(), label="route-B post-save")
        after_context = _event_context(
            service,
            after,
            owner_character_id=owner,
            subject_character_id=subject,
        )
        stable_fields = (
            "date_raw",
            "player_character_id",
            "event_instance_id",
        )
        if any(after[key] != before[key] for key in stable_fields):
            _fail("checkpoint_save_changed_event_frame", before=before, after=after)
        evidence.update(
            {
                "result": "GREEN",
                "projection_binding": projection,
                "subject_to_owner_transition": transition,
                "event_binding": before,
                "event_context": context,
                "post_save_event_binding": after,
                "post_save_event_context": after_context,
                "native_save_receipt": copy.deepcopy(dict(result)),
                "checkpoint": {
                    "path": str(destination),
                    "bytes": observed_size,
                    "sha256": observed_sha,
                    "native_source_path": str(source),
                    "date_raw": before["date_raw"],
                    "owner_character_id": owner,
                    "subject_character_id": subject,
                    "event_instance_id": before["event_instance_id"],
                    "product_tree_sha256": projection["product_tree_sha256"],
                    "transition_fixture_tree_sha256": projection[
                        "transition_fixture_tree_sha256"
                    ],
                },
                "failure_reason": None,
            }
        )
        _write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        _write_json(evidence_path, evidence)
        raise


def _validate_owner_to_subject_transition(
    value: object, *, owner: int, subject: int, date_raw: int
) -> dict[str, object]:
    receipt = dict(value) if isinstance(value, Mapping) else {}
    post = receipt.get("native_played_character_postcondition")
    valid = (
        receipt.get("result") == "GREEN"
        and receipt.get("expected_event_definition_key") == SWITCH_BACK_EVENT
        and receipt.get("owner_character_id") == owner
        and receipt.get("subject_character_id") == subject
        and receipt.get("expected_player_before") == owner
        and receipt.get("expected_player_after") == subject
        and receipt.get("ack_used_as_identity_postcondition") is False
        and isinstance(post, Mapping)
        and post.get("played_character_id") == subject
        and post.get("date_raw") == date_raw
    )
    if not valid:
        _fail("owner_to_subject_transition_unbound", transition_receipt=value)
    return receipt


def _case_identity(workforce_proof: Mapping[str, object]) -> RouteBCaseIdentity:
    projection = workforce_proof.get("postcondition")
    if not isinstance(projection, Mapping):
        _fail("workforce_projection_missing", workforce_proof=workforce_proof)
    return RouteBCaseIdentity(
        owner_character_id=_positive_character(
            projection.get("owner_character_id"), "workforce owner"
        ),
        subject_character_id=_positive_character(
            projection.get("subject_character_id"), "workforce subject"
        ),
        cycle_serial=_integer(
            projection.get("cycle_serial"), "workforce cycle", minimum=1
        ),
        case_serial=_integer(
            projection.get("case_serial"), "workforce case", minimum=1
        ),
    )


def query_career_hc_if_available(
    service: RouteBCheckpointService,
    *,
    expected_revision: int,
    expected_date_raw: int,
    identity: RouteBCaseIdentity,
) -> Mapping[str, object]:
    """Invoke the separate career-HC provider only when it is advertised."""

    capabilities = service.capabilities()
    advertised = (
        capabilities.get("bridge_capabilities")
        if isinstance(capabilities, Mapping)
        else None
    )
    if not isinstance(advertised, list) or CAREER_CAPABILITY not in advertised:
        return {
            "status": "not_available",
            "reason": "career_hc_capability_not_advertised",
            "provider_observed": False,
            "response": None,
        }
    query = getattr(
        service, "query_zhongguo_career_hc_workforce_postcondition_v1", None
    )
    if not callable(query):
        _fail("advertised_career_hc_query_missing")
    response = query(
        "zg361.p2.hc-workforce.b4.route-b.career",
        expected_revision=expected_revision,
        owner_character_id=identity.owner_character_id,
    )
    if not isinstance(response, Mapping):
        _fail("career_hc_query_not_an_object", response=response)
    case = response.get("m360_identity")
    receipt = response.get("m360_receipt")

    def typed(group: object, key: str) -> object:
        field = group.get(key) if isinstance(group, Mapping) else None
        if not (
            isinstance(field, Mapping)
            and field.get("status") == "available"
            and field.get("unavailable_reason") is None
        ):
            _fail("career_hc_identity_field_unavailable", key=key, field=field)
        return field.get("value")

    observed = (
        typed(case, "owner_character_id"),
        typed(case, "subject_character_id"),
        typed(case, "cycle_serial"),
        typed(case, "case_serial"),
    )
    expected = (
        identity.owner_character_id,
        identity.subject_character_id,
        identity.cycle_serial,
        identity.case_serial,
    )
    observed_receipt = (
        typed(receipt, "owner_character_id"),
        typed(receipt, "subject_character_id"),
        typed(receipt, "cycle_serial"),
        typed(receipt, "case_serial"),
    )
    partition = response.get("career_hc_partition")
    partition_values = {
        key: _integer(typed(partition, key), f"career_hc_partition.{key}")
        for key in (
            "authorized",
            "available",
            "reserved",
            "occupied",
            "frozen",
            "reclaimed",
        )
    }
    partition_sum = sum(
        partition_values[key]
        for key in ("available", "reserved", "occupied", "frozen", "reclaimed")
    )
    route_cost = response.get("route_b_cost")
    readiness = response.get("readiness")
    if not (
        response.get("status") == "available"
        and response.get("snapshot_revision") == expected_revision
        and response.get("date_raw") == expected_date_raw
        and response.get("player_character_id") == identity.subject_character_id
        and response.get("subject_character_id") == identity.subject_character_id
        and response.get("requested_owner_character_id")
        == identity.owner_character_id
        and observed == expected
        and observed_receipt == expected
        and typed(receipt, "state") == 4
        and typed(receipt, "choice") == 2
        and receipt.get("provider_observed") is True
        and isinstance(partition, Mapping)
        and partition.get("provider_observed") is True
        and typed(partition, "conserved") is True
        and partition_values["authorized"] == partition_sum
        and isinstance(route_cost, Mapping)
        and route_cost.get("provider_observed") is True
        and typed(route_cost, "manager_cost_total") == 0
        and isinstance(readiness, Mapping)
        and readiness.get("ready") is True
    ):
        _fail(
            "career_hc_provider_binding_drifted",
            expected=expected,
            response=response,
        )
    return {
        "status": "observed",
        "reason": None,
        "provider_observed": True,
        "response": copy.deepcopy(dict(response)),
    }


def run_route_b_and_collect_postconditions(
    owner_service: RouteBCheckpointService,
    *,
    checkpoint_capture: Mapping[str, object],
    subject_session_factory: SubjectSessionFactory,
    evidence_directory: Path,
    expected_case_identity: RouteBCaseIdentity | None = None,
    career_hc_hook: CareerHcHook = query_career_hc_if_available,
) -> dict[str, object]:
    """Execute route B and seal the real provider identity onto its checkpoint."""

    capture = dict(checkpoint_capture)
    checkpoint = capture.get("checkpoint")
    if capture.get("result") != "GREEN" or not isinstance(checkpoint, Mapping):
        _fail("pre_action_checkpoint_not_green", checkpoint_capture=capture)
    owner = _positive_character(capture.get("owner_character_id"), "capture owner")
    subject = _positive_character(
        capture.get("subject_character_id"), "capture subject"
    )
    source_binding = capture.get("event_binding")
    if not isinstance(source_binding, Mapping):
        _fail("checkpoint_event_binding_missing", checkpoint_capture=capture)
    evidence_directory = Path(evidence_directory).resolve()
    evidence_directory.mkdir(parents=True, exist_ok=True)
    evidence_path = evidence_directory / "route_b_postconditions.json"
    evidence: dict[str, object] = {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_postconditions",
        "result": "RED",
        "readiness": READINESS,
        "checkpoint_sha256": checkpoint.get("sha256"),
        "action_ack_is_business_postcondition": False,
        "workforce_required_facts": {
            fact: False for fact in WORKFORCE_REQUIRED_FACTS
        },
        "owner_action": None,
        "subject_transition": None,
        "workforce_provider": None,
        "career_hc_provider": None,
        "case_identity": None,
        "failure_reason": None,
    }
    _write_json(evidence_path, evidence)
    try:
        action = submit_m360_route_action(
            owner_service,
            route=ROUTE,
            evidence_path=evidence_directory / "route_b_action_ack.json",
            post_ack_event_definition_allowlist=(SWITCH_BACK_EVENT,),
        )
        evidence["owner_action"] = action
        action_binding = action.get("binding") if isinstance(action, Mapping) else None
        if not (
            action.get("result") == "ACKED"
            and action.get("business_receipt_claimed") is False
            and isinstance(action_binding, Mapping)
            and action_binding.get("route") == ROUTE
            and action_binding.get("option_number") == OPTION_NUMBER
            and action_binding.get("owner_character_id") == owner
            and action_binding.get("subject_character_id") == subject
            and action_binding.get("date_raw") == source_binding.get("date_raw")
        ):
            _fail("route_b_ack_binding_drifted", action=action)
        binding = M360ActionBinding(
            route=ROUTE,
            owner_character_id=owner,
            subject_character_id=subject,
            event_instance_id=int(action_binding["event_instance_id"]),
            option_number=OPTION_NUMBER,
            date_raw=int(action_binding["date_raw"]),
            pre_action_revision=int(action_binding["pre_action_revision"]),
        )
        session = subject_session_factory(binding)
        if not isinstance(session, RouteBSubjectSession):
            _fail("subject_session_factory_returned_wrong_type")
        transition = _validate_owner_to_subject_transition(
            session.transition_receipt,
            owner=owner,
            subject=subject,
            date_raw=binding.date_raw,
        )
        evidence["subject_transition"] = transition
        workforce = prove_m360_postcondition(
            session.service,
            route=ROUTE,
            owner_character_id=owner,
            subject_character_id=subject,
            evidence_path=evidence_directory / "route_b_workforce_provider.json",
            max_timeline_steps=0,
        )
        identity = _case_identity(workforce)
        if (
            identity.owner_character_id != owner
            or identity.subject_character_id != subject
        ):
            _fail("workforce_identity_drifted", identity=asdict(identity))
        if expected_case_identity is not None and identity != expected_case_identity:
            _fail(
                "restored_case_identity_drifted",
                expected=asdict(expected_case_identity),
                observed=asdict(identity),
            )
        after = _paused_binding(
            session.service.snapshot(),
            label="route-B provider join",
            require_event=False,
        )
        successful_queries = workforce.get("paused_queries")
        last_query = (
            successful_queries[-1]
            if isinstance(successful_queries, list) and successful_queries
            else None
        )
        if not (
            isinstance(last_query, Mapping)
            and after["revision"] == last_query.get("revision")
            and after["date_raw"] == last_query.get("date_raw")
            and after["player_character_id"] == subject
        ):
            _fail(
                "workforce_career_join_frame_drifted",
                workforce_last_query=last_query,
                after=after,
            )
        career = career_hc_hook(
            session.service,
            expected_revision=int(after["revision"]),
            expected_date_raw=int(after["date_raw"]),
            identity=identity,
        )
        if not (
            isinstance(career, Mapping)
            and career.get("status") in {"observed", "not_available"}
            and (
                career.get("provider_observed") is True
                if career.get("status") == "observed"
                else career.get("provider_observed") is False
            )
        ):
            _fail("career_hc_hook_returned_untyped_result", result=career)
        evidence["workforce_provider"] = workforce
        evidence["career_hc_provider"] = copy.deepcopy(dict(career))
        evidence["case_identity"] = {
            **asdict(identity),
            "source": "workforce_provider_post_action",
            "checkpoint_sha256": checkpoint.get("sha256"),
        }
        evidence["workforce_required_facts"] = {
            fact: True for fact in WORKFORCE_REQUIRED_FACTS
        }
        evidence["result"] = "GREEN"
        evidence["failure_reason"] = None
        _write_json(evidence_path, evidence)
        return evidence
    except BaseException as error:
        evidence["failure_reason"] = f"{type(error).__name__}: {error}"
        _write_json(evidence_path, evidence)
        raise


def restore_route_b_pre_action_checkpoint(
    service: RouteBCheckpointService,
    *,
    checkpoint_capture: Mapping[str, object],
    case_identity: RouteBCaseIdentity,
    evidence_path: Path | None = None,
) -> dict[str, object]:
    """Restore the latest native checkpoint and verify the real M360 frame."""

    capture = dict(checkpoint_capture)
    checkpoint = capture.get("checkpoint")
    binding = capture.get("event_binding")
    if not (
        capture.get("result") == "GREEN"
        and isinstance(checkpoint, Mapping)
        and isinstance(binding, Mapping)
    ):
        _fail("checkpoint_capture_not_restorable", checkpoint_capture=capture)
    owner = _positive_character(capture.get("owner_character_id"), "capture owner")
    subject = _positive_character(
        capture.get("subject_character_id"), "capture subject"
    )
    if (
        case_identity.owner_character_id != owner
        or case_identity.subject_character_id != subject
    ):
        _fail("case_identity_not_bound_to_checkpoint", identity=asdict(case_identity))
    archive = Path(str(checkpoint.get("path"))).resolve()
    expected_bytes = checkpoint.get("bytes")
    expected_sha = str(checkpoint.get("sha256", "")).lower()
    if not (
        archive.is_file()
        and archive.stat().st_size == expected_bytes
        and _SHA256_RE.fullmatch(expected_sha) is not None
        and _sha256(archive) == expected_sha
    ):
        _fail("checkpoint_archive_drifted", checkpoint=checkpoint)
    before = _paused_binding(
        service.snapshot(), label="route-B pre-restore", require_event=False
    )
    result = service.restore_checkpoint(expected_revision=int(before["revision"]))
    restored = _checkpoint_payload(
        result,
        status="restored",
        expected_player=owner,
        expected_date=int(binding["date_raw"]),
    )
    if (
        restored.get("size") != expected_bytes
        or str(restored.get("sha256", "")).lower() != expected_sha
    ):
        _fail(
            "restored_checkpoint_hash_drifted",
            expected_checkpoint=checkpoint,
            restored_checkpoint=restored,
        )
    after = _paused_binding(service.snapshot(), label="route-B post-restore")
    context = _event_context(
        service,
        after,
        owner_character_id=owner,
        subject_character_id=subject,
    )
    # Runtime event instance ids may be reallocated by a cold restore. The
    # fixed definition, exact scopes, date and option surface are the stable
    # restored product identity.
    if any(
        after[key] != binding[key]
        for key in ("date_raw", "player_character_id")
    ):
        _fail("restored_event_binding_drifted", expected=binding, observed=after)
    evidence = {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_checkpoint_restore",
        "result": "GREEN",
        "readiness": READINESS,
        "before": before,
        "after": after,
        "event_context": context,
        "restore_receipt": copy.deepcopy(dict(result)),
        "checkpoint_sha256": expected_sha,
        "expected_case_identity": asdict(case_identity),
        "case_identity_observed_at_restore": False,
        "case_identity_replay_required": True,
        "failure_reason": None,
    }
    _write_json(evidence_path, evidence)
    return evidence


__all__ = [
    "CareerHcHook",
    "RouteBCaseIdentity",
    "RouteBCheckpointError",
    "RouteBCheckpointService",
    "RouteBSubjectSession",
    "WORKFORCE_REQUIRED_FACTS",
    "bind_current_cumulative_projection",
    "freeze_route_b_pre_action_checkpoint",
    "query_career_hc_if_available",
    "restore_route_b_pre_action_checkpoint",
    "run_route_b_and_collect_postconditions",
]

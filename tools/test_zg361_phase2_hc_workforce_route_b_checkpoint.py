#!/usr/bin/env python3
from __future__ import annotations

import copy
from dataclasses import asdict
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import zg361_phase2_hc_workforce_route_b_checkpoint as checkpoint  # noqa: E402


OWNER = 32904
SUBJECT = 29037
CYCLE = 16
CASE = 16056
DATE = 53146920
EVENT_ID = 360123
PRODUCT_HASH = "a" * 64
FIXTURE_HASH = "b" * 64
GIT_COMMIT = "c" * 40


def character_scope(character_id: int) -> dict[str, object]:
    return {
        "status": "available",
        "raw_type_index": 4,
        "type_key": "character",
        "subtype": 0,
        "typed_identity": {
            "status": "available",
            "kind": "character",
            "character_id": character_id,
        },
    }


def snapshot(
    *, player: int, revision: int, event_id: int | None = EVENT_ID
) -> dict[str, object]:
    return {
        "snapshot_id": f"snapshot-{player}-{revision}",
        "revision": revision,
        "native_revision": revision + 100,
        "date_raw": DATE,
        "paused": True,
        "map_ready": True,
        "played_character": {"character_id": player},
        "active_event": (
            {"instance_id": event_id, "option_count": 3}
            if event_id is not None
            else None
        ),
    }


def event_response(
    *,
    revision: int,
    definition: str = "zg361we.360",
    event_id: int = EVENT_ID,
) -> dict[str, object]:
    context = {
        "status": "available",
        "event_definition_key": definition,
        "current_event_instance_id": event_id,
        "snapshot_revision": revision + 100,
        "date_raw": DATE,
        "root_scope": character_scope(OWNER),
        "saved_scopes": [
            {
                "name": "zg361_we_al_owner",
                "name_identifier": 1,
                "scope": character_scope(OWNER),
            },
            {
                "name": "zg361_we_al_subject",
                "name_identifier": 2,
                "scope": character_scope(SUBJECT),
            },
            {"name": "zg361_we_al_cycle", "name_identifier": 3, "scope": {}},
            {"name": "zg361_we_al_case", "name_identifier": 4, "scope": {}},
        ],
        "options": [
            {
                "rendered_index": index,
                "native_option_index": index,
                "shown": True,
                "enabled": True,
                "resolved_name": f"route {chr(65 + index)}",
            }
            for index in range(3)
        ],
        "readiness": {
            "event_definition_identity_ready": True,
            "root_scope_ready": True,
            "saved_scopes_ready": True,
            "option_presentation_ready": True,
        },
    }
    return {"status": "available", "current_event_window_context": context}


def bootstrap() -> dict[str, object]:
    projection = {
        "schema_version": 1,
        "projection": "current-cumulative-r20",
        "mode": "allowlist",
        "tree_sha256": PRODUCT_HASH,
    }
    return {
        "tree_sha256": {"product": PRODUCT_HASH},
        "enabled_mods": ["mod/zg361_acceptance.mod"],
        "manifest": {
            "projection": projection,
            "tree_sha256": PRODUCT_HASH,
        },
    }


def fixture_install() -> dict[str, object]:
    before = ["mod/zg361_acceptance.mod"]
    return {
        "result": "GREEN",
        "acceptance_only": True,
        "release_included": False,
        "promo_included": False,
        "source_tree_sha256": FIXTURE_HASH,
        "target_tree_sha256": FIXTURE_HASH,
        "enabled_mods_before": before,
        "enabled_mods_after": [
            *before,
            "mod/zga_phase2_workforce_action_fixture.mod",
        ],
    }


def projection_binding() -> dict[str, object]:
    return checkpoint.bind_current_cumulative_projection(
        bootstrap(), fixture_install(), source_git_commit=GIT_COMMIT
    )


def transition(*, to_owner: bool) -> dict[str, object]:
    before, after = (SUBJECT, OWNER) if to_owner else (OWNER, SUBJECT)
    return {
        "result": "GREEN",
        "expected_event_definition_key": (
            "zga_phase2_workforce.1"
            if to_owner
            else "zga_phase2_workforce.3"
        ),
        "owner_character_id": OWNER,
        "subject_character_id": SUBJECT,
        "expected_player_before": before,
        "expected_player_after": after,
        "ack_used_as_identity_postcondition": False,
        "native_played_character_postcondition": {
            "played_character_id": after,
            "date_raw": DATE,
        },
    }


def capture(archive: Path) -> dict[str, object]:
    return {
        "schema_version": 1,
        "kind": "zg361_hc_workforce_route_b_pre_action_checkpoint",
        "result": "GREEN",
        "readiness": "static-ready-live-pending",
        "owner_character_id": OWNER,
        "subject_character_id": SUBJECT,
        "event_binding": {
            "snapshot_id": "pre-route-b",
            "revision": 10,
            "native_revision": 110,
            "date_raw": DATE,
            "player_character_id": OWNER,
            "event_instance_id": EVENT_ID,
        },
        "checkpoint": {
            "path": str(archive.resolve()),
            "bytes": archive.stat().st_size,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "date_raw": DATE,
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "event_instance_id": EVENT_ID,
            "product_tree_sha256": PRODUCT_HASH,
            "transition_fixture_tree_sha256": FIXTURE_HASH,
        },
    }


def action_ack() -> dict[str, object]:
    return {
        "result": "ACKED",
        "business_receipt_claimed": False,
        "binding": {
            "route": "B",
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "event_instance_id": EVENT_ID,
            "option_number": 2,
            "date_raw": DATE,
            "pre_action_revision": 10,
        },
    }


def workforce_proof(*, case: int = CASE) -> dict[str, object]:
    return {
        "result": "GREEN",
        "m361_charter_required": False,
        "paused_queries": [
            {
                "revision": 30,
                "date_raw": DATE,
                "response": {"status": "available"},
            }
        ],
        "postcondition": {
            "owner_character_id": OWNER,
            "subject_character_id": SUBJECT,
            "cycle_serial": CYCLE,
            "case_serial": case,
            "route": "B",
            "m361_charter_required": False,
        },
    }


def typed(value: object) -> dict[str, object]:
    return {"status": "available", "value": value, "unavailable_reason": None}


def career_response() -> dict[str, object]:
    identity = {
        "owner_character_id": typed(OWNER),
        "subject_character_id": typed(SUBJECT),
        "cycle_serial": typed(CYCLE),
        "case_serial": typed(CASE),
    }
    return {
        "status": "available",
        "snapshot_revision": 30,
        "date_raw": DATE,
        "player_character_id": SUBJECT,
        "subject_character_id": SUBJECT,
        "requested_owner_character_id": OWNER,
        "m360_identity": identity,
        "m360_receipt": {
            **copy.deepcopy(identity),
            "state": typed(4),
            "choice": typed(2),
            "provider_observed": True,
        },
        "career_hc_partition": {
            "authorized": typed(10),
            "available": typed(4),
            "reserved": typed(2),
            "occupied": typed(2),
            "frozen": typed(1),
            "reclaimed": typed(1),
            "conserved": typed(True),
            "provider_observed": True,
        },
        "route_b_cost": {
            "manager_cost_total": typed(0),
            "provider_observed": True,
        },
        "readiness": {"ready": True},
    }


class CaptureService:
    def __init__(self, source: Path, *, definition: str = "zg361we.360") -> None:
        self.source = source
        self.definition = definition
        self.snapshots = [
            snapshot(player=OWNER, revision=10),
            snapshot(player=OWNER, revision=11),
        ]
        self.save_calls = 0

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshots.pop(0))

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        if event_instance_id != EVENT_ID:
            raise AssertionError("wrong event")
        return event_response(revision=expected_revision, definition=self.definition)

    def save_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self.save_calls += 1
        if expected_revision != 10:
            raise AssertionError("save crossed frame")
        return {
            "accepted": True,
            "checkpoint": {
                "status": "saved",
                "path": str(self.source.resolve()),
                "size": self.source.stat().st_size,
                "sha256": hashlib.sha256(self.source.read_bytes()).hexdigest(),
                "date_raw": DATE,
                "episode_character_id": OWNER,
            },
        }


class SubjectService:
    def __init__(self, *, advertise_career: bool = False) -> None:
        self.advertise_career = advertise_career
        self.career_calls: list[tuple[str, int, int]] = []

    def snapshot(self) -> dict[str, object]:
        return snapshot(player=SUBJECT, revision=30, event_id=None)

    def capabilities(self) -> dict[str, object]:
        capabilities: list[str] = []
        if self.advertise_career:
            capabilities.append(checkpoint.CAREER_CAPABILITY)
        return {"bridge_capabilities": capabilities}

    def query_zhongguo_career_hc_workforce_postcondition_v1(
        self,
        request_nonce: str,
        *,
        expected_revision: int,
        owner_character_id: int,
    ) -> dict[str, object]:
        self.career_calls.append(
            (request_nonce, expected_revision, owner_character_id)
        )
        return career_response()


class RestoreService:
    def __init__(self, archive: Path) -> None:
        self.archive = archive
        self.snapshots = [
            snapshot(player=SUBJECT, revision=40, event_id=None),
            snapshot(player=OWNER, revision=50, event_id=EVENT_ID + 1),
        ]
        self.restore_calls = 0

    def snapshot(self) -> dict[str, object]:
        return copy.deepcopy(self.snapshots.pop(0))

    def restore_checkpoint(self, *, expected_revision: int) -> dict[str, object]:
        self.restore_calls += 1
        if expected_revision != 40:
            raise AssertionError("restore crossed frame")
        return {
            "accepted": True,
            "checkpoint": {
                "status": "restored",
                "path": str(self.archive.resolve()),
                "size": self.archive.stat().st_size,
                "sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                "date_raw": DATE,
            },
        }

    def query_current_event_window_context_v1(
        self, event_instance_id: int, *, expected_revision: int
    ) -> dict[str, object]:
        return event_response(
            revision=expected_revision, event_id=event_instance_id
        )


class ProjectionBindingTests(unittest.TestCase):
    def test_binds_actual_product_and_fixture_tree_hashes(self) -> None:
        result = projection_binding()
        self.assertEqual(
            "zg361_current_cumulative_product_projection", result["kind"]
        )
        self.assertEqual(PRODUCT_HASH, result["product_tree_sha256"])
        self.assertEqual(FIXTURE_HASH, result["transition_fixture_tree_sha256"])

    def test_rejects_manifest_runtime_tree_drift(self) -> None:
        value = bootstrap()
        value["manifest"]["tree_sha256"] = "d" * 64
        with self.assertRaises(checkpoint.RouteBCheckpointError) as raised:
            checkpoint.bind_current_cumulative_projection(
                value, fixture_install(), source_git_commit=GIT_COMMIT
            )
        self.assertEqual(
            "current_cumulative_projection_unbound", raised.exception.reason_code
        )


class FreezeCheckpointTests(unittest.TestCase):
    def test_freezes_real_m360_before_action_and_archives_exact_bytes(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-route-b-freeze-") as name:
            root = Path(name)
            source = root / "native.ck3"
            source.write_bytes(b"real-route-b-checkpoint")
            archive = root / "archive" / "pre-route-b.ck3"
            service = CaptureService(source)
            result = checkpoint.freeze_route_b_pre_action_checkpoint(
                service,
                owner_character_id=OWNER,
                subject_character_id=SUBJECT,
                projection_binding=projection_binding(),
                subject_to_owner_transition=transition(to_owner=True),
                archive_path=archive,
            )
        self.assertEqual("GREEN", result["result"])
        self.assertEqual(1, service.save_calls)
        self.assertEqual("pending_post_action_workforce_provider", result["case_identity"]["status"])
        self.assertIsNone(result["case_identity"]["cycle_serial"])
        self.assertFalse(result["gameplay_action_executed"])
        self.assertFalse(result["business_postcondition_claimed"])

    def test_wrong_event_is_red_before_save(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-route-b-freeze-") as name:
            root = Path(name)
            source = root / "native.ck3"
            source.write_bytes(b"checkpoint")
            service = CaptureService(source, definition="zg361we.359")
            with self.assertRaises(checkpoint.RouteBCheckpointError) as raised:
                checkpoint.freeze_route_b_pre_action_checkpoint(
                    service,
                    owner_character_id=OWNER,
                    subject_character_id=SUBJECT,
                    projection_binding=projection_binding(),
                    subject_to_owner_transition=transition(to_owner=True),
                    archive_path=root / "archive.ck3",
                )
        self.assertEqual("real_m360_event_not_ready", raised.exception.reason_code)
        self.assertEqual(0, service.save_calls)


class PostconditionJoinTests(unittest.TestCase):
    def _run(
        self,
        root: Path,
        *,
        service: SubjectService,
        proof: dict[str, object] | None = None,
        expected: checkpoint.RouteBCaseIdentity | None = None,
    ) -> dict[str, object]:
        archive = root / "pre-route-b.ck3"
        archive.write_bytes(b"checkpoint")

        def factory(_binding: object) -> checkpoint.RouteBSubjectSession:
            return checkpoint.RouteBSubjectSession(
                service=service,
                transition_receipt=transition(to_owner=False),
            )

        with mock.patch.object(
            checkpoint, "submit_m360_route_action", return_value=action_ack()
        ), mock.patch.object(
            checkpoint,
            "prove_m360_postcondition",
            return_value=proof or workforce_proof(),
        ):
            return checkpoint.run_route_b_and_collect_postconditions(
                object(),
                checkpoint_capture=capture(archive),
                subject_session_factory=factory,
                evidence_directory=root / "evidence",
                expected_case_identity=expected,
            )

    def test_collects_all_workforce_facts_and_typed_career_unavailability(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-route-b-post-") as name:
            result = self._run(Path(name), service=SubjectService())
        self.assertEqual("GREEN", result["result"])
        self.assertTrue(all(result["workforce_required_facts"].values()))
        self.assertEqual(
            "not_available", result["career_hc_provider"]["status"]
        )
        self.assertFalse(result["career_hc_provider"]["provider_observed"])
        self.assertEqual(CYCLE, result["case_identity"]["cycle_serial"])
        self.assertEqual(CASE, result["case_identity"]["case_serial"])
        self.assertFalse(result["action_ack_is_business_postcondition"])
        self.assertEqual(
            "m360_current_cycle_route_b", result["provider_seal_scope"]
        )
        self.assertFalse(result["m361_charter_required"])

    def test_joins_advertised_career_provider_on_same_revision_and_case(self) -> None:
        service = SubjectService(advertise_career=True)
        with tempfile.TemporaryDirectory(prefix="zg361-route-b-post-") as name:
            result = self._run(Path(name), service=service)
        self.assertEqual("observed", result["career_hc_provider"]["status"])
        self.assertTrue(result["career_hc_provider"]["provider_observed"])
        self.assertEqual(1, len(service.career_calls))
        self.assertEqual((30, OWNER), service.career_calls[0][1:])

    def test_advertised_career_provider_must_conserve_partition(self) -> None:
        service = SubjectService(advertise_career=True)
        response = career_response()
        response["career_hc_partition"]["available"] = typed(5)
        with mock.patch.object(
            service,
            "query_zhongguo_career_hc_workforce_postcondition_v1",
            return_value=response,
        ), self.assertRaises(checkpoint.RouteBCheckpointError) as raised:
            checkpoint.query_career_hc_if_available(
                service,
                expected_revision=30,
                expected_date_raw=DATE,
                identity=checkpoint.RouteBCaseIdentity(
                    OWNER, SUBJECT, CYCLE, CASE
                ),
            )
        self.assertEqual(
            "career_hc_provider_binding_drifted", raised.exception.reason_code
        )

    def test_replay_rejects_different_provider_case(self) -> None:
        expected = checkpoint.RouteBCaseIdentity(OWNER, SUBJECT, CYCLE, CASE + 1)
        with tempfile.TemporaryDirectory(prefix="zg361-route-b-post-") as name:
            with self.assertRaises(checkpoint.RouteBCheckpointError) as raised:
                self._run(
                    Path(name), service=SubjectService(), expected=expected
                )
        self.assertEqual("restored_case_identity_drifted", raised.exception.reason_code)


class RestoreCheckpointTests(unittest.TestCase):
    def test_restores_hash_identical_real_m360_frame(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-route-b-restore-") as name:
            archive = Path(name) / "pre-route-b.ck3"
            archive.write_bytes(b"checkpoint")
            service = RestoreService(archive)
            result = checkpoint.restore_route_b_pre_action_checkpoint(
                service,
                checkpoint_capture=capture(archive),
                case_identity=checkpoint.RouteBCaseIdentity(
                    OWNER, SUBJECT, CYCLE, CASE
                ),
            )
        self.assertEqual("GREEN", result["result"])
        self.assertEqual(1, service.restore_calls)
        self.assertFalse(result["case_identity_observed_at_restore"])
        self.assertTrue(result["case_identity_replay_required"])
        self.assertEqual(EVENT_ID + 1, result["after"]["event_instance_id"])
        self.assertEqual(
            {
                "owner_character_id": OWNER,
                "subject_character_id": SUBJECT,
                "cycle_serial": CYCLE,
                "case_serial": CASE,
            },
            result["expected_case_identity"],
        )

    def test_tampered_archive_is_red_before_restore(self) -> None:
        with tempfile.TemporaryDirectory(prefix="zg361-route-b-restore-") as name:
            archive = Path(name) / "pre-route-b.ck3"
            archive.write_bytes(b"checkpoint")
            frozen = capture(archive)
            archive.write_bytes(b"tampered")
            service = RestoreService(archive)
            with self.assertRaises(checkpoint.RouteBCheckpointError) as raised:
                checkpoint.restore_route_b_pre_action_checkpoint(
                    service,
                    checkpoint_capture=frozen,
                    case_identity=checkpoint.RouteBCaseIdentity(
                        OWNER, SUBJECT, CYCLE, CASE
                    ),
                )
        self.assertEqual("checkpoint_archive_drifted", raised.exception.reason_code)
        self.assertEqual(0, service.restore_calls)


if __name__ == "__main__":
    unittest.main()

"""One new synthetic formal-submit -> durable baseline -> receipt compound.

Run directly with --output-dir. No old wires, native callbacks or live actions
are used; source observations and the Driver boundary are fixture-owned.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from xar_autoplayer.bridge.prisoner_release_preview_contract_12003 import (
    RELEASE_COST_KEYS_12003, RELEASE_OPTION_KEYS_12003,
)
from xar_autoplayer.bridge.version_identity import CK3_12004
from xar_autoplayer.prisoner_release_formal_consumer import (
    SUBMIT_STEP, plan_release_formal, read_release_ledger, submit_release_formal,
)
from xar_autoplayer.prisoner_release_receipt_consumer_12004 import (
    RECEIPT_STEP, read_release_receipt_private,
)

ACTOR, TARGET = 29829, 67108867


def material(native, date, *, opinion, named, target=TARGET, available=True):
    return {
        "schema": "xar.ck3.prisoner-release-material-opinion-12004-v1",
        "build_version": CK3_12004.game_version,
        "executable_sha256": CK3_12004.executable_sha256,
        "available": available,
        "unavailable_reason": "" if available else "fixture_material_unavailable",
        "snapshot_revision": native, "date_raw": date,
        "actor_character_id": ACTOR, "target_character_id": target,
        "target_opinion_of_actor": opinion if available else None,
        "released_from_prison": {
            "observed": available, "present": available and named is not None,
            "value": named if available else None,
        },
        "release_causation_observed": False, "custody_change_observed": False,
    }


def observation(before_material):
    preview = {
        "private_build": True, "read_only": True, "advertised": False,
        "action_surface_present": False, "status": "available",
        "snapshot_id": "native:9", "public_revision": 9,
        "native_revision": 9, "proof_epoch": 4, "date_raw": 1200000,
        "definition": {"canonical_key": "release_from_prison_interaction",
                       "deterministic_key_hash": 17, "runtime_ordinal": 19},
        "payload_shape": "two_role_all_release_options_off",
        "roles": {"actor_character_id": ACTOR, "recipient_character_id": TARGET},
        "unconditional_prisoner_release": True, "can_send": True,
        "costs": {"raw_scale": 100000, "payer_role": "actor",
                  "application_timing": "on_send",
                  "entries": [{"resource_key": key, "raw": 0}
                              for key in RELEASE_COST_KEYS_12003]},
        "acceptance": {"kind": "auto_accept", "auto_accept": True,
                       "would_accept_now": True},
        "readiness": {key: True for key in (
            "definition_ready", "actor_ready", "recipient_ready",
            "finalized_context_ready", "can_send_ready", "costs_ready",
            "acceptance_ready", "same_frame_ready")},
        "option_keys": list(RELEASE_OPTION_KEYS_12003),
        "selected_option_mask_bits": 0, "puppet_or_actor_character_id": ACTOR,
    }
    collection = {
        "status": "available", "step": "query-player-prisoner-collection-private-v1",
        "snapshot_revision": 9, "query_sequence": 8, "observation_revision": 4,
        "queried_revision": 3, "queried_snapshot_id": "fixture:3",
        "player_prisoner_collection": {
            "status": "available", "played_character_id": ACTOR,
            "date_raw": 1200000, "collection_complete": True,
            "prisoners": [{"source_ordinal": 0, "prisoner_character_id": TARGET,
                           "collection_owner_character_id": ACTOR,
                           "jailer_character_id": ACTOR,
                           "custody_relation_verified": True,
                           "unconditional_release_preview": preview}],
        },
    }
    if before_material is not None:
        collection["prisoner_release_material_opinion"] = before_material
    snapshot = {
        "revision": 3, "snapshot_id": "fixture:3", "native_revision": 9,
        "date_raw": 1200000, "paused": True, "map_ready": True,
        "played_character": {"character_id": ACTOR}, "active_wars": [],
        "active_event": None, "pending_character_interaction": None,
        "history": [{"ok": True, "command": collection["step"], "result": collection}],
    }
    return snapshot, collection


class Driver:
    allow_private_prisoner_ransom_action = True

    def __init__(self, state_dir, snapshot, collection):
        self.state_dir, self.snapshot, self.collection = state_dir, snapshot, collection
        self.submits, self.queries = 0, 0

    def take_internal_semantic_snapshot(self):
        return copy.deepcopy(self.snapshot)

    def submit_player_prisoner_release_private_v1(self, **kwargs):
        self.submits += 1
        assert kwargs["prisoner_character_id"] == TARGET
        return {"status": "submitted_verification_pending", "material_result": False,
                "pre_native_revision": 9, "pre_date_raw": 1200000,
                "request_id": "fixture-original-release"}

    def query_player_prisoner_collection_private_v1(self, **kwargs):
        self.queries += 1
        assert kwargs == {"expected_revision": 4,
                          "release_material_target_character_id": TARGET}
        return copy.deepcopy(self.collection)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    report = {"status": "RED", "qualification": "new synthetic connected source seam",
              "live_actions": 0, "native_callbacks": 0, "cases": []}
    cases = (
        ("new-named-material", None, 20, "free", "applied", "observed"),
        ("preexisting-named-held", 20, 20, "held_by_player", "pending", "observed"),
        ("legacy-no-baseline", None, 20, "free", "applied", "before_missing"),
        ("no-after-material", None, 20, "free", "applied", "after_missing"),
        ("other-target-baseline", None, 20, "held_by_other", "transferred", "before_mismatch"),
        ("unavailable-material-dead", None, 20, "dead", "dead", "after_unavailable"),
    )
    try:
        for name, pre_named, post_named, custody, status, expectation in cases:
            case_dir = args.output_dir / name
            case_dir.mkdir()
            pre = material(9, 1200000, opinion=40, named=pre_named)
            if expectation == "before_missing":
                pre = None
            elif expectation == "before_mismatch":
                pre["target_character_id"] = TARGET + 1
            snapshot, collection = observation(pre)
            driver = Driver(case_dir, snapshot, collection)
            base = {"plan": {"selected_step": "life-advance"}}
            planned = plan_release_formal(driver, base, snapshot)
            assert planned["plan"]["selected_step"] == SUBMIT_STEP
            pending = submit_release_formal(driver, plan=planned["plan"])
            original_pending = copy.deepcopy(pending)
            if expectation == "observed":
                assert pending["pre_release_material_opinion"] == pre
                pre["target_opinion_of_actor"] = 999
                assert read_release_ledger(case_dir)["pending"]["pre_release_material_opinion"]["target_opinion_of_actor"] == 40
            driver.snapshot.update(revision=4, snapshot_id="fixture:4",
                                   native_revision=10, date_raw=1200024, history=[])
            target_state = {
                "schema": "xar.ck3.prisoner-retained-target-state-12004-v1",
                "build_version": CK3_12004.game_version,
                "executable_sha256": CK3_12004.executable_sha256,
                "available": True, "unavailable_reason": "", "snapshot_revision": 10,
                "date_raw": 1200024, "actor_character_id": ACTOR,
                "target_character_id": TARGET, "custody_state": custody,
                "target_alive": custody != "dead",
                "is_imprisoned": None if custody == "dead" else custody != "free",
                "jailer_character_id": (ACTOR if custody == "held_by_player" else
                                       83886084 if custody == "held_by_other" else None),
            }
            driver.collection = {"prisoner_retained_target_state": target_state}
            if expectation != "after_missing":
                driver.collection["prisoner_release_material_opinion"] = material(
                    10, 1200024, opinion=47, named=post_named,
                    available=expectation != "after_unavailable")
            planned = plan_release_formal(driver, base, driver.snapshot)
            assert planned["plan"]["selected_step"] == RECEIPT_STEP
            result = read_release_receipt_private(driver, pending=planned["plan"]["prisoner_release_pending"])
            assert result["status"] == status
            assert result["material_result"] is (custody == "free")
            assert result["release_causation_observed"] is False
            assert result["command_costs_verified"] is False
            assert result["source_pending"] == original_pending
            comparison = result["release_material_opinion_comparison"]
            if expectation == "observed":
                assert comparison["observed_total_opinion_delta"] == 7
                assert comparison["observed_released_from_prison_delta"] == post_named - (pre_named or 0)
                assert comparison["named_relation_improved"] is (pre_named is None)
                assert comparison["release_causation_observed"] is False
                assert result["release_material_opinion_comparison_unavailable_reason"] is None
            else:
                assert comparison is None
                assert result["release_material_opinion_comparison_unavailable_reason"]
            ledger = read_release_ledger(case_dir)
            assert (ledger["pending"] is None) is (custody != "held_by_player")
            assert driver.submits == 1 and driver.queries == 1
            report["cases"].append({"name": name, "status": "GREEN", "outcome": result})
        report["status"] = "GREEN"
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        (args.output_dir / "RESULT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"status": report["status"], "cases": len(report["cases"]),
                          "result": str(args.output_dir / "RESULT.json")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

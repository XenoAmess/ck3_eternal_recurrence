"""Read-only RAM qualification; no Source26 export or canonical authority issued."""
from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
import prepare_source26_export_base_v1 as m

PLAN = Path("D:/codex-ck3-demos/2026-10-19-robert-v20261019-storage01/") / (
    "A05-SOURCE26-QUALIFICATION0630-01/source26_writer/PLAN.json")
PLAN_PIN = (26306, "a2b3ba812b56361d7c4040c5c68fde3671c21bc2ff2302dda66c847c4307c51b")


def qualify_v1():
    """Use actual historical authority and actual planned row pins, never a commit guess."""
    previous, history_refs = m.actual_source25_v1()
    plan_ref = m.ref(PLAN, 65536)
    m.require((plan_ref["bytes"], plan_ref["sha256"]) == PLAN_PIN,
              "actual reviewed Source26 RAM row plan differs")
    plan = m.read_document(plan_ref, 65536)
    m.require(plan["machine_id"] == m.MACHINE
              and plan["status"] == "RAM_SOURCE26_NOT_CANONICAL_NOT_EXPORTED_NOT_RUNTIME_ADOPTED"
              and plan["base"]["commit"] == m.PARENT and len(plan["delta"]) == 12,
              "RAM row plan has no canonical authority")
    indexed = {row["relative"]: row for row in m.rows(previous)}
    for change in plan["delta"]:
        m.require(indexed.get(change["relative"]) == change["before"], "exact old row differs")
        indexed[change["relative"]] = change["after"]
    planned_rows = sorted(indexed.values(), key=lambda row: row["relative"])
    m.require(m.pin(m.canonical(planned_rows)) == plan["output"]["canonical_rows_JSON"],
              "complete planned row reconstruction differs")
    # The pure payload renderer is exercised below. These refs and commit text
    # deliberately cannot pass public actual-document/anchor entry points.
    synthetic = "SYNTHETIC_RAM_ONLY_NO_GIT_COMMIT"
    source_ref = {"qualification_only": "synthetic generic source payload"}
    reference_ref = {"qualification_only": "synthetic generic reference payload"}
    export_ref = {"qualification_only": "synthetic complete payload"}
    anchor_ref = {"qualification_only": "synthetic anchor; no commit exists"}
    capacity = {"qualification_only": "synthetic capacity; no release"}
    source = dict(previous)
    for key in ("native_transition", "source25_canonical_anchor", "source25_parent_commit"):
        source.pop(key, None)
    source.update(files=planned_rows, source_root=str(m.SRC.resolve()),
        business_source_commit=synthetic, source_file_count=1462, source_bytes=59253402,
        base_freeze=history_refs["source25_BASE"], capacity_admission=capacity)
    reference = dict(source, source_root=str(m.REFERENCE.resolve()))
    anchor = dict(commit=synthetic, source_file_count=1462, source_bytes=59253402,
        machine_id=m.MACHINE, complete_rows_JSON=plan["output"]["canonical_rows_JSON"],
        output_pins=[change["after"] for change in plan["delta"]])
    complete = dict(schema="xar.ck3.immutable-sdk-view-export/v1", machine_id=m.MACHINE,
        status="SOURCE_READY_NOT_LOADED", manifests=[source_ref, reference_ref],
        old_content_write_operations=0, game_sdk_native_obs_calls=0, new_unique_file_count=24,
        changed_relative_paths=[change["relative"] for change in plan["delta"]],
        logical_bytes_each=59253402, business_source_commit=synthetic, capacity=capacity)
    now = datetime.now(timezone.utc).isoformat()
    args = dict(source=source, reference=reference, complete=complete, anchor=anchor,
        previous=previous, source_ref=source_ref, reference_ref=reference_ref,
        export_ref=export_ref, anchor_ref=anchor_ref, native_history_refs=history_refs,
        observed_at_utc=now)
    base, review = m._compose_values_v1(**args)
    actual = json.loads(base)
    m.require(actual["native_transition"] == previous["native_transition"]
        and actual["native_transition"]["build_chain_provenance"]["functional09_status_preserved"] == "FAILED"
        and actual["native_transition"]["build_chain_provenance"]["artifact11_status"]
            == "OFFLINE_ARTIFACT_QUALIFIED_NOT_DEPLOYED"
        and actual["files"] == planned_rows and len(base) <= m.BASE_HARD
        and actual["source26_canonical_anchor"] == anchor_ref
        and actual["attempt_id"] == "a05" and "canonical_preload_policy" not in actual,
        "complete RAM BASE/native historical provenance output differs")
    checks = ["actual_Source25_BASE_and_original_transition_three_party_checked",
              "complete_1462_rows_reconstructed_from_actual_PLAN_delta",
              "RAM_payload_keeps_all_rows_and_exact_historical_native_transition",
              "RAM_payload_policy_free_and_below_512KiB"]

    def denied(label, mutate):
        changed = copy.deepcopy(args)
        mutate(changed)
        try:
            m._compose_values_v1(**changed)
        except (ValueError, KeyError):
            checks.append(label)
        else:
            raise AssertionError("accepted bad RAM input: " + label)

    denied("row_SHA_drift_rejected", lambda a: a["source"]["files"][0].update(sha256="0" * 64))
    denied("missing_complete_row_rejected", lambda a: a["source"]["files"].pop())
    denied("case_colliding_row_rejected", lambda a: a["source"]["files"].append(a["source"]["files"][0]))
    denied("generic_rich_native_transition_injection_rejected",
           lambda a: a["source"].update(native_transition=a["previous"]["native_transition"]))
    denied("generic_complete_native_transition_injection_rejected",
           lambda a: a["complete"].update(native_transition=a["previous"]["native_transition"]))
    denied("old_policy_injection_rejected", lambda a: a["source"].update(canonical_preload_policy={}))
    denied("wrong_machine_rejected", lambda a: a["reference"].update(machine_id="unknown"))
    denied("wrong_changed_path_rejected", lambda a: a["complete"]["changed_relative_paths"].pop())
    denied("changed_blob_alias_count_rejected", lambda a: a["complete"].update(new_unique_file_count=12))
    denied("fixture_marked_input_rejected", lambda a: a["anchor"].update(source_fixture=True))
    denied("capacity_binding_drift_rejected", lambda a: a["complete"].update(capacity={}))
    try:
        m.actual_anchor_v1(history_refs["anchor"])
    except ValueError:
        checks.append("public_actual_anchor_refuses_Source25_authority")
    else:
        raise AssertionError("Source25 accepted as Source26 actual authority")
    wrong = dict(history_refs["source25_BASE"], sha256="0" * 64)
    try:
        m.actual_source25_v1(wrong)
    except ValueError:
        checks.append("public_historical_source_pin_drift_rejected")
    else:
        raise AssertionError("tampered Source25 historical pin accepted")
    return dict(schema="xar.source26.generic-export-BASE-RAM-qualification/v1",
        machine_id=m.MACHINE, observed_at_utc=now, source_fixture=True,
        status="READONLY_RAM_QUALIFIED_ACTUAL_SOURCE26_EXPORT_NOT_RUN",
        checks=len(checks), passed=checks, source25_actual_history=history_refs,
        Source26_actual_row_plan=plan_ref,
        synthetic_BASE_bytes=len(base), synthetic_BASE_is_actual_file=False,
        actual_Source26_anchor_or_commit_issued=False, actual_Source26_export_issued=False,
        actual_source26_public_renderer_NOTRUN=True,
        renderer=m.ref(m.__file__), qualifier=m.ref(__file__),
        outputs_created=0, Git_calls=0, export_calls=0, runtime_calls=0,
        qualification_note="Actual Source25 provenance and planned rows read; future payload fixtures stay RAM only.")


if __name__ == "__main__":
    print(json.dumps(qualify_v1(), ensure_ascii=False, separators=(",", ":")))

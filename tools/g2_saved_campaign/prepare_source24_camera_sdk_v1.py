"""RAM-only minimal continuous-camera wiring over the actual Source23 anchor.

The frozen donor has unrelated planner timing, wall-clock camera policy and
settle diagnostics. Only the named tracking hunks are transferred. No writer,
Native reader, launcher, exporter, or Git mutation is provided.
"""
from __future__ import annotations

import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import prepare_source22_m7_candidate_sdk_v1 as prior

exact = prior.exact
REPO, EVIDENCE, MACHINE = prior.REPO, prior.EVIDENCE, prior.MACHINE
BRIDGE = "xar_autoplayer/bridge/"
BASE_COMMIT = "330d6e67c99eb22a60919b2bf7666c1ed0ca1b71"
BASE_ROWS_PIN = (374182, "f16995df275525a39ceacf3825f38f5f9a508a67970d59e83cb3bb43e7f7fdb4")
BASE_ANCHOR = EVIDENCE / "source23-canonical-root-anchor-actual-2026-10-20.json"
BASE_ANCHOR_PIN = (7206, "aa5880db457ba6b892fa24c11a4afe15f5a7ee1d28cd37b1e566a4ac75b67e39")
PRIOR_PIN = (17552, "4b3fe7fe1397aec7c705a4ac52ec339421d4fc6648b98b1d1475c0145caad778")
PRIOR_PLAN = EVIDENCE / "source22-m7-candidate-sdk-source-plan-2026-10-20.json"
PRIOR_PLAN_PIN = (44530, "2642fcf89699ce2ea1af8d693786dbb1f7653ddd6a98df3dd6f3ce6d5649fed6")
DONOR_PARENT = "704bdd3362bdc282ed5f5f8cf31fd3f50b90d747"
DONOR = "18c4bfcdac7e7afaff64c2802907d8c9e644b378"
TRACKING = BRIDGE + "camera_tracking_v1.py"
TRACKING_PIN = (7621, "b202796bbeecd911ab608855dd09014ff9ecf8d551babb96f51fdd717832ef8c")
PATCH_PINS = {
    "native_driver.py": (1385, "fad7aa1fab54cd0cd6f1c038477b207410c13cc3e9ebdd8ff7888936b9222e1b"),
    "service.py": (24355, "3ee6e000cb2f4753ff3053c10b7d70d08c2bf81dfb0fdfadaaeebc022ee9547c"),
    "realm_overview_camera.py": (11294, "20faa0c7f0b913be9a8c0fe182d2547964e50a14e0ffd4faf238f86137ce0506"),
    "auto_camera_pre_advance_v1.py": (2169, "1e173d3aaac5a73bf7ad0c23bfe3aba9c6f04c432436bafcb156915020d36648"),
    "auto_camera_follow.py": (1320, "a7f22bdcf635192b530ad1554182c3313311b5cf512a18552e67c711484b4e95"),
}
ALLOWED = {
    "native_driver.py": {"NativeHeadlessGameplayDriver._execute_primitive_step", "NativeHeadlessGameplayDriver._execute_battle_sentinel_advance"},
    "service.py": {"GameplayBridgeService._auto_camera_hotspot_input", "GameplayBridgeService._bound_camera_presentation_actual",
                   "GameplayBridgeService._select_auto_camera_hotspot", "GameplayBridgeService._publish_camera_presentation_v1"},
    "realm_overview_camera.py": {"NativeCameraPresentationClient.__init__", "NativeCameraPresentationClient.submit",
                               "NativeCameraPresentationClient.latest", "NativeCameraPresentationClient.close"},
    "auto_camera_pre_advance_v1.py": {"camera_pre_advance_scope_v1"},
    "auto_camera_follow.py": {"LatestCameraFollowWorker._reference"},
}
OWNED = (
    REPO / "tools/g2_saved_campaign/prepare_source24_camera_sdk_v1.py",
    REPO / "tools/g2_saved_campaign/qualify_source24_camera_sdk_v1.py",
    EVIDENCE / "source24-camera-sdk-source-plan-2026-10-20.json",
)


def remove_once(payload, snippet):
    exact.require(payload.count(snippet) == 1, "unique excluded donor fragment required")
    return payload.replace(snippet, b"", 1)


def camera_hunks():
    all_hunks = {}
    for name, expected in PATCH_PINS.items():
        raw = prior.git_read("diff", "--no-ext-diff", "--no-color", "--binary", DONOR_PARENT, DONOR,
                             "--", prior.PREFIX + BRIDGE + name)
        exact.check_bytes(raw, expected, "frozen tracking donor diff " + name)
        all_hunks[name] = exact.parse_hunks(raw)
    exact.require([len(all_hunks[n]) for n in PATCH_PINS] == [2, 21, 7, 3, 1], "donor hunk inventory differs")
    selected = {"native_driver.py": all_hunks["native_driver.py"],
                "service.py": [all_hunks["service.py"][i] for i in (0, 1, 2, 5)],
                "auto_camera_pre_advance_v1.py": all_hunks["auto_camera_pre_advance_v1.py"]}
    # Retain only tracking fields from the mixed NativeClient hunks. The exact
    # whole donor diff is pinned before this finite inverse exclusion.
    realm = []
    for index in (3, 4, 5, 6):
        before, after = all_hunks["realm_overview_camera.py"][index]
        if index in (3, 6):
            after = remove_once(after, b"        self._diagnostic_request_binding = None\n")
        if index == 4:
            after = remove_once(after, b'''            # One latest request only. A new client/cold connection cannot bind
            # an old tail without its own matching submission context.
            self._diagnostic_request_binding = {
                "request_sequence": sequence,
                "source_frame": {key: frame.get(key) for key in (
                    "actor_character_id", "date_raw", "bridge_pid",
                    "connection_generation", "episode_run_id")},
            }
''')
        if index == 5:
            after = remove_once(after, b'''            # Copy the fixed tail before the SAME trailing seqlock read.
            tail = ctypes.string_at(self._view + DIAGNOSTICS_OFFSET, DIAGNOSTICS_BYTES)
            header = _Shared.from_address(self._view)
            identity = (header.magic, header.version, header.pid)
''')
        if index == 6:
            after = remove_once(after, b'''            self._latest["settle_diagnostics"] = decode_camera_settle_diagnostics_v1(
                tail, result=self._latest, mapping_identity=identity,
                result_region_end=_Shared.result.offset + ctypes.sizeof(_Result),
                request_binding=getattr(self, "_diagnostic_request_binding", None))
''')
        realm.append((before, after))
    selected["realm_overview_camera.py"] = realm
    before, after = all_hunks["auto_camera_follow.py"][0]
    old = b'''"native_elapsed_us",
                    "settle_diagnostics")}'''
    exact.require(after.count(old) == 1, "mixed worker donor fragment differs")
    after = after.replace(old, b'"native_elapsed_us")}', 1)
    selected["auto_camera_follow.py"] = [(before, after)]
    return selected


def class_ast(raw, name):
    return next(ast.dump(n, include_attributes=False) for n in ast.parse(raw).body
                if isinstance(n, ast.ClassDef) and n.name == name)


def compose(*, verify_all_base=True):
    exact.check_bytes(Path(prior.__file__).read_bytes(), PRIOR_PIN, "frozen Source23 composer")
    exact.check_bytes(PRIOR_PLAN.read_bytes(), PRIOR_PLAN_PIN, "frozen Source23 source plan")
    anchor = json.loads(exact.check_bytes(BASE_ANCHOR.read_bytes(), BASE_ANCHOR_PIN, "actual Source23 anchor"))
    exact.require(anchor["machine_id"] == MACHINE and anchor["commit"] == BASE_COMMIT
                  and anchor["source_file_count"] == 1456 and anchor["source_bytes"] == 59198354,
                  "actual Source23 anchor differs")
    inherited, base_rows, inherited_report = prior.compose(verify_all_base=verify_all_base)
    exact.check_bytes(prior.canonical(base_rows), BASE_ROWS_PIN, "complete actual Source23 rows")
    indexed = {r["relative"]: r for r in base_rows}
    _, src18 = prior.read_manifest()
    selected = camera_hunks()
    changed, originals, details, ast_changes = {}, {}, [], {}
    for name, hunks in selected.items():
        relative = BRIDGE + name
        original = inherited.get(relative)
        if original is None:
            original = prior.read_base(relative, src18)
        originals[relative] = original
        row = indexed[relative]
        exact.check_bytes(original, (row["bytes"], row["sha256"]), "Source23 camera preimage")
        after = exact.transfer_exact_hunks(original, hunks)
        exact.require(prior.inverse_hunks(after, hunks) == original, "whole Source23 camera inverse differs")
        changed[relative] = after
        before_ast, after_ast = exact.function_asts(original), exact.function_asts(after)
        modified = {k for k in set(before_ast) | set(after_ast) if before_ast.get(k) != after_ast.get(k)}
        exact.require(modified == ALLOWED[name], "unowned camera function AST changed: " + name)
        ast_changes[relative] = sorted(modified)
        details.append({"relative": relative, "hunks": len(hunks), "entire_original_inverse": True,
                        "hunk_pins": [{"before": exact.pin(a), "after": exact.pin(b)} for a, b in hunks]})
    raw = prior.git_read("show", DONOR + ":" + prior.PREFIX + TRACKING)
    exact.check_bytes(raw, TRACKING_PIN, "independent tracking module")
    exact.require(TRACKING not in indexed, "tracking module already exists")
    changed[TRACKING] = raw
    realm = BRIDGE + "realm_overview_camera.py"
    exact.require(class_ast(changed[realm], "PeaceRealmCameraPolicy") == class_ast(originals[realm], "PeaceRealmCameraPolicy"),
                  "original quiet30/refresh30 policy changed")
    exact.require(b"quiet_days: int = 30" in changed[realm] and b"refresh_days: int = 30" in changed[realm]
                  and b"quiet_seconds" not in changed[realm]
                  and b"camera_settle_diagnostics_v1" not in changed[realm]
                  and b"_diagnostic_request_binding" not in changed[realm], "unrequested donor feature entered realm client")
    rows = {n: dict(r) for n, r in indexed.items()}
    delta = []
    for name, value in sorted(changed.items()):
        compile(value, name, "exec", dont_inherit=True)
        before = rows.get(name)
        after = {"relative": name, **exact.pin(value), "git_blob_sha1": exact.blob_sha(value),
                 "git_mode": before["git_mode"] if before else "100644"}
        rows[name] = after
        delta.append({"relative": name, "before": before, "after": after,
                      "net_bytes": len(value) - (before["bytes"] if before else 0)})
    stable = [rows[n] for n in sorted(rows)]
    exact.require(len(stable) == 1457 and len(changed) == 6 and len({n.casefold() for n in rows}) == 1457,
                  "complete1457 path closure differs")
    exact.require(sum(d["before"] is None for d in delta) == 1, "one new tracking leaf required")
    exact.require(all(rows[n] == indexed[n] for n in indexed if n not in changed), "unchanged Source23 row differs")
    full_changes = {**inherited, **changed}
    exact.require(len(full_changes) == 17, "actual Source22 exporter requires seventeen changed outputs")
    actual_delta = [rows[n] for n in sorted(full_changes)]
    epoch_names = inherited_report["epoch_names"]
    epoch_inputs = {n: rows["xar_autoplayer/" + n]["sha256"] for n in epoch_names}
    logical = sum(len(v) for v in full_changes.values())
    report = {
        "schema": "xar.source24.minimal-camera-sdk/v1", "machine_id": MACHINE,
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "machine_source": "tools/ck3_live_run_id.py machine c707cc; exact Source22/23 same-machine frozen source chain",
        "status": "RAM_SOURCE24_CANDIDATE_NOT_CANONICAL_NOT_EXPORTED_NOT_RUNTIME_ADOPTED",
        "base": {"business_commit": BASE_COMMIT, "anchor": {"path": str(BASE_ANCHOR), "bytes": BASE_ANCHOR_PIN[0], "sha256": BASE_ANCHOR_PIN[1]},
                 "source_plan": {"path": str(PRIOR_PLAN), "bytes": PRIOR_PLAN_PIN[0], "sha256": PRIOR_PLAN_PIN[1]},
                 "files": 1456, "source_bytes": 59198354, "rows": {"bytes": BASE_ROWS_PIN[0], "sha256": BASE_ROWS_PIN[1]},
                 "SDK_views_of_Source23_exist": False},
        "output": {"files": 1457, "source_bytes": sum(r["bytes"] for r in stable),
                   "canonical_rows_JSON": exact.pin(prior.canonical(stable)), "changed_existing_from_Source23": 5,
                   "new_from_Source23": 1, "unchanged_Source23_rows": 1451,
                   "actual_Source22_changed_outputs": 17, "actual_Source22_changed_logical_bytes_each": logical,
                   "prospective_dual4096cluster_data_upper": 2 * sum(((len(v)+4095)//4096)*4096 for v in full_changes.values())},
        "delta": delta, "actual_Source22_delta17_after": actual_delta,
        "donor": {"parent": DONOR_PARENT, "commit": DONOR, "whole_diff_pins": {n: {"bytes": p[0], "sha256": p[1]} for n,p in PATCH_PINS.items()},
                  "scope": "Only Driver2/Service4/pre-advance3/worker scalar1 and tracking-only NativeClient4 hunks; no whole donor Driver/Service/class adoption"},
        "exact_inverse_hunks": details, "changed_function_ASTs": ast_changes,
        "unowned_function_ASTs_preserved": True,
        "static_internal_dependency_closure": prior.dependencies(changed, rows),
        "all_original_Source22_bodies_verified": verify_all_base,
        "inherited_M7_WAL_fullinverse_and_commutativity_preserved": True,
        "quiet_policy": {"quiet_days": 30, "refresh_days": 30, "entire_class_AST_unchanged": True},
        "source_epoch_detached_model": hashlib.sha256(prior.canonical(epoch_inputs)).hexdigest(),
        "epoch_inputs_after_final_Driver_Service": epoch_inputs, "source_epoch_actual_authority": False,
        "kept": ["Source20 typed ROOT/shared once budget/bounded error/audit/family", "Source21 five outputs",
                 "Source22 WAL thin/exact clock DTO/MCP75e", "Source23 M7 seven leaves/five seams and original Native29 history"],
        "not_added": ["quiet_seconds policy", "M1 settle diagnostics", "planner remainder timing", "old C19 finite/MultiWAL", "Native binary or metadata"],
        "native_requirement": "Actual Native30 Mode4 plus matching0x18400 capability/epoch; absent capability refuses. No live DLL read, RPC, camera success, actual custody or H claimed.",
        "source_participation": {"seventeen_existing_refs_or_RAM_outputs_bytes": logical, "new_three_hard_bytes": 98304,
                                 "complete_logical_hard_upper": logical+98304, "full_logical_quote_cap": 3407872,
                                 "new_production_source_copies": 0, "scratch_bytes": 0, "physical_RAM_peak_measured": False,
                                 "meaning": "Logical participating output payload plus owned sources; old Src18/Source23 objects/proofs remain shared under original cards, no full SDK copy; interpreter/AST resident peak unmeasured"},
        "future_capacity": "Data-only dualcluster quote above. Root writer must quote uncompressed Git/trees/temp/ref/aliases separately; exporter rich/MFT/compact/control/Task/log/atomic gross needs a new exact card. Old16MiB sufficiency not assumed.",
        "operations": {"Git_object_reads_only": True, "Git_writes": 0, "SDK_exports": 0, "D_writes": 0,
                       "Task_Game_Native_RPC": 0, "DLL_lib_map_Driver_SAVE_state_body_reads": 0},
        "actual_H": "unknown", "actual_tracking_or_realm_result": "NOTRUN", "clock_root_cause": "UNKNOWN; diagnostics preserved",
        "future_writes_after_freeze": 0,
    }
    exact.require(logical + 98304 <= 3407872, "logical participating source quote exceeds3.25MiB")
    return changed, stable, report


if __name__ == "__main__":
    raise SystemExit("Library-only RAM composer; no source tree, Git writer, exporter, or runtime launcher")

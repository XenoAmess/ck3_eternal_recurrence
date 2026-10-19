"""Pinned metadata-only Native29 -> Native30 export transition.

This is not a loaded-provider issuer or runtime admission. The actual existing
Native RESULT/phase format is consumed; a label or a boolean is insufficient.
No path is opened by this pure contract. Synthetic inputs remain unadmitted.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import ntpath
import re

MAX_JSON = 2 * 1024**2
CARD_SCHEMA = "xar.ck3.immutable-sdk-view-capacity/v1"
TRANSITION_SCHEMA = "xar.ck3.native29-to30-transition/v1"
# Root-authored target pin metadata, not a DLL string or qualification signal.
NATIVE30_BUILD_LABEL = "Native30 continuous hotspot tracking and idle realm overview"
EVIDENCE_NAMES = ("target_native_pin", "build_result", "production_delivery",
                  "source_freeze", "build_plan", "compatibility",
                  "base_exe_binding", "target_exe_binding")
FIXTURE_TARGETS = (
    "xar_ck3_camera_tracking_v1_test", "xar_ck3_camera_settle_diagnostics_v1_test",
    "xar_ck3_camera_follow_pending_v1_test", "xar_ck3_realm_camera_geometry_v1_test",
    "xar_ck3_realm_camera_subrealm_v1_test", "xar_ck3_12004_faction_adopted_whole_test",
    "xar_ck3_player_faction_alerts_v1_mailbox_test",
    "xar_ck3_main_thread_query_mailbox_v1_test", "xar_ck3_native_layout_report_v1")
ROOT_FIELDS = ("step", "accepted", "status", "query_sequence", "snapshot_revision",
               "campaign_root_context", "backend_id")


def native_transition_evidence_names_v1(capacity_value):
    transition = capacity_value.get("native_transition")
    require(isinstance(transition, dict), "admitted transition evidence required")
    chain = transition.get("build_chain", "wholeclean_v1")
    if chain == "wholeclean_v1":
        return EVIDENCE_NAMES
    if chain == "resume02_fixture07_snapshot":
        from g2_saved_campaign.native30_resume_fixture07_snapshot_chain_v1 import EXTRA_EVIDENCE
        return EVIDENCE_NAMES + EXTRA_EVIDENCE
    if chain == "resume02_snapshot07_two_stage08B":
        from g2_saved_campaign.native30_two_stage_export_contract_v1 import EXTRA_EVIDENCE
        return EVIDENCE_NAMES + EXTRA_EVIDENCE
    require(chain == "resume02_fixture06", "unsupported Native build chain")
    from g2_saved_campaign.native30_resume_fixture_chain_v1 import EXTRA_EVIDENCE
    return EVIDENCE_NAMES + EXTRA_EVIDENCE


def require(value, message):
    if not value:
        raise ValueError("Native29->30 export denied: " + message)


def _sha(value, length=64):
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{" + str(length) + "}", value) is not None


def _path(value):
    require(isinstance(value, str) and value and "\0" not in value
            and ntpath.isabs(value), "absolute evidence/artifact path required")
    return ntpath.normcase(ntpath.normpath(value))


def _time(value):
    require(isinstance(value, str), "UTC observation required")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(result.tzinfo is not None and result.utcoffset().total_seconds() == 0,
            "explicit UTC observation required")
    return result


def _ref(value):
    require(isinstance(value, dict) and set(value) == {"path", "bytes", "sha256"},
            "exact evidence reference required")
    require(type(value["bytes"]) is int and 0 <= value["bytes"] <= 2**63 - 1
            and _sha(value["sha256"]), "reference size/SHA required")
    return (_path(value["path"]), value["bytes"], value["sha256"])


def _pairs(rows):
    result = {}
    for key, value in rows:
        require(key not in result, "duplicate JSON key")
        result[key] = value
    return result


@dataclass(frozen=True)
class PinnedNativeDocumentV1:
    raw: bytes
    path: str
    sha256: str

    @property
    def reference(self):
        return {"path": self.path, "bytes": len(self.raw), "sha256": self.sha256}

    @property
    def value(self):
        return parse_document_v1(self.raw, self.reference)._value()

    def _value(self):
        return json.loads(self.raw.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=lambda value: require(False, "non-finite JSON"))


def parse_document_v1(raw, reference):
    require(type(raw) is bytes and len(raw) <= MAX_JSON, "bounded JSON bytes required")
    _ref(reference)
    require(len(raw) == reference["bytes"] and hashlib.sha256(raw).hexdigest() == reference["sha256"],
            "JSON bytes differ from exact reference")
    result = PinnedNativeDocumentV1(raw, reference["path"], reference["sha256"])
    require(isinstance(result._value(), dict), "JSON object required")
    return result


def _doc(value):
    require(type(value) is PinnedNativeDocumentV1, "pinned document required, not a status dict")
    return parse_document_v1(value.raw, value.reference).value


def _same_ref(first, second):
    require(_ref(first) == _ref(second), "evidence backlink differs")


@dataclass(frozen=True)
class NativeTransitionV1:
    """Immutable metadata recipe, never a Native custody qualification token."""
    target_native_json: bytes
    manifest_metadata_json: bytes
    source_fixture: bool

    @property
    def target_native(self):
        return json.loads(self.target_native_json)

    @property
    def manifest_metadata(self):
        return json.loads(self.manifest_metadata_json)


def validate_native_transition_v1(*, base_freeze, base_native_pin, evidence, capacity,
                                  machine_id, source_fixture=False, now=None):
    """Require closed original build phases before selecting new output metadata.

    Evidence names are fixed. EXE binding documents are explicit source-owner
    projections with schema ``xar.ck3.native-executable-binding/v1``. They must
    cite the native pin and matching source freeze; this does not read an EXE.
    The caller must preserve original exporter admission separately.
    """
    require(type(source_fixture) is bool, "explicit fixture boundary required")
    require(isinstance(machine_id, str) and machine_id not in ("", "unknown"), "known machine required")
    base, old, card = _doc(base_freeze), _doc(base_native_pin), _doc(capacity)
    evidence_names = native_transition_evidence_names_v1(card)
    require(isinstance(evidence, dict) and set(evidence) == set(evidence_names), "complete fixed evidence set required")
    # The new07 branch has exactly one bounded original text log. All other
    # evidence retains the original pinned-JSON type and parser unchanged.
    chain = card.get("native_transition", {}).get("build_chain")
    raw_names = {"fixture07_no_work_log"} if chain == "resume02_fixture07_snapshot" else set()
    if chain == "resume02_snapshot07_two_stage08B":
        from g2_saved_campaign.native30_two_stage_export_contract_v1 import (
            RAW_NAMES, Native08AdminDocumentV1, parse_native08_admin_document_v1)
        raw_names = set(RAW_NAMES) | {"admin_result"}
    docs = {name: _doc(evidence[name]) for name in evidence_names if name not in raw_names}
    if chain == "resume02_snapshot07_two_stage08B":
        value = evidence["admin_result"]
        require(type(value) is Native08AdminDocumentV1, "08 typed bounded admin result required")
        docs["admin_result"] = parse_native08_admin_document_v1(value.raw, value.reference).value
    all_docs = [base, old, card, *docs.values()]
    for value in all_docs:
        if "machine_id" in value:
            require(value["machine_id"] == machine_id, "foreign/unknown machine")
        require(source_fixture or value.get("source_fixture") is not True, "synthetic evidence cannot admit export")
    require(base.get("machine_id") == old.get("machine_id") == card.get("machine_id") == machine_id,
            "base/native/card machine binding required")
    require(base.get("status") == "FINAL_SOURCE_FROZEN", "original frozen base required")
    require(old.get("native_build_label") == base.get("native_build_label")
            and old.get("native_dll_sha256") == base.get("native_dll_sha256")
            and _sha(old.get("native_dll_sha256")), "original Native29 base binding differs")
    require(card.get("schema") == CARD_SCHEMA and card.get("status") == "ADMITTED", "admitted original capacity card required")
    now = datetime.now(timezone.utc) if now is None else now
    require(now.tzinfo is not None and now < _time(card.get("review_at_utc")), "capacity review expired")
    require(card.get("native_pin_sha256") == base_native_pin.sha256
            and card.get("base_freeze_sha256") == base_freeze.sha256, "old card/native fields must remain unchanged")
    transition = card.get("native_transition")
    require(isinstance(transition, dict) and transition.get("schema") == TRANSITION_SCHEMA
            and transition.get("from_generation") == 29 and transition.get("to_generation") == 30,
            "exact admitted generation transition required")
    for name in evidence_names:
        _same_ref(transition.get(name), evidence[name].reference)
    target, result, delivery, freeze, plan, compat = [docs[name] for name in EVIDENCE_NAMES[:6]]
    label = target.get("native_build_label")
    require(label == NATIVE30_BUILD_LABEL
            and not any(word in label.lower() for word in ("placeholder", "unknown", "pending", "tbd", "fixture")),
            "non-placeholder admitted Native30 metadata description required")
    require(target.get("machine_id") == result.get("machine_id") == machine_id
            and transition.get("target_native_build_label") == label,
            "target Native30 label/machine differs from admission")
    require("error" not in result and type(result.get("Game_calls")) is int
            and result["Game_calls"] == 0 and result.get("DLL_loaded") is False,
            "closed successful actual Native build required; FAILED/RUNNING are not qualification")
    start, end = _time(result.get("start_utc")), _time(result.get("end_utc"))
    require(start <= end <= now, "build observation times differ")
    chain_audit = {"build_chain": "wholeclean_v1"}
    if transition.get("build_chain", "wholeclean_v1") == "wholeclean_v1":
        require(result.get("schema") == "native30-wholeclean-result-v1"
                and result.get("status") == "BUILT_FIXTURES_PASS_NOT_DEPLOYED",
                "closed successful actual Native build required; wrong wholeclean status/schema")
        _same_ref(result.get("plan"), evidence["build_plan"].reference)
        _same_ref(delivery.get("source_freeze"), evidence["source_freeze"].reference)
    elif transition.get("build_chain") == "resume02_fixture06":
        from g2_saved_campaign.native30_resume_fixture_chain_v1 import validate_resume_fixture_chain_v1
        chain_audit = validate_resume_fixture_chain_v1(docs=docs, evidence=evidence,
            transition=transition, machine_id=machine_id, now=now)
    elif transition.get("build_chain") == "resume02_fixture07_snapshot":
        from g2_saved_campaign.native30_resume_fixture07_snapshot_chain_v1 import validate_resume_fixture07_snapshot_chain_v1
        chain_audit = validate_resume_fixture07_snapshot_chain_v1(docs=docs, evidence=evidence,
            transition=transition, machine_id=machine_id, now=now)
    else:
        from g2_saved_campaign.native30_two_stage_export_contract_v1 import validate_two_stage_export_chain_v1
        chain_audit = validate_two_stage_export_chain_v1(docs=docs, evidence=evidence,
            transition=transition, machine_id=machine_id, now=now, source_fixture=source_fixture)
    require(plan.get("schema") == "native30-wholeclean-plan-v1", "actual frozen Native30 plan required")
    commit = delivery.get("source_commit")
    require(_sha(commit, 40) and freeze.get("commit") == commit
            and transition.get("source_commit") == commit and delivery.get("deployed") is False,
            "artifact/source commit differs")
    artifact = delivery.get("DLL")
    _ref(artifact)
    require(artifact["sha256"] == target.get("native_dll_sha256")
            and artifact["sha256"] != old["native_dll_sha256"], "target artifact pin differs or is old DLL")
    build = ntpath.dirname(artifact["path"])
    require(ntpath.basename(artifact["path"]) == ntpath.basename(plan.get("dll_artifact", "")), "DLL artifact differs from frozen plan")
    fixtures = plan.get("fixtures")
    require(isinstance(fixtures, list) and tuple(row.get("target") for row in fixtures) == FIXTURE_TARGETS,
            "all nine exact fixture targets required")
    phases = result.get("phases")
    require(isinstance(phases, list) and phases, "actual phase receipts required")
    for phase in phases:
        require(isinstance(phase, dict) and type(phase.get("returncode")) is int and phase["returncode"] == 0
                and type(phase.get("owned_active_after")) is int and phase["owned_active_after"] == 0,
                "failed/unknown/unclosed build phase")
        require(type(phase.get("pid")) is int and phase["pid"] > 0
                and start <= _time(phase.get("start_utc")) <= _time(phase.get("end_utc")) <= end,
                "actual phase identity/time required")
        require(isinstance(phase.get("argv"), list) and phase["argv"]
                and all(isinstance(value, str) for value in phase["argv"]), "actual argv required")
        _ref(phase.get("log"))
    for row in fixtures:
        require(row.get("artifact") == row["target"] + ".exe", "fixture artifact must be its exact frozen target")
        expected = _path(ntpath.join(build, row["artifact"]))
        matches = [phase for phase in phases if _path(phase["argv"][0]) == expected]
        require(len(matches) == 1, "missing/duplicate actual fixture execution: " + row["target"])
        declared = row.get("args", [])
        argv = matches[0]["argv"][1:]
        require(isinstance(declared, list) and len(declared) == len(argv), "actual fixture argument count differs")
        for wanted, actual in zip(declared, argv):
            if wanted == "$OBSERVED_UTC":
                require(start <= _time(actual) <= _time(matches[0]["start_utc"]), "fixture observation UTC differs")
            else:
                require(actual == (machine_id if wanted == "$MACHINE_ID" else wanted), "actual fixture arguments differ")
        if row.get("postcheck"):
            require(any(any(ntpath.basename(arg) == ntpath.basename(row["postcheck"]) for arg in phase["argv"])
                        and phase["argv"][-1] == matches[0]["log"]["path"] for phase in phases),
                    "layout postcheck missing")
    rows = freeze.get("files")
    require(isinstance(rows, list) and rows, "source freeze rows required")
    seen = set()
    for row in rows:
        require(isinstance(row, dict) and isinstance(row.get("path"), str)
                and row["path"] not in seen and not ntpath.isabs(row["path"])
                and not ntpath.splitdrive(row["path"])[0]
                and "\\" not in row["path"] and all(part not in ("", ".", "..") for part in row["path"].split("/"))
                and type(row.get("bytes")) is int and row["bytes"] >= 0
                and _sha(row.get("sha256")) and _sha(row.get("git_blob"), 40), "incomplete/unsafe source freeze row")
        seen.add(row["path"])
    require(compat.get("schema") == "xar.ck3.native29-to30-compatibility/v1"
            and compat.get("machine_id") == machine_id, "explicit compatibility binding required")
    for name in ("base_exe_binding", "target_exe_binding", "build_result", "production_delivery", "source_freeze"):
        _same_ref(compat.get(name), evidence[name].reference)
    bindings = []
    for name, native in (("base_exe_binding", base_native_pin), ("target_exe_binding", evidence["target_native_pin"])):
        binding = docs[name]
        require(binding.get("schema") == "xar.ck3.native-executable-binding/v1"
                and binding.get("machine_id") == machine_id, "fixed EXE/source binding required")
        _same_ref(binding.get("native_pin"), native.reference)
        image = binding.get("game_executable")
        require(isinstance(image, dict) and _sha(image.get("sha256")) and type(image.get("bytes")) is int
                and image["bytes"] > 0 and image.get("version") == "1.20.0.4"
                and image.get("architecture") == "x64", "exact supported EXE/build required")
        require(binding.get("wire_contract") == {"protocol_version": 1, "campaign_root_envelope_fields": list(ROOT_FIELDS)}
                and binding.get("native_layout_id") == "ck3-1.20.0.4", "wire/layout contract differs")
        bindings.append(image)
    require(bindings[0] == bindings[1], "cross-EXE/build transition is not supported")
    _same_ref(docs["target_exe_binding"].get("source_freeze"), evidence["source_freeze"].reference)
    audit = {"schema": TRANSITION_SCHEMA, "machine_id": machine_id,
             "base_freeze": base_freeze.reference, "base_native_pin": base_native_pin.reference,
             "base_native_build_label": old["native_build_label"],
             "base_native_dll_sha256": old["native_dll_sha256"],
             **{name: evidence[name].reference for name in evidence_names},
             "build_chain_provenance": chain_audit,
             "target_native_build_label": label, "source_fixture": source_fixture,
             "runtime_admitted": False, "actual_loaded_provider_issued": False}
    return NativeTransitionV1(json.dumps({"native_build_label": label,
        "native_dll_sha256": artifact["sha256"]}).encode(), json.dumps(audit).encode(), source_fixture)

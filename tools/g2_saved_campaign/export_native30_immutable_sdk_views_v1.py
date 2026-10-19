"""Default-OFF metadata transition entry; never edits an old freeze/exporter.

The card still binds original Native29 through its original fields. Its extra
native_transition member pins the separate closed Native30 evidence set. This
entry reads JSON evidence only, never DLL/EXE bodies or any runtime connection.
"""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from g2_saved_campaign.native29_to30_export_contract_v1 import (
    MAX_JSON, native_transition_evidence_names_v1, parse_document_v1, validate_native_transition_v1, require, _ref)
from g2_saved_campaign.native30_export_adapter_v1 import FrozenExporterAdapterV1


def _read_document(reference):
    require(isinstance(reference, dict) and set(reference) == {"path", "bytes", "sha256"},
            "exact bounded JSON reference required")
    require(type(reference["bytes"]) is int and 0 <= reference["bytes"] <= MAX_JSON,
            "JSON evidence bound exceeded")
    path = Path(reference["path"])
    require(path.is_absolute() and path.suffix.lower() == ".json", "only absolute JSON evidence can be read")
    with path.open("rb") as stream:
        raw = stream.read(MAX_JSON + 1)
    return parse_document_v1(raw, reference)


def _read_fixture07_no_work_log(reference):
    """Only original07 NoWork text, never a general artifact/body reader."""
    from g2_saved_campaign.native30_resume_fixture07_snapshot_chain_v1 import (
        RAW_LOG_LIMIT, parse_native07_no_work_log_v1)
    _ref(reference)
    require(reference["bytes"] <= RAW_LOG_LIMIT, "07 NoWork log bound exceeded")
    path = Path(reference["path"])
    require(path.is_absolute() and path.name == "production-no-work.log", "only exact07 NoWork log can be read")
    with path.open("rb") as stream:
        raw = stream.read(RAW_LOG_LIMIT + 1)
    return parse_native07_no_work_log_v1(raw, reference)


def read_native_transition_v1(*, base_freeze_ref, base_native_ref, capacity_ref,
                              machine_id, source_fixture=False):
    """Reusable source-pinned qualification loader; it creates no output.

    Canonical control producers can consume .target_native only after this
    succeeds. This is metadata qualification, never actual loaded custody.
    """
    base = _read_document(base_freeze_ref)
    native = _read_document(base_native_ref)
    capacity = _read_document(capacity_ref)
    transition = capacity.value.get("native_transition")
    require(isinstance(transition, dict), "capacity lacks admitted Native30 transition evidence")
    reader = _read_document
    if transition.get("build_chain") == "resume02_snapshot07_two_stage08B":
        from g2_saved_campaign.native30_two_stage_export_contract_v1 import RAW_NAMES
        def reader_for(name):
            if name in RAW_NAMES: return _read_fixture07_no_work_log
            return _read_08_admin_result if name == "admin_result" else _read_document
    else:
        def reader_for(name):
            return _read_fixture07_no_work_log if name == "fixture07_no_work_log" else reader
    evidence = {name: reader_for(name)(transition.get(name))
                for name in native_transition_evidence_names_v1(capacity.value)}
    return validate_native_transition_v1(base_freeze=base, base_native_pin=native,
        evidence=evidence, capacity=capacity, machine_id=machine_id, source_fixture=source_fixture)


def _read_08_admin_result(reference):
    """Only the finite08 admin RESULT receives the producer's 4MiB bound."""
    from g2_saved_campaign.native30_two_stage_export_contract_v1 import (
        ADMIN_JSON_LIMIT, parse_native08_admin_document_v1)
    _ref(reference)
    require(reference["bytes"] <= ADMIN_JSON_LIMIT, "08 admin JSON bound exceeded")
    path = Path(reference["path"])
    require(path.is_absolute() and path.name == "RESULT.json", "only exact08 admin RESULT can be read")
    with path.open("rb") as stream:
        raw = stream.read(ADMIN_JSON_LIMIT + 1)
    return parse_native08_admin_document_v1(raw, reference)


def export_native30_views_v1(args, *, execute=False):
    if execute is not True:
        return {"status": "DISABLED", "runtime_admitted": False, "output_created": False}
    # Ref sizes are independently bounded by the original input parser and
    # old exporter as well; here stat is only for exact JSON input references.
    def ref(path, sha):
        path = Path(path).resolve(strict=True)
        return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha}
    transition = read_native_transition_v1(
        base_freeze_ref=ref(args.base_freeze, args.base_freeze_sha256),
        base_native_ref=ref(args.native_pin, args.native_pin_sha256),
        capacity_ref=ref(args.capacity_card, args.capacity_card_sha256), machine_id=args.machine_id)
    adapter = FrozenExporterAdapterV1()
    context = adapter.validate_base(args)  # original unchanged 29/Host/tree/NTFS/capacity admission
    ready = adapter.prepare(args, context, transition)
    return adapter.export(args, ready)  # first mkdir occurs only inside this exact core


def main():
    # Original parser is reused, with one explicit new opt-in. Original command
    # and default old Native29 exporter remain untouched.
    adapter = FrozenExporterAdapterV1()
    parser = adapter.namespace["parser"]()
    parser.add_argument("--execute-native-transition", action="store_true")
    args = parser.parse_args()
    import json
    print(json.dumps(export_native30_views_v1(args, execute=args.execute_native_transition), indent=2))


if __name__ == "__main__":
    main()

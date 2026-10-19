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
    MAX_JSON, native_transition_evidence_names_v1, parse_document_v1, validate_native_transition_v1, require)
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
    evidence = {name: _read_document(transition.get(name))
                for name in native_transition_evidence_names_v1(capacity.value)}
    return validate_native_transition_v1(base_freeze=base, base_native_pin=native,
        evidence=evidence, capacity=capacity, machine_id=machine_id, source_fixture=source_fixture)


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

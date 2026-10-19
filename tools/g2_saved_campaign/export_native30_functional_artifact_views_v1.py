"""Default-OFF, independent09+11 metadata exporter; no08B fallback.

Reads only bounded pinned JSON. The original Native29 validator and exact
exporter adapter remain authoritative for filesystem/source admission.
"""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from g2_saved_campaign.export_native30_immutable_sdk_views_v1 import _read_document
from g2_saved_campaign.native30_functional09_artifact11_transition_v1 import (
    CHAIN, EVIDENCE_NAMES, validate_functional_artifact_transition_v1)
from g2_saved_campaign.native29_to30_export_contract_v1 import require
from g2_saved_campaign.native30_export_adapter_v1 import FrozenExporterAdapterV1


def read_native_transition_v1(*, base_freeze_ref, base_native_ref, capacity_ref,
                              machine_id, source_fixture=False):
    """Same four-reference signature, explicitly different protocol/module."""
    base, native, capacity = [_read_document(ref) for ref in (base_freeze_ref, base_native_ref, capacity_ref)]
    transition = capacity.value.get("native_transition", {})
    require(transition.get("build_chain") == CHAIN, "independent09+11 admission required; no legacy fallback")
    evidence = {name: _read_document(transition.get(name)) for name in EVIDENCE_NAMES}
    return validate_functional_artifact_transition_v1(base_freeze=base, base_native_pin=native,
        capacity=capacity, evidence=evidence, machine_id=machine_id, source_fixture=source_fixture)


def export_native30_views_v1(args, *, execute=False):
    if execute is not True:
        return {"status": "DISABLED", "output_created": False, "runtime_admitted": False}
    def ref(path, sha):
        path = Path(path).resolve(strict=True)
        return {"path": str(path), "bytes": path.stat().st_size, "sha256": sha}
    transition = read_native_transition_v1(base_freeze_ref=ref(args.base_freeze, args.base_freeze_sha256),
        base_native_ref=ref(args.native_pin, args.native_pin_sha256),
        capacity_ref=ref(args.capacity_card, args.capacity_card_sha256), machine_id=args.machine_id)
    adapter = FrozenExporterAdapterV1()
    context = adapter.validate_base(args)  # unchanged Native29/Host/NTFS/card/source checks
    ready = adapter.prepare(args, context, transition)
    return adapter.export(args, ready)  # first mkdir only after both validations


def main():
    adapter = FrozenExporterAdapterV1()
    parser = adapter.namespace["parser"]()
    parser.add_argument("--execute-functional-artifact-transition", action="store_true")
    args = parser.parse_args()
    import json
    print(json.dumps(export_native30_views_v1(args, execute=args.execute_functional_artifact_transition), indent=2))


if __name__ == "__main__": main()

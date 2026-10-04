"""Bind root-authorized exact primitive evidence; no game or tracked mutation."""

import hashlib
import json
from pathlib import Path

from gen_school_consent import ROOT
from native_admission_v2 import BINDING_SCHEMA, validate_binding
from school_consent_data import BASELINE_COMMIT

RUNTIME = Path("C:/workspace/ck3_lyd_runtime_20261004")
CHECKOUT = Path("C:/workspace/ck3_eternal_recurrence")
GAME = Path("C:/Program Files (x86)/Steam/steamapps/common/Crusader Kings III/game")
GRAPH = RUNTIME / "preserved-checkpoints/ed90dbe3374e44881fd6bb6f075acde4363fc79ebbae50e82a4fdfdf392482ca"
SOURCE = CHECKOUT / "docs/li-yu-dao/acceptance/2026-10-04-R0002-native-cycles-formal-red/source-r0002/fixture"


def main():
    destination = ROOT / "evidence/native-admission-binding.json"
    if destination.exists():
        raise ValueError("Preserve previous admission binding")
    references = {
        "native_attestation_v2": RUNTIME / "live-attempt-002/probe-audit-three-rounds/native-primitive-attestation-candidate-v2.json",
        "saved_graph_summary": GRAPH / "three-rounds.summary.json",
        "saved_artifact": GRAPH / "xar_checkpoint.ck3",
        "saved_projection": GRAPH / "three-rounds.objects.complete.json",
        "native_probe_effects": SOURCE / "common/scripted_effects/lyd_np_effects.txt",
        "native_probe_triggers": SOURCE / "common/scripted_triggers/lyd_np_triggers.txt",
        "native_title_factory_source": GAME / "common/scripted_effects/00_religion_effects.txt",
    }
    record = {
        "schema": BINDING_SCHEMA, "scope": "native-primitives-only", "baseline_commit": BASELINE_COMMIT,
        "authorized_by": "/root", "prepared_by": "/root/confucian_history_plan",
        "authorization": "Delegated instruction: Continue externaliteration2candidate audit+admission fromactualR0002 primitiveproofattestation-v2 andsave108; Acceptnativeprimitivesonly; formalapprovalstillNOT_LIVE.",
        "primitives": ["set_parent_faith", "detach_rite_to_new_faith"],
        "evidence_refs": [{"role": role, "path": str(path.resolve()), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
                          for role, path in references.items()],
        "consent_flow_live": "NOT_RUN", "shared_narrow_head_factory_live": "NOT_RUN",
        "boundary": "Binding and delegated admission of actual bounded native primitive evidence; not a new live or human approval receipt.",
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Validate before writing the binding itself; validator hashes only evidence here.
    # The complete binding is then validated again with its own exact bytes.
    destination.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    result = validate_binding(destination, record)
    report = ROOT / "evidence/native-admission-validation.json"
    report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"binding": str(destination), "status": result["status"], "consent_flow_live": "NOT_RUN"}, indent=2))


if __name__ == "__main__":
    main()

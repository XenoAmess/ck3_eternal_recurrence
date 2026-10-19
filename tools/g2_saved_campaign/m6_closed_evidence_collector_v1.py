"""Collect explicit closed small Sway sources; no game, RPC or directory scan.

This is a pointer index of producer records, not a business qualification tool.
Owners must freeze inputs after batch settlement; active ledgers are forbidden.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

LIMIT = 256 * 1024
OUTPUT_LIMIT = 1024 * 1024
IDENTITY = ("action_id", "actor_character_id", "target_character_id",
            "scheme_instance_id", "scheme_instance_generation")
FIELDS = (*IDENTITY, "exact_ck3_build", "exe_sha256", "source_native_revision", "source_date_raw",
          "baseline_source_native_revision", "baseline_source_date_raw", "scheme_sway_opinion",
          "previous_scheme_sway_opinion", "sway_blocker_opinion", "tracked_instance_active",
          "dedicated_benefit_observed", "incremental_named_gain_observed",
          "instance_terminal_outcome_observed", "native_status_key", "terminal_cause_observed",
          "terminal_cause", "completion_source_native_revision", "source_sequence",
          "execution_date_raw", "source_branch")
CONSUMPTION = ("next_turn_consumed", "following_native_revision", "following_date_raw")


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _pointer(document, pointer):
    if not isinstance(pointer, str) or not pointer.startswith("/"):
        raise ValueError("a non-root JSON pointer is required")
    current = document
    for part in pointer[1:].split("/"):
        if re.search(r"~(?![01])", part):
            raise ValueError("invalid JSON pointer escape")
        key = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict):
            if key not in current:
                return None, False
            current = current[key]
        elif isinstance(current, list) and key.isascii() and key.isdecimal() and key == str(int(key)):
            if int(key) >= len(current):
                return None, False
            current = current[int(key)]
        else:
            return None, False
    return current, True


def _read_source(pin):
    if (not isinstance(pin, dict) or pin.get("closed") is not True
            or not isinstance(pin.get("path"), str) or type(pin.get("bytes")) is not int
            or pin["bytes"] <= 0 or not isinstance(pin.get("sha256"), str)
            or re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is None):
        raise ValueError("an explicit closed source path/bytes/SHA pin is required")
    path = Path(pin["path"])
    if path.suffix.lower() != ".json":
        raise ValueError("only explicit closed JSON sources are permitted")
    size = path.stat().st_size
    if size != pin["bytes"]:
        raise ValueError("closed source size changed: " + str(path))
    if size > LIMIT:
        return None, "oversized_source/not_observed"
    raw = path.read_bytes()
    if len(raw) != size or hashlib.sha256(raw).hexdigest() != pin["sha256"]:
        raise ValueError("closed source content changed: " + str(path))
    return json.loads(raw), "pin_verified"


def _identity(episode):
    instance = episode.get("native_receipt") or episode.get("recovered_instance_observation")
    if not isinstance(instance, dict):
        return None
    value = {key: episode.get(key) for key in IDENTITY[:3]}
    value.update({key: instance.get(key) for key in IDENTITY[3:]})
    if (not isinstance(value["action_id"], str) or not value["action_id"]
            or any(type(value[key]) is not int or not 0 < value[key] <= 0xFFFFFFFF for key in IDENTITY[1:3])
            or type(value["scheme_instance_id"]) is not int
            or not 0 < value["scheme_instance_id"] < 0xFFFFFFFF
            or type(value["scheme_instance_generation"]) is not int
            or value["scheme_instance_generation"] != value["scheme_instance_id"] >> 24):
        return None
    return value


def collect(manifest, *, collector_machine_id):
    if (manifest.get("schema") != "g2.m6.closed-evidence-manifest/v1"
            or any(not isinstance(manifest.get(key), str) or not manifest[key]
                   for key in ("machine_id", "campaign_id", "batch_id", "closed_at_utc"))):
        raise ValueError("closed manifest machine/campaign/batch/time required")
    closed = datetime.fromisoformat(manifest["closed_at_utc"].replace("Z", "+00:00"))
    if closed.tzinfo is None:
        raise ValueError("closed_at_utc needs an explicit offset")
    sources, selections = manifest.get("sources"), manifest.get("selections")
    if (not isinstance(sources, list) or not len(sources) <= 64
            or not isinstance(selections, list) or not len(selections) <= 256):
        raise ValueError("at most 64 explicit sources and 256 pointers are permitted")
    documents, states = [], []
    for pin in sources:
        document, state = _read_source(pin)
        documents.append(document)
        states.append({"pin": pin, "state": state})
    groups, issues = {}, []

    def episode(row, pointer, source, ordinary):
        if not isinstance(row, dict):
            issues.append({"source": source, "pointer": pointer, "state": "episode_not_observed"})
            return
        identity = _identity(row)
        if identity is None:
            issues.append({"source": source, "pointer": pointer, "state": "identity_not_observed"})
            return
        group_key = _digest([manifest["machine_id"], manifest["campaign_id"], identity])
        group = groups.setdefault(group_key, {"identity": identity, "observations": {}})
        for kind in ("first_named_gain_intervention", "material_intervention", "terminal_intervention"):
            record = row.get(kind)
            if not isinstance(record, dict):
                continue
            if any(type(record.get(key)) is not type(value) or record[key] != value
                   for key, value in identity.items()):
                issues.append({"source": source, "pointer": pointer + "/" + kind,
                               "state": "record_identity_mismatch"})
                continue
            measurement = {key: record[key] for key in FIELDS if key in record}
            # A later consumer may add following_* fields to the exact original
            # measurement. Keep that source separately instead of duplicating it.
            fact_key = _digest([kind, measurement])
            fact = group["observations"].setdefault(fact_key, {
                "kind": kind, "measurement": measurement, "occurrences": []})
            occurrence = {"source": source, "pointer": pointer + "/" + kind,
                          "record_sha256": _digest(record),
                          "consumption": {key: record[key] for key in CONSUMPTION if key in record},
                          "ordinary_auto": ordinary}
            if occurrence not in fact["occurrences"]:
                fact["occurrences"].append(occurrence)
        if row.get("status") == "applied" and row.get("postcondition_verified") is True:
            fact = group["observations"].setdefault("applied_episode_reference", {
                "kind": "applied_episode_reference", "strict_Start_validation": "not_performed", "occurrences": []})
            occurrence = {"source": source, "pointer": pointer,
                          "receipt_pointer": pointer + ("/native_receipt" if row.get("native_receipt")
                                                         else "/recovered_instance_observation"),
                          "ordinary_auto": ordinary}
            if occurrence not in fact["occurrences"]:
                fact["occurrences"].append(occurrence)

    for selection in selections:
        index = selection.get("source")
        if type(index) is not int or not 0 <= index < len(sources):
            raise ValueError("selection requires an explicit source index")
        pointer, kind = selection.get("pointer"), selection.get("kind")
        if states[index]["state"] != "pin_verified":
            issues.append({"source": index, "pointer": pointer, "state": states[index]["state"]})
            continue
        value, exists = _pointer(documents[index], pointer)
        if not exists:
            issues.append({"source": index, "pointer": pointer, "state": "pointer_not_observed"})
            continue
        ordinary = None
        if kind == "ordinary_auto":
            if not isinstance(value, dict):
                raise ValueError("ordinary_auto pointer must select its returned body")
            ordinary = {"status": value.get("status"), "selected_step": value.get("selected_step"),
                        "planning_source_frame": value.get("planning_source_frame")}
            if value.get("selected_step") == "ordinary-sway-opportunity-v1":
                episode(value.get("result"), pointer + "/result", index, ordinary)
            value, pointer = value.get("sway_following_turn"), pointer + "/sway_following_turn"
            if value is None:
                continue
        elif kind != "ledger_episode":
            raise ValueError("selection kind must be ordinary_auto or ledger_episode")
        episode(value, pointer, index, ordinary)
        previous = value.get("previous_interventions", []) if isinstance(value, dict) else []
        if not isinstance(previous, list) or len(previous) > 128:
            raise ValueError("bounded previous_interventions list required")
        for offset, row in enumerate(previous):
            episode(row, pointer + "/previous_interventions/" + str(offset), index, ordinary)
    return {"schema": "g2.m6.closed-evidence-pointer-index/v1", "collector_machine_id": collector_machine_id,
            "source_machine_id": manifest["machine_id"], "campaign_id": manifest["campaign_id"],
            "batch_id": manifest["batch_id"], "closed_at_utc": manifest["closed_at_utc"],
            "collected_at_utc": datetime.now(timezone.utc).isoformat(), "sources": states,
            "groups": [{"group_id": key, "identity": group["identity"],
                        "observations": list(group["observations"].values())} for key, group in groups.items()],
            "issues": issues, "G2_M6_credit_awarded": False, "evidence_packet_ready": "not_evaluated",
            "Game_MCP_SDK_calls": 0, "boundary": "Producer facts and pinned pointers only; no natural cause, same-connection, useful outcome or actual following independently inferred"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 0 < args.manifest.stat().st_size <= LIMIT:
        raise ValueError("manifest exceeds the small JSON limit")
    raw = args.manifest.read_bytes()
    machine = subprocess.run([sys.executable, "-B", str(Path(__file__).resolve().parents[1] / "ck3_live_run_id.py"),
                              "machine"], capture_output=True, text=True, check=True).stdout.strip()
    result = collect(json.loads(raw), collector_machine_id=machine)
    result["manifest"] = {"path": str(args.manifest), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    encoded = (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > OUTPUT_LIMIT:
        raise ValueError("pointer index exceeds 1 MiB; split the explicit batch manifest")
    with args.output.open("xb") as stream:
        stream.write(encoded)
    print(json.dumps({"output": str(args.output), "groups": len(result["groups"]),
                      "G2_M6_credit_awarded": False, "Game_MCP_SDK_calls": 0}))


if __name__ == "__main__":
    main()

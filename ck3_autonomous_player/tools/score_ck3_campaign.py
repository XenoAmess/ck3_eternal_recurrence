"""Bounded offline campaign score runner; no Game/MCP or melted file writes."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from xar_autoplayer import campaign_development_score_v1 as scoring
from xar_autoplayer import campaign_score_save_reader as reader
from xar_autoplayer.ck3_live_run_identity_v1 import current_machine_id


def validate_admission(admission, output, machine_id, *, now=None):
    now = now or datetime.now(timezone.utc)
    if machine_id != current_machine_id() or admission.get("machine_id") != machine_id:
        raise ValueError("capacity/current execution machine mismatch")
    if (admission.get("schema") != "xar.first30.scoring-metadata-staging-capacity-admission/v1"
            or admission.get("owner") != "/root" or admission.get("status") != "ADMITTED"
            or admission.get("scoring_metadata_staging_admitted") is not True):
        raise ValueError("scoring metadata card schema/owner/status mismatch")
    issued = datetime.fromisoformat(admission["at_utc"])
    deadline = datetime.fromisoformat(admission["review_at_utc"])
    if issued.tzinfo is None or deadline.tzinfo is None or not issued <= now < deadline:
        raise ValueError("capacity card expired or not yet valid")
    root = Path(admission["allowed_output_root"])
    if root.exists() and (root.is_symlink() or getattr(root.lstat(), "st_file_attributes", 0) & 0x400):
        raise ValueError("admitted namespace is a reparse point")
    root = root.resolve()
    if Path(output).resolve() != root:
        raise ValueError("output differs from admitted namespace")
    maximum = admission.get("maximum_logical_output_bytes")
    if type(maximum) is not int or maximum <= 0:
        raise ValueError("explicit positive logical capacity required")
    size, entries = 0, 0
    if root.exists():
        for directory, dirs, files in os.walk(root, followlinks=False):
            for entry in [Path(directory)] + [Path(directory) / name for name in dirs + files]:
                info = entry.lstat()
                if entry.is_symlink() or getattr(info, "st_file_attributes", 0) & 0x400:
                    raise ValueError("reparse point in scoring namespace")
                entries += 1
                if entries > 4096:
                    raise ValueError("scoring namespace entry cap exceeded")
            size += sum((Path(directory) / name).stat().st_size for name in files)
            if size > maximum:
                raise ValueError("scoring namespace logical capacity exceeded")
    return root, size, maximum


def write_new(path, data, cap=4 * 1024 * 1024, *, admission, machine_id):
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    if len(encoded) > cap:
        raise ValueError("bounded scoring metadata cap exceeded")
    root, used, maximum = validate_admission(admission, path.parent, machine_id)
    if path.resolve().parent != root or path.suffix not in admission.get("allowed_extensions", []):
        raise ValueError("output name/extension outside admission")
    if used + len(encoded) > maximum:
        raise ValueError("new output would exceed namespace logical capacity")
    with path.open("xb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    validate_admission(admission, root, machine_id)
    return {"path": str(path), "bytes": len(encoded), "sha256": hashlib.sha256(encoded).hexdigest()}


def emit(data):
    print(json.dumps(data, ensure_ascii=False), flush=True)


def lower_priority():
    if os.name == "nt":
        import ctypes
        from ctypes import wintypes as W
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.GetCurrentProcess.restype = W.HANDLE
        k.SetPriorityClass.argtypes = [W.HANDLE, W.DWORD]
        if not k.SetPriorityClass(k.GetCurrentProcess(), 0x4000):
            raise ctypes.WinError(ctypes.get_last_error())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--permanent-receipt", type=Path, required=True)
    parser.add_argument("--baseline-save", type=Path, required=True)
    parser.add_argument("--baseline-receipt", type=Path, required=True)
    parser.add_argument("--decoder", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--metadata-admission", type=Path, required=True)
    parser.add_argument("--machine-id", required=True)
    parser.add_argument("--actor", type=int, required=True)
    parser.add_argument("--founder", type=int, required=True)
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--attempt-id", default="01")
    static_args = parser.add_mutually_exclusive_group()
    static_args.add_argument("--game-dir", type=Path, help="Explicit CK3 game directory containing common/landed_titles")
    static_args.add_argument("--landed-titles-source", type=Path, action="append", help="Explicit effective definition file; repeat for multiple files")
    static_args.add_argument("--static-title-map", type=Path, help="Pinned small mapping for offline recalculation")
    args = parser.parse_args()
    if not args.attempt_id.isdigit() or len(args.attempt_id) > 3:
        raise ValueError("bounded numeric attempt id required")
    lower_priority()
    permanent, permanent_pin = reader.small_json(args.permanent_receipt)
    baseline_receipt, baseline_pin = reader.small_json(args.baseline_receipt)
    admission, admission_pin = reader.small_json(args.metadata_admission)
    if permanent.get("machine_id") != args.machine_id:
        raise ValueError("permanent source receipt machine mismatch")
    validate_admission(admission, args.output, args.machine_id)
    def save_new(path, data):
        return write_new(path, data, admission=admission, machine_id=args.machine_id)
    args.output.mkdir(exist_ok=True)
    if args.static_title_map:
        static, map_pin = reader.small_json(args.static_title_map, cap=2 * 1024 * 1024)
        if static.get("machine_id") != args.machine_id:
            raise ValueError("static map machine not verified for this execution")
        static["metadata_pin"] = map_pin
    else:
        paths = args.landed_titles_source or (sorted((args.game_dir / "common" / "landed_titles").glob("*.txt")) if args.game_dir else [])
        if args.game_dir and not paths:
            raise ValueError("explicit game directory has no landed title definitions")
        static = reader.landed_title_map(paths, machine_id=args.machine_id) if paths else {}
    for key in ("founding_house_id", "founding_dynasty_id", "founding_anchor_source", "baseline_counties"):
        static.pop(key, None)  # A reused geographic map cannot supply another campaign's anchors.
    save = Path(permanent["independent_SAVE"]["path"])
    expected = permanent["locked_copy_evidence"]["target_identity_after"]
    sources = [{"id": "current_save", "path": str(save), "bytes": expected["bytes"],
                "sha256": permanent["independent_SAVE"]["sha256"],
                "sha_basis": "prior_exact_locked_copy_receipt_not_rehashed",
                "machine_id": args.machine_id, "source_receipt": permanent_pin}]
    emit({"phase": "parsing_current", "body_sha_passes": 0})
    current, current_custody = reader.melt_projection(args.decoder, save, expected, {args.actor, args.founder})
    emit({"phase": "parsed_current", "record_counts": dict(current.root_counts), "metadata": current.metadata})
    # Save6 was immutable at creation. Preserve that historical claim separately
    # from newly observed file identity; no current hash is fabricated.
    def find_seed(value):
        if isinstance(value, dict):
            if value.get("path") and Path(str(value["path"])).name == args.baseline_save.name:
                return value
            for child in value.values():
                found = find_seed(child)
                if found:
                    return found
        if isinstance(value, list):
            for child in value:
                found = find_seed(child)
                if found:
                    return found
        return None
    seed = find_seed(baseline_receipt)
    if seed is None:
        raise ValueError("baseline original receipt does not identify seed")
    if Path(seed["path"]).resolve() != args.baseline_save.resolve():
        raise ValueError("baseline path differs from original seed receipt")
    expected_seed = {"bytes": seed.get("size", seed.get("bytes"))}
    sources.append({"id": "baseline_save", "path": str(args.baseline_save),
                    "bytes": expected_seed["bytes"], "sha256": seed.get("sha256"),
                    "sha_basis": "historical_immutable_seed_receipt_not_rehashed",
                    "historical_machine_id": "unknown", "machine_id": args.machine_id,
                    "source_receipt": baseline_pin})
    emit({"phase": "parsing_baseline", "body_sha_passes": 0})
    baseline, baseline_custody = reader.melt_projection(args.decoder, args.baseline_save, expected_seed, {args.founder})
    emit({"phase": "parsed_baseline", "record_counts": dict(baseline.root_counts), "metadata": baseline.metadata})
    now = reader.utc()
    for source in sources:
        source["observed_at_utc"] = now
    # Both worlds were streamed once. All later mapping/scoring is compact memory work.
    _, baseline_initial, _ = reader.project_metrics(baseline, actor=args.founder, founder=args.founder,
                                                   source_id="baseline_save", static_context=static)
    static["baseline_counties"] = baseline_initial["realm_counties"]
    static.update(founding_house_id=baseline_initial["founder_house_id"],
                  founding_dynasty_id=baseline_initial["dynasty_anchor_id"], founding_anchor_source="baseline_save")
    _, current_initial, _ = reader.project_metrics(current, actor=args.actor, founder=args.founder,
                                                  source_id="current_save", static_context=static)
    if static.get("county_baronies"):
        wanted_counties = {row["key"] for detail in (baseline_initial, current_initial)
                           for name in ("realm_counties", "dynasty_counties") for row in detail[name]}
        static["county_baronies"] = {key: rows for key, rows in static["county_baronies"].items() if key in wanted_counties}
        mapping_pin = save_new(args.output / f"static-title-map-{args.attempt_id}.json", static)
        static["metadata_pin"] = mapping_pin
    custody_pin = save_new(args.output / f"source-custody-{args.attempt_id}.json", {
        "machine_id": args.machine_id, "observed_at_utc": now,
        "current": current_custody, "baseline": baseline_custody,
        "metadata_admission": admission_pin, "melted_world_files_written": 0})

    def selected_inputs(obj, actor):
        _, detail, _ = reader.project_metrics(obj, actor=actor, founder=args.founder, source_id="pending", static_context=static)
        h0 = detail["founder_house_id"]
        house = obj.houses.get(h0, {})
        dynasty = detail["dynasty_anchor_id"]
        houses = {hid: row for hid, row in obj.houses.items()
                  if hid == h0 or (dynasty is not None and reader.integer(row.get("dynasty")) == dynasty)}
        selected_counties = {row["title_id"] for row in detail["realm_counties"]}
        selected_counties |= {identity for identity, row in obj.titles.items()
                              if str(row.get("key", "")).startswith("c_")
                              and obj.character_houses.get(reader.integer(row.get("holder"))) in houses}
        titles = {str(identity): row for identity, row in obj.titles.items() if identity in selected_counties}
        county_keys = {row["key"] for row in titles.values() if "key" in row}
        return {"summary": obj.summary(), "detail": detail, "dynasty_id": dynasty,
                "houses": {str(k): v for k, v in houses.items()}, "titles": titles,
                "county_states": {str(k): v for k, v in obj.counties.items()
                                  if k in county_keys or str(k) in {str(x) for x in selected_counties}},
                "holder_houses": {str(reader.integer(row.get("holder"))):
                                   obj.character_houses.get(reader.integer(row.get("holder")))
                                   for row in titles.values()}}

    selected_pin = save_new(args.output / f"selected-inputs-{args.attempt_id}.json", {
        "machine_id": args.machine_id, "observed_at_utc": now,
        "current": selected_inputs(current, args.actor),
        "baseline": selected_inputs(baseline, args.founder)})

    def inspect(command):
        obj = baseline if command.get("save") == "baseline" else current
        table = command.get("table")
        if table == "schema":
            return {"schema_fields": {k: sorted(v) for k, v in obj.schema_fields.items()},
                    "root_keys": obj.root_keys, "record_counts": dict(obj.root_counts)}
        tables = {"characters": obj.characters, "titles": obj.titles,
                  "counties": obj.counties, "provinces": obj.provinces,
                  "houses": obj.houses, "dynasties": obj.dynasties, "wars": obj.wars}
        if table not in tables:
            raise ValueError("unknown inspect table")
        data = tables[table]
        ids = command.get("ids")
        if ids is None:
            ids = list(data)[:min(int(command.get("limit", 2)), 5)]
        if len(ids) > 12:
            raise ValueError("bounded selection only")
        return {str(identity): data.get(identity, data.get(str(identity))) for identity in ids}

    def export():
        cm, detail, facts = reader.project_metrics(current, actor=args.actor, founder=args.founder, source_id="current_save", static_context=static)
        bm, bdetail, bfacts = reader.project_metrics(baseline, actor=args.founder, founder=args.founder, source_id="baseline_save", static_context=static)
        date = current.metadata.get("date") or current.metadata.get("meta_data.meta_date")
        snap = {"date": date, "actor_id": args.actor,
                "actor_name": current.characters.get(args.actor, {}).get("first_name"), "source_ref": "current_save",
                "T0": baseline.metadata.get("date") or baseline.metadata.get("meta_data.meta_date"),
                "strict_endpoint_verified": False}
        labels = {"gross_income": "月度总收入", "total_expenses": "月度总支出", "military_current": "当前月军费",
                  "military_all_raised": "全动员月军费", "due_commitments": "到期债务与承诺", "P_quality": "常规军质量当量",
                  "continuation_legal": "合法玩家后继", "backup_heirs": "合法备用继承人", "u_discretionary": "可支配经常收入",
                  "Q_realm": "领地品质", "K_dynasty": "宗族土地", "legacy_ranks": "宗族传承等级",
                  "control_average": "治理集合加权控制", "rebel_share": "本国叛乱份额", "gold": "现金"}
        unknown = [{"name": labels.get(key, key), "key": key, "reason_zh": row["unavailable_reason"]}
                   for key, row in cm.items() if row["availability"] == "unknown"]
        unknown += [{"name": "固定360个月历史", "key": "monthly_samples_360", "reason_zh": "未提供完整固定月度样本；不得由稀疏检查点插值。"}]
        report = scoring.build_report(cm, bm, snapshot=snap, sources=sources,
                                      facts=facts, machine_id=args.machine_id, observed_at_utc=reader.utc(),
                                      unknown_fields=unknown)
        report["input_custody"] = custody_pin
        report["scoring_detail"] = detail
        report["baseline_detail"] = bdetail
        detail_pin = save_new(args.output / f"projection-summary-{args.attempt_id}.json", {
            "machine_id": args.machine_id, "observed_at_utc": reader.utc(),
            "current": current.summary(), "baseline": baseline.summary(),
            "scoring_detail": detail, "baseline_detail": bdetail})
        result_pin = save_new(args.output / f"score-result-{args.attempt_id}.json", report)
        emit({"phase": "exported", "score": result_pin, "projection": detail_pin,
              "qualification": report["qualification"], "aggregate": report["aggregate"]})

    if args.interactive:
        emit({"phase": "ready_for_bounded_queries", "save_locks_released": True,
              "compact_projections_in_memory": True, "custody": custody_pin,
              "selected_inputs": selected_pin})
        for line in sys.stdin:
            try:
                command = json.loads(line)
                if command.get("action") == "export":
                    export()
                elif command.get("action") == "inspect":
                    emit(inspect(command))
                elif command.get("action") == "stop":
                    break
                else:
                    raise ValueError("unknown action")
            except Exception as error:
                emit({"command_error": str(error)})
    else:
        export()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

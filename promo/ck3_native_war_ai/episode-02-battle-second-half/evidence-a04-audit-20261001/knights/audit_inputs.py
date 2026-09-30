from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
OUT = Path("C:/Users/1/ck3-a04-mechanism-evidence-20261001/knights-attempt-02")
OUT.mkdir(parents=True, exist_ok=True)
FIXED = Path("C:/w/ep2a04")
PROJECT = FIXED / "promo/ck3_native_war_ai/episode-02-battle-second-half/project"
RUN = Path("C:/Users/1/AppData/Local/ck3-review-render/episode02-review-20260930-a04-a04")
RAW = Path("D:/workspace/ck3_native_war_ai_promo_work")
FACT = Path("C:/Users/1/ck3-video-vanilla-verification-20260930/attempt-a03/knight/facts-v1.json")
FULL = Path("C:/Users/1/ck3-video-vanilla-verification-20260930/attempt-a04/knight/full-knight-facts-v1.json")
DATA = FIXED / "ck3_autonomous_player/src/xar_autoplayer/simulation/data"

def read(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))

inventory = {}
def bind(p, expected=None):
    p = Path(p)
    key = str(p).replace("\\", "/")
    if key in inventory:
        if expected and inventory[key].get("sha256"):
            inventory[key].setdefault("expected_hashes", []).append(expected.upper())
            inventory[key]["matches_all_expected"] = all(x == inventory[key]["sha256"] for x in inventory[key]["expected_hashes"])
        return inventory[key]
    row = {"path": key, "exists": p.is_file()}
    if p.is_file():
        with p.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest().upper()
        row.update(bytes=p.stat().st_size, sha256=digest, sha_basis="independently_rehashed_local_bytes")
        if expected:
            row.update(expected_hashes=[expected.upper()], matches_all_expected=digest == expected.upper())
    inventory[key] = row
    return row

story_path = PROJECT / "review-story-a04-v2.json"
board_path = PROJECT / "review-story-a04-board-specs-v2.json"
project_edit_path = PROJECT / "review-story-a04-edit-v2.json"
story = read(story_path)
knights = next(c for c in story["chapters"] if c["id"] == "knights")
final_story = next(c for c in read(RUN / "sources/story.json")["chapters"] if c["id"] == "knights")
timeline = next(c for c in read(RUN / "timeline.json")["chapters"] if c["id"] == "knights")
edit = read(RUN / "edit.json")
boards = read(board_path)
project_edit = read(project_edit_path)
for p in (story_path, board_path, project_edit_path, RUN / "sources/story.json", RUN / "timeline.json", RUN / "edit.json", FACT, FULL,
          FIXED / "docs/ck3-native-ai/combat-phase-event-trace.md",
          FIXED / "promo/ck3_native_war_ai/episode-02-battle-second-half/e2-05-a03-native-selector-death-stop-20260930.md"):
    bind(p)
for utterance in knights["utterances"]:
    for fact in utterance["facts"]:
        bind(fact["source_path"])
for ref in read(FACT)["source_refs"]:
    p = str(ref["path"])
    if p.startswith("D:/workspace/ck3_eternal_recurrence/"):
        p = str(FIXED / p.removeprefix("D:/workspace/ck3_eternal_recurrence/"))
    bind(p, ref.get("expected_sha256") or ref.get("sha256"))

# Keep historical attempts separate. Only their public, relevant raw responses,
# read-only captures and immutable save products are inventoried here.
attempt_names = [
    "episode01-day05-wound-growth-attempt-039",
    "episode01-day06-maim-next-input-attempt-040",
    "episode01-day26-knight-selector-attempt-020",
    "episode01-day26-random-list-type-attempt-036",
    "episode01-day27-next-input-attempt-038",
    "episode01-day26-runtime-weight-attempt-070",
]
captures = []
for name in attempt_names:
    p = RAW / name
    for f in (p / "ck3-output/interactive-requests-responses").glob("*.json"):
        if f.name != "service.json":
            bind(f)
    for filename in ("one-day-summary.json", "next-input-summary.json", "launch-argv.json", "ck3-output/capture-report.json", "ck3-output/session-result.json"):
        f = p / filename
        if f.is_file():
            meta = bind(f)
            if filename == "ck3-output/capture-report.json":
                val = read(f)
                captures.append({"attempt": name, "binding": meta,
                                 "raw_video": val.get("raw_video"), "clean_spans": val.get("clean_spans"),
                                 "recording": val.get("recording"),
                                 "checkpoint_source": val.get("checkpoint_source"),
                                 "environment_session_complete": val.get("environment_session_complete")})
    for filename in ("d26-episode-seed-immutable.ck3", "d27-postevent-immutable.ck3", "d26-episode-seed-melted.ck3", "d27-postevent-melted.ck3", "d06-postevent-immutable.ck3", "d05-replay-source-melted.ck3", "d06-melted.ck3"):
        f = p / filename
        if f.is_file():
            bind(f)

ui_map_path = Path("C:/Users/1/AppData/Local/ck3-review-analysis/episode02-20260930-a03/ui-knights/knights-ui-edit-map.json")
ui_map = read(ui_map_path)
ui = []
for f in ui_map["frames"]:
    original = bind(f["original_frame_path"], f["png_sha256"])
    copy = bind(f["copied_frame_path"], f["png_sha256"])
    ui.append({"frame_id": f["id"], "source_id": f["source_id"], "binding": copy,
               "original_binding": original, "visible_values": f["visible_values"],
               "raw_pts_seconds": f["raw_pts_seconds"],
               "review": "Directly visually reviewed at original 2560x1440 via view_image on 2026-10-01; values and distinct source labels agree; no CharacterID inferred."})
raw_video_provenance = []
for key, source in ui_map["sources"].items():
    p = Path(source["raw_path"])
    raw_video_provenance.append({"source_id": key, "path": str(p).replace("\\", "/"), "exists": p.is_file(),
                                 "bytes": p.stat().st_size if p.is_file() else None,
                                 "sha256": source["raw_sha256"],
                                 "sha_basis": source["sha_basis"], "independently_rehashed_this_audit": False})
current = RAW / "episode02-e2-05-d26-live-20260929-a02"
current_trace = current / "ck3-output/interactive-requests-responses/e2-05-d26-trace-finish.json"
bind(current_trace, "BFF0A9CFCE858C88B9FEA67D0FB646CDB7175BA7DC957898769BE02D5479C7D0")
ct = read(current_trace)["body"]["managed_trace"]["trace"]
current_summary = {"trace_status": ct.get("status"), "failure_flags": ct.get("failure_flags"),
                   "knight_selects_key_present": "knight_selects" in ct,
                   "records": [{"index": n, "boundary": r.get("boundary"),
                                "capture_failure_flags": r.get("capture_failure_flags"),
                                "target_rows": [v for v in r.get("characters", []) if v.get("character_id") == 33437]}
                               for n, r in enumerate(ct["records"])],
                   "postframe_character_status": "UNKNOWN",
                   "unknown_reason": "No target row at failed final boundary; six earlier markers false do not establish d27 saved/later state; no selector rows; historical attempts cannot fill this."}

reprojection = []
for module, args, output in [
    ("project_native_knight_maim_next_input", (RAW / attempt_names[0], RAW / attempt_names[1], DATA / "ck3_1_19_0_6_episode01_messina_knight_maim_replay_v3.json"), DATA / "ck3_1_19_0_6_episode01_messina_knight_maim_next_input.json"),
    ("project_native_knight_kill_next_input", (RAW / attempt_names[3], RAW / attempt_names[4]), DATA / "ck3_1_19_0_6_episode01_messina_knight_kill_next_input_v1.json"),
    ("project_native_knight_selector_receipt", (RAW / attempt_names[2],), DATA / "ck3_1_19_0_6_episode01_messina_knight_selector_native_parity.json"),
]:
    src = FIXED / "ck3_autonomous_player/tools" / (module + ".py")
    meta = bind(src)
    try:
        spec = importlib.util.spec_from_file_location(module, src)
        obj = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(obj)
        func = getattr(obj, "build", None) or obj.project
        val = func(*args)
        result = {"module": meta, "result": "MATCH" if val == read(output) else "MISMATCH", "frozen_output": bind(output)}
        reprojection.append(result)
        with (OUT / (module + "-reprojection.json")).open("x", encoding="utf-8") as stream:
            json.dump(val, stream, ensure_ascii=False, indent=2)
    except Exception as exc:
        reprojection.append({"module": meta, "result": "ENVIRONMENT_OR_REPROJECTION_ERROR", "error": repr(exc)})

per_line = []
for index, u in enumerate(knights["utterances"]):
    key = "knights-" + u["id"]
    item = edit["utterances"][key]
    display = item.get("still_alternative", item)
    if item["kind"] == "raw-excerpt":
        p = Path(item["image"])
        actual_visual = {**item["source_binding"], "exists": p.is_file(),
                         "observed_bytes": p.stat().st_size if p.is_file() else None,
                         "sha_basis": "frozen full raw SHA in source binding; size checked; not independently rehashed in this attempt"}
    else:
        actual_visual = bind(item["image"], item.get("rendered_image", {}).get("sha256"))
    image_meta = bind(display["image"], display.get("rendered_image", {}).get("sha256"))
    spec_sources = [bind(display["spec"]["source_image"])]
    for extra in display["spec"].get("extra_ui", []):
        spec_sources.append(bind(extra["image"]))
    t = timeline["utterances"][index]
    per_line.append({"key": key, "zh": u["zh"], "facts": u["facts"],
                     "source_metadata": [bind(f["source_path"]) for f in u["facts"]],
                     "final_story_zh_matches": final_story["utterances"][index]["zh"] == u["zh"],
                     "timeline_zh_matches": t["zh"] == u["zh"],
                     "timeline_facts_match": t["facts"] == u["facts"],
                     "global_start_seconds": t["global_start"], "duration_seconds": t["duration"],
                     "board_spec_matches_final_edit": display["spec"] == boards["utterances"][key],
                     "project_edit_matches_final_edit": project_edit["utterances"].get(key) == item,
                     "actual_visual_kind": item["kind"], "actual_visual_binding": actual_visual,
                     "raw_start_seconds": item.get("start"), "raw_duration_seconds": item.get("source_duration"),
                     "rendered_card_or_unused_still_alternative": image_meta, "card_source_kind": display["source_kind"],
                     "card_case": item["case"], "card_spec": display["spec"], "card_source_bindings": spec_sources})

report = {"schema": "ck3.a04.knights.input-audit.v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
          "read_only_source_audit": True, "ck3_launches": 0, "desktop_inputs": 0,
          "branch_policy": "codex/war-series-brown-gold-20261001; fixed a04 source; no master intake, no commit/push",
          "interpreter": {"path": sys.executable, "version": sys.version},
          "chapter_global_start": timeline["global_start"], "chapter_duration": timeline["duration"],
          "reprojection": reprojection, "current_a02": current_summary,
          "independent_ui_frames": ui, "raw_video_provenance": raw_video_provenance,
          "historical_capture_reports": captures, "utterances": per_line, "source_inventory": list(inventory.values())}
with (OUT / "input-audit.json").open("x", encoding="utf-8", newline="\n") as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps({"output": str(OUT / "input-audit.json"), "lines": len(per_line), "source_files": len(inventory),
                  "mismatched_expected_hashes": [p for p, v in inventory.items() if v.get("matches_all_expected") is False],
                  "reprojection": [{"module": r["module"]["path"], "result": r["result"], "error": r.get("error")} for r in reprojection],
                  "story_mismatches": [u["key"] for u in per_line if not u["timeline_zh_matches"] or not u["final_story_zh_matches"]]}, ensure_ascii=False, indent=2))

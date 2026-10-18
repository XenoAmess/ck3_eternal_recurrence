"""Verify only this small canonical package; never infer media or target-machine QA."""
from pathlib import Path
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parent

def need(ok, message):
    if not ok:
        raise ValueError(message)

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def pin(path):
    data = path.read_bytes()
    return len(data), hashlib.sha256(data).hexdigest()

def main():
    files = read(ROOT / "PACKAGE-FILES.json")
    need(files.get("schema") == "xar.e04.review02-full69-small-package-files.v1", "wrong package schema")
    records = files.get("files")
    need(isinstance(records, list) and len(records) >= 10, "small package manifest incomplete")
    names = set()
    for item in records:
        name = item["relative_path"]
        need(name not in names, "duplicate package path")
        names.add(name)
        path = (ROOT / name).resolve()
        need(path.is_relative_to(ROOT.resolve()) and path.is_file() and not path.is_symlink(), "package path missing or escaped: " + name)
        need(pin(path) == (item["bytes"], item["sha256"]), "package bytes changed: " + name)
    binding = read(ROOT / "project-binding.json")
    mapping = read(ROOT / "encoded-segment-map.json")
    delivery = read(ROOT / "evidence/ROOT-DELIVERY.final-a02.json")
    qa = read(ROOT / "evidence/AUTO-MEDIA-CHECK.actual-a03.json")
    visual = read(ROOT / "evidence/VISUAL-SAMPLES.actual-a02.json")
    closed = read(ROOT / "evidence/MEDIA-PURPOSE-CLOSED.actual-a02.json")
    original = read(ROOT / "evidence/original-full69-run-manifest.machine-bound.json")
    current = read(ROOT / "evidence/typography-a02-run-manifest.machine-bound.json")
    index = read(ROOT / "evidence/source-index.machine-bound.json")
    machine = "desktop-3fevhd2-1c74096080"
    need(binding["source_machine_id"] == machine, "binding source machine differs")
    need(all(doc["machine_id"] == machine for doc in (delivery, qa, visual, closed, index)),
         "evidence source machine differs")
    need(binding["cue_count"] == mapping["cue_count"] == delivery["cue_count"] == 69, "cue count differs")
    need(binding["duration_frames"] == mapping["duration_frames"] == qa["frame_count"] == 58406,
         "frame count differs")
    need(mapping["movie_sha256"] == qa["native_deliverable"]["sha256"] == delivery["native_deliverable_cas"]["sha256"]
         == visual["movie_sha256"] == closed["native_deliverable"]["sha256"], "movie identity differs")
    rows = mapping["cues"]
    need(len(rows) == 69 and len({r["cue_id"] for r in rows}) == 69, "cue map order/uniqueness differs")
    need(sum(r["duration_frames"] for r in rows) == 58406, "cue map frame sum differs")
    current_by = {a["id"]: a for a in current["artifacts"]}
    original_by = {a["id"]: a for a in original["artifacts"]}
    reused = 0
    changed = []
    for row in rows:
        key = row["cue_id"]
        old = row["original_encoded_segment"]
        new = row["actual_encoded_segment"]
        old_artifact = original_by["segment." + key]
        new_artifact = current_by["segment." + key]
        need((old["bytes"], old["sha256"]) == (old_artifact["bytes"], old_artifact["sha256"].lower()),
             "old segment pin differs: " + key)
        need((new["bytes"], new["sha256"]) == (new_artifact["bytes"], new_artifact["sha256"].lower()),
             "new segment pin differs: " + key)
        exact = old == new
        need(exact is row["exact_encoded_reuse"], "reuse flag differs: " + key)
        if exact:
            reused += 1
        else:
            changed.append(key)
    need(reused == 66 and changed == ["C05-09", "C05-10", "C05-14"], "66/3 source selection differs")
    need(index["unchanged_segment_reuse_count"] == reused and index["new_render_count"] == len(changed),
         "machine-bound index scope differs")
    need(qa["status"].startswith("GREEN_AUTOMATED_MEDIA_ONLY")
         and visual["status"] == "AI_THREE_SAMPLE_PASS_PENDING_HUMAN_1X"
         and closed["status"] == "PURPOSE_CLOSED_MEDIA_WRITES_STOPPED", "review status differs")
    need(delivery["full_human_1x_review"] is False and delivery["signoff"] is False
         and delivery["formal_dynamic_credit"] == 0 and delivery["pending_key_footage_cues"] == 45,
         "method-review boundary differs")
    print(json.dumps({"status": "SMALL_CANONICAL_PACKAGE_PASS_NOT_MEDIA_QA", "machine_id": machine,
                      "files": len(records), "cues": len(rows), "exact_reuse": reused,
                      "changed": changed, "movie_sha256": mapping["movie_sha256"]}, ensure_ascii=False))

if __name__ == "__main__":
    main()

"""Audit every R6 narration cue and generated subtitle before final rendering."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from war_ai_promo.captions import caption_cues


Q = 100_000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("production_inputs", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected-cues", type=int, choices=(32, 33), default=32)
    args = parser.parse_args()
    data = json.loads(args.production_inputs.read_text(encoding="utf-8"))
    rows = data["cues"]
    errors = []
    metrics = {"cue_count": len(rows), "subtitle_blocks": 0, "longest_subtitle_seconds": 0,
               "longest_caption_characters": 0, "total_duration_seconds": data["actual_duration_seconds"]}
    if len(rows) != args.expected_cues or len({row["id"] for row in rows}) != args.expected_cues:
        errors.append("R6 cue count or uniqueness mismatch")
    for row in rows:
        if not row["zh"].strip() or not row["en"].strip():
            errors.append(row["id"] + ": missing bilingual copy")
        if any(term in row["zh"] for term in ("旧顺序", "旧乘法", "未完全确认")):
            errors.append(row["id"] + ": unrequested pilot or inconclusive phrasing")
        for cue in caption_cues(row):
            duration = cue.end_seconds - cue.start_seconds
            paragraph = row.get("subtitle_mode") == "paragraph"
            metrics["subtitle_blocks"] += 1
            metrics["longest_subtitle_seconds"] = max(metrics["longest_subtitle_seconds"], duration)
            metrics["longest_caption_characters"] = max(metrics["longest_caption_characters"], len(cue.text))
            if duration > (65.0 if paragraph else 15.0):
                errors.append(f"{row['id']} {cue.track_id} subtitle too long: {duration:.2f}s: {cue.text}")
            if (not paragraph and "\n" in cue.text) or "\\N" in cue.text or cue.text.count("\n") > 1:
                errors.append(f"{row['id']} {cue.track_id} unwanted line break")
            if not cue.text.strip():
                errors.append(f"{row['id']} {cue.track_id} empty subtitle")
    checks = {
        "M03_width_factor": 1_269 * Q // 2_324 == 54_604,
        "M05_advantage_factor": 145_000 * 3_000 // Q == 4_350,
        "M06_width_multiplier": 4_350 * 54_604 // Q == 2_375,
        "M07_side_one_damage": 2_375 * 4_911_382_134 // Q == 116_645_325,
        "M07_side_zero_damage": 3_000 * 413_810_144 // Q == 12_414_304,
        "C02_damage_share": 81_149_972 * Q // 122_225_074 == 66_393,
        "C02_loss_factor": 66_393 * Q // 1_000_000 == 6_639,
        "C02_levy_total": 6_282_657 * 6_639 // Q == 417_105,
        "C03_first_step": 19_705_044 * 81_149_972 // Q == 15_990_637_688,
        "C03_second_step": 15_990_637_688 * Q // 122_225_074 == 13_082_943,
        "C03_final_fixed_point": 13_082_943 * Q // 4_224_000 == 309_728,
        "C04_first_step": 99_111 * 81_149_972 // Q == 80_428_548,
        "C04_second_step": 80_428_548 * Q // 122_225_074 == 65_803,
        "C04_final_fixed_point": 65_803 * Q // 7_000_000 == 940,
        "C05_levy_hard": 417_105 * 36_000 // Q == 150_157,
        "C05_maa_hard": 309_728 * 36_000 // Q == 111_502,
        "C07_half_toughness": 13_082_943 * Q // 2_112_000 == 619_457,
        "C07_double_toughness": 13_082_943 * Q // 8_448_000 == 154_864,
        "pursuit_base": 1_400_000_000 * 5_000 // Q == 70_000_000,
        "pursuit_minimum": 1_400_000_000 * 1_000 // Q == 14_000_000,
        "pursuit_net": 225_000_000 - 200_000_000 == 25_000_000,
        "pursuit_A_ratio": 25_000_000 * Q // 1_400_000_000 == 1_785,
        "pursuit_B_ratio": 70_000_000 * Q // 1_400_000_000 == 5_000,
        "pursuit_levy_A_budget": (60_000_000 * 1_785 // Q) // 3 == 357_000,
        "pursuit_levy_B_budget": (60_000_000 * 5_000 // Q) // 3 == 1_000_000,
        "pursuit_maa_A_budget": (40_000_000 * 1_785 // Q) // 3 == 238_000,
        "pursuit_maa_B_budget": (40_000_000 * 5_000 // Q) // 3 == 666_666,
        "pursuit_day_one_sum": 791_584 + 565_416 + 904_666 == 2_261_666,
    }
    for name, passed in checks.items():
        if not passed:
            errors.append(name)
    report = {"schema": "ck3-war-ai-r6-input-audit.v1", "state": "GREEN" if not errors else "RED",
              "metrics": metrics, "numeric_checks": checks, "errors": errors}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

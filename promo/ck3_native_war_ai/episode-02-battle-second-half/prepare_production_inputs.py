"""Preflight a real six-chapter assembly declaration and write a preserve plan.

The source files are read only. No game, recorder, FFmpeg, native run or human
approval is created here. Output, when requested, is a new external directory.
The official xar-promo ``start-run`` and ``preserve`` commands must consume the
plan in a later, separate attempt before the production composer can run.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

SRC = Path(__file__).resolve().parents[1] / "integration" / "src"
sys.path.insert(0, str(SRC))
from xar_promo.adapters.ck3.capture import load_capture_bundle  # noqa: E402
from war_ai_promo.episode_two_second_half import (  # noqa: E402
    CARD_REPLAYS, CHAPTER_CARDS, CHAPTER_IDS, HISTORICAL_PRIMARY,
    _bound_tts_sentences, _capture_audit_contract, _card_replays,
    _replay_primary, card_filename, script_chapters,
)
from war_ai_promo.episode_two_subtitle_contract import identity  # noqa: E402
from war_ai_promo.episode_two_pts_contract import validate_pts_span  # noqa: E402


def _json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _source(row: dict, label: str) -> tuple[Path, dict]:
    if not isinstance(row, dict) or not isinstance(row.get("source"), str):
        raise ValueError(f"{label} needs an explicit absolute source")
    path = Path(row["source"])
    if not path.is_absolute():
        raise ValueError(f"{label} source must be absolute")
    path = path.resolve(strict=True)
    if type(row.get("bytes")) is not int or row["bytes"] < 1:
        raise ValueError(f"{label} needs a positive original byte count")
    observed = identity(path)
    if observed != {"bytes": row.get("bytes"), "sha256": str(row.get("sha256", "")).upper()}:
        raise ValueError(f"{label} source bytes/SHA differ")
    return path, {"source": str(path), **observed}


def _item(artifact_id: str, row: dict, role: str) -> tuple[Path, dict]:
    path, bound = _source(row, artifact_id)
    return path, {"artifact_id": artifact_id, **bound, "collection": "raw", "role": role}


def _positive_duration(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        raise ValueError(f"{label} needs a positive finite duration")
    return float(value)


def _subtitle_sources(declaration: dict, script: Path, config: Path) -> tuple[list[dict], list[dict]]:
    fragments_path, _ = _source(declaration["subtitle_fragments"], "subtitle fragments")
    plan_path, _ = _source(declaration["subtitle_preserve_plan"], "subtitle preserve plan")
    fragments, plan = _json(fragments_path), _json(plan_path)
    if (fragments.get("schema") != "ck3-war-ai.episode02.subtitle-input-fragments.v1"
            or fragments.get("status") != "machine-source-checked-not-human-reviewed"
            or plan.get("schema") != "ck3-war-ai.episode02.subtitle-preserve-plan.v1"
            or plan.get("status") != "source-checked-not-preserved-in-assembly-run"
            or fragments.get("narration_script") != identity(script)
            or fragments.get("project_config") != identity(config)
            or plan.get("subtitle_fragments") != {"source": str(fragments_path), **identity(fragments_path)}
            or [row.get("id") for row in fragments.get("chapters", [])] != list(CHAPTER_IDS)):
        raise ValueError("Subtitle fragments/plan do not bind the frozen six-chapter script/config")
    group_source = fragments.get("source_groups", {})
    if (not isinstance(group_source, dict) or not isinstance(group_source.get("path"), str)
            or not Path(group_source["path"]).is_absolute()
            or identity(Path(group_source["path"]).resolve(strict=True)) !=
            {"bytes": group_source.get("bytes"),
             "sha256": str(group_source.get("sha256", "")).upper()}):
        raise ValueError("Subtitle group selection manifest changed")
    source_root = Path(declaration["subtitle_source_root"])
    if not source_root.is_absolute():
        raise ValueError("TTS source root must be absolute")
    source_root = source_root.resolve(strict=True)
    preflight_root = Path(source_root.anchor)
    a05_fact_source = (Path(declaration["card_index"]["source"]).resolve(strict=True).parent /
                       "e2-09-a05-writer-facts-20260928.json").resolve(strict=True)
    source_rows = []
    namespace = []
    for row in plan.get("artifacts", []):
        artifact_id = row.get("artifact_id")
        path, bound = _source(row, f"TTS {artifact_id}")
        if artifact_id == "episode02-tts-a05-facts":
            if path != a05_fact_source or row.get("role") != "a05-writer-facts":
                raise ValueError("A05 TTS facts must use the indexed checked-in receipt")
        elif not path.is_relative_to(source_root):
            raise ValueError(f"TTS source escapes explicit source root: {artifact_id}")
        if not path.is_relative_to(preflight_root):
            raise ValueError(f"TTS source cannot be preflighted across volumes: {artifact_id}")
        source_rows.append({"artifact_id": artifact_id, **bound,
                            "collection": "raw", "role": row["role"]})
        namespace.append(SimpleNamespace(artifact_id=artifact_id, path=path.relative_to(preflight_root),
                                         bytes=bound["bytes"], sha256=bound["sha256"]))
    expected_tts_ids = {"episode02-tts-source-groups"}
    for row in fragments["chapters"]:
        chapter_id, source = row["id"], row["tts_source"]
        expected_tts_ids.update((f"audio.{chapter_id}", source["native_run_artifact_id"],
                                 source["render_manifest_artifact_id"]))
        if source.get("source_draft_artifact_id"):
            expected_tts_ids.add(source["source_draft_artifact_id"])
        if source.get("a05_facts_artifact_id"):
            expected_tts_ids.add(source["a05_facts_artifact_id"])
        for paragraph in source["paragraphs"]:
            expected_tts_ids.update((paragraph["request_artifact_id"],
                                     paragraph["events_artifact_id"]))
    if (len({row.artifact_id for row in namespace}) != len(namespace)
            or {row.artifact_id for row in namespace} != expected_tts_ids):
        raise ValueError("Episode 2 original TTS artifacts differ from six chapter declarations")
    by_id = {row.artifact_id: row for row in namespace}
    fake_run = SimpleNamespace(artifacts=tuple(namespace))
    fake_manifest = preflight_root / "__production_preflight_only__.json"
    narration = script_chapters(script)
    for row in fragments["chapters"]:
        audio = by_id.get(f"audio.{row['id']}")
        if (audio is None or audio.sha256 != row["audio_sha256"].upper()
                or audio.bytes != row["audio_bytes"]):
            raise ValueError(f"{row['id']} source audio is missing from the preserve plan")
        candidate = {**row, "zh": narration[row["id"]]}
        _bound_tts_sentences(fake_run, fake_manifest, candidate, script, config)
    return fragments["chapters"], source_rows


def _capture_source_gate(span: dict, extras: dict[str, tuple[Path, dict]],
                         reel_sha: str, duration: float) -> None:
    attempt = span.get("attempt_id", "")
    if not isinstance(attempt, str) or not attempt or attempt.startswith("SYNTHETIC-"):
        raise ValueError("Real capture needs a non-synthetic attempt ID")
    for key in ("cold_load_save_artifact_id", "raw_video_artifact_id", "control_artifact_id",
                "clean_span_receipt_artifact_id", "label_audit_artifact_id",
                "raw_video_pts_probe_artifact_id", "raw_video_recorder_final_artifact_id"):
        if span.get(key) not in extras:
            raise ValueError(f"{attempt} lacks preserved source {key}")
    for prefix in ("cold_load_save", "raw_video", "control"):
        row = extras[span[f"{prefix}_artifact_id"]][1]
        if (span.get(f"{prefix}_sha256", "").upper() != row["sha256"]
                or span.get(f"{prefix}_bytes") != row["bytes"]):
            raise ValueError(f"{attempt} {prefix} does not bind original bytes")
    width, height = span.get("raw_video_width"), span.get("raw_video_height")
    if (type(width) is not int or type(height) is not int or min(width, height) < 1
            or span.get("upscaled_to_reel") is not (width < 2560 or height < 1440)
            or span.get("resampled_to_reel") is not (width != 2560 or height != 1440)):
        raise ValueError(f"{attempt} raw capture dimension claim is inconsistent")
    checkpoint = span.get("midrun_checkpoint_save_artifact_id")
    if checkpoint is not None:
        if checkpoint not in extras:
            raise ValueError(f"{attempt} midrun checkpoint source missing")
        checkpoint_row = extras[checkpoint][1]
        if (span.get("midrun_checkpoint_save_sha256", "").upper() != checkpoint_row["sha256"]
                or span.get("midrun_checkpoint_save_bytes") != checkpoint_row["bytes"]):
            raise ValueError(f"{attempt} midrun checkpoint differs from original bytes")
    clean = _json(extras[span["clean_span_receipt_artifact_id"]][0])
    label = _json(extras[span["label_audit_artifact_id"]][0])
    if clean.get("result") != "GREEN":
        raise ValueError(f"{attempt} lacks a GREEN clean span; unreviewed raw is not admitted")
    frame_id = label.get("frame_artifact_id")
    if frame_id not in extras:
        raise ValueError(f"{attempt} source label lacks a preserved frame")
    frame_path, frame_row = extras[frame_id]
    if (label.get("frame_sha256", "").upper() != frame_row["sha256"]
            or label.get("frame_bytes") != frame_row["bytes"]):
        raise ValueError(f"{attempt} source label frame bytes differ")
    root = clean.get("capture_artifact_root")
    if not isinstance(root, str) or not Path(root).is_absolute():
        raise ValueError(f"{attempt} clean span lacks an absolute CK3 bundle root")
    bundle = load_capture_bundle(root, required_span_ids=[clean.get("span_id", "")])
    _capture_audit_contract(clean, label, span, reel_sha, duration, bundle, frame_path)
    probe_id = span["raw_video_pts_probe_artifact_id"]
    recorder_id = span["raw_video_recorder_final_artifact_id"]
    for field, artifact_id in (("raw_video_pts_probe", probe_id),
                               ("raw_video_recorder_final", recorder_id)):
        item = extras[artifact_id][1]
        if (span.get(f"{field}_sha256", "").upper() != item["sha256"]
                or span.get(f"{field}_bytes") != item["bytes"]):
            raise ValueError(f"{attempt} {field} differs from preserved source")
    source_span = bundle.clean_span(clean["span_id"])
    validate_pts_span(extras[span["raw_video_artifact_id"]][0],
                      extras[probe_id][0], extras[recorder_id][0],
                      source_span.begin_seconds, source_span.end_seconds,
                      verified_raw_identity=extras[span["raw_video_artifact_id"]][1])


def _reel_source_gate(chapter: str, row: dict, receipt: dict,
                      extras: dict[str, tuple[Path, dict]], card_replays: dict,
                      card_index: dict, card_sha: dict) -> None:
    if (receipt.get("schema") != "ck3-war-ai.episode02.chapter-reel.v1"
            or receipt.get("synthetic") is True
            or receipt.get("chapter_id") != chapter
            or receipt.get("media_sha256", "").upper() != row["reel_sha256"]
            or receipt.get("media_bytes") != row["reel_bytes"]
            or receipt.get("duration_seconds") != row["duration_seconds"]
            or receipt.get("reel_width") != 2560 or receipt.get("reel_height") != 1440
            or receipt.get("different_attempts_explicitly_labelled") is not True):
        raise ValueError(f"{chapter} reel receipt is not a real, source-bound 2560×1440 reel")
    cards = receipt.get("cards", {})
    if set(cards) != set(CHAPTER_CARDS.get(chapter, ())):
        raise ValueError(f"{chapter} cards do not match the frozen shot plan")
    spans = receipt.get("capture_spans")
    if not isinstance(spans, list) or not spans:
        raise ValueError(f"{chapter} has no source capture spans")
    for span in spans:
        _capture_source_gate(span, extras, row["reel_sha256"], row["duration_seconds"])
    for card_id, card in cards.items():
        replay = card_replays[card_id]
        source = card_index["replays"][replay]
        primary = _replay_primary(source)
        if (card.get("sha256", "").upper() != card_sha[card_id]
                or card.get("replay") != replay
                or card.get("primary_receipt_sha256", "").upper() != primary):
            raise ValueError(f"{chapter} card {card_id} does not bind its indexed replay")
        for field, indexed in (("indexed_cold_load_save_sha256", "source_save_sha256"),
                               ("indexed_midrun_checkpoint_save_sha256", "source_day27_checkpoint_sha256")):
            if indexed in source and card.get(field, "").upper() != source[indexed].upper():
                raise ValueError(f"{chapter} card {card_id} confuses source saves")
        if card.get("evidence_mode") == "historical_research_card":
            if primary != HISTORICAL_PRIMARY.get(replay):
                raise ValueError(f"{card_id} historical primary changed")
            label_id = card.get("visible_label_audit_artifact_id")
            if label_id not in extras:
                raise ValueError(f"{card_id} lacks a visible historical label audit")
            label = _json(extras[label_id][0])
            text = card.get("visible_label_text", "")
            if (label.get("schema") != "ck3-war-ai.episode02.card-label-audit.v1"
                    or label.get("status") != "visible" or label.get("card_id") != card_id
                    or label.get("reel_sha256", "").upper() != row["reel_sha256"]
                    or label.get("label_text") != text or replay not in text
                    or "历史研究" not in text or "非当前录制" not in text):
                raise ValueError(f"{card_id} historical source label is not visible/bound")
        elif card.get("evidence_mode") == "current_run_recomputed":
            if primary == HISTORICAL_PRIMARY.get(replay):
                raise ValueError(f"{card_id} old figures cannot be marked current")
            recompute_id = card.get("recomputed_receipt_artifact_id")
            if recompute_id not in extras:
                raise ValueError(f"{card_id} lacks recomputation receipt")
            recomputed = _json(extras[recompute_id][0])
            if (recomputed.get("schema") != "ck3-war-ai.episode02.recomputed-card.v1"
                    or recomputed.get("card_id") != card_id
                    or recomputed.get("card_sha256", "").upper() != card_sha[card_id]
                    or recomputed.get("source_primary_receipt_sha256", "").upper() != primary
                    or not any(span["attempt_id"] == recomputed.get("capture_attempt_id")
                               and span["cold_load_save_sha256"].upper() ==
                               recomputed.get("cold_load_save_sha256", "").upper()
                               for span in spans)):
                raise ValueError(f"{card_id} current card lacks same-attempt evidence")
        else:
            raise ValueError(f"{card_id} needs an explicit historical/current mode")


def prepare(declaration_path: Path) -> tuple[dict, list[dict], dict]:
    declaration_path = declaration_path.resolve(strict=True)
    declaration = _json(declaration_path)
    if (declaration.get("schema") != "ck3-war-ai.episode02.production-declaration.v1"
            or declaration.get("human_signoff") != "not-provided"
            or declaration.get("synthetic") is True):
        raise ValueError("Expected an unsigned, non-synthetic Episode 2 production declaration")
    config, config_binding = _source(declaration["project_config"], "ProjectConfig")
    script, script_binding = _source(declaration["narration_script"], "narration script")
    card_path, card_binding = _source(declaration["card_index"], "card index")
    config_data, card_data = _json(config), _json(card_path)
    if (config_data.get("project", {}).get("id") != "ck3-war-ai-battle-second-half"
            or [item["id"] for item in config_data.get("chapters", [])] != list(CHAPTER_IDS)):
        raise ValueError("Declaration ProjectConfig is not the six-chapter Episode 2 config")
    narration = script_chapters(script)
    replay_by_card = _card_replays(card_data)
    card_sources = declaration.get("cards", {})
    if set(card_sources) != set(CARD_REPLAYS):
        raise ValueError("Nine exact formal card SVG source bindings are required")
    cards = {}
    card_sha, card_bytes = {}, {}
    for card_id in CARD_REPLAYS:
        path, item = _item(f"episode02-card-{card_id}", card_sources[card_id], "source-calculation-card")
        expected = card_path.parent / card_filename(card_id)
        if path != expected.resolve(strict=True):
            raise ValueError(f"{card_id} must use the SVG beside the indexed card JSON")
        cards[card_id] = item
        card_sha[card_id], card_bytes[card_id] = item["sha256"], item["bytes"]
    fragments, tts_sources = _subtitle_sources(declaration, script, config)
    music_id = declaration["music"].get("artifact_id")
    if music_id != "episode02-series-theme":
        raise ValueError("Episode 2 needs the explicit single series theme artifact")
    _, music = _item(music_id, declaration["music"], "series-theme")
    extra_sources = {}
    for declared in declaration.get("source_artifacts", []):
        artifact_id = declared.get("artifact_id")
        if not isinstance(artifact_id, str) or not artifact_id or artifact_id in extra_sources:
            raise ValueError("Source dependency artifact IDs must be unique and nonempty")
        role = declared.get("role", "source-evidence")
        if not isinstance(role, str) or not role:
            raise ValueError(f"{artifact_id} needs a nonempty evidence role")
        path, item = _item(artifact_id, declared, role)
        extra_sources[artifact_id] = (path, item)
    chapters = declaration.get("chapters", [])
    if [item.get("id") for item in chapters] != list(CHAPTER_IDS):
        raise ValueError("Declaration needs six chapters in ProjectConfig order")
    production_rows = []
    reel_sources = []
    for index, (declared, subtitles) in enumerate(zip(chapters, fragments)):
        chapter = declared["id"]
        if (declared.get("title") != config_data["chapters"][index]["title"]["zh-CN"]
                or not isinstance(declared.get("en"), str) or not declared["en"].strip()):
            raise ValueError(f"{chapter} title/English text missing or differs from ProjectConfig")
        duration = _positive_duration(declared.get("duration_seconds"), chapter)
        if duration < subtitles["speech_duration_seconds"]:
            raise ValueError(f"{chapter} reel is shorter than source TTS")
        reel_path, reel = _item(f"reel.{chapter}", declared["reel"], "source-bound-chapter-reel")
        receipt_path, receipt_item = _item(f"reel-receipt.{chapter}", declared["reel_receipt"],
                                           "chapter-reel-receipt")
        row = {**subtitles, "title": declared["title"], "zh": narration[chapter],
               "en": declared["en"], "duration_seconds": declared["duration_seconds"],
               "audio_artifact_id": f"audio.{chapter}",
               "reel_artifact_id": reel["artifact_id"], "reel_sha256": reel["sha256"],
               "reel_bytes": reel["bytes"],
               "reel_receipt_artifact_id": receipt_item["artifact_id"],
               "reel_receipt_sha256": receipt_item["sha256"],
               "reel_receipt_bytes": receipt_item["bytes"]}
        receipt = _json(receipt_path)
        _reel_source_gate(chapter, row, receipt, extra_sources, replay_by_card, card_data, card_sha)
        production_rows.append(row)
        reel_sources.extend((reel, receipt_item))
    if len({str(Path(item["source"]).resolve()) for item in reel_sources[::2]}) != len(CHAPTER_IDS):
        raise ValueError("Each chapter needs its own reel source")
    required_extras = set()
    for declared in chapters:
        receipt = _json(Path(declared["reel_receipt"]["source"]))
        for span in receipt["capture_spans"]:
            required_extras.update(span[key] for key in (
                "cold_load_save_artifact_id", "raw_video_artifact_id", "control_artifact_id",
                "clean_span_receipt_artifact_id", "label_audit_artifact_id",
                "raw_video_pts_probe_artifact_id", "raw_video_recorder_final_artifact_id"))
            label = _json(extra_sources[span["label_audit_artifact_id"]][0])
            required_extras.add(label["frame_artifact_id"])
            if span.get("midrun_checkpoint_save_artifact_id"):
                required_extras.add(span["midrun_checkpoint_save_artifact_id"])
        for card in receipt["cards"].values():
            required_extras.add(card.get("visible_label_audit_artifact_id")
                                or card.get("recomputed_receipt_artifact_id"))
    if required_extras != set(extra_sources):
        raise ValueError("Source dependency list must match exactly the six reel receipts")
    plan = ([{"artifact_id": "episode02-narration-script", **script_binding,
              "collection": "raw", "role": "frozen-narration-script"},
             {"artifact_id": "episode02-card-index", **card_binding,
              "collection": "raw", "role": "frozen-calculation-card-index"}]
            + list(cards.values()) + tts_sources + [music]
            + [item for _, item in extra_sources.values()] + reel_sources)
    ids = [item["artifact_id"] for item in plan]
    if len(ids) != len(set(ids)):
        raise ValueError("Production preserve plan repeats an artifact ID")
    production = {
        "schema": "ck3-war-ai.episode02.production-inputs.v1",
        "human_signoff": "not-provided",
        "project_config_sha256": config_binding["sha256"],
        "project_config_bytes": config_binding["bytes"],
        "narration_script_sha256": script_binding["sha256"],
        "narration_script_bytes": script_binding["bytes"],
        "card_index_sha256": card_binding["sha256"],
        "card_index_bytes": card_binding["bytes"],
        "card_sha256": card_sha, "card_bytes": card_bytes,
        "replay_by_card": replay_by_card,
        "music_artifact_id": music_id,
        "music_sha256": music["sha256"], "music_bytes": music["bytes"],
        "chapters": production_rows,
    }
    audit = {"schema": "ck3-war-ai.episode02.production-source-audit.v1",
             "status": "source-preflight-passed-not-preserved-or-human-reviewed",
             "declaration": {"source": str(declaration_path), **identity(declaration_path)},
             "project_config": config_binding,
             "chapters": list(CHAPTER_IDS), "tts_artifacts": len(tts_sources),
             "reel_count": len(reel_sources) // 2,
             "source_dependencies": len(extra_sources), "all_original_bytes_checked": True,
             "native_run_preservation": "not-performed", "video_build": "not-performed",
             "human_signoff": "not-provided"}
    return production, plan, audit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--declaration", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path,
                        help="New absolute external attempt; omit for read-only preflight")
    args = parser.parse_args()
    production, plan, audit = prepare(args.declaration)
    if args.output_directory is None:
        print(json.dumps(audit, ensure_ascii=False, indent=2))
        return
    root = args.output_directory
    if not root.is_absolute() or root.exists():
        raise ValueError("Output must be a new absolute directory outside the project worktree")
    resolved = root.resolve()
    if any((parent / ".git").exists() for parent in (resolved, *resolved.parents)):
        raise ValueError("Output must be a new absolute directory outside the project worktree")
    root.mkdir(parents=True, exist_ok=False)
    production_path = root / "production-inputs.json"
    with production_path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(production, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    full_plan = {"schema": "ck3-war-ai.episode02.production-preserve-plan.v1",
                 "status": "source-checked-not-preserved-in-native-run",
                 "project_config": audit["project_config"],
                 "artifacts": plan + [{"artifact_id": "episode02-production-inputs-v1",
                                       "source": str(production_path), **identity(production_path),
                                       "collection": "derived", "role": "production-inputs"}]}
    for name, value in (("preserve-plan.json", full_plan), ("source-audit.json", audit)):
        with (root / name).open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
    print(json.dumps({"status": audit["status"], "output": str(root),
                      "artifacts": len(full_plan["artifacts"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()

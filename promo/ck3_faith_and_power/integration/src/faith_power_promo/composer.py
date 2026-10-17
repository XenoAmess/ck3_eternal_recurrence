"""A plan-only PipelineComposer for future measured, preserved real footage.

This initial integration has no qualified media renderer. Missing footage or
audio fails explicitly; a ProjectConfig/authoring run never receives invented
segments, duration, generated-card substitutes, or a production PASS.
"""
from pathlib import Path

from xar_promo.pipeline import PipelineDependencies, PipelineDraft, PipelineInvocation, SegmentDraft
from xar_promo.render import RenderOptions
from xar_promo.sources import VIDEO, VisualSource

from .evidence import binding, load


def _not_qualified(*args, **kwargs):
    raise ValueError("Faith/power media build is not qualified: only source planning is implemented")


def _artifact(run, run_path, identifier):
    if run is None or run_path is None:
        raise ValueError("No native run; use build_evidence_index for the unbound source-only pilot plan")
    records = [row for row in run.artifacts if row.artifact_id == identifier]
    if len(records) != 1:
        raise ValueError(f"Missing one preserved production input: {identifier}; no media/timing is assumed")
    record = records[0]
    path = (Path(run_path).parent / record.path).resolve()
    observed = binding(path)
    if observed["bytes"] != record.bytes or observed["sha256"] != record.sha256.lower():
        raise ValueError(f"Preserved input bytes differ: {identifier}")
    return path


def _preserved_binding(run, run_path, declared):
    """Resolve by content, requiring the evidence bytes to exist in this run."""
    matches = [row for row in run.artifacts
               if row.bytes == declared["bytes"] and row.sha256.lower() == declared["sha256"].lower()]
    if not matches:
        raise ValueError(f"Evidence was not preserved in this run: {declared['path']}")
    return _artifact(run, run_path, matches[0].artifact_id)


def _check_index_files(value, run, run_path):
    if isinstance(value, dict):
        if set(value) == {"path", "bytes", "sha256"}:
            _preserved_binding(run, run_path, value)
        else:
            for child in value.values():
                _check_index_files(child, run, run_path)
    elif isinstance(value, list):
        for child in value:
            _check_index_files(child, run, run_path)


def compose(config, run, *, config_path, run_path, workdir, adapter_factory,
            preset_factory, validate_only):
    """Implement xar_promo.pipeline.PipelineComposer's installed v0.3.0 ABI.

    A future plan can consume a measured input artifact and a complete,
    byte-preserved evidence index. No build is enabled by this implementation.
    """
    del config_path
    if not validate_only:
        _not_qualified()
    adapter, preset = adapter_factory(), preset_factory()
    if (config.project_id != "ck3-faith-and-power" or adapter["id"] != config.adapter
            or preset["id"] != config.preset):
        raise ValueError("Faith/power project components do not match")
    inputs = load(_artifact(run, run_path, "faith-production-inputs-v1"))
    if inputs.get("schema") != "ck3-faith-power-production-inputs-v1":
        raise ValueError("Unknown measured production-input schema")
    index = load(_artifact(run, run_path, inputs["evidence_index_artifact_id"]))
    if index.get("schema") != "ck3-faith-power-evidence-index-v1":
        raise ValueError("Unknown religious evidence-index schema")
    _check_index_files(index, run, run_path)
    chains = {row["chain_id"]: row for row in index["chains"]}
    cues = inputs.get("cues", [])
    if not cues or len({row["id"] for row in cues}) != len(cues):
        raise ValueError("Expected nonempty, unique measured narration cues")
    segments = []
    for cue in cues:
        chain = chains[cue["chain_id"]]
        if (not set(cue["claim_ids"]).issubset(chain["claim_ids"])
                or not set(cue["shot_ids"]).issubset(chain["shot_ids"])):
            raise ValueError("Cue claim/shot mapping does not match its capture chain")
        clip = _artifact(run, run_path, cue["prepared_clip_artifact_id"])
        receipt = load(_artifact(run, run_path, cue["clip_receipt_artifact_id"]))
        if (receipt.get("schema") != "ck3-faith-power-prepared-capture-clip-v1"
                or receipt.get("chain_id") != chain["chain_id"]
                or receipt.get("raw_sha256", "").lower() != chain["raw"]["sha256"].lower()):
            raise ValueError("Prepared clip does not bind this native/raw evidence chain")
        if (receipt.get("playback_speed") != 1 or receipt.get("fps") != preset["fps"]
                or any(receipt.get(key) is not False for key in ("interpolation", "looping", "tail_padding"))):
            raise ValueError("Clip needs a measured 1x/no-interpolation/no-loop/no-padding receipt")
        declared = receipt["prepared_media"]
        actual = binding(clip)
        if actual["bytes"] != declared["bytes"] or actual["sha256"] != declared["sha256"].lower():
            raise ValueError("Prepared clip bytes differ from its receipt")
        duration = cue["duration_seconds"]
        if (not 0 < cue["speech_duration_seconds"] <= duration
                or abs(receipt["duration_seconds"] - duration) > 0.000001):
            raise ValueError("Measured speech and real clip duration do not cover the same cue")
        audio = _artifact(run, run_path, cue["audio_artifact_id"])
        _artifact(run, run_path, cue["subtitle_ass_artifact_id"])
        segments.append(SegmentDraft(
            segment_id=cue["id"],
            visual_source=VisualSource(cue["id"], VIDEO, clip, "ck3-existing-clean-capture",
                                       metadata={"chain_id": chain["chain_id"],
                                                 "business_result_verified": False}),
            render_options=RenderOptions(preset["width"], preset["height"], preset["fps"], duration),
            subtitles={"zh-CN": cue["zh"], "en": cue["en"]},
            prepared_narration=audio,
        ))
    return PipelineInvocation(
        PipelineDraft(config, tuple(segments), Path("faith-power-pilot.mp4"),
                      "faith-power-pilot-candidate", "video/mp4"),
        PipelineDependencies("ffmpeg", _not_qualified, _not_qualified, _not_qualified),
        Path(workdir),
    )

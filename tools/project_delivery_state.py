from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs/project-state/current-state.source.json"
DEFAULT_CURRENT = ROOT / "docs/project-state/current-state.json"
DEFAULT_P2_LEDGER = ROOT / "docs/phase2-promo/p2-stage-ledger.json"
DEFAULT_RED_INDEX_DIR = ROOT / "docs/project-state/red-indexes"

CURRENT_SCHEMA = "xar.project-delivery-state"
SOURCE_SCHEMA = "xar.project-delivery-state-source"
P2_SCHEMA = "xar.phase2-promo-stage-ledger"
RED_INDEX_SCHEMA = "xar.compact-red-index"
PACKAGE_SCHEMA = "xar.work-package-resource-declaration"
SCHEMA_VERSION = 1

SHA256_RE = re.compile(r"^[0-9A-F]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
STAGE_RESULTS = frozenset({"GREEN", "PENDING", "RED"})
BUSINESS_RESULTS = frozenset({"GREEN", "RED", "NOT_EVALUATED"})
HARNESS_RESULTS = frozenset({"GREEN", "RED"})
LIFECYCLE_RESULTS = frozenset({"GREEN", "RED", "ACTIVE"})
RED_CLASSES = frozenset(
    {
        "PRODUCT_RED",
        "HARNESS_RED",
        "SCENARIO_RED",
        "ENVIRONMENT_RED",
        "CAPABILITY_RED",
    }
)
SOURCE_SPANS = (
    "phase2_promotion_compensation",
    "phase2_projects_metrics",
    "phase2_incidents_operations",
    "phase2_cross_cycle_endgame",
)
RAW_SPANS = (
    "phase2_fact_quota_calibration",
    "phase2_receipt_appeal_pip",
    "phase2_manager_governance",
    "phase2_promotion_compensation",
    "phase2_hc_workforce",
    "phase2_projects_metrics",
    "phase2_incidents_operations",
    "phase2_cross_cycle_endgame",
)
CUTS = ("character_led", "institution_led")
CUT_STAGES = (
    "source_review",
    "candidate",
    "automated_audit",
    "human_review_1x",
    "export",
    "publication",
)


class ProjectionError(ValueError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ProjectionError(message)


def _mapping(value: object, name: str) -> Mapping[str, Any]:
    _require(isinstance(value, Mapping), f"{name} must be an object")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"{path} must contain a JSON object")
    return value


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _json_bytes(value)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest().upper()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _validate_artifact_ref(value: object, name: str) -> dict[str, Any]:
    ref = dict(_mapping(value, name))
    _require(ref.get("base") in {"workspace_root", "repo_root"}, f"{name}.base invalid")
    locator = ref.get("locator")
    _require(isinstance(locator, str) and locator and Path(locator).is_absolute() is False,
             f"{name}.locator must be a relative path")
    _require(isinstance(ref.get("bytes"), int) and ref["bytes"] >= 0,
             f"{name}.bytes must be non-negative")
    _require(isinstance(ref.get("sha256"), str) and SHA256_RE.fullmatch(ref["sha256"]),
             f"{name}.sha256 must be uppercase SHA-256")
    return ref


def _resolve_artifact_ref(
    ref: Mapping[str, Any], *, repo_root: Path, workspace_root: Path
) -> Path:
    base = repo_root if ref["base"] == "repo_root" else workspace_root
    return base / str(ref["locator"])


def _verify_artifact_ref(
    ref: Mapping[str, Any], *, repo_root: Path, workspace_root: Path, name: str
) -> None:
    path = _resolve_artifact_ref(ref, repo_root=repo_root, workspace_root=workspace_root)
    _require(path.is_file(), f"{name} missing: {path}")
    _require(path.stat().st_size == ref["bytes"], f"{name} byte length changed: {path}")
    _require(_sha256_file(path) == ref["sha256"], f"{name} SHA-256 changed: {path}")


def artifact_ref(path: Path, *, base: str, root: Path) -> dict[str, Any]:
    resolved = path.resolve()
    relative = resolved.relative_to(root.resolve()).as_posix()
    return {
        "base": base,
        "locator": relative,
        "bytes": resolved.stat().st_size,
        "sha256": _sha256_file(resolved),
    }


def _validate_stage(value: object, name: str) -> dict[str, Any]:
    stage = dict(_mapping(value, name))
    _require(stage.get("status") in STAGE_RESULTS, f"{name}.status invalid")
    refs = stage.get("artifact_refs", [])
    _require(isinstance(refs, list), f"{name}.artifact_refs must be a list")
    stage["artifact_refs"] = [
        _validate_artifact_ref(ref, f"{name}.artifact_refs[{index}]")
        for index, ref in enumerate(refs)
    ]
    red_ids = stage.get("red_index_ids", [])
    _require(
        isinstance(red_ids, list)
        and all(isinstance(item, str) and item for item in red_ids),
        f"{name}.red_index_ids must be a string list",
    )
    stage["red_index_ids"] = list(red_ids)
    _require(
        stage["status"] != "RED" or bool(stage["red_index_ids"]),
        f"{name} RED must reference a compact RED index",
    )
    return stage


def _summary(stages: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    required = len(stages)
    passed = sum(stage["status"] == "GREEN" for stage in stages.values())
    red = sum(stage["status"] == "RED" for stage in stages.values())
    return {
        "result": "RED" if red else ("GREEN" if passed == required else "PENDING"),
        "passed": passed,
        "required": required,
        "red": red,
    }


def build_red_index(
    spec_value: object,
    *,
    repo_root: Path,
    workspace_root: Path,
    verify_artifacts: bool = False,
) -> dict[str, Any]:
    spec = dict(_mapping(spec_value, "red index spec"))
    red_id = spec.get("red_id")
    _require(isinstance(red_id, str) and red_id, "red index red_id missing")
    _require(spec.get("red_class") in RED_CLASSES, f"{red_id} red_class invalid")
    axes = dict(_mapping(spec.get("axes"), f"{red_id}.axes"))
    _require(axes.get("business_result") in BUSINESS_RESULTS, f"{red_id} business result invalid")
    _require(axes.get("harness_result") in HARNESS_RESULTS, f"{red_id} harness result invalid")
    _require(axes.get("lifecycle_result") in LIFECYCLE_RESULTS, f"{red_id} lifecycle result invalid")
    detail_ref = _validate_artifact_ref(spec.get("detail_artifact_ref"), f"{red_id}.detail_artifact_ref")
    if verify_artifacts:
        _verify_artifact_ref(
            detail_ref,
            repo_root=repo_root,
            workspace_root=workspace_root,
            name=f"{red_id}.detail_artifact_ref",
        )
    _require(isinstance(spec.get("input_attempted"), bool), f"{red_id}.input_attempted must be bool")
    _require(
        isinstance(spec.get("same_frame_retry_eligible"), bool),
        f"{red_id}.same_frame_retry_eligible must be bool",
    )
    deadline = spec.get("absolute_game_deadline")
    _require(deadline is None or (isinstance(deadline, int) and deadline >= 0),
             f"{red_id}.absolute_game_deadline invalid")
    minimal_diff = spec.get("minimal_diff")
    _require(isinstance(minimal_diff, Mapping) and minimal_diff,
             f"{red_id}.minimal_diff must be a non-empty object")
    result = {
        "schema": RED_INDEX_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "red_id": red_id,
        "result": "RED",
        "red_class": spec["red_class"],
        "axes": axes,
        "blocking_scope": spec.get("blocking_scope"),
        "failure_stage": spec.get("failure_stage"),
        "reason_code": spec.get("reason_code"),
        "last_verified_stage": spec.get("last_verified_stage"),
        "input_attempted": spec["input_attempted"],
        "same_frame_retry_eligible": spec["same_frame_retry_eligible"],
        "absolute_game_deadline": deadline,
        "binding": dict(_mapping(spec.get("binding", {}), f"{red_id}.binding")),
        "minimal_diff": dict(minimal_diff),
        "detail_artifact_ref": detail_ref,
        "resolution": dict(_mapping(spec.get("resolution", {}), f"{red_id}.resolution")),
        "preservation": {
            "detail_is_immutable": True,
            "classification_does_not_downgrade_red": True,
            "index_is_not_business_evidence": True,
        },
    }
    _require("product_result" not in result, "compact RED index must not publish product_result")
    _require(len(_json_bytes(result)) < 10 * 1024, f"{red_id} compact index exceeds 10 KiB")
    return result


def build_p2_ledger(
    source_value: object,
    *,
    red_index_refs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    source = dict(_mapping(source_value, "p2"))
    source_values = dict(_mapping(source.get("source_lineage"), "p2.source_lineage"))
    raw_values = dict(_mapping(source.get("raw_capture"), "p2.raw_capture"))
    _require(tuple(source_values) == SOURCE_SPANS, "p2.source_lineage keys/order must be canonical")
    _require(tuple(raw_values) == RAW_SPANS, "p2.raw_capture keys/order must be canonical")
    sources = {
        name: _validate_stage(value, f"p2.source_lineage.{name}")
        for name, value in source_values.items()
    }
    raw = {
        name: _validate_stage(value, f"p2.raw_capture.{name}")
        for name, value in raw_values.items()
    }
    shared_intake = _validate_stage(source.get("shared_intake"), "p2.shared_intake")
    tool_update = _validate_stage(source.get("tool_update"), "p2.tool_update")
    cuts_value = dict(_mapping(source.get("cuts"), "p2.cuts"))
    _require(tuple(cuts_value) == CUTS, "p2.cuts keys/order must be canonical")
    cuts: dict[str, Any] = {}
    for cut_name, raw_cut in cuts_value.items():
        cut = dict(_mapping(raw_cut, f"p2.cuts.{cut_name}"))
        expected_duration = 570 if cut_name == "character_led" else 580
        _require(
            cut.get("duration_seconds") == expected_duration,
            f"{cut_name} duration must remain {expected_duration} seconds",
        )
        stages_value = dict(_mapping(cut.get("stages"), f"p2.cuts.{cut_name}.stages"))
        _require(tuple(stages_value) == CUT_STAGES, f"{cut_name} stage keys/order must be canonical")
        stages = {
            name: _validate_stage(value, f"p2.cuts.{cut_name}.stages.{name}")
            for name, value in stages_value.items()
        }
        cuts[cut_name] = {
            "duration_seconds": cut.get("duration_seconds"),
            "stages": stages,
            "summary": _summary(stages),
        }
    known_red_ids = set(red_index_refs)

    def attach_red_refs(stage: dict[str, Any]) -> None:
        _require(set(stage["red_index_ids"]) <= known_red_ids, "unknown red_index_id")
        stage["red_index_refs"] = [
            {"red_id": red_id, "index_ref": red_index_refs[red_id]}
            for red_id in stage.pop("red_index_ids")
        ]

    attach_red_refs(tool_update)
    for group in (sources, raw):
        for stage in group.values():
            attach_red_refs(stage)
    for cut in cuts.values():
        for stage in cut["stages"].values():
            attach_red_refs(stage)
    attach_red_refs(shared_intake)
    source_summary = _summary(sources)
    raw_summary = _summary(raw)
    cut_stage_summaries = {
        stage: {
            "passed": sum(cut["stages"][stage]["status"] == "GREEN" for cut in cuts.values()),
            "required": 2,
        }
        for stage in CUT_STAGES
    }
    any_red = (
        source_summary["red"]
        or raw_summary["red"]
        or shared_intake["status"] == "RED"
        or any(cut["summary"]["red"] for cut in cuts.values())
    )
    all_published = cut_stage_summaries["publication"]["passed"] == 2
    return {
        "schema": P2_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "updated_at": source.get("updated_at"),
        "result": "RED" if any_red else ("GREEN" if all_published else "ACTIVE"),
        "p1_unlock": dict(_mapping(source.get("p1_unlock"), "p2.p1_unlock")),
        "tool_update": tool_update,
        "shared": {
            "source_lineage": {"summary": source_summary, "items": sources},
            "raw_capture": {"summary": raw_summary, "items": raw},
            "media_intake": shared_intake,
        },
        "cuts": cuts,
        "cut_stage_summaries": cut_stage_summaries,
        "invariants": {
            "source_lineage_is_not_raw_footage": True,
            "raw_intake_is_shared_once": True,
            "cut_source_reviews_are_independent": True,
            "cut_candidates_and_reviews_are_independent": True,
            "p2_does_not_reopen_p1": True,
        },
    }


def _validate_commit(value: object, name: str) -> str:
    _require(isinstance(value, str) and COMMIT_RE.fullmatch(value), f"{name} must be a full commit")
    return value


def build_current_state(
    source: Mapping[str, Any],
    *,
    p2_ledger: Mapping[str, Any],
    p2_ledger_ref: Mapping[str, Any],
    red_index_refs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    p1 = dict(_mapping(source.get("t0_p1"), "t0_p1"))
    _require(p1.get("result") == "GREEN", "current signed P1 must be GREEN")
    _require(isinstance(p1.get("passed"), int) and isinstance(p1.get("required"), int),
             "P1 counts must be integers")
    _require(p1["passed"] == p1["required"] == 9, "P1 signed count must remain 9/9")
    p1["gate_ref"] = _validate_artifact_ref(p1.get("gate_ref"), "t0_p1.gate_ref")
    repository = dict(_mapping(source.get("repository_provenance"), "repository_provenance"))
    root_tx = dict(_mapping(repository.get("root_last_completed_transaction"), "root transaction"))
    companion_tx = dict(_mapping(repository.get("t2_last_completed_transaction"), "T2 transaction"))
    _validate_commit(root_tx.get("commit"), "root transaction commit")
    _validate_commit(companion_tx.get("commit"), "T2 transaction commit")
    t1 = dict(_mapping(source.get("t1"), "t1"))
    _require(t1.get("percentage") is None, "T1 percentage must remain null without a fixed denominator")
    t2 = dict(_mapping(source.get("t2"), "t2"))
    _validate_commit(t2.get("upstream_root_commit"), "t2 upstream_root_commit")
    _validate_commit(t2.get("compat_commit"), "t2 compat_commit")
    live_red = dict(_mapping(source.get("live_red_source"), "live_red_source"))
    _require(live_red.get("git_cached") is False, "live RED must not be cached in Git")
    _require(live_red.get("active") is None, "stable projection must not cache a live RED")
    _require(live_red.get("unresolved_count") == 0, "current stable RED count must be zero")
    ck3 = dict(_mapping(source.get("ck3"), "ck3"))
    _require(ck3.get("live_state_not_git_cached") is True, "CK3 live state must not be Git cached")
    reporting = dict(_mapping(source.get("reporting"), "reporting"))
    return {
        "schema": CURRENT_SCHEMA,
        "schema_version": SCHEMA_VERSION,
        "updated_at": source.get("updated_at"),
        "status_semantics": "stable package projection; live CK3/RED/Git inventory comes from named sources",
        "repository_provenance": repository,
        "t0": {
            "priority": "T0",
            "p1": p1,
            "p2": {
                "result": p2_ledger["result"],
                "tool_update": p2_ledger["tool_update"]["status"],
                "source_lineage": p2_ledger["shared"]["source_lineage"]["summary"],
                "raw_footage": p2_ledger["shared"]["raw_capture"]["summary"],
                "cut_stage_summaries": p2_ledger["cut_stage_summaries"],
                "ledger_ref": dict(p2_ledger_ref),
            },
        },
        "t1": t1,
        "t2": t2,
        "red": {
            "current": None,
            "unresolved_count": 0,
            "live_source": {
                key: value
                for key, value in live_red.items()
                if key not in {"active", "unresolved_count"}
            },
            "preserved_indexes": [
                {
                    "red_id": red_id,
                    "role": "HISTORICAL_PRESERVED",
                    "index_ref": index_ref,
                }
                for red_id, index_ref in red_index_refs.items()
            ],
            "axes": {
                "business_result": sorted(BUSINESS_RESULTS),
                "harness_result": sorted(HARNESS_RESULTS),
                "lifecycle_result": sorted(LIFECYCLE_RESULTS),
            },
        },
        "ck3": ck3,
        "reporting": reporting,
    }


def validate_work_package_resource(value: object) -> dict[str, Any]:
    package = dict(_mapping(value, "work package"))
    _require(package.get("schema") == PACKAGE_SCHEMA, "work package schema invalid")
    _require(package.get("schema_version") == SCHEMA_VERSION, "work package schema version invalid")
    _require(package.get("priority") in {"T0", "T1", "T2"}, "work package priority invalid")
    for field in ("reads", "writes", "blocks"):
        value_list = package.get(field)
        _require(
            isinstance(value_list, list)
            and all(isinstance(item, str) and item for item in value_list),
            f"work package {field} must be a string list",
        )
    for field in (
        "requires_ck3",
        "requires_operator",
        "changes_product_tree",
        "changes_bridge",
        "triggers_open_kaishek",
    ):
        _require(isinstance(package.get(field), bool), f"work package {field} must be bool")
    writers = dict(_mapping(package.get("report_writers"), "work package report_writers"))
    _require(writers.get("daily") == "coordinator", "daily report must have coordinator as single writer")
    _require(writers.get("weekly") == "coordinator", "weekly report must have coordinator as single writer")
    _require(set(package["reads"]).isdisjoint(package["writes"]),
             "work package must not declare an identical path as read and write")
    return package


def render(
    *,
    source_path: Path,
    current_path: Path,
    p2_ledger_path: Path,
    red_index_dir: Path,
    workspace_root: Path,
    verify_artifacts: bool,
) -> dict[str, Any]:
    source = _load_json(source_path)
    _require(source.get("schema") == SOURCE_SCHEMA, "source schema invalid")
    _require(source.get("schema_version") == SCHEMA_VERSION, "source schema version invalid")
    red_specs = source.get("red_indexes")
    _require(isinstance(red_specs, list), "red_indexes must be a list")
    red_indexes: dict[str, dict[str, Any]] = {}
    red_paths: dict[str, Path] = {}
    for raw_spec in red_specs:
        spec = dict(_mapping(raw_spec, "red index spec"))
        index = build_red_index(
            spec,
            repo_root=ROOT,
            workspace_root=workspace_root,
            verify_artifacts=verify_artifacts,
        )
        red_id = str(index["red_id"])
        _require(red_id not in red_indexes, f"duplicate red_id: {red_id}")
        output_name = spec.get("output_name")
        _require(isinstance(output_name, str) and output_name.endswith(".json"),
                 f"{red_id}.output_name invalid")
        red_indexes[red_id] = index
        red_paths[red_id] = red_index_dir / output_name
    red_refs = {
        red_id: artifact_ref_from_bytes(path, _json_bytes(red_indexes[red_id]), root=ROOT)
        for red_id, path in red_paths.items()
    }
    p2_source = dict(_mapping(source.get("p2"), "p2"))
    p2_source["updated_at"] = source.get("updated_at")
    p2_ledger = build_p2_ledger(p2_source, red_index_refs=red_refs)
    p2_bytes = _json_bytes(p2_ledger)
    p2_ref = artifact_ref_from_bytes(p2_ledger_path, p2_bytes, root=ROOT)
    current = build_current_state(
        source,
        p2_ledger=p2_ledger,
        p2_ledger_ref=p2_ref,
        red_index_refs=red_refs,
    )
    if verify_artifacts:
        for name, p1_ref in (("t0_p1.gate_ref", current["t0"]["p1"]["gate_ref"]),):
            _verify_artifact_ref(
                p1_ref,
                repo_root=ROOT,
                workspace_root=workspace_root,
                name=name,
            )
        tool_refs = p2_ledger["tool_update"]["artifact_refs"]
        for index, ref in enumerate(tool_refs):
            _verify_artifact_ref(
                ref,
                repo_root=ROOT,
                workspace_root=workspace_root,
                name=f"p2.tool_update.artifact_refs[{index}]",
            )
        for group_name in ("source_lineage", "raw_capture"):
            items = p2_ledger["shared"][group_name]["items"]
            for item_name, item in items.items():
                for index, ref in enumerate(item["artifact_refs"]):
                    _verify_artifact_ref(
                        ref,
                        repo_root=ROOT,
                        workspace_root=workspace_root,
                        name=f"p2.{group_name}.{item_name}.artifact_refs[{index}]",
                    )
    for red_id, path in red_paths.items():
        _write_json_atomic(path, red_indexes[red_id])
    _write_json_atomic(p2_ledger_path, p2_ledger)
    _write_json_atomic(current_path, current)
    return {
        "result": "GREEN",
        "current_state": artifact_ref(current_path, base="repo_root", root=ROOT),
        "p2_stage_ledger": artifact_ref(p2_ledger_path, base="repo_root", root=ROOT),
        "red_indexes": [artifact_ref(path, base="repo_root", root=ROOT) for path in red_paths.values()],
    }


def artifact_ref_from_bytes(path: Path, payload: bytes, *, root: Path) -> dict[str, Any]:
    relative = path.resolve().relative_to(root.resolve()).as_posix()
    return {
        "base": "repo_root",
        "locator": relative,
        "bytes": len(payload),
        "sha256": _sha256_bytes(payload),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the canonical delivery-state projection")
    subparsers = parser.add_subparsers(dest="command", required=True)
    render_parser = subparsers.add_parser("render")
    render_parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    render_parser.add_argument("--current-state", type=Path, default=DEFAULT_CURRENT)
    render_parser.add_argument("--p2-ledger", type=Path, default=DEFAULT_P2_LEDGER)
    render_parser.add_argument("--red-index-dir", type=Path, default=DEFAULT_RED_INDEX_DIR)
    render_parser.add_argument("--workspace-root", type=Path, default=ROOT.parent)
    render_parser.add_argument("--verify-artifacts", action="store_true")
    package_parser = subparsers.add_parser("validate-package")
    package_parser.add_argument("package", type=Path)
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "render":
            result = render(
                source_path=args.source.resolve(),
                current_path=args.current_state.resolve(),
                p2_ledger_path=args.p2_ledger.resolve(),
                red_index_dir=args.red_index_dir.resolve(),
                workspace_root=args.workspace_root.resolve(),
                verify_artifacts=args.verify_artifacts,
            )
        else:
            validate_work_package_resource(_load_json(args.package.resolve()))
            result = {"result": "GREEN", "package": str(args.package.resolve())}
    except (OSError, json.JSONDecodeError, ProjectionError) as error:
        print(json.dumps({"result": "RED", "error": str(error)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

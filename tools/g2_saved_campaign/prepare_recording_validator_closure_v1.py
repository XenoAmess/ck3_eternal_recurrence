"""Project the one missing frozen validator dependency; never run Game/OBS."""
from __future__ import annotations
import ast
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

MACHINE_ID = "xenoamess-full-tower-eb9d2c1186"
HOST_HEAD = "d90d5e79ac7d22b3376ca70f3fccebd3faef516f"
VALIDATOR_SHA = "bf5552199a53bea1909fb8271873740b47b06e04f6856998005296b83b495151"
OLD_HOTFIX_SHA = "1aec2129c0206a41362ac9b872eed096c83c6c2a402374d175a6004779b20338"
NEW_HOTFIX_SHA = "393705ab38a78ce917aaa33548b7fe8da0c319c7f1c7f7a6e01edb9e5a042789"
CAPTURE_SHA = "89e7d416bc03863b50e17a4946e77bcc35207081677b7f4f7d34374f1c97efa5"
STD_IMPORTS = ["__future__", "hashlib", "json", "pathlib", "re", "uuid"]


def require(ok, why):
    if not ok:
        raise ValueError("validator dependency closure: " + why)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def pin(path, raw=None):
    path = Path(path).resolve()
    if raw is None:
        raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": digest(raw)}


def pythonpath_v1(value, frozen_host):
    """Keep the actual Task roots and explicitly bind the parent import root."""
    parts = value.split(os.pathsep)
    root = str((Path(frozen_host).resolve() / "tools"))
    parts = [p for p in parts if os.path.normcase(p) != os.path.normcase(root)]
    require(parts and all(Path(p).is_dir() for p in parts), "actual dependency root missing")
    parts.insert(1, root)
    require(Path(root).is_dir(), "frozen tools root missing")
    return os.pathsep.join(parts)


def project_v1(hotfix_raw, manifest_raw, *, runtime, frozen_host, validator_raw,
               observed_at_utc):
    """Pure projection: return two replacement byte strings and a small review."""
    runtime, host = Path(runtime).resolve(), Path(frozen_host).resolve()
    require(len(hotfix_raw) == 1355 and digest(hotfix_raw) == OLD_HOTFIX_SHA,
            "exact unamended hotfix required")
    require(len(validator_raw) == 8175 and digest(validator_raw) == VALIDATOR_SHA,
            "exact frozen validator required")
    imports = sorted({(n.module if isinstance(n, ast.ImportFrom) else a.name).split(".")[0]
                      for n in ast.walk(ast.parse(validator_raw))
                      if isinstance(n, (ast.Import, ast.ImportFrom))
                      for a in (n.names if isinstance(n, ast.Import) else [None])})
    require(imports == STD_IMPORTS, "validator import closure changed")
    tree = ast.parse(hotfix_raw)
    assigned = next(n.value for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "F" for t in n.targets))
    require(Path(ast.literal_eval(assigned.args[0])).resolve() == host, "foreign frozen host")
    marker = b"F/'tools/g2_saved_campaign'"
    require(hotfix_raw.count(marker) == 1, "single ROOTS seam required")
    amended = hotfix_raw.replace(marker, b"F/'tools'," + marker)
    require(len(amended) == 1365 and digest(amended) == NEW_HOTFIX_SHA,
            "exact ten byte amendment differs")
    compile(amended, "amended-hotfix-provider", "exec")
    manifest = json.loads(manifest_raw)
    require(manifest.get("machine_id") == MACHINE_ID and len(manifest["files"]) == 17,
            "original seventeen source rows required")
    rows = []
    for row in manifest["files"]:
        row = dict(row)
        require(Path(row["path"]).resolve() == (runtime / row["relative_path"]).resolve(),
                "base source row escaped runtime")
        if row["relative_path"] == "presentation-c23/hotfix_provider.py":
            require(row["bytes"] == len(hotfix_raw) and row["sha256"] == digest(hotfix_raw),
                    "base hotfix manifest differs")
            row.update(bytes=len(amended), sha256=digest(amended))
        rows.append(row)
    require(sum(r["relative_path"] == "presentation-c23/hotfix_provider.py" for r in rows) == 1,
            "one hotfix source row required")
    dependency = pin(host / "tools/ck3_capture_closed_receipt.py", validator_raw)
    dependency["relative_path"] = "@frozen-host/tools/ck3_capture_closed_receipt.py"
    rows.append(dependency)
    manifest.update(schema="xar.display-source-pins-with-frozen-dependency/v1", files=rows)
    raw_manifest = encode(manifest)
    provider = next(r for r in rows if r["relative_path"] == "ROOT-DECISION-TEXT-PROVIDER-C23.json")
    review = {
        "schema": "xar.recording-validator-dependency-projection/v1",
        "machine_id": MACHINE_ID, "observed_at_utc": observed_at_utc,
        "frozen_host_head": HOST_HEAD, "validator": dependency, "stdlib_imports": imports,
        "required_Task_PYTHONPATH_root": str(host / "tools"),
        "hotfix_ROOTS_contains_frozen_tools": True,
        "static_provider_input_guard": provider,
        "recording_parent_prerequisite": {
            "path": str(runtime / "recordings"), "must_exist_before_Task_Run": True,
            "create_before_prepare_or_Run": True},
        "outputs": [
            pin(runtime / "presentation-c23/hotfix_provider.py", amended),
            pin(runtime / "presentation-c23/SOURCE-PINS-C23.json", raw_manifest)],
        "changes": {"hotfix_delta_bytes": 10, "source_rows_before": 17, "source_rows_after": 18,
                    "capture_bytes_changed": 0, "owner_wait_semantics_changed": False,
                    "Game_OBS_Task_desktop_calls": 0}}
    return {"hotfix": amended, "manifest": raw_manifest, "review": review}


def plan(*, runtime, frozen_host, observed_at_utc=None):
    runtime, host = Path(runtime).resolve(), Path(frozen_host).resolve()
    manifest_raw = (runtime / "presentation-c23/SOURCE-PINS-C23.json").read_bytes()
    manifest = json.loads(manifest_raw)
    for row in manifest["files"]:
        raw = Path(row["path"]).read_bytes()
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"],
                "actual base source pin differs: " + row["relative_path"])
    return project_v1(
        (runtime / "presentation-c23/hotfix_provider.py").read_bytes(), manifest_raw,
        runtime=runtime, frozen_host=host,
        validator_raw=(host / "tools/ck3_capture_closed_receipt.py").read_bytes(),
        observed_at_utc=observed_at_utc or datetime.now(timezone.utc).isoformat())


def prepare_staging(*, root, projection):
    """Create only a reviewable staging package; never replace runtime leaves."""
    root = Path(root).resolve()
    root.mkdir(parents=True, exist_ok=False)
    outputs = []
    for leaf, raw in (("hotfix_provider.py", projection["hotfix"]),
                      ("SOURCE-PINS-C23.json", projection["manifest"]),
                      ("VALIDATOR-CLOSURE-REVIEW.json", encode(projection["review"]))):
        path = root / leaf
        with path.open("xb") as stream:
            stream.write(raw)
        outputs.append(pin(path))
    return {"machine_id": MACHINE_ID, "root": str(root), "outputs": outputs,
            "logical_bytes": sum(p["bytes"] for p in outputs),
            "actual_runtime_written": False}


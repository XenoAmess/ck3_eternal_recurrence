"""Read the exact Native25 link/archive recipes and plan a narrow successor.

No compile, link, source copy, Game/process query or external output is made.
Only the requested <=1MiB plan is written. The old build graph remains the
baseline; current master is used solely for the explicitly reviewed deltas.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
LAYOUT_HEADER = "ck3_12002_declarations.hpp"
ADDITIVE_HEADERS = ("ck3_12004_person_six_stage_capture.hpp", "person_callback_entry_inputs_12004.hpp")
CHANGED_SOURCES = {
    "ck3_12002_declarations.cpp", "ck3_12004_war_declarations.cpp",
    "ck3_12004_person_six_stage_capture.cpp", "person_callback_entry_inputs_12004.cpp",
    "ck3_12004_knight_stat_consumption_serializer.cpp", "ck3_12002_nonwar_router.cpp",
}


def norm(path: str | Path) -> str:
    return str(Path(path)).lower()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pin(path: str | Path) -> dict:
    path = Path(path)
    data = path.read_bytes()
    return {"path": str(path.resolve()), "bytes": len(data), "sha256": digest(data)}


def tokens(path: Path) -> list[str]:
    # These preserved response files have exactly one token on each line.
    # Quotes wrap only absolute library paths with spaces.
    return [line.strip().strip('"') for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


class Recipes:
    def __init__(self, legacy_index: Path):
        self.documents = {}
        self.legacy = {norm(row["object"]): row for row in self.read(legacy_index)}
        self.directory_receipts = {}

    def read(self, path: str | Path):
        key = norm(path)
        if key not in self.documents:
            self.documents[key] = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        return self.documents[key]

    def get(self, obj: str, origin: str) -> dict:
        directory = Path(obj).parent
        key = norm(directory)
        if key not in self.directory_receipts:
            receipts = {}
            for path in list(directory.glob("*COMPILE-RESULT.json")) + list(directory.glob("*.compile.json")):
                data = self.read(path)
                if data.get("exit_code") == 0 and data.get("object"):
                    receipts[norm(data["object"])] = (path, data)
            self.directory_receipts[key] = receipts
        exact = self.directory_receipts[key].get(norm(obj))
        if exact:
            recipe_path, data = exact
            pointer = ""
        else:
            row = self.legacy.get(norm(obj))
            if row is None:
                raise ValueError("unresolved actual object recipe: " + obj)
            recipe_path, pointer = Path(row["recipe_file"]), row["recipe_pointer"]
            data = self.read(recipe_path)
            if pointer:
                for part in pointer.strip("/").split("/"):
                    data = data[int(part)] if isinstance(data, list) else data[part]
        argv = data.get("argv", data.get("compiler_argv", data.get("compile_argv")))
        if not argv:
            raise ValueError("missing exact compiler argv: " + str(recipe_path))
        lower = [arg.lower() for arg in argv]
        dep = argv[lower.index("/sourcedependencies") + 1] if "/sourcedependencies" in lower else data.get("dependencies_file")
        source = data.get("source", data.get("copied", data.get("physical_source")))
        if not source:
            matches = [arg for arg in argv if arg.lower().endswith(".cpp")]
            if len(matches) != 1:
                raise ValueError("ambiguous source argument: " + obj)
            source = matches[0]
        # Some legacy repair records retain a logical source and a physical
        # copy. The actual compiler argument, not a newer public path, wins.
        actual_sources = [arg for arg in argv if arg.lower().endswith(".cpp")]
        if len(actual_sources) == 1:
            source = actual_sources[0]
        includes = None
        if dep and Path(dep).is_file():
            includes = self.read(dep).get("Data", {}).get("Includes")
        if includes is None and data.get("actual_include_pins") is not None:
            includes = [item["path"] for item in data["actual_include_pins"]]
        names = {Path(path).name.lower() for path in includes or []}
        reasons = []
        if includes is None:
            reasons.append("include_receipt_unavailable_conservative")
        if LAYOUT_HEADER in names:
            reasons.append("declarations_layout_header")
        if Path(source).name in CHANGED_SOURCES:
            reasons.append("reviewed_source_delta")
        return {
            "object": obj, "origin": origin, "source": source,
            "recipe": str(recipe_path), "recipe_pointer": pointer,
            "argv_sha256": digest(json.dumps(argv, ensure_ascii=True, separators=(",", ":")).encode()),
            "dependencies": dep, "includes_available": includes is not None,
            "layout_consumer": LAYOUT_HEADER in names,
            "additive_header_consumers": [name for name in ADDITIVE_HEADERS if name in names],
            "rebuild_reasons": reasons,
            "object_bytes": Path(obj).stat().st_size,
            "source_bytes": Path(source).stat().st_size,
            "includes": includes,
            "expected_source_sha256": data.get("source_sha256"),
            "expected_object_sha256": data.get("object_sha256"),
        }


def main() -> None:
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--native25-response", type=Path, required=True)
    parser.add_argument("--archive-response", type=Path, required=True)
    parser.add_argument("--legacy-recipes", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("plan output must be create-only")
    native_tokens, archive_tokens = tokens(args.native25_response), tokens(args.archive_response)
    direct = [item for item in native_tokens if item.lower().endswith(".obj")]
    members = [item for item in archive_tokens if item.lower().endswith(".obj")]
    recipes = Recipes(args.legacy_recipes)
    rows = [recipes.get(obj, origin) for origin, objects in (("direct", direct), ("archive", members)) for obj in objects]
    affected = [row for row in rows if row["rebuild_reasons"]]
    sources, headers, documents = {}, {}, {}
    for row in affected:
        source = pin(row["source"])
        if row["expected_source_sha256"] and source["sha256"] != row["expected_source_sha256"]:
            raise ValueError("actual frozen source differs from its compiler receipt: " + row["source"])
        sources[norm(row["source"])] = source
        for item in row["includes"] or []:
            path = Path(item)
            # System headers remain in the recorded original toolchain; the
            # source graph pins every project input actually consumed here.
            if "xar_bridge" in norm(path) or "ck3_autonomous_player" in norm(path) or "frozen" in norm(path):
                if norm(path) not in headers:
                    headers[norm(path)] = pin(path)
        for item in (row["recipe"], row["dependencies"]):
            if item and norm(item) not in documents:
                documents[norm(item)] = pin(item)
    for row in rows:
        del row["includes"]
    header_pins = sorted(headers.values(), key=lambda item: item["path"].lower())
    header_versions = {}
    for item in header_pins:
        header_versions.setdefault(item["sha256"], item)
    summary = {
        "schema": "xar.native25-successor-narrow-build-plan/v1",
        "machine_id": subprocess.check_output([sys.executable, str(ROOT / "tools/ck3_live_run_id.py"), "machine"], text=True).strip(),
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "producer": pin(Path(__file__)),
        "baseline_response": pin(args.native25_response), "archive_response": pin(args.archive_response),
        "legacy_recipe_index": pin(args.legacy_recipes),
        "direct_objects": len(direct), "archive_members": len(members),
        "layout_header_consumers": sum(row["layout_consumer"] for row in rows),
        "additive_header_consumers": {name: sum(name in row["additive_header_consumers"] for row in rows) for name in ADDITIVE_HEADERS},
        "rebuild_objects": len(affected), "rebuild_by_origin": dict(Counter(row["origin"] for row in affected)),
        "unavailable_include_receipts": sum(not row["includes_available"] for row in rows),
        "affected_old_object_bytes": sum(row["object_bytes"] for row in affected),
        "frozen_source_logical_bytes": sum(row["bytes"] for row in sources.values()),
        "frozen_project_header_logical_bytes": sum(row["bytes"] for row in headers.values()),
        "frozen_sources": list(sources.values()),
        "frozen_project_header_paths": len(header_pins),
        "frozen_project_header_versions": list(header_versions.values()),
        "frozen_project_header_pin_digest": digest(json.dumps(header_pins, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()),
        "header_reconstruction": "Re-read each selected exact dependency receipt and every project include; recompute the sorted physical pin digest before any build. Identical contents are represented once here, never inferred from a basename.",
        "recipe_and_dependency_documents": list(documents.values()),
        "objects": affected,
        "additive_only_consumer_objects": [row["object"] for row in rows if row["additive_header_consumers"] and not row["rebuild_reasons"]],
        "retained_other_objects": "Exact response tokens minus objects[]; reuse only as read-only inputs, with no new source substitution.",
        "compile_link_or_Game_calls": 0,
        "large_output_created": False,
        "scope": "Exact Native25 final direct objects plus exact runtime-native18 archive inputs; only source delta/layout consumers rebuilt. Additive serializer declarations preserve old DTO/ABI and do not alone require recompilation.",
        "heavy_build_storage_child": None,
        "current_Game_or_Native25_changed": False,
    }
    raw = (json.dumps(summary, ensure_ascii=True, separators=(",", ":")) + "\n").encode()
    if len(raw) > 1024 * 1024:
        raise ValueError("small plan exceeds admitted1MiB")
    args.output.write_bytes(raw)
    print(json.dumps({key: value for key, value in summary.items()
                      if key in {"direct_objects", "archive_members", "layout_header_consumers", "additive_header_consumers",
                                 "rebuild_objects", "rebuild_by_origin", "unavailable_include_receipts",
                                 "affected_old_object_bytes", "frozen_source_logical_bytes", "frozen_project_header_logical_bytes"}}))
    print(json.dumps({"output": str(args.output), "bytes": len(raw), "sha256": digest(raw)}))


if __name__ == "__main__":
    main()

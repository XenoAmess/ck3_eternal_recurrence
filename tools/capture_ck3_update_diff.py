"""Freeze an updated CK3 executable and compare data without touching a game session."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import shutil

from freeze_ck3_migration_metadata import digest, identify, save_json


DATA_FOLDERS = ("common", "events", "gui", "localization", "history", "map_data", "dlc")
DATA_SUFFIXES = {".txt", ".gui", ".yml", ".yaml", ".json", ".csv", ".dlc", ".info"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--steam-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = args.game.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    frozen = out / "installation"
    (frozen / "binaries").mkdir(parents=True)
    (frozen / "launcher").mkdir()
    for relative in ("binaries/ck3.exe", "launcher/launcher-settings.json"):
        shutil.copy2(root / relative, frozen / relative)
    shutil.copy2(args.steam_manifest, out / args.steam_manifest.name)
    identity = identify(frozen)
    identity["source_installation"] = str(root)
    manifest = (out / args.steam_manifest.name).read_text(encoding="utf-8-sig")
    identity["steam_build_id"] = re.search(r'"buildid"\s+"([^"]+)"', manifest).group(1)
    identity["steam_manifest_sha256"] = digest(out / args.steam_manifest.name)
    identity["captured_at_utc"] = datetime.now(timezone.utc).isoformat()
    save_json(out / "build-identity.json", identity)
    old_rows = json.loads(args.baseline.read_text(encoding="utf-8-sig"))
    old = {row["path"]: row for row in old_rows}
    new = {}
    for folder in DATA_FOLDERS:
        for path in sorted((root / "game" / folder).rglob("*")):
            if path.is_file() and path.suffix.lower() in DATA_SUFFIXES:
                relative = path.relative_to(root).as_posix()
                new[relative] = {"path": relative, "size": path.stat().st_size, "sha256": digest(path)}
    save_json(out / "game-data.json", list(new.values()))
    added = sorted(new.keys() - old.keys())
    removed = sorted(old.keys() - new.keys())
    changed = sorted(name for name in old.keys() & new.keys()
                     if old[name]["sha256"] != new[name]["sha256"])
    # Changed/new source files plus the preserved old installation reconstruct
    # the complete inventoried data scope without another full game copy.
    for relative in added + changed:
        target = frozen / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
        if digest(target) != new[relative]["sha256"]:
            raise RuntimeError(f"Data changed during capture: {relative}")
    categories = {}
    for label, paths in (("added", added), ("removed", removed), ("changed", changed)):
        categories[label] = dict(sorted(Counter("/".join(p.split("/")[1:3]) for p in paths).items()))
    result = {
        "baseline": str(args.baseline.resolve()), "baseline_sha256": digest(args.baseline),
        "baseline_count": len(old), "updated_count": len(new),
        "unchanged_count": len(new) - len(added) - len(changed),
        "added": added, "removed": removed, "changed": changed,
        "categories": categories,
        "frozen_data_bytes": sum(new[name]["size"] for name in added + changed),
        "scope": {"folders": DATA_FOLDERS, "suffixes": sorted(DATA_SUFFIXES)},
        "runtime_actions": [], "live_validation": False,
    }
    save_json(out / "data-diff.json", result)
    print(json.dumps({"output": str(out), "version": identity["launcher_identity"],
                      "steam_build": identity["steam_build_id"],
                      "sha256": identity["executable_sha256"],
                      "old": len(old), "new": len(new), "added": len(added),
                      "removed": len(removed), "changed": len(changed),
                      "frozen_data_bytes": result["frozen_data_bytes"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()

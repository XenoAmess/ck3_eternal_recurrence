"""Freeze build/data/source metadata after migration state has been copied."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tarfile


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def save_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def identify(root: Path) -> dict[str, object]:
    exe = root / "binaries/ck3.exe"
    image = exe.read_bytes()
    pe = struct.unpack_from("<I", image, 0x3C)[0]
    optional = pe + 24
    launcher = root / "launcher/launcher-settings.json"
    settings = json.loads(launcher.read_text(encoding="utf-8-sig"))
    return {
        "root": str(root), "executable_sha256": hashlib.sha256(image).hexdigest(),
        "executable_size": len(image),
        "pe_timestamp": struct.unpack_from("<I", image, pe + 8)[0],
        "machine": hex(struct.unpack_from("<H", image, pe + 4)[0]),
        "preferred_image_base": hex(struct.unpack_from("<Q", image, optional + 24)[0]),
        "size_of_image": struct.unpack_from("<I", image, optional + 56)[0],
        "launcher_settings_sha256": digest(launcher),
        "launcher_identity": {k: settings.get(k) for k in (
            "gameId", "version", "rawVersion", "gameVersion", "displayVersion", "distPlatform")},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--game", action="append", required=True, help="label=installation-root")
    parser.add_argument("--steam-manifest", type=Path)
    args = parser.parse_args()
    out = args.archive.resolve()
    out.mkdir(parents=True, exist_ok=True)
    meta = out / "metadata"
    meta.mkdir(exist_ok=False)
    identities = {}
    inventory_counts = {}
    for item in args.game:
        label, location = item.split("=", 1)
        root = Path(location).resolve()
        identities[label] = identify(root)
        rows = []
        for folder in ("common", "events", "gui", "localization", "history", "map_data", "dlc"):
            base = root / "game" / folder
            for path in sorted(base.rglob("*")):
                if path.is_file() and path.suffix.lower() in (
                    ".txt", ".gui", ".yml", ".yaml", ".json", ".csv", ".dlc", ".info"):
                    rows.append({"path": path.relative_to(root).as_posix(),
                                 "size": path.stat().st_size, "sha256": digest(path)})
        save_json(meta / f"game-data-{label}.json", rows)
        inventory_counts[label] = len(rows)
        shutil.copy2(root / "launcher/launcher-settings.json", meta / f"launcher-{label}.json")
        print(f"Frozen {label}: {len(rows)} data files", flush=True)
    save_json(meta / "build-identity.json", identities)
    if args.steam_manifest:
        shutil.copy2(args.steam_manifest, meta / args.steam_manifest.name)
        text = args.steam_manifest.read_text(encoding="utf-8")
        save_json(meta / "steam-build.json", {
            "source": str(args.steam_manifest), "sha256": digest(args.steam_manifest),
            "build_id": re.search(r'"buildid"\s+"([^"]+)"', text).group(1),
        })

    repo = args.repo.resolve()
    selected = ["ck3_autonomous_player", "tools", "XenoAmess_s_Eternal_Recurrence",
                "Eternal_Recurrence_Vivhite_Courtier", "docs/ck3-native-ai",
                "docs/ck3-native-version-adapters.md", "docs/testing-workflow.md",
                "docs/ck3-update-migration-plan.md", "docs/operator-mcp.md"]
    def git(*arguments: str) -> bytes:
        return subprocess.check_output(["git", "-C", str(repo), *arguments])
    revision = git("rev-parse", "HEAD").decode().strip()
    (meta / "working-tree.patch").write_bytes(git("diff", "--binary", "HEAD", "--", *selected))
    tracked = git("ls-files", "-z", "--", *selected).split(b"\0")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z", "--",
                    "ck3_autonomous_player/src", "ck3_autonomous_player/tests",
                    "ck3_autonomous_player/native_bridge/research",
                    "ck3_autonomous_player/*.py", "docs/operator-mcp.md",
                    "tools/freeze_ck3_migration_metadata.py", "tools/run_one_generation_canary.ps1").split(b"\0")
    files = sorted({os.fsdecode(name) for name in tracked + untracked if name})
    with tarfile.open(meta / "source-working-tree.tar.gz", "w:gz") as archive:
        for name in files:
            path = repo / name
            if path.is_file():
                archive.add(path, arcname=name, recursive=False)
    save_json(meta / "source-state.json", {
        "head": revision, "snapshot_paths": files,
        "patch_sha256": digest(meta / "working-tree.patch"),
        "source_archive_sha256": digest(meta / "source-working-tree.tar.gz"),
        "source_archive_includes_uncommitted_work": True,
    })

    state = out / "autoplayer-state"
    driver = json.loads((state / "native-session/driver-state.json").read_text(encoding="utf-8"))
    seed = json.loads((state / "native-session/episode-seed.json").read_text(encoding="utf-8"))
    bindings = {}
    for label, anchor in (("checkpoint", driver["last_checkpoint"]), ("episode_seed", seed)):
        copied = state / "profile/save games" / anchor["name"]
        actual = digest(copied) if copied.exists() else None
        bindings[label] = {"original_anchor": anchor,
                           "copied_path": str(copied), "actual_sha256": actual,
                           "matches_metadata": actual == anchor.get("sha256", "").lower()}
    save_json(meta / "state-bindings.json", bindings)
    source = (repo / "ck3_autonomous_player/native_bridge/src/ck3_11906_adapter.cpp").read_text(encoding="utf-8-sig")
    block = source.split("kCapabilities{", 1)[1].split("};", 1)[0]
    capabilities = re.findall(r'"(game\.[^"]+)"', block)
    title = (repo / "ck3_autonomous_player/native_bridge/include/xar_bridge/title_map_navigation_v1.hpp").read_text(encoding="utf-8-sig")
    capabilities += re.findall(r'"(game\.command\.center-map[^\"]+)"', title)
    save_json(meta / "adapter-capabilities-static.json", {
        "evidence": "source-declared; not a new live hello", "source_head": revision,
        "capabilities": capabilities,
    })
    save_json(meta / "capture-result.json", {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_head": revision, "data_inventory_counts": inventory_counts,
        "state_anchor_matches": {k: v["matches_metadata"] for k, v in bindings.items()},
        "no_new_game_launch": True,
    })
    print(json.dumps({"archive": str(out), "state_anchor_matches": {
        k: v["matches_metadata"] for k, v in bindings.items()},
        "static_capability_count": len(capabilities)}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

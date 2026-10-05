"""Build the Li Yu Dao runtime allowlist, manifest and reproducible ZIP.

This packages repository source; it never registers a mod or launches CK3.
Run validate_static.py before treating a build as static-ready.
"""

from __future__ import annotations

import argparse
from fnmatch import fnmatchcase
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

SOURCE = Path(__file__).resolve().parents[1]
ROOT = SOURCE.parent
PRODUCT_ID = "mod_li_yu_dao"
REQUIRED_RUNTIME_FILES = frozenset({
    'common/character_interactions/lyd_i3b_nomination_interactions.txt',
    'common/decisions/lyd_i3b_institution_decisions.txt',
    'common/script_values/lyd_i3b_institution_values.txt',
    'common/scripted_effects/lyd_i3b_commit_effects.txt',
    'common/scripted_effects/lyd_i3b_response_effects.txt',
    'common/scripted_effects/lyd_i3b_setup_effects.txt',
    'common/scripted_effects/lyd_i3b_terms_effects.txt',
    'common/scripted_triggers/lyd_i3b_institution_triggers.txt',
    'events/lyd_i3b_institution_events.txt',
    'localization/english/lyd_i3b_institution_l_english.yml',
    'localization/simp_chinese/lyd_i3b_institution_l_simp_chinese.yml',
    "descriptor.mod",
    "common/religion/faith_types/lyd_faiths.txt",
    "common/religion/rite_types/lyd_rites.txt",
    "common/religion/tenet_types/lyd_tenets.txt",
    "history/faiths/lyd_faith_history.txt",
    "common/decisions/lyd_decisions.txt",
    "common/character_interactions/lyd_interactions.txt",
    "common/decisions/lyd_c2_consent_decisions.txt",
    "common/character_interactions/lyd_c2_consent_interactions.txt",
    "common/script_values/lyd_c2_consent_values.txt",
    "common/decisions/lyd_c3_leadership_decisions.txt",
    "common/character_interactions/lyd_c3_teacher_interactions.txt",
    "common/on_action/lyd_c3_lifecycle_on_actions.txt",
    "events/lyd_events.txt",
    "events/lyd_c2_consent_events.txt",
    "events/lyd_c3_leadership_events.txt",
    "localization/english/lyd_content_l_english.yml",
    "localization/english/lyd_runtime_l_english.yml",
    "localization/english/lyd_c2_consent_l_english.yml",
    "localization/english/lyd_c3_leadership_l_english.yml",
    "localization/simp_chinese/lyd_content_l_simp_chinese.yml",
    "localization/simp_chinese/lyd_runtime_l_simp_chinese.yml",
    "localization/simp_chinese/lyd_c2_consent_l_simp_chinese.yml",
    "localization/simp_chinese/lyd_c3_leadership_l_simp_chinese.yml",
})
# These two deliberately bounded families accommodate the small helper files.
# collect_runtime_files freezes the actual production paths in every manifest.
RUNTIME_FAMILIES = (
    "common/scripted_triggers/lyd_*.txt",
    "common/scripted_effects/lyd_*.txt",
)
SOURCE_ONLY_DIRS = frozenset({"tools", "docs", "tests", "debug", "fixtures", "test_fixtures", "__pycache__"})
FORBIDDEN_MARKER = re.compile(r"(?:^|[_./-])(?:debug|fixture|selftest|acceptance|probe|test)(?:[_./-]|$)", re.I)
RUNTIME_DIRS = frozenset({"common", "events", "history", "localization", "gfx", "gui"})
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def collect_runtime_files(source: Path = SOURCE) -> tuple[str, ...]:
    source = source.resolve()
    if not source.is_dir():
        raise ValueError(f"source directory missing: {source}")
    actual: set[str] = set()
    unexpected: list[str] = []
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source).as_posix()
        parts = relative.split("/")
        if any(part in SOURCE_ONLY_DIRS for part in parts):
            continue
        if path.is_symlink():
            raise ValueError(f"symlink outside source-only directories: {relative}")
        if not path.is_file():
            continue
        allowed = relative in REQUIRED_RUNTIME_FILES or (len(parts) == 3 and any(fnmatchcase(relative, pattern) for pattern in RUNTIME_FAMILIES))
        if allowed:
            if FORBIDDEN_MARKER.search(relative):
                raise ValueError(f"test/debug file matches runtime family: {relative}")
            actual.add(relative)
        elif parts[0] in RUNTIME_DIRS or relative == "descriptor.mod":
            unexpected.append(relative)
    missing = sorted(REQUIRED_RUNTIME_FILES - actual)
    if missing or unexpected:
        raise ValueError(f"runtime inventory mismatch; missing={missing}; unexpected={unexpected}")
    for family in RUNTIME_FAMILIES:
        if not any(fnmatchcase(relative, family) for relative in actual):
            raise ValueError(f"runtime helper family is empty: {family}")
    descriptor = (source / "descriptor.mod").read_text(encoding="utf-8-sig")
    if re.search(r"\b(?:remote_file_id|path)\s*=", descriptor):
        raise ValueError("inner descriptor must not contain remote_file_id or development path")
    if not re.search(r'^version\s*=\s*"[0-9]+\.[0-9]+\.[0-9]+"\s*$', descriptor, re.M):
        raise ValueError("descriptor needs a semantic version")
    return tuple(sorted(actual))


def git_revision() -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=False)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def build_release(source: Path, output: Path, *, revision: str | None = None) -> dict:
    source, output = source.resolve(), output.resolve()
    inventory = collect_runtime_files(source)
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("staging and source must not contain one another")
    if output.exists():
        raise ValueError(f"staging already exists; choose a fresh output: {output}")
    manifest_path = output.with_name(output.name + ".manifest.json")
    archive_path = output.with_name(output.name + ".zip")
    if manifest_path.exists() or archive_path.exists():
        raise ValueError("build sidecar already exists; choose a fresh output")
    descriptor = (source / "descriptor.mod").read_text(encoding="utf-8-sig")
    version = re.search(r'^version\s*=\s*"([^"]+)"', descriptor, re.M).group(1)
    payloads = {relative: (source / relative).read_bytes() for relative in inventory}
    manifest = {
        "format_version": 1,
        "product_id": PRODUCT_ID,
        "mod_version": version,
        "git_sha": revision if revision is not None else git_revision(),
        "files": [{"path": relative, "size": len(data), "sha256": sha256(data)} for relative, data in payloads.items()],
    }
    for relative, data in payloads.items():
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    manifest_path.write_bytes((json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8"))
    with zipfile.ZipFile(archive_path, "w") as archive:
        for relative, data in payloads.items():
            info = zipfile.ZipInfo(f"{PRODUCT_ID}/{relative}", ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compresslevel=9)
    verify_manifest(output, manifest_path)
    return {"staging": str(output), "manifest": str(manifest_path), "archive": str(archive_path), "file_count": len(inventory), "manifest_sha256": sha256(manifest_path.read_bytes()), "zip_sha256": sha256(archive_path.read_bytes())}


def verify_manifest(staging: Path, manifest_path: Path) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format_version") != 1 or manifest.get("product_id") != PRODUCT_ID:
        raise ValueError("manifest product/schema mismatch")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise ValueError("manifest files must be a list")
    paths = [entry["path"] for entry in entries]
    if paths != sorted(set(paths)) or any(Path(path).is_absolute() or ".." in Path(path).parts for path in paths):
        raise ValueError("unsafe or duplicate manifest paths")
    actual = collect_runtime_files(staging)
    # Staging must contain only runtime, unlike the development source.
    if tuple(paths) != actual or {path.relative_to(staging).as_posix() for path in staging.rglob("*") if path.is_file()} != set(paths):
        raise ValueError("staging contains missing or extra files")
    for entry in entries:
        data = (staging / entry["path"]).read_bytes()
        if len(data) != entry["size"] or sha256(data) != entry["sha256"]:
            raise ValueError(f"staging hash mismatch: {entry['path']}")
    return len(paths)


def check_reproducible(source: Path = SOURCE) -> dict:
    revision = git_revision()
    with tempfile.TemporaryDirectory(prefix="lyd-reproducible-") as temporary:
        base = Path(temporary)
        first = build_release(source, base / "first" / PRODUCT_ID, revision=revision)
        second = build_release(source, base / "second" / PRODUCT_ID, revision=revision)
        if first["manifest_sha256"] != second["manifest_sha256"] or first["zip_sha256"] != second["zip_sha256"]:
            raise ValueError("identical inputs did not yield identical manifest and ZIP bytes")
        return {key: first[key] for key in ("file_count", "manifest_sha256", "zip_sha256")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / PRODUCT_ID)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--verify", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.verify:
            if not args.manifest:
                raise ValueError("--verify requires --manifest")
            result = {"file_count": verify_manifest(args.verify.resolve(), args.manifest)}
        elif args.manifest:
            raise ValueError("--manifest requires --verify")
        elif args.check:
            result = check_reproducible(args.source)
        else:
            result = build_release(args.source, args.output)
        print(json.dumps({"result": "GREEN", "layer": "L0-packaging", "live": "NOT_RUN", **result}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError) as error:
        print(f"LYD BUILD FAILED: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

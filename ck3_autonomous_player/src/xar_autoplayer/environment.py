"""Prepare and verify a production-only, single-mod CK3 profile."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import csv
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from . import __version__
from .errors import AgentError, UnsafeCleanupError
from .locking import exclusive_state_lock
from .rules import parsed_preset_settings, render_presets, rule_contract


REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import build_release  # noqa: E402


STEAM_APP_ID = "1158310"
EXPECTED_GAME_VERSION = "1.19.0.6"
OUTER_DESCRIPTOR_NAME = "xar_autoplayer.mod"
OUTER_DESCRIPTOR_REF = f"mod/{OUTER_DESCRIPTOR_NAME}"
EXPECTED_MOD_NAME = "琉焰卿的永恒轮回"
PROFILE_MANIFEST_NAME = "xar-autoplayer-environment.json"
RUNTIME_DISTRIBUTIONS = (
    "attrs",
    "jsonschema",
    "jsonschema-specifications",
    "numpy",
    "onnxruntime",
    "opencv-python",
    "Pillow",
    "PyAutoGUI",
    "pyclipper",
    "PyYAML",
    "pywin32",
    "rapidocr-onnxruntime",
    "rfc3339-validator",
    "referencing",
    "rpds-py",
    "Shapely",
    "six",
)


def process_creation_utc(value: object) -> datetime:
    """Parse the two exact Windows process-time encodings used by this agent.

    COM WMI exposes DMTF local time with a minute offset, while the global
    PowerShell CIM inventory serializes the same value as seven-digit UTC ISO.
    Raw strings remain in evidence; this helper is only for strict cross-source
    identity comparison.
    """
    text = str(value).strip()
    dmtf = re.fullmatch(
        r"(?P<stamp>\d{14})\.(?P<fraction>\d{6})(?P<sign>[+-])(?P<offset>\d{3})",
        text,
    )
    if dmtf is not None:
        local = datetime.strptime(dmtf.group("stamp"), "%Y%m%d%H%M%S")
        local = local.replace(microsecond=int(dmtf.group("fraction")))
        minutes = int(dmtf.group("offset"))
        if minutes > 14 * 60:
            raise ValueError("DMTF UTC offset is outside the supported range")
        if dmtf.group("sign") == "-":
            minutes = -minutes
        return local.replace(tzinfo=timezone(timedelta(minutes=minutes))).astimezone(
            timezone.utc
        )
    iso = re.fullmatch(
        r"(?P<stamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})\."
        r"(?P<fraction>\d{7})Z",
        text,
    )
    if iso is None:
        raise ValueError("unsupported process creation timestamp")
    # DMTF carries microseconds while CIM serializes Windows' seventh
    # fractional (100 ns) digit as well.  Accepting a non-zero final digit and
    # truncating it would collapse distinct process creations, so fail closed
    # unless the CIM instant is exactly representable in DMTF precision.
    if iso.group("fraction")[-1] != "0":
        raise ValueError("CIM process timestamp exceeds DMTF precision")
    utc = datetime.strptime(iso.group("stamp"), "%Y-%m-%dT%H:%M:%S")
    return utc.replace(
        microsecond=int(iso.group("fraction")[:6]), tzinfo=timezone.utc
    )


def same_process_creation_time(first: object, second: object) -> bool:
    try:
        return process_creation_utc(first) == process_creation_utc(second)
    except (TypeError, ValueError, OverflowError):
        return False


def default_state_dir() -> Path:
    override = os.environ.get("XAR_AUTOPLAYER_STATE_DIR")
    if override:
        return Path(os.path.expandvars(override)).expanduser().resolve()
    local = os.environ.get("LOCALAPPDATA")
    base = Path(local) if local else Path.home() / "AppData" / "Local"
    return (base / "XarAutoplayer").resolve()


def default_game_dir() -> Path:
    override = os.environ.get("XAR_CK3_GAME_DIR")
    if override:
        return Path(os.path.expandvars(override)).expanduser().resolve()
    return (REPO_ROOT / "Crusader Kings III").resolve()


def real_ck3_profile() -> Path:
    override = os.environ.get("XAR_REAL_CK3_PROFILE")
    if override:
        return Path(os.path.expandvars(override)).expanduser().resolve()
    return (
        Path.home()
        / "Documents"
        / "Paradox Interactive"
        / "Crusader Kings III"
    ).resolve()


@dataclass(frozen=True)
class EnvironmentSpec:
    state_dir: Path
    game_dir: Path
    expected_game_version: str = EXPECTED_GAME_VERSION

    @property
    def profile_dir(self) -> Path:
        return self.state_dir / "profile"

    @property
    def production_dir(self) -> Path:
        return self.profile_dir / "mod-content" / "xar-production"

    @property
    def manifest_path(self) -> Path:
        return self.profile_dir / PROFILE_MANIFEST_NAME

    @property
    def game_exe(self) -> Path:
        return self.game_dir / "binaries" / "ck3.exe"

    @property
    def vanilla_rules(self) -> Path:
        return (
            self.game_dir
            / "game"
            / "common"
            / "game_rules"
            / "00_game_rules.txt"
        )


def make_spec(state_dir: Path | None = None, game_dir: Path | None = None) -> EnvironmentSpec:
    return EnvironmentSpec(
        state_dir=(state_dir or default_state_dir()).expanduser().resolve(),
        game_dir=(game_dir or default_game_dir()).expanduser().resolve(),
    )


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def paths_overlap(first: Path, second: Path) -> bool:
    first = first.resolve()
    second = second.resolve()
    return first == second or is_relative_to(first, second) or is_relative_to(second, first)


def _steam_path() -> Path | None:
    if os.name != "nt":
        return None
    candidates: list[Path] = []
    override = os.environ.get("XAR_STEAM_DIR")
    if override:
        candidates.append(Path(os.path.expandvars(override)).expanduser())
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            raw, _ = winreg.QueryValueEx(key, "SteamPath")
        candidates.append(Path(raw).expanduser())
    except OSError:
        pass
    candidates.extend(
        (
            Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"))
            / "Steam",
            Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Steam",
        )
    )
    for candidate in candidates:
        resolved = candidate.resolve()
        if (resolved / "steamapps" / "libraryfolders.vdf").is_file():
            return resolved
    return None


def steam_protected_roots() -> list[tuple[str, Path]]:
    steam = _steam_path()
    if steam is None:
        return []
    roots: list[tuple[str, Path]] = [("Steam userdata", steam / "userdata")]
    libraries = [steam]
    registry = steam / "steamapps" / "libraryfolders.vdf"
    if registry.is_file():
        text = registry.read_text(encoding="utf-8-sig", errors="strict")
        libraries.extend(
            Path(raw.replace("\\\\", "\\")).expanduser().resolve()
            for raw in re.findall(r'(?im)^\s*"path"\s+"([^"]+)"', text)
        )
    for library in libraries:
        roots.append(
            (
                "Steam CK3 Workshop app root",
                library / "steamapps" / "workshop" / "content" / STEAM_APP_ID,
            )
        )
    unique: dict[str, tuple[str, Path]] = {}
    for label, path in roots:
        unique[str(path.resolve()).casefold()] = (label, path.resolve())
    return list(unique.values())


def protected_roots() -> list[tuple[str, Path]]:
    return [
        ("repository", REPO_ROOT.resolve()),
        ("real CK3 profile", real_ck3_profile()),
        *steam_protected_roots(),
    ]


def ensure_state_path_safe(
    state_dir: Path, roots: Iterable[tuple[str, Path]] | None = None
) -> None:
    candidate = state_dir.resolve()
    if candidate.parent == candidate:
        raise AgentError(f"state directory cannot be a filesystem root: {candidate}")
    for label, protected in roots if roots is not None else protected_roots():
        if paths_overlap(candidate, protected):
            raise AgentError(
                f"state directory overlaps {label}: {candidate} <-> {protected.resolve()}"
            )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_snapshot(root: Path) -> dict[str, dict[str, object]]:
    return {
        path.relative_to(root).as_posix(): {
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in sorted(item for item in root.rglob("*") if item.is_file())
    }


def snapshot_digest(snapshot: object) -> str:
    raw = json.dumps(
        snapshot, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")
    return hashlib.sha256(raw).hexdigest()


def write_bytes_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def write_text_atomic(path: Path, text: str, encoding: str = "utf-8") -> None:
    write_bytes_atomic(path, text.encode(encoding))


def write_json_atomic(path: Path, payload: object) -> None:
    write_text_atomic(
        path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    )


def launcher_identity(game_dir: Path) -> dict[str, str]:
    path = game_dir / "launcher" / "launcher-settings.json"
    if not path.is_file():
        raise AgentError(f"launcher identity is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    return {
        "raw_version": str(payload.get("rawVersion", "")),
        "display_version": str(payload.get("version", "")),
        "distribution": str(payload.get("distPlatform", "")),
        "launcher_settings_sha256": sha256_file(path),
    }


def installed_dlc_fingerprint(game_dir: Path) -> dict[str, object]:
    descriptors = sorted((game_dir / "game" / "dlc").glob("*/*.dlc"))
    entries = [
        {
            "path": path.relative_to(game_dir).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in descriptors
    ]
    mount_roots = sorted(
        {str(descriptor.parent.resolve()) for descriptor in descriptors}
    )
    return {
        "installed_descriptor_count": len(entries),
        "installed_descriptors_sha256": snapshot_digest(entries),
        "allowed_mount_roots": mount_roots,
        "allowed_mount_roots_sha256": snapshot_digest(mount_roots),
        "note": (
            "This fingerprints installed DLC descriptors, not account entitlements. "
            "disabled_dlcs=[] leaves owned DLC enabled; runtime mounts are attested separately."
        ),
    }


def render_settings() -> str:
    return '''"game"={
\t"promt_for_tutorial"={ version=0 enabled=no }
\t"prompt_for_china_tutorial"={ version=0 enabled=no }
\t"cloud_save"={ version=0 enabled=no }
}
"Graphics"={
\t"display_mode"={ version=0 value="fullscreen" }
\t"display_index"={ version=0 value="0" }
\t"fullscreen_resolution"={ version=0 value="2560x1440" }
}
"System"={
\t"language"={ version=0 value="l_simp_chinese" }
}
'''


def write_outer_descriptor(inner: Path, outer: Path, target: Path) -> None:
    text = inner.read_text(encoding="utf-8-sig")
    if "remote_file_id" in text:
        raise AgentError(f"production descriptor contains remote_file_id: {inner}")
    if re.search(r"(?m)^\s*path\s*=", text):
        raise AgentError(f"production descriptor already contains path=: {inner}")
    rendered = text.rstrip("\r\n") + f'\npath="{target.as_posix()}"\n'
    write_bytes_atomic(outer, rendered.encode("utf-8-sig"))


def parse_descriptor_target(path: Path) -> Path:
    text = path.read_text(encoding="utf-8-sig")
    matches = re.findall(r'(?m)^\s*path\s*=\s*"([^"\r\n]+)"\s*$', text)
    if len(matches) != 1:
        raise AgentError(f"outer descriptor must contain exactly one path=: {path}")
    target = Path(os.path.expandvars(matches[0])).expanduser()
    if not target.is_absolute():
        raise AgentError(f"outer descriptor path is not absolute: {target}")
    return target.resolve()


def _git_revision() -> str:
    revision = build_release.git_sha()
    if not revision or not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise AgentError("a full Git revision is required for an auditable runtime")
    return revision


def _git_lines(*arguments: str) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(REPO_ROOT), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError) as error:
        raise AgentError(f"git {' '.join(arguments)} failed") from error
    return [line for line in result.stdout.splitlines() if line.strip()]


def mod_source_fingerprint() -> dict[str, object]:
    source = build_release.DEFAULT_SOURCE.resolve()
    projected = [
        {
            "path": relative,
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
        for relative, data in build_release.release_entries(source)
    ]
    relative_source = source.relative_to(REPO_ROOT).as_posix()
    status = _git_lines(
        "status", "--porcelain", "--untracked-files=all", "--", relative_source
    )
    projected_repo_paths = {
        f"{relative_source}/{entry['path']}" for entry in projected
    }
    tracked = set(_git_lines("ls-files", "--", relative_source))
    untracked_release_files = sorted(projected_repo_paths - tracked)
    revision = _git_revision()
    tags = _git_lines("tag", "--points-at", revision)
    return {
        "git_revision": revision,
        "git_tags_at_revision": tags,
        "git_dirty": bool(status),
        "git_status": status,
        "all_release_files_tracked": not untracked_release_files,
        "untracked_release_files": untracked_release_files,
        "release_source_file_count": len(projected),
        "release_source_sha256": snapshot_digest(projected),
    }


def verify_projection_manifest(
    target: Path, manifest_path: Path, expected_revision: str
) -> dict[str, object]:
    """Verify a development production projection without inventing a release tag."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    version = build_release.descriptor_version(target)
    expected_identity = {
        "format_version": 2,
        "mod_version": version,
        "workshop_item_id": build_release.WORKSHOP_ITEM_ID,
        "git_sha": expected_revision,
    }
    for key, expected in expected_identity.items():
        if manifest.get(key) != expected:
            raise AgentError(
                f"production manifest identity {key} differs: "
                f"{manifest.get(key)!r} != {expected!r}"
            )
    tag = manifest.get("git_tag")
    if tag is not None and tag != f"v{version}":
        raise AgentError(f"production manifest has an invalid Git tag: {tag!r}")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise AgentError("production manifest files is not a list")
    expected: dict[str, dict[str, object]] = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("path"), str):
            raise AgentError("production manifest contains a malformed file entry")
        relative = str(entry["path"])
        if relative in expected:
            raise AgentError(f"production manifest repeats path: {relative}")
        expected[relative] = entry
    actual = {
        path.relative_to(target).as_posix(): path
        for path in target.rglob("*")
        if path.is_file()
    }
    errors: list[str] = []
    for relative, entry in expected.items():
        path = actual.pop(relative, None)
        if path is None:
            errors.append(f"missing: {relative}")
            continue
        if (
            path.stat().st_size != entry.get("size")
            or sha256_file(path) != entry.get("sha256")
        ):
            errors.append(f"mismatch: {relative}")
    errors.extend(f"extra: {relative}" for relative in sorted(actual))
    if errors:
        raise AgentError("production tree differs from manifest:\n  " + "\n  ".join(errors))
    return manifest


def settings_contract(text: str) -> dict[str, object]:
    expected: dict[str, object] = {
        "promt_for_tutorial": False,
        "prompt_for_china_tutorial": False,
        "cloud_save": False,
        "display_mode": "fullscreen",
        "display_index": "0",
        "fullscreen_resolution": "2560x1440",
        "language": "l_simp_chinese",
    }
    actual: dict[str, object] = {}
    for key, wanted in expected.items():
        matches = re.findall(
            rf'"{re.escape(key)}"\s*=\s*\{{([^{{}}]*)\}}', text, re.DOTALL
        )
        if len(matches) != 1:
            raise AgentError(f"pdx_settings must contain exactly one {key!r}")
        body = matches[0]
        if isinstance(wanted, bool):
            value = re.findall(r"\benabled\s*=\s*(yes|no)\b", body)
            actual[key] = value[0] == "yes" if len(value) == 1 else None
        else:
            value = re.findall(r'\bvalue\s*=\s*"([^"\r\n]*)"', body)
            actual[key] = value[0] if len(value) == 1 else None
    if actual != expected:
        raise AgentError(f"pdx_settings contract differs: {actual!r}")
    return actual


def _contract_digest(payload: dict[str, object]) -> str:
    stable = json.loads(json.dumps(payload, ensure_ascii=False))
    stable.pop("prepared_at", None)
    stable.pop("environment_sha256", None)
    tutorial = stable.get("persistent_tutorial_state")
    if isinstance(tutorial, dict):
        tutorial.pop("initialized_this_prepare", None)
    return snapshot_digest(stable)


def agent_runtime_fingerprint() -> dict[str, object]:
    root = REPO_ROOT / "ck3_autonomous_player"
    roots = [
        root / "agent.py",
        root / "pyproject.toml",
        root / "src",
        root / "configs",
        root / "schemas",
        root / "strategies",
        root / "knowledge",
        TOOLS_DIR / "build_release.py",
    ]
    paths: list[Path] = []
    for item in roots:
        if item.is_file():
            paths.append(item)
        elif item.is_dir():
            paths.extend(
                path
                for path in item.rglob("*")
                if path.is_file() and "__pycache__" not in path.parts
            )
    entries = []
    for path in sorted(set(paths)):
        if is_relative_to(path, root):
            label = f"agent/{path.relative_to(root).as_posix()}"
        else:
            label = f"repo/{path.relative_to(REPO_ROOT).as_posix()}"
        entries.append(
            {
                "path": label,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    distributions: dict[str, str] = {}
    for name in RUNTIME_DISTRIBUTIONS:
        try:
            distributions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise AgentError(f"required runtime distribution is missing: {name}") from error
    repo_paths = sorted(path.relative_to(REPO_ROOT).as_posix() for path in set(paths))
    selected_roots = [
        item.relative_to(REPO_ROOT).as_posix()
        for item in roots
    ]
    tracked = set(_git_lines("ls-files", "--", *selected_roots))
    untracked_runtime_files = sorted(set(repo_paths) - tracked)
    git_status = _git_lines(
        "status", "--porcelain", "--untracked-files=all", "--", *selected_roots
    )
    selected_revision_lines = _git_lines(
        "log", "-1", "--format=%H", "--", *selected_roots
    )
    selected_revision = selected_revision_lines[0] if selected_revision_lines else None
    runtime = {
        "file_count": len(entries),
        "files": entries,
        "interpreter": {
            "path": str(Path(sys.executable).resolve()),
            "sha256": sha256_file(Path(sys.executable).resolve()),
            "version": sys.version,
        },
        "distributions": distributions,
        "git": {
            "selected_runtime_revision": selected_revision,
            "all_files_tracked": not untracked_runtime_files,
            "untracked_runtime_files": untracked_runtime_files,
            "dirty": bool(git_status),
            "status": git_status,
        },
    }
    runtime["sha256"] = snapshot_digest(runtime)
    return runtime


def prepare_profile(spec: EnvironmentSpec) -> dict[str, object]:
    """Exclusively create/refresh the profile; refuse while any CK3 is active."""
    ensure_state_path_safe(spec.state_dir)
    with exclusive_state_lock(spec.state_dir, "prepare-profile"):
        unsafe_marker = spec.state_dir / "control" / "unsafe-cleanup.json"
        if unsafe_marker.is_file():
            raise AgentError(
                f"an unresolved unsafe cleanup marker blocks prepare: {unsafe_marker}"
            )
        running = ck3_processes()
        if running:
            raise AgentError(
                "refusing to prepare a profile while ck3.exe is running: "
                + "; ".join(running)
            )
        return _prepare_profile_locked(spec)


def _prepare_profile_locked(spec: EnvironmentSpec) -> dict[str, object]:
    """Create or refresh the profile without touching persistent tutorial state."""
    ensure_state_path_safe(spec.state_dir)
    identity = launcher_identity(spec.game_dir)
    if identity["raw_version"] != spec.expected_game_version:
        raise AgentError(
            "unsupported CK3 version: "
            f"{identity['raw_version']!r}, expected {spec.expected_game_version!r}"
        )
    if not spec.game_exe.is_file():
        raise AgentError(f"CK3 executable not found: {spec.game_exe}")
    source_errors = build_release.release_source_errors(build_release.DEFAULT_SOURCE)
    if source_errors:
        raise AgentError("production source is invalid:\n  " + "\n  ".join(source_errors))

    for directory in (
        spec.profile_dir / "mod",
        spec.profile_dir / "mod-content",
        spec.profile_dir / "logs",
        spec.profile_dir / "save games",
        spec.profile_dir / "player" / "game_rules",
        spec.state_dir / "runs",
        spec.state_dir / "control",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    control = spec.state_dir / "control"
    for stale in (
        control / "ck3.json",
        control / "ck3.watchdog_error",
        control / "ck3.pid",
    ):
        stale.unlink(missing_ok=True)
    for stale in control.glob("watchdog-*.ready.json"):
        stale.unlink()

    source_fingerprint = mod_source_fingerprint()
    revision = str(source_fingerprint["git_revision"])
    mod_version = build_release.descriptor_version(build_release.DEFAULT_SOURCE)
    expected_tag = f"v{mod_version}"
    exact_tag = (
        expected_tag
        if expected_tag in source_fingerprint["git_tags_at_revision"]
        and not source_fingerprint["git_dirty"]
        else None
    )
    try:
        _, release_manifest_path, archive_path, release_manifest = (
            build_release.build_release(
                build_release.DEFAULT_SOURCE,
                spec.production_dir,
                revision=revision,
                tag=exact_tag,
                version=mod_version,
            )
        )
    except (OSError, ValueError) as error:
        raise AgentError(f"production projection failed: {error}") from error
    try:
        verify_projection_manifest(spec.production_dir, release_manifest_path, revision)
    except (OSError, ValueError, AgentError) as error:
        raise AgentError(f"production manifest verification failed: {error}") from error

    outer = spec.profile_dir / "mod" / OUTER_DESCRIPTOR_NAME
    write_outer_descriptor(
        spec.production_dir / "descriptor.mod", outer, spec.production_dir
    )
    rules = rule_contract(spec.vanilla_rules)
    presets_path = spec.profile_dir / "player" / "game_rules" / "presets.txt"
    dlc_load_path = spec.profile_dir / "dlc_load.json"
    settings_path = spec.profile_dir / "pdx_settings.txt"
    write_text_atomic(presets_path, render_presets(rules))
    write_json_atomic(
        dlc_load_path,
        {"enabled_mods": [OUTER_DESCRIPTOR_REF], "disabled_dlcs": []},
    )
    write_text_atomic(settings_path, render_settings())
    tutorial = spec.profile_dir / "tutorial.txt"
    tutorial_initialized = False
    if not tutorial.exists():
        write_text_atomic(
            tutorial,
            'last_lesson_chain="reactive_advice"\ncompleted_lessons={\n}\n',
        )
        tutorial_initialized = True

    projection_snapshot = tree_snapshot(spec.production_dir)
    payload: dict[str, object] = {
        "format_version": 1,
        "agent_version": __version__,
        "agent_runtime": agent_runtime_fingerprint(),
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "state_dir": str(spec.state_dir),
        "profile_dir": str(spec.profile_dir),
        "game": {
            **identity,
            "executable": str(spec.game_exe),
            "executable_sha256": sha256_file(spec.game_exe),
            "vanilla_rules": str(spec.vanilla_rules),
            "vanilla_rules_sha256": sha256_file(spec.vanilla_rules),
            "debug_mode": False,
        },
        "mod": {
            "name": EXPECTED_MOD_NAME,
            "git_revision": revision,
            "source_provenance": source_fingerprint,
            "source": str(build_release.DEFAULT_SOURCE.resolve()),
            "production_path": str(spec.production_dir),
            "production_manifest": str(release_manifest_path),
            "production_manifest_sha256": sha256_file(release_manifest_path),
            "production_tree_sha256": snapshot_digest(projection_snapshot),
            "production_file_count": len(projection_snapshot),
            "archive": str(archive_path),
            "release_identity": {
                key: release_manifest.get(key)
                for key in (
                    "format_version",
                    "mod_version",
                    "git_tag",
                    "workshop_item_id",
                )
            },
        },
        "load_profile": {
            "enabled_mods": [OUTER_DESCRIPTOR_REF],
            "disabled_dlcs": [],
            "outer_descriptor": str(outer),
            "outer_descriptor_sha256": sha256_file(outer),
            "dlc_load_sha256": sha256_file(dlc_load_path),
            "presets_sha256": sha256_file(presets_path),
            "pdx_settings_prepared_sha256": sha256_file(settings_path),
            "pdx_settings_contract": settings_contract(
                settings_path.read_text(encoding="utf-8-sig")
            ),
        },
        "rules": rules,
        "display": {
            "language": "l_simp_chinese",
            "resolution": [2560, 1440],
            "mode": "fullscreen",
        },
        "dlc": installed_dlc_fingerprint(spec.game_dir),
        "persistent_tutorial_state": {
            "path": str(tutorial),
            "initialized_this_prepare": tutorial_initialized,
            "policy": "preserve; never read as strategy input or reset between episodes",
        },
        "legality": {
            "production_only": True,
            "single_mod": True,
            "visible_ui_only_for_decisions": True,
            "save_rollback": False,
            "runtime_logs": "environment attestation only; never policy input",
        },
    }
    payload["environment_sha256"] = _contract_digest(payload)
    write_json_atomic(spec.manifest_path, payload)
    verify_profile(spec)
    return payload


def verify_profile(spec: EnvironmentSpec) -> dict[str, object]:
    """Verify the prelaunch contract without reading persistent score storage."""
    ensure_state_path_safe(spec.state_dir)
    unsafe_marker = spec.state_dir / "control" / "unsafe-cleanup.json"
    if unsafe_marker.is_file():
        raise AgentError(
            f"an unresolved unsafe cleanup marker blocks verification: {unsafe_marker}"
        )
    if not spec.manifest_path.is_file():
        raise AgentError(f"environment manifest is missing: {spec.manifest_path}")
    manifest = json.loads(spec.manifest_path.read_text(encoding="utf-8"))
    if manifest.get("environment_sha256") != _contract_digest(manifest):
        raise AgentError("environment manifest contract hash differs")
    if manifest.get("state_dir") != str(spec.state_dir.resolve()) or manifest.get(
        "profile_dir"
    ) != str(spec.profile_dir.resolve()):
        raise AgentError("environment manifest belongs to a different state directory")
    current_agent = agent_runtime_fingerprint()
    if manifest.get("agent_runtime", {}).get("sha256") != current_agent["sha256"]:
        raise AgentError("agent runtime fingerprint differs; prepare a new environment")

    game = manifest.get("game", {})
    current_identity = launcher_identity(spec.game_dir)
    for key in (
        "raw_version",
        "display_version",
        "distribution",
        "launcher_settings_sha256",
    ):
        if game.get(key) != current_identity[key]:
            raise AgentError(f"current launcher identity differs for {key}")
    if current_identity["raw_version"] != spec.expected_game_version:
        raise AgentError(
            f"current game version is not {spec.expected_game_version}: "
            f"{current_identity['raw_version']}"
        )
    if game.get("executable") != str(spec.game_exe.resolve()):
        raise AgentError("environment manifest points to a different CK3 executable")
    if not spec.game_exe.is_file() or game.get("executable_sha256") != sha256_file(
        spec.game_exe
    ):
        raise AgentError("CK3 executable fingerprint differs")
    if game.get("vanilla_rules") != str(spec.vanilla_rules.resolve()) or game.get(
        "vanilla_rules_sha256"
    ) != sha256_file(spec.vanilla_rules):
        raise AgentError("installed vanilla game-rule declarations differ")
    current_dlc = installed_dlc_fingerprint(spec.game_dir)
    if manifest.get("dlc") != current_dlc:
        raise AgentError("installed DLC descriptor fingerprint differs")

    mod = manifest.get("mod", {})
    current_source = mod_source_fingerprint()
    recorded_source = mod.get("source_provenance", {})
    if current_source.get("release_source_sha256") != recorded_source.get(
        "release_source_sha256"
    ):
        raise AgentError("production mod source bytes differ; prepare a new environment")

    load_profile = manifest.get("load_profile", {})
    dlc_load_path = spec.profile_dir / "dlc_load.json"
    dlc_load = json.loads(dlc_load_path.read_text(encoding="utf-8"))
    expected_load = {"enabled_mods": [OUTER_DESCRIPTOR_REF], "disabled_dlcs": []}
    if dlc_load != expected_load:
        raise AgentError(
            f"enabled-mod profile is not the exact singleton: {dlc_load!r}"
        )
    if load_profile.get("dlc_load_sha256") != sha256_file(dlc_load_path):
        raise AgentError("dlc_load.json bytes differ from the prepared contract")
    outer = spec.profile_dir / "mod" / OUTER_DESCRIPTOR_NAME
    if load_profile.get("outer_descriptor") != str(outer.resolve()) or load_profile.get(
        "outer_descriptor_sha256"
    ) != sha256_file(outer):
        raise AgentError("outer descriptor fingerprint differs")
    target = parse_descriptor_target(outer)
    if target != spec.production_dir.resolve() or not is_relative_to(
        target, spec.profile_dir.resolve()
    ):
        raise AgentError(f"outer descriptor escapes the isolated profile: {target}")
    inner_text = (target / "descriptor.mod").read_text(encoding="utf-8-sig")
    if "remote_file_id" in inner_text:
        raise AgentError("production inner descriptor contains remote_file_id")

    release_manifest_path = Path(str(mod.get("production_manifest", "")))
    if not release_manifest_path.is_file() or mod.get(
        "production_manifest_sha256"
    ) != sha256_file(release_manifest_path):
        raise AgentError("production sidecar manifest fingerprint differs")
    try:
        release_manifest = verify_projection_manifest(
            target, release_manifest_path, str(mod.get("git_revision", ""))
        )
    except (OSError, ValueError, AgentError) as error:
        raise AgentError(f"production tree differs from manifest: {error}") from error
    current_tree_hash = snapshot_digest(tree_snapshot(target))
    if current_tree_hash != mod.get("production_tree_sha256"):
        raise AgentError("production tree fingerprint differs from environment manifest")
    expected_release_identity = {
        key: release_manifest.get(key)
        for key in ("format_version", "mod_version", "git_tag", "workshop_item_id")
    }
    if mod.get("release_identity") != expected_release_identity:
        raise AgentError("production release identity differs from the environment manifest")

    presets_path = spec.profile_dir / "player" / "game_rules" / "presets.txt"
    if load_profile.get("presets_sha256") != sha256_file(presets_path):
        raise AgentError("game-rule preset bytes differ from the prepared contract")
    preset_text = presets_path.read_text(encoding="utf-8-sig")
    actual_settings, actual_ironman = parsed_preset_settings(preset_text)
    current_rules = rule_contract(spec.vanilla_rules)
    if manifest.get("rules") != current_rules:
        raise AgentError("game-rule source/profile fingerprint differs")
    expected_settings = [entry["setting"] for entry in current_rules["profile"]]
    if actual_settings != expected_settings or actual_ironman:
        raise AgentError("LastAppliedRules differs from the growth + 100% contract")
    settings_path = spec.profile_dir / "pdx_settings.txt"
    actual_settings_contract = settings_contract(
        settings_path.read_text(encoding="utf-8-sig")
    )
    if actual_settings_contract != load_profile.get("pdx_settings_contract"):
        raise AgentError("pdx_settings semantic contract differs")
    if not (spec.profile_dir / "tutorial.txt").is_file():
        raise AgentError("persistent tutorial storage is missing")
    return manifest


def ck3_process_inventory() -> dict[str, object]:
    """Fail-closed, cross-checked inventory of every running CK3 process."""
    if os.name != "nt":
        return {
            "tasklist_returncode": None,
            "tasklist_pids": [],
            "wmi_pids": [],
            "processes": [],
        }
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ck3.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=10,
        )
    except subprocess.TimeoutExpired as error:
        raise UnsafeCleanupError("CK3 tasklist inventory timed out") from error
    if result.returncode != 0 or result.stderr.strip():
        raise UnsafeCleanupError(
            "CK3 tasklist inventory failed: "
            f"rc={result.returncode}, stderr={result.stderr.strip()!r}"
        )
    tasklist_pids: list[int] = []
    unexpected: list[str] = []
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('"'):
            try:
                row = next(csv.reader([stripped]))
                if len(row) < 2 or row[0].casefold() != "ck3.exe":
                    raise ValueError("unexpected tasklist row")
                tasklist_pids.append(int(row[1]))
            except (ValueError, csv.Error) as error:
                raise UnsafeCleanupError(
                    f"CK3 tasklist inventory could not be parsed: {stripped!r}"
                ) from error
        elif stripped.casefold().startswith(("info:", "信息:")):
            continue
        else:
            unexpected.append(stripped)
    if unexpected:
        raise UnsafeCleanupError(
            f"CK3 tasklist inventory returned unexpected output: {unexpected!r}"
        )
    wmi_script = (
        "$rows=@(Get-CimInstance -ClassName Win32_Process "
        "-Filter \"Name='ck3.exe'\"|ForEach-Object{[pscustomobject]@{"
        "pid=[int]$_.ProcessId;parent_pid=[int]$_.ParentProcessId;"
        "name=[string]$_.Name;executable=[string]$_.ExecutablePath;"
        "creation_date=$_.CreationDate.ToUniversalTime().ToString('o')}});"
        "ConvertTo-Json -InputObject $rows -Compress"
    )
    try:
        wmi_result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                wmi_script,
            ],
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
            timeout=15,
        )
    except subprocess.TimeoutExpired as error:
        raise UnsafeCleanupError("CK3 WMI inventory timed out") from error
    if wmi_result.returncode != 0 or wmi_result.stderr.strip():
        raise UnsafeCleanupError(
            "CK3 WMI inventory failed: "
            f"rc={wmi_result.returncode}, stderr={wmi_result.stderr.strip()!r}"
        )
    try:
        decoded = json.loads(wmi_result.stdout)
        if not isinstance(decoded, list):
            raise ValueError("WMI JSON root is not an array")
        processes = sorted(
            (
                {
                    "pid": int(item["pid"]),
                    "parent_pid": int(item["parent_pid"]),
                    "name": str(item["name"]),
                    "executable": str(item["executable"] or ""),
                    "creation_date": str(item["creation_date"]),
                }
                for item in decoded
            ),
            key=lambda item: int(item["pid"]),
        )
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        raise UnsafeCleanupError(
            f"CK3 WMI inventory returned malformed JSON: {wmi_result.stdout!r}"
        ) from error
    wmi_pids = [int(item["pid"]) for item in processes]
    if sorted(tasklist_pids) != wmi_pids:
        raise UnsafeCleanupError(
            "CK3 process inventories disagree: "
            f"tasklist={sorted(tasklist_pids)!r}, wmi={wmi_pids!r}"
        )
    return {
        "tasklist_returncode": result.returncode,
        "tasklist_pids": sorted(tasklist_pids),
        "wmi_pids": wmi_pids,
        "processes": processes,
    }


def ck3_processes() -> list[str]:
    return [
        json.dumps(process, ensure_ascii=False, sort_keys=True)
        for process in ck3_process_inventory()["processes"]
    ]


def doctor(spec: EnvironmentSpec, require_prepared: bool = False) -> dict[str, object]:
    ensure_state_path_safe(spec.state_dir)
    identity = launcher_identity(spec.game_dir)
    errors: list[str] = []
    if os.name != "nt":
        errors.append("CK3 desktop operation requires Windows")
    if identity["raw_version"] != spec.expected_game_version:
        errors.append(
            f"game version {identity['raw_version']!r} != {spec.expected_game_version!r}"
        )
    if not spec.game_exe.is_file():
        errors.append(f"CK3 executable not found: {spec.game_exe}")
    if ck3_processes():
        errors.append("another ck3.exe is running")
    source_errors = build_release.release_source_errors(build_release.DEFAULT_SOURCE)
    errors.extend(f"production source: {error}" for error in source_errors)
    desktop: list[int] | None = None
    try:
        import pyautogui

        pyautogui.FAILSAFE = True
        desktop = list(pyautogui.size())
        if desktop != [2560, 1440]:
            errors.append(f"desktop must be 2560x1440, got {desktop[0]}x{desktop[1]}")
    except Exception as error:  # pragma: no cover - depends on interactive desktop
        errors.append(f"desktop inspection failed: {error}")
    if require_prepared:
        try:
            verify_profile(spec)
        except AgentError as error:
            errors.append(str(error))
    report = {
        "ok": not errors,
        "errors": errors,
        "game": identity,
        "game_executable": str(spec.game_exe),
        "state_dir": str(spec.state_dir),
        "profile_dir": str(spec.profile_dir),
        "desktop": desktop,
        "protected_roots": [
            {"label": label, "path": str(path)} for label, path in protected_roots()
        ],
    }
    if errors:
        raise AgentError("doctor failed:\n  " + "\n  ".join(errors))
    return report

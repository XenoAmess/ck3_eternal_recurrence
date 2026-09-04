#!/usr/bin/env python3
"""Create one frozen ZhongGuo phase-two seed capture attempt.

The caller supplies an immutable clean source export and every machine-local
runtime dependency.  This runner never imports the invoking worktree's CK3
modules or guesses a domain selector.  Its only visual exception is the
shared, owner-authorized Paradox legal-agreement gate; seed observation and
mutation remain MCP-only.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

# The runner is executed from inside the immutable clean export.  Set the
# process-wide guard before importing even the optional adapter below: a
# module import can otherwise leave a ``tools/__pycache__`` entry before the
# source manifest is taken.  Child Python commands receive the same guard (and
# an explicit ``-B`` at their call site), while the detached watchdog has its
# own equivalent entrypoint guard.
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

import threading
import time
import traceback
from types import ModuleType
from typing import Any, Callable
import zipfile

import kaishek_preflight
from zg361_phase2_acceptance_observer_gate import evaluate_observer_gate


EXPECTED_ENABLED_MODS = (
    "mod/zg361_acceptance.mod",
    "mod/zga_acceptance_fixture.mod",
)
# These are the four generated B2 providers that produced the 93 first-use
# optional-variable diagnostics in the explicit-AND seed refresh.  A full
# cumulative B3+ seed run must never mount an older copy while claiming a
# newer clean-source commit.  Keep the paths narrow and evidence-backed: this
# is a byte-equivalence gate for the observed stale-product failure, not a
# second whole-tree release verifier.
CRITICAL_B2_PRODUCT_PATHS = (
    "common/scripted_effects/zg361_b2_debt_consumers_effects.txt",
    "common/scripted_effects/zg361_b2_069_delivery_effects.txt",
    "common/scripted_effects/zg361_b2_072_access_audit_effects.txt",
    "common/scripted_effects/zg361_b2_081_projection_access_effects.txt",
)
SEED_EVENT_DEFINITION_KEY = "zga_phase2_seed.1"
KNOWN_PRE_BOOTSTRAP_EVENT = {
    "source_save_sha256": (
        "bfc73fd9e7e80145cdf39aabc66bc2d731881122adab0cc0ba675fa07d1e6733"
    ),
    "event_definition_key": "zg361.4",
    "date_raw": 53147016,
    "root_character_id": 29037,
    "reviewing_superior_character_id": 32904,
    "option_count": 4,
    "selected_option_number": 1,
    "selected_native_option_index": 0,
}
KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT = {
    # This is not a wildcard for vanilla events.  It is the exact incidental
    # event observed while replaying this immutable checkpoint.
    "source_save_sha256": (
        "bfc73fd9e7e80145cdf39aabc66bc2d731881122adab0cc0ba675fa07d1e6733"
    ),
    "event_definition_key": "spymaster_task.0381",
    "date_raw": 53148768,
    "root_character_id": 29037,
    "excluded_character_to_hook_ids": (29037, 32904),
    "option_count": 2,
    # Option 1 spends gold and fabricates a hook.  Option 2 is the narrowest
    # available dismissal: it spends no resource and only grants the selected
    # courtier a decaying +30 opinion of root.
    "selected_option_number": 2,
    "selected_native_option_index": 1,
}
LOADER_FATAL_STALL_SECONDS = 45.0
DEFAULT_LOADER_TIMEOUT_SECONDS = 300.0
DEFAULT_NATIVE_READINESS_TIMEOUT_SECONDS = 300.0
DEFAULT_EVENT_TIMEOUT_SECONDS = 300.0
DEFAULT_BINDING_TIMEOUT_SECONDS = 300.0
DEFAULT_KEYBOARD_WATCHDOG_INTERVAL_SECONDS = 15.0
DEFAULT_FRONTEND_FIRST_TIMEOUT_SECONDS = 180.0
# Shader caches can live on a slow/networked volume.  Provenance must never
# turn a preflight into an unbounded recursive walk, so retain a deterministic
# bounded sample and state explicitly when it was truncated.
CACHE_PROVENANCE_SCAN_LIMIT = 512
PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_KEY = (
    "phase2_wrapper_consumer_edge_observer_v1"
)
PHASE2_PRODUCER_CORRELATION_OBSERVER_KEY = (
    "phase2_producer_consumer_correlation_observer_v1"
)
GIT_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
PIPE_PREFIX = "\\\\.\\pipe\\"
WINDOWS_ENGLISH_US_HKL = 0x04090409
WM_INPUTLANGCHANGEREQUEST = 0x0050
STEAM_CK3_APP_ID = "1158310"
REPOSITORY_GAME_DIR = Path(__file__).resolve().parents[1] / "Crusader Kings III"
STEAM_GAME_INSTALL_DIR_NAME = "Crusader Kings III"
# Keep automatic resolution conservative: a repository copy can be useful for
# static fixtures, but it is not a supported launch target.  It must be passed
# explicitly through ``--game-dir``/``XAR_CK3_GAME_DIR`` so a missing Steam
# install cannot silently send a live run into the wrong tree.
AUTOMATIC_GAME_DIR_REQUIRES_STEAM = True
_STEAM_VDF_PATH_PATTERN = re.compile(
    r'(?im)^\s*"path"\s+"(?P<path>[^"]+)"'
)
_STEAM_INSTALL_DIR_PATTERN = re.compile(
    r'(?im)^\s*"installdir"\s+"(?P<name>[^"]+)"'
)


def _game_dir_is_valid(path: Path) -> bool:
    """Return whether a directory contains the exact CK3 launch inputs."""

    return (
        (path / "binaries" / "ck3.exe").is_file()
        and (path / "game" / "common" / "game_rules" / "00_game_rules.txt").is_file()
    )


def _steam_library_roots() -> list[Path]:
    """Discover Steam library roots without changing any user configuration."""

    candidates: list[Path] = []
    explicit_steam = os.environ.get("XAR_STEAM_DIR")
    if explicit_steam:
        candidates.append(Path(os.path.expandvars(explicit_steam)).expanduser())
    # The normal Windows installation locations are cheap to probe.  A
    # registry read is intentionally avoided here so the resolver remains
    # deterministic in the frozen runner and in offline unit tests.
    candidates.extend(
        Path(value)
        for value in (
            os.path.join(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"), "Steam"),
            os.path.join(os.environ.get("ProgramFiles", "C:/Program Files"), "Steam"),
        )
    )
    # Some managed hosts expose the Steam library on a mounted drive while
    # leaving the primary Steam client on C:.  Probe the conventional
    # ``<drive>:\\SteamLibrary`` leaf as a read-only fallback.
    if os.name == "nt":
        candidates.extend(Path(f"{drive}:\\SteamLibrary") for drive in "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    roots: list[Path] = []
    seen: set[str] = set()

    def add(path: Path) -> None:
        resolved = path.expanduser().resolve()
        key = str(resolved).casefold()
        if key not in seen:
            seen.add(key)
            roots.append(resolved)

    for candidate in candidates:
        candidate = candidate.expanduser().resolve()
        add(candidate)
        vdf = candidate / "steamapps" / "libraryfolders.vdf"
        if not vdf.is_file():
            continue
        try:
            text = vdf.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue
        for match in _STEAM_VDF_PATH_PATTERN.finditer(text):
            add(Path(match.group("path").replace("\\\\", "\\")))
    return roots


def resolve_ck3_game_dir(
    requested: Path | None = None,
) -> tuple[Path, str, tuple[dict[str, object], ...]]:
    """Select CK3's actual Steam install while preserving explicit paths.

    A CLI ``--game-dir`` or ``XAR_CK3_GAME_DIR`` override is authoritative and
    is never replaced.  Automatic discovery is used only when neither is
    supplied; every candidate and the selected source are returned for the
    immutable runner report.
    """

    if requested is not None:
        selected = Path(requested).expanduser().resolve()
        return (
            selected,
            "explicit-cli",
            (
                {
                    "path": str(selected),
                    "source": "explicit-cli",
                    "valid": _game_dir_is_valid(selected),
                },
            ),
        )
    env_override = os.environ.get("XAR_CK3_GAME_DIR")
    if env_override:
        selected = Path(os.path.expandvars(env_override)).expanduser().resolve()
        return (
            selected,
            "explicit-env",
            (
                {
                    "path": str(selected),
                    "source": "explicit-env",
                    "valid": _game_dir_is_valid(selected),
                },
            ),
        )

    candidates: list[dict[str, object]] = []
    seen: set[str] = set()

    def record(path: Path, source: str) -> None:
        resolved = path.expanduser().resolve()
        key = str(resolved).casefold()
        if key in seen:
            return
        seen.add(key)
        candidates.append(
            {
                "path": str(resolved),
                "source": source,
                "valid": _game_dir_is_valid(resolved),
            }
        )

    for library in _steam_library_roots():
        steamapps = library / "steamapps"
        manifest = steamapps / f"appmanifest_{STEAM_CK3_APP_ID}.acf"
        install_name = STEAM_GAME_INSTALL_DIR_NAME
        if manifest.is_file():
            try:
                manifest_text = manifest.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError):
                manifest_text = ""
            match = _STEAM_INSTALL_DIR_PATTERN.search(manifest_text)
            if match is not None and match.group("name").strip():
                install_name = match.group("name").strip()
        record(
            steamapps / "common" / install_name,
            "steam-library",
        )

    repository = REPOSITORY_GAME_DIR.expanduser().resolve()
    # Retain the repository candidate as evidence, but never select it during
    # automatic resolution.  The old fallback made a typo/missing Steam
    # library look like a valid launch and was the exact failure mode seen in
    # the Phase2 frozen runner.  An operator who intentionally wants the copy
    # must provide it explicitly via one of the overrides above.
    record(repository, "repository-not-selected")
    for candidate in candidates:
        if (
            candidate["valid"] is True
            and candidate["source"] != "repository-not-selected"
        ):
            return Path(str(candidate["path"])), str(candidate["source"]), tuple(candidates)
    raise SeedCaptureError(
        "automatic CK3 game discovery found no valid SteamLibrary install; "
        "pass --game-dir (or XAR_CK3_GAME_DIR) only when an explicit path is "
        "intended",
        {
            "automatic_requires_steam": AUTOMATIC_GAME_DIR_REQUIRES_STEAM,
            "repository_candidate": str(repository),
            "candidates": candidates,
        },
    )


class SeedCaptureError(RuntimeError):
    """A typed seed-capture contract failed."""

    def __init__(self, message: str, evidence: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.evidence = evidence or {}


@dataclass(frozen=True)
class CaptureConfig:
    clean_source: Path
    attempt_dir: Path
    artifacts_dir: Path
    source_zip: Path
    frozen_git_sha: str
    game_dir: Path
    bridge_dll: Path
    bridge_injector: Path
    pipe_name: str
    seed_contract: Path | None = None
    loader_timeout_seconds: float = DEFAULT_LOADER_TIMEOUT_SECONDS
    native_readiness_timeout_seconds: float = (
        DEFAULT_NATIVE_READINESS_TIMEOUT_SECONDS
    )
    event_timeout_seconds: float = DEFAULT_EVENT_TIMEOUT_SECONDS
    binding_timeout_seconds: float = DEFAULT_BINDING_TIMEOUT_SECONDS
    keyboard_watchdog_interval_seconds: float = (
        DEFAULT_KEYBOARD_WATCHDOG_INTERVAL_SECONDS
    )
    # Optional static handshake for the next private Phase-2 observer.  The
    # contract is part of the frozen source; its native seam manifest remains
    # external until the native implementation is ready.
    list_domain_observer_gate: bool = False
    acceptance_observer_manifest: Path | None = None
    # CLI-only mode that stops before any native session or bridge transport
    # is started.  Full capture remains the default for existing callers.
    preflight_only: bool = False
    # Private loader-only observation: launch/bind the exact bridge and sample
    # cached heartbeats without inspecting the desktop or sending UI/gameplay
    # input.  This mode deliberately does not attempt seed capture.
    native_observer_only: bool = False
    # Profile settings template for a formal isolated run.  When unset, the
    # runner only inspects the real local CK3 profile for provenance; it never
    # copies operator-specific renderer values and a native launch is blocked.
    # No-launch/legacy callers may omit it and retain inspection-only behavior.
    profile_settings_template: Path | None = None
    frontend_first_load_save_name: str | None = None
    frontend_first_timeout_seconds: float = (
        DEFAULT_FRONTEND_FIRST_TIMEOUT_SECONDS
    )
    # ``game_dir`` remains an explicit field for API callers.  CLI callers may
    # omit it and use ``resolve_ck3_game_dir``; the selected source/candidates
    # are retained as immutable provenance rather than silently rewriting a
    # caller-provided path.
    game_dir_source: str = "explicit-cli"
    game_dir_candidates: tuple[dict[str, object], ...] = ()
    # Optional immutable bundle manifest emitted by the Release bridge build.
    # When supplied it is checked against the selected DLL/injector before a
    # launch and copied into the receipt as build provenance.  Leaving it
    # unset preserves API compatibility for synthetic/unit callers.
    bridge_bundle_manifest: Path | None = None
    # Phase-2 product projection controls.  ``broad`` preserves the historical
    # copy-all runtime projection; ``core`` resolves the checked-in historical
    # 51-file manifest.  Other named groups require an explicit manifest.  An
    # external product source is useful for replaying an exact historical
    # projection (for example the offline bisect trees) while the frozen clean
    # source continues to provide the runner and static contracts.
    product_projection: str = "broad"
    product_projection_manifest: Path | None = None
    product_source_override: Path | None = None

    def resolved(self) -> "CaptureConfig":
        clean_source = self.clean_source.resolve()
        return replace(
            self,
            clean_source=clean_source,
            attempt_dir=self.attempt_dir.resolve(),
            artifacts_dir=self.artifacts_dir.resolve(),
            source_zip=self.source_zip.resolve(),
            frozen_git_sha=self.frozen_git_sha.lower(),
            game_dir=self.game_dir.resolve(),
            bridge_dll=self.bridge_dll.resolve(),
            bridge_injector=self.bridge_injector.resolve(),
            seed_contract=(
                self.seed_contract.resolve()
                if self.seed_contract is not None
                else clean_source / "tools" / "zg361_phase2_seed_contract.json"
            ),
            acceptance_observer_manifest=(
                self.acceptance_observer_manifest.resolve()
                if self.acceptance_observer_manifest is not None
                else None
            ),
            profile_settings_template=(
                self.profile_settings_template.resolve()
                if self.profile_settings_template is not None
                else None
            ),
            bridge_bundle_manifest=(
                self.bridge_bundle_manifest.resolve()
                if self.bridge_bundle_manifest is not None
                else None
            ),
            product_projection=self.product_projection,
            product_projection_manifest=(
                self.product_projection_manifest.resolve()
                if self.product_projection_manifest is not None
                else None
            ),
            product_source_override=(
                self.product_source_override.resolve()
                if self.product_source_override is not None
                else None
            ),
            frontend_first_load_save_name=self.frontend_first_load_save_name,
        )

    @property
    def state_dir(self) -> Path:
        return self.attempt_dir / "native-state"

    @property
    def profile_dir(self) -> Path:
        return self.state_dir / "profile"

    @property
    def product_source(self) -> Path:
        return (
            self.product_source_override
            if self.product_source_override is not None
            else self.clean_source / "mod_zhongguo_style"
        )

    @property
    def fixture_source(self) -> Path:
        return (
            self.clean_source
            / "tools"
            / "fixtures"
            / "zg361_phase2_seed_bootstrap"
        )

    @property
    def game_executable(self) -> Path:
        return self.game_dir / "binaries" / "ck3.exe"

    @property
    def vanilla_game_rules(self) -> Path:
        return self.game_dir / "game" / "common" / "game_rules" / "00_game_rules.txt"

    @property
    def acceptance_observer_contract(self) -> Path:
        return (
            self.clean_source
            / "tools"
            / "zg361_phase2_list_domain_acceptance_contract.json"
        )


@dataclass(frozen=True)
class RuntimeBindings:
    acceptance: Any
    zgrun: Any
    seed: Any
    driver_factory: Callable[..., Any]
    service_factory: Callable[[Any], Any]
    bridge_unavailable_error: type[BaseException]
    pre_submission_revision_mismatch_error: type[BaseException]
    loader_stage_error: type[BaseException]
    wait_for_loader_stage: Callable[..., dict[str, Any]]
    keyboard_layout_attestor: Callable[[int, Path, str], dict[str, Any]]
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], None] = time.sleep


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _bridge_artifact_row(path: Path, label: str) -> dict[str, object]:
    """Return the immutable identity of one bridge artifact."""

    if not path.is_file():
        raise SeedCaptureError(f"{label} is missing: {path}")
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path).upper(),
    }


def bridge_bundle_provenance(config: CaptureConfig) -> dict[str, object] | None:
    """Validate and project an optional Release bridge bundle manifest.

    A binary hash alone cannot establish how a bridge was built.  If the
    Release build emitted ``bundle-manifest.json``, bind its source commit,
    configuration, feature flags, compiler and adjacent DLL/injector hashes
    to the seed receipt.  The manifest is advisory when omitted for backwards
    compatibility; supplying a malformed or non-Release manifest is a typed
    preflight error rather than a best-effort guess.
    """

    manifest_path = config.bridge_bundle_manifest
    if manifest_path is None:
        return None
    if not manifest_path.is_file():
        raise SeedCaptureError(
            f"bridge bundle manifest is missing: {manifest_path}"
        )
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SeedCaptureError(
            f"cannot read bridge bundle manifest {manifest_path}: {error}"
        ) from error
    if not isinstance(payload, dict):
        raise SeedCaptureError("bridge bundle manifest root must be an object")
    build = payload.get("build")
    artifacts = payload.get("artifacts")
    if not isinstance(build, dict) or not isinstance(artifacts, dict):
        raise SeedCaptureError(
            "bridge bundle manifest must contain build and artifacts objects"
        )
    configuration = build.get("configuration")
    if configuration != "Release":
        raise SeedCaptureError(
            "Phase2 seed capture requires a Release bridge bundle; "
            f"manifest configuration={configuration!r}"
        )
    dll_row = artifacts.get("dll")
    injector_row = artifacts.get("injector")
    if not isinstance(dll_row, dict) or not isinstance(injector_row, dict):
        raise SeedCaptureError(
            "bridge bundle manifest artifacts.dll/injector are malformed"
        )
    selected_dll = _bridge_artifact_row(config.bridge_dll, "bridge DLL")
    selected_injector = _bridge_artifact_row(
        config.bridge_injector, "bridge injector"
    )

    def manifest_identity(row: dict[str, object], label: str) -> tuple[str, int]:
        digest = row.get("sha256")
        size = row.get("bytes")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
            raise SeedCaptureError(
                f"bridge bundle manifest {label} SHA-256 is malformed"
            )
        if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
            raise SeedCaptureError(
                f"bridge bundle manifest {label} size is malformed"
            )
        return digest.upper(), size

    expected_dll = manifest_identity(dll_row, "DLL")
    expected_injector = manifest_identity(injector_row, "injector")
    matches = {
        "dll_sha256": selected_dll["sha256"] == expected_dll[0],
        "dll_bytes": selected_dll["bytes"] == expected_dll[1],
        "injector_sha256": selected_injector["sha256"] == expected_injector[0],
        "injector_bytes": selected_injector["bytes"] == expected_injector[1],
    }
    if not all(matches.values()):
        raise SeedCaptureError(
            "selected bridge artifacts do not match the Release bundle manifest",
            {
                "manifest": str(manifest_path.resolve()),
                "selected": {"dll": selected_dll, "injector": selected_injector},
                "manifest_artifacts": {"dll": dll_row, "injector": injector_row},
                "matches": matches,
            },
        )
    pe_imports = artifacts.get("pe_imports")
    if isinstance(pe_imports, dict) and pe_imports.get("debug_crt_present") is True:
        raise SeedCaptureError(
            "Release bridge bundle manifest reports debug CRT imports"
        )
    source = payload.get("source")
    source = source if isinstance(source, dict) else {}
    cmake_flags = payload.get("cmake_flags")
    cmake_flags = cmake_flags if isinstance(cmake_flags, dict) else None
    return {
        "manifest_path": str(manifest_path.resolve()),
        "manifest_sha256": sha256_file(manifest_path).upper(),
        "kind": payload.get("kind"),
        "status": payload.get("status"),
        "source_git_sha": source.get("git_head"),
        "source_fingerprint_sha256": source.get("fingerprint_sha256"),
        "build_dir": build.get("build_dir"),
        "build_type": configuration,
        "generator": build.get("generator"),
        "compiler": build.get("compiler"),
        "built_at_local": payload.get("built_at_local"),
        "compile_link": build.get("compile_link"),
        "tests_ran": build.get("tests_ran"),
        "cmake_flags": cmake_flags,
        "dll": selected_dll,
        "injector": selected_injector,
        "manifest_artifacts": {"dll": dll_row, "injector": injector_row},
        "debug_crt_present": (
            pe_imports.get("debug_crt_present")
            if isinstance(pe_imports, dict)
            else None
        ),
        "matches": matches,
    }


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def verify_critical_b2_product_bytes(
    config: CaptureConfig,
    *,
    mounted_product: Path | None = None,
) -> dict[str, Any]:
    """Prove the four failure-relevant B2 providers equal clean source bytes.

    The first call checks the external/staged product before projection.  The
    second call adds the actual isolated product target returned by bootstrap,
    closing the gap where a correct source could still materialize a stale or
    incomplete mount.  Direct byte comparison is intentional; SHA-256 and
    sizes are retained only as operator-readable provenance.
    """

    clean_root = config.clean_source / "mod_zhongguo_style"
    targets = {"product_source": config.product_source}
    if mounted_product is not None:
        targets["mounted_product"] = mounted_product.resolve()

    rows: list[dict[str, Any]] = []
    mismatches: list[dict[str, str]] = []
    for relative in CRITICAL_B2_PRODUCT_PATHS:
        clean_path = clean_root / relative
        clean_exists = clean_path.is_file()
        clean_bytes = clean_path.read_bytes() if clean_exists else None
        clean_identity = {
            "path": str(clean_path.resolve()),
            "exists": clean_exists,
            "bytes": len(clean_bytes) if clean_bytes is not None else None,
            "sha256": (
                hashlib.sha256(clean_bytes).hexdigest()
                if clean_bytes is not None
                else None
            ),
        }
        comparisons: dict[str, dict[str, Any]] = {}
        for target_name, target_root in targets.items():
            target_path = target_root / relative
            target_exists = target_path.is_file()
            target_bytes = target_path.read_bytes() if target_exists else None
            byte_identical = (
                clean_bytes is not None
                and target_bytes is not None
                and target_bytes == clean_bytes
            )
            comparisons[target_name] = {
                "path": str(target_path.resolve()),
                "exists": target_exists,
                "bytes": len(target_bytes) if target_bytes is not None else None,
                "sha256": (
                    hashlib.sha256(target_bytes).hexdigest()
                    if target_bytes is not None
                    else None
                ),
                "byte_identical_to_clean_source": byte_identical,
            }
            if not byte_identical:
                mismatches.append(
                    {
                        "path": relative,
                        "target": target_name,
                        "reason": (
                            "clean-source-file-missing"
                            if clean_bytes is None
                            else "target-file-missing"
                            if target_bytes is None
                            else "bytes-differ"
                        ),
                    }
                )
        rows.append(
            {
                "path": relative,
                "clean_source": clean_identity,
                "comparisons": comparisons,
            }
        )

    return {
        "schema_version": 1,
        "kind": "zg361_critical_b2_product_byte_equivalence",
        "result": "GREEN" if not mismatches else "RED",
        "required_paths": list(CRITICAL_B2_PRODUCT_PATHS),
        "checked_targets": list(targets),
        "all_byte_identical": not mismatches,
        "mismatches": mismatches,
        "files": rows,
    }


def enforce_critical_b2_product_bytes(
    config: CaptureConfig,
    artifacts: Path,
    *,
    mounted_product: Path | None = None,
) -> dict[str, Any]:
    """Persist and enforce the critical B2 source/product/mount contract."""

    evidence = verify_critical_b2_product_bytes(
        config,
        mounted_product=mounted_product,
    )
    write_json(artifacts / "critical-b2-product-byte-equivalence.json", evidence)
    if evidence["result"] != "GREEN":
        raise SeedCaptureError(
            "critical B2 product files are not byte-identical to clean source",
            evidence,
        )
    return evidence


def _settings_file_is_full(path: Path) -> bool:
    """Recognize a real CK3 renderer settings file, not the tiny bootstrap."""

    try:
        text = path.read_text(encoding="utf-8-sig")
        size = path.stat().st_size
    except (OSError, UnicodeError):
        return False
    # The runner's intentional bootstrap is ~375 bytes/14 lines.  A file
    # written by CK3 after a normal launcher run contains the renderer and
    # system option sections and is materially larger.  Keep this heuristic
    # conservative; it only decides whether an isolated copy is useful and
    # never changes the user's profile.
    return (
        size > 1024
        and len(text.splitlines()) >= 20
        and '"game"={' in text
        and '"Graphics"={' in text
        and '"System"={' in text
    )


def _profile_settings_candidates(config: CaptureConfig) -> list[tuple[Path, str]]:
    """Return only explicitly selected settings templates.

    The real profile is intentionally *not* a default copy source: its
    renderer/GPU values are operator-specific and can differ from the known
    formal baseline.  It is inspected and recorded separately below.
    """

    candidates: list[tuple[Path, str]] = []
    if config.profile_settings_template is not None:
        candidates.append((config.profile_settings_template, "explicit-config"))
    env_template = os.environ.get("XAR_CK3_SETTINGS_TEMPLATE")
    if env_template:
        candidates.append(
            (
                Path(os.path.expandvars(env_template)).expanduser(),
                "explicit-env",
            )
        )
    unique: list[tuple[Path, str]] = []
    seen: set[str] = set()
    for path, source in candidates:
        resolved = path.expanduser().resolve()
        key = str(resolved).casefold()
        if key not in seen:
            seen.add(key)
            unique.append((resolved, source))
    return unique


def _real_profile_settings_path() -> Path:
    override = os.environ.get("XAR_REAL_CK3_PROFILE")
    if override:
        return (
            Path(os.path.expandvars(override)).expanduser()
            / "pdx_settings.txt"
        ).resolve()
    return (
        Path.home()
        / "Documents"
        / "Paradox Interactive"
        / "Crusader Kings III"
        / "pdx_settings.txt"
    ).resolve()


def _directory_provenance(path: Path) -> dict[str, Any]:
    """Describe a cache tree with a bounded, honest metadata scan.

    ``Path.rglob`` over the real CK3 shader cache was observed to take tens of
    seconds on the mounted Steam volume.  This function is called during
    profile preflight, so an unbounded walk would itself become a startup
    failure.  We walk directories with ``os.scandir`` and retain at most
    ``CACHE_PROVENANCE_SCAN_LIMIT`` regular-file rows.  ``complete`` and
    ``scanned_*`` distinguish a complete small tree from a truncated sample;
    no partial count is presented as the cache's total size.
    """

    root = Path(path).expanduser().resolve()
    rows: list[dict[str, object]] = []
    scanned_bytes = 0
    visited_directories = 0
    scan_error: str | None = None
    truncated = False
    pending: list[Path] = [root] if root.is_dir() else []
    while pending and not truncated:
        current = pending.pop()
        visited_directories += 1
        try:
            with os.scandir(current) as stream:
                entries = sorted(stream, key=lambda entry: entry.name.casefold())
        except OSError as error:
            scan_error = f"{type(error).__name__}: {error}"
            continue
        for entry in entries:
            try:
                if entry.is_dir(follow_symlinks=False):
                    pending.append(Path(entry.path))
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                if len(rows) >= CACHE_PROVENANCE_SCAN_LIMIT:
                    truncated = True
                    break
                stat = entry.stat(follow_symlinks=False)
            except OSError as error:
                scan_error = f"{type(error).__name__}: {error}"
                continue
            size = int(stat.st_size)
            scanned_bytes += size
            # ``entry.path`` is rooted below ``root`` and symlinks are not
            # followed, so a lexical relative path avoids an extra networked
            # ``resolve()`` call for every cache file.
            relative = os.path.relpath(entry.path, root).replace("\\", "/")
            rows.append(
                {
                    "path": relative,
                    "bytes": size,
                    "mtime_ns": int(stat.st_mtime_ns),
                }
            )
    # A deterministic ordering is important even though directory traversal is
    # stack-based; it also makes the signature stable across equivalent trees.
    rows.sort(key=lambda row: str(row["path"]).casefold())
    canonical = json.dumps(
        rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    exists = root.is_dir()
    return {
        "path": str(root),
        "exists": exists,
        "complete": bool(exists and not truncated and scan_error is None),
        "truncated": truncated,
        "scan_limit": CACHE_PROVENANCE_SCAN_LIMIT,
        "scanned_file_count": len(rows),
        "scanned_bytes": scanned_bytes,
        # Keep legacy aliases for consumers that only display a count/hash;
        # ``complete`` tells them whether these are totals or a bounded sample.
        "file_count": len(rows),
        "bytes": scanned_bytes,
        "visited_directories": visited_directories,
        "signature_sha256": hashlib.sha256(canonical).hexdigest(),
        "algorithm": (
            "sha256(canonical-json[path,bytes,mtime_ns])-bounded-scandir"
        ),
        "scan_error": scan_error,
    }


def _warm_shadercache_manifest(path: Path) -> dict[str, Any]:
    """Return a byte-bound manifest for an explicitly pinned CK3 cache.

    The bounded ``_directory_provenance`` sample above is useful for cheap
    diagnostics, but it cannot establish that a cache was copied completely
    (the known-good cache has thousands of files).  A cache selected for a
    formal Phase2 launch is an explicit operator input, so pay the one-time
    full-tree cost here and compare the resulting content digest after copy.
    The source is never modified.
    """

    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        return {
            "path": str(root),
            "exists": False,
            "ready": False,
            "failure_reason": "shadercache directory is missing",
            "file_count": 0,
            "bytes": 0,
            "tree_sha256": None,
            "required_lanes": {},
            "symlink_count": 0,
        }

    symlinks = [
        item
        for item in root.rglob("*")
        if item.is_symlink()
    ]
    if symlinks:
        return {
            "path": str(root),
            "exists": True,
            "ready": False,
            "failure_reason": "shadercache contains symlinks",
            "file_count": 0,
            "bytes": 0,
            "tree_sha256": None,
            "required_lanes": {},
            "symlink_count": len(symlinks),
            "symlink_paths": [
                str(item.relative_to(root)).replace("\\", "/")
                for item in symlinks[:16]
            ],
        }

    try:
        manifest = tree_manifest(root)
    except (OSError, UnicodeError, ValueError) as error:
        return {
            "path": str(root),
            "exists": True,
            "ready": False,
            "failure_reason": f"shadercache manifest failed: {type(error).__name__}: {error}",
            "file_count": 0,
            "bytes": 0,
            "tree_sha256": None,
            "required_lanes": {},
            "symlink_count": 0,
        }

    entries = manifest.get("files", [])
    if not isinstance(entries, list):
        entries = []
    lane_counts: dict[str, dict[str, int]] = {}
    total_bytes = 0
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        relative = str(entry.get("path", "")).replace("\\", "/")
        total_bytes += int(entry.get("bytes", 0))
        lane = None
        for candidate in ("dx11/ps_5_0", "dx11/vs_5_0"):
            if relative.startswith(candidate + "/"):
                lane = candidate
                break
        if lane is None:
            continue
        suffix = Path(relative).suffix.lower()
        counts = lane_counts.setdefault(lane, {})
        counts[suffix] = counts.get(suffix, 0) + 1

    # A CK3 DX11 cache is considered warm only when both shader lanes have at
    # least one compiled binary and one companion cache record.  This is a
    # deliberately small, observable contract: it rejects an empty/partial
    # profile while allowing the exact machine-specific file count to vary.
    required_lanes = {
        lane: {
            ".bin": counts.get(".bin", 0),
            ".scache": counts.get(".scache", 0),
        }
        for lane, counts in lane_counts.items()
    }
    ready = bool(
        manifest.get("file_count", 0) > 0
        and total_bytes > 0
        and all(
            required_lanes.get(lane, {}).get(".bin", 0) > 0
            and required_lanes.get(lane, {}).get(".scache", 0) > 0
            for lane in ("dx11/ps_5_0", "dx11/vs_5_0")
        )
    )
    return {
        "path": str(root),
        "exists": True,
        "ready": ready,
        "failure_reason": None
        if ready
        else "shadercache lacks both populated DX11 PS/VS lanes",
        "file_count": int(manifest.get("file_count", 0)),
        "bytes": total_bytes,
        "tree_sha256": manifest.get("tree_sha256"),
        "required_lanes": required_lanes,
        "symlink_count": 0,
    }


def _profile_startup_assets_error(
    evidence: dict[str, Any], reason: str
) -> SeedCaptureError:
    """Build one typed, reportable RED for an incomplete startup profile."""

    evidence["result"] = "BLOCKED"
    evidence["profile_ready"] = False
    evidence["failure_reason"] = reason
    return SeedCaptureError(
        "formal Phase2 startup profile is not ready: " + reason,
        evidence,
    )


def prepare_profile_settings(config: CaptureConfig) -> dict[str, Any]:
    """Prepare the settings/cache pair required by a formal Phase2 launch.

    ``bootstrap_userdir`` deliberately creates a tiny deterministic settings
    file so legacy acceptance tests can construct an isolated profile.  That
    file is not a sufficient renderer profile for the formal Phase2 path.  A
    launch therefore has to pin a full ``pdx_settings.txt`` explicitly (CLI
    or ``XAR_CK3_SETTINGS_TEMPLATE``) *and* provide its sibling populated
    ``shadercache`` tree.  The whole cache is copied and content-compared;
    silently falling back to the operator's live profile or an empty cache is
    prohibited.
    """

    destination = (config.profile_dir / "pdx_settings.txt").resolve()
    destination_cache = (config.profile_dir / "shadercache").resolve()
    evidence: dict[str, Any] = {
        "schema_version": 2,
        "result": "NOT_AVAILABLE",
        "strategy": "explicit-full-settings-plus-warm-shadercache",
        "template_required_for_copy": True,
        "auto_copy": False,
        "cache_copy": False,
        "profile_ready": False,
        "destination": str(destination),
        "destination_cache": str(destination_cache),
        "source": None,
        "source_kind": None,
        "source_sha256": None,
        "source_bytes": None,
        "destination_sha256": None,
        "destination_bytes": None,
        "preserved_existing": False,
        "auto_candidate": None,
        "auto_shadercache": None,
        "selected_shadercache": None,
        "cache_source": None,
        "cache_source_manifest": None,
        "cache_destination_manifest": None,
        "failure_reason": None,
    }

    explicit_sources = {"explicit-config", "explicit-env"}
    explicit_candidates = _profile_settings_candidates(config)
    auto_path = _real_profile_settings_path()
    auto_full = auto_path.is_file() and _settings_file_is_full(auto_path)
    auto_candidate: dict[str, object] = {
        "path": str(auto_path),
        "exists": auto_path.is_file(),
        "full_settings": auto_full,
        "selected": False,
        "reason": (
            "operator-specific source requires explicit pin"
            if auto_full
            else "no full settings file available"
        ),
    }
    if auto_full:
        auto_candidate.update(
            {
                "bytes": auto_path.stat().st_size,
                "sha256": sha256_file(auto_path),
            }
        )
    evidence["auto_candidate"] = auto_candidate
    evidence["auto_shadercache"] = _directory_provenance(
        auto_path.parent / "shadercache"
    )

    # Never treat a full file left by CK3 or found in the real profile as an
    # implicit selection.  The caller must pin the exact known-good pair.
    if not explicit_candidates:
        evidence["result"] = (
            "AVAILABLE_NOT_SELECTED" if auto_full else "NOT_AVAILABLE"
        )
        evidence["failure_reason"] = (
            "formal Phase2 launch requires --profile-settings-template (or "
            "XAR_CK3_SETTINGS_TEMPLATE) plus a populated sibling shadercache"
        )
        evidence["destination_bytes"] = (
            destination.stat().st_size if destination.is_file() else None
        )
        if destination.is_file():
            try:
                evidence["destination_sha256"] = sha256_file(destination)
            except OSError as error:
                evidence["failure_reason"] += (
                    f"; destination hash failed: {type(error).__name__}: {error}"
                )
        evidence["selected_shadercache"] = _directory_provenance(
            destination_cache
        )
        return evidence

    source_path, source_kind = explicit_candidates[0]
    evidence.update(
        {
            "source": str(source_path),
            "source_kind": source_kind,
        }
    )
    if not source_path.is_file() or not _settings_file_is_full(source_path):
        raise _profile_startup_assets_error(
            evidence,
            "explicit profile settings template is missing or not a full CK3 "
            f"settings file: {source_path}",
        )

    try:
        source_bytes = source_path.stat().st_size
        source_sha256 = sha256_file(source_path)
    except OSError as error:
        raise _profile_startup_assets_error(
            evidence,
            f"could not inspect explicit profile settings template: {error}",
        ) from error
    evidence.update(
        {
            "source_bytes": source_bytes,
            "source_sha256": source_sha256,
        }
    )

    cache_source = (source_path.parent / "shadercache").resolve()
    evidence["cache_source"] = str(cache_source)
    source_cache_manifest = _warm_shadercache_manifest(cache_source)
    evidence["cache_source_manifest"] = source_cache_manifest
    if source_cache_manifest.get("ready") is not True:
        raise _profile_startup_assets_error(
            evidence,
            "explicit settings template does not have a complete warm "
            "shadercache sibling: "
            + str(source_cache_manifest.get("failure_reason")),
        )

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source_path != destination:
            shutil.copy2(source_path, destination)

        # A fresh seed profile should not contain a cache yet.  Refuse a
        # pre-existing tree rather than merging stale shaders into the pinned
        # source; this keeps the copy reversible and its digest meaningful.
        if cache_source != destination_cache:
            if destination_cache.exists():
                raise OSError(
                    "isolated profile shadercache already exists; refusing "
                    "to merge an unpinned cache"
                )
            shutil.copytree(cache_source, destination_cache, copy_function=shutil.copy2)

        destination_cache_manifest = _warm_shadercache_manifest(destination_cache)
        evidence["cache_destination_manifest"] = destination_cache_manifest
        if (
            destination_cache_manifest.get("ready") is not True
            or destination_cache_manifest.get("tree_sha256")
            != source_cache_manifest.get("tree_sha256")
            or destination_cache_manifest.get("file_count")
            != source_cache_manifest.get("file_count")
            or destination_cache_manifest.get("bytes")
            != source_cache_manifest.get("bytes")
        ):
            raise OSError(
                "copied shadercache failed source/destination manifest equality"
            )

        destination_bytes = destination.stat().st_size
        destination_sha256 = sha256_file(destination)
    except (OSError, UnicodeError, ValueError) as error:
        raise _profile_startup_assets_error(
            evidence,
            f"could not materialize pinned settings/cache pair: {type(error).__name__}: {error}",
        ) from error

    evidence.update(
        {
            "result": "PRESERVED" if source_path == destination else "GREEN",
            "profile_ready": True,
            "cache_copy": source_path != destination,
            "preserved_existing": source_path == destination,
            "destination_bytes": destination_bytes,
            "destination_sha256": destination_sha256,
            "selected_shadercache": _directory_provenance(destination_cache),
        }
    )
    return evidence


def _validate_frontend_first_save_name(value: object) -> str:
    """Validate the basename shared by the warm-up copy and ``-loadsave``."""

    if (
        not isinstance(value, str)
        or not value
        or Path(value).name != value
        or Path(value).suffix
        or any(character in value for character in ("/", "\\", "\0"))
    ):
        raise SeedCaptureError(
            "frontend-first load save name must be one basename without "
            "a path or extension"
        )
    return value


def prepare_frontend_first_save(
    config: CaptureConfig, old_save: Path
) -> dict[str, Any] | None:
    """Materialize the selected seed under ``save games`` for ``-loadsave``.

    The legacy Phase2 path keeps the root ``last_save.ck3`` copy for
    ``-continuelastsave``.  ``-loadsave=<name>`` resolves a basename in the
    profile's ``save games`` directory, so an opt-in frontend-first run needs
    an explicit second copy there.  A pre-existing byte-identical file is
    retained; a conflicting file is rejected instead of being overwritten.
    """

    if config.frontend_first_load_save_name is None:
        return None
    name = _validate_frontend_first_save_name(
        config.frontend_first_load_save_name
    )
    source = Path(old_save).resolve()
    if not source.is_file() or source.stat().st_size <= 0:
        raise SeedCaptureError(
            f"frontend-first source save is unavailable: {source}"
        )
    target_root = (config.profile_dir / "save games").resolve()
    target = (target_root / f"{name}.ck3").resolve()
    try:
        target.relative_to(target_root)
    except ValueError as error:
        raise SeedCaptureError(
            "frontend-first save target escaped the isolated profile"
        ) from error
    source_size = source.stat().st_size
    source_sha256 = sha256_file(source)
    result = "COPIED"
    if target.exists():
        if not target.is_file():
            raise SeedCaptureError(
                f"frontend-first save target is not a regular file: {target}"
            )
        if (
            target.stat().st_size != source_size
            or sha256_file(target) != source_sha256
        ):
            raise SeedCaptureError(
                "frontend-first save target already exists with different "
                f"bytes: {target}"
            )
        result = "PRESERVED"
    else:
        target_root.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(source, target)
        except OSError as error:
            raise SeedCaptureError(
                f"could not copy frontend-first save into isolated profile: {error}"
            ) from error
    target_size = target.stat().st_size
    target_sha256 = sha256_file(target)
    if target_size != source_size or target_sha256 != source_sha256:
        raise SeedCaptureError(
            "frontend-first save copy failed immutable byte verification: "
            f"{target}"
        )
    return {
        "result": result,
        "name": name,
        "load_save_name": name,
        "source": str(source),
        "source_bytes": source_size,
        "source_sha256": source_sha256,
        "path": str(target),
        "bytes": target_size,
        "sha256": target_sha256,
        "immutable": True,
    }


def _run_open_kaishek_seed_preflight(
    config: CaptureConfig,
    artifacts: Path,
    *,
    runtime: RuntimeBindings | None,
) -> dict[str, Any]:
    """Run the offline phase-two gate before native session/CK3 startup.

    Unit seams inject a fake runtime and disable only the external accelerator;
    production capture keeps the real parser/validator/fixture command.  Both
    paths retain the same machine-readable result and never promote it to live
    evidence.
    """

    executable_sha256 = None
    if config.game_executable.is_file():
        try:
            executable_sha256 = sha256_file(config.game_executable)
        except OSError:
            executable_sha256 = None
    environment = (
        {"XAR_KAISHEK_PREFLIGHT_DISABLED": "1"}
        if runtime is not None
        else None
    )
    try:
        result = kaishek_preflight.run_preflight(
            root=config.product_source,
            profile="ck3-1.19.0.6-zg361",
            fixture="synthetic-361-014",
            artifact_path=artifacts / "open_kaishek-preflight.json",
            ck3_build="1.19.0.6",
            ck3_exe_sha256=executable_sha256,
            env=environment,
        )
    except BaseException as error:
        result = {
            "schema": kaishek_preflight.ADAPTER_SCHEMA,
            "status": "failed",
            "result": "FAILED",
            "ok": False,
            "reason": "adapter-exception",
            "error": f"{type(error).__name__}: {error}",
            "provenance": {
                "cli_contract_commit": kaishek_preflight.CLI_CONTRACT_COMMIT,
            },
        }
    result["runner_scope"] = "run_zg361_phase2_seed_capture"
    result["coverage_decision"] = (
        "injected-runtime-test-disabled"
        if runtime is not None
        else "zg361-product-parser-validator-plus-synthetic-fixture"
    )
    # The adapter writes its own JSON before returning.  Persist once more
    # after adding runner-owned provenance so the archived artifact and the
    # report carry the same contract fields.
    try:
        write_json(artifacts / "open_kaishek-preflight.json", result)
    except OSError as error:
        result["artifact_error"] = f"{type(error).__name__}: {error}"
    return result


def append_jsonl(path: Path, value: object) -> None:
    """Durably append evidence; never replace a live producer's target."""

    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(payload + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def log(artifacts: Path, message: str) -> None:
    line = f"[{utc_now()}] {message}"
    print(line, flush=True)
    with (artifacts / "runner-events.log").open(
        "a", encoding="utf-8", newline="\n"
    ) as stream:
        stream.write(line + "\n")


def attest_ck3_us_english_hkl(
    tracked_pid: int, artifacts: Path, stem: str
) -> dict[str, Any]:
    """Set CK3's window thread HKL without focus changes or desktop input."""

    output = artifacts / f"{stem}.json"
    evidence: dict[str, Any] = {
        "schema_version": 1,
        "result": "RED",
        "policy": "keep_us_english_hkl_without_desktop_input",
        "tracked_ck3_pid": tracked_pid,
        "requested_hkl": f"0x{WINDOWS_ENGLISH_US_HKL:08x}",
        "window_focus_changed": False,
        "desktop_input_sent": False,
        "restore_requested": False,
        "restore_performed": False,
        "poll_observations": [],
    }
    try:
        if os.name != "nt":
            raise SeedCaptureError("CK3 keyboard-layout attestation requires Windows")
        if tracked_pid <= 0:
            raise SeedCaptureError("CK3 keyboard-layout attestation lacks a PID")

        import ctypes
        from ctypes import wintypes

        user32 = ctypes.WinDLL("user32", use_last_error=True)
        enum_callback_type = ctypes.WINFUNCTYPE(
            wintypes.BOOL, wintypes.HWND, wintypes.LPARAM
        )
        user32.EnumWindows.argtypes = [enum_callback_type, wintypes.LPARAM]
        user32.EnumWindows.restype = wintypes.BOOL
        user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        user32.GetWindowThreadProcessId.restype = wintypes.DWORD
        user32.IsWindowVisible.argtypes = [wintypes.HWND]
        user32.IsWindowVisible.restype = wintypes.BOOL
        user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        user32.GetWindowTextLengthW.restype = ctypes.c_int
        user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]
        user32.GetWindowTextW.restype = ctypes.c_int
        user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
        user32.GetKeyboardLayout.restype = ctypes.c_void_p
        user32.GetKeyboardLayoutList.argtypes = [
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_void_p),
        ]
        user32.GetKeyboardLayoutList.restype = ctypes.c_int
        user32.PostMessageW.argtypes = [
            wintypes.HWND,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        user32.PostMessageW.restype = wintypes.BOOL

        windows: list[dict[str, Any]] = []

        @enum_callback_type
        def collect(hwnd: int, _lparam: int) -> bool:
            pid = wintypes.DWORD()
            thread_id = int(
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            )
            if int(pid.value) != tracked_pid:
                return True
            length = int(user32.GetWindowTextLengthW(hwnd))
            buffer = ctypes.create_unicode_buffer(max(1, length + 1))
            user32.GetWindowTextW(hwnd, buffer, len(buffer))
            windows.append(
                {
                    "hwnd": int(hwnd or 0),
                    "thread_id": thread_id,
                    "visible": bool(user32.IsWindowVisible(hwnd)),
                    "title": buffer.value,
                }
            )
            return True

        if not user32.EnumWindows(collect, 0):
            raise SeedCaptureError("EnumWindows failed for the tracked CK3 PID")
        candidates = sorted(
            windows,
            key=lambda row: (
                "crusader kings" not in str(row["title"]).lower(),
                not bool(row["visible"]),
                not bool(row["title"]),
                int(row["hwnd"]),
            ),
        )
        if not candidates:
            raise SeedCaptureError("tracked CK3 PID has no top-level window yet")
        target = candidates[0]
        target_hwnd = int(target["hwnd"])
        target_thread_id = int(target["thread_id"])
        if target_hwnd <= 0 or target_thread_id <= 0:
            raise SeedCaptureError("tracked CK3 window identity is invalid")

        def normalized_hkl(thread_id: int) -> int:
            return int(user32.GetKeyboardLayout(thread_id) or 0) & 0xFFFFFFFF

        count = int(user32.GetKeyboardLayoutList(0, None))
        installed_buffer = (ctypes.c_void_p * max(1, count))()
        installed_count = int(
            user32.GetKeyboardLayoutList(count, installed_buffer)
        )
        installed = [
            int(installed_buffer[index] or 0) & 0xFFFFFFFF
            for index in range(max(0, installed_count))
        ]
        evidence.update(
            {
                "candidate_windows": windows,
                "target_window_handle": target_hwnd,
                "target_window_title": target["title"],
                "target_thread_id": target_thread_id,
                "installed_hkls": [f"0x{value:08x}" for value in installed],
            }
        )
        if WINDOWS_ENGLISH_US_HKL not in installed:
            raise SeedCaptureError("US English HKL 0x04090409 is not installed")
        before = normalized_hkl(target_thread_id)
        posted: bool | None = None
        if before != WINDOWS_ENGLISH_US_HKL:
            posted = bool(
                user32.PostMessageW(
                    target_hwnd,
                    WM_INPUTLANGCHANGEREQUEST,
                    0,
                    WINDOWS_ENGLISH_US_HKL,
                )
            )
            if not posted:
                raise SeedCaptureError(
                    "CK3 rejected WM_INPUTLANGCHANGEREQUEST"
                )
        deadline = time.monotonic() + 2.0
        after = before
        observations: list[dict[str, Any]] = evidence["poll_observations"]
        while True:
            after = normalized_hkl(target_thread_id)
            observations.append({"hkl": f"0x{after:08x}"})
            if after == WINDOWS_ENGLISH_US_HKL or time.monotonic() >= deadline:
                break
            time.sleep(0.1)
        evidence.update(
            {
                "before_hkl": f"0x{before:08x}",
                "message_posted": posted,
                "after_hkl": f"0x{after:08x}",
                "left_in_english": after == WINDOWS_ENGLISH_US_HKL,
            }
        )
        if after != WINDOWS_ENGLISH_US_HKL:
            raise SeedCaptureError(
                "CK3 window thread did not attest US English HKL 0409"
            )
        evidence["result"] = "GREEN"
        write_json(output, evidence)
        return evidence
    except BaseException as error:
        evidence["error"] = f"{type(error).__name__}: {error}"
        write_json(output, evidence)
        raise


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_config(config: CaptureConfig) -> None:
    required_directories = {
        "clean source": config.clean_source,
        "product source": config.product_source,
        "seed fixture source": config.fixture_source,
        "game directory": config.game_dir,
    }
    for label, path in required_directories.items():
        if not path.is_dir():
            raise SeedCaptureError(f"{label} is missing: {path}")
    required_files = {
        "source ZIP": config.source_zip,
        "seed contract": config.seed_contract,
        "CK3 executable": config.game_executable,
        "vanilla game rules": config.vanilla_game_rules,
        "bridge DLL": config.bridge_dll,
        "bridge injector": config.bridge_injector,
    }
    if config.bridge_bundle_manifest is not None:
        required_files["bridge bundle manifest"] = config.bridge_bundle_manifest
    if config.product_projection_manifest is not None:
        required_files["product projection manifest"] = config.product_projection_manifest
    for label, path in required_files.items():
        if not isinstance(path, Path) or not path.is_file():
            raise SeedCaptureError(f"{label} is missing: {path}")
    observer_gate_enabled = (
        config.list_domain_observer_gate
        or config.acceptance_observer_manifest is not None
    )
    if observer_gate_enabled and not config.acceptance_observer_contract.is_file():
        raise SeedCaptureError(
            "list-domain acceptance observer contract is missing: "
            f"{config.acceptance_observer_contract}"
        )
    if (
        config.acceptance_observer_manifest is not None
        and not config.acceptance_observer_manifest.is_file()
    ):
        raise SeedCaptureError(
            "native observer seam manifest is missing: "
            f"{config.acceptance_observer_manifest}"
        )
    if GIT_SHA_PATTERN.fullmatch(config.frozen_git_sha) is None:
        raise SeedCaptureError("frozen git SHA must be exactly 40 hexadecimal digits")
    if (
        not isinstance(config.product_projection, str)
        or not config.product_projection.strip()
        or "/" in config.product_projection
        or "\\" in config.product_projection
    ):
        raise SeedCaptureError(
            "product projection name must be a non-empty path-free identifier"
        )
    if (
        config.product_projection != "broad"
        and config.product_projection != "core"
        and config.product_projection_manifest is None
    ):
        raise SeedCaptureError(
            f"product projection {config.product_projection!r} requires an explicit manifest"
        )
    if not isinstance(config.game_dir_source, str) or not config.game_dir_source:
        raise SeedCaptureError("game directory provenance source is missing")
    if not config.pipe_name.startswith(PIPE_PREFIX):
        raise SeedCaptureError("bridge pipe must be an explicit Windows named pipe")
    timings = {
        "loader timeout": config.loader_timeout_seconds,
        "native readiness timeout": config.native_readiness_timeout_seconds,
        "event timeout": config.event_timeout_seconds,
        "binding timeout": config.binding_timeout_seconds,
        "keyboard watchdog interval": config.keyboard_watchdog_interval_seconds,
    }
    if config.frontend_first_load_save_name is not None:
        timings["frontend-first timeout"] = config.frontend_first_timeout_seconds
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        or value <= 0
        for value in timings.values()
    ):
        raise SeedCaptureError(f"capture timing values must be positive: {timings}")
    if config.loader_timeout_seconds <= LOADER_FATAL_STALL_SECONDS:
        raise SeedCaptureError(
            "loader timeout must leave room for the fixed 45-second parser stall gate"
        )
    if config.frontend_first_load_save_name is not None:
        _validate_frontend_first_save_name(config.frontend_first_load_save_name)
    if config.profile_settings_template is not None and not isinstance(
        config.profile_settings_template, Path
    ):
        raise SeedCaptureError("profile settings template path is malformed")
    if config.bridge_bundle_manifest is not None and not isinstance(
        config.bridge_bundle_manifest, Path
    ):
        raise SeedCaptureError("bridge bundle manifest path is malformed")
    if config.product_projection_manifest is not None and not isinstance(
        config.product_projection_manifest, Path
    ):
        raise SeedCaptureError("product projection manifest path is malformed")
    if config.product_source_override is not None and not isinstance(
        config.product_source_override, Path
    ):
        raise SeedCaptureError("product source override path is malformed")
    if _is_relative_to(config.attempt_dir, config.clean_source):
        raise SeedCaptureError("attempt directory must be outside the clean source")
    if _is_relative_to(config.artifacts_dir, config.clean_source):
        raise SeedCaptureError("artifacts directory must be outside the clean source")
    if config.state_dir.exists():
        raise SeedCaptureError(
            f"attempt native-state already exists; use a fresh attempt: {config.state_dir}"
        )
    if config.artifacts_dir.exists() and any(config.artifacts_dir.iterdir()):
        raise SeedCaptureError(
            f"artifacts directory is not empty: {config.artifacts_dir}"
        )


def _bootstrap_product_projection(zgrun: Any, config: CaptureConfig) -> dict[str, Any]:
    """Mount the selected product projection through the isolated runner API.

    The default call intentionally keeps the two-argument API used by older
    frozen clean exports and CK3-free fakes.  Projection-specific arguments are
    sent only when requested; an old runtime then fails with a typed message
    instead of silently mounting the broad tree.
    """

    kwargs: dict[str, object] = {}
    if (
        config.product_projection != "broad"
        or config.product_projection_manifest is not None
    ):
        kwargs["product_projection"] = config.product_projection
        kwargs["product_projection_manifest"] = config.product_projection_manifest
    bootstrap_fn = getattr(zgrun, "bootstrap_userdir", None)
    if not callable(bootstrap_fn):
        raise SeedCaptureError("isolated runtime lacks bootstrap_userdir")
    try:
        result = bootstrap_fn(config.profile_dir, config.product_source, **kwargs)
    except TypeError as error:
        if kwargs and "unexpected keyword" in str(error).lower():
            raise SeedCaptureError(
                "selected product projection is unsupported by the frozen runtime; "
                "refresh the clean source export before retrying",
                {
                    "projection": config.product_projection,
                    "manifest": (
                        str(config.product_projection_manifest)
                        if config.product_projection_manifest is not None
                        else None
                    ),
                },
            ) from error
        raise
    if kwargs:
        # A stale frozen export might accept **kwargs yet ignore the selected
        # projection.  Inspect the bootstrap receipt and fail closed rather
        # than silently running a broad mount under a named/core request.
        manifest = result.get("manifest") if isinstance(result, dict) else None
        projection = manifest.get("projection") if isinstance(manifest, dict) else None
        actual_name: object = None
        if isinstance(projection, dict):
            actual_name = projection.get("name", projection.get("projection"))
        elif isinstance(projection, str):
            actual_name = projection
        if actual_name != config.product_projection:
            raise SeedCaptureError(
                "isolated bootstrap did not honor the selected product projection",
                {
                    "requested_projection": config.product_projection,
                    "observed_projection": actual_name,
                    "manifest": (
                        str(config.product_projection_manifest)
                        if config.product_projection_manifest is not None
                        else None
                    ),
                },
            )
    return result


def prepare_output_paths(config: CaptureConfig) -> None:
    """Create only fresh out-of-source outputs before full preflight evidence."""

    if _is_relative_to(config.attempt_dir, config.clean_source):
        raise SeedCaptureError("attempt directory must be outside the clean source")
    if _is_relative_to(config.artifacts_dir, config.clean_source):
        raise SeedCaptureError("artifacts directory must be outside the clean source")
    if config.state_dir.exists():
        raise SeedCaptureError(
            f"attempt native-state already exists; use a fresh attempt: {config.state_dir}"
        )
    if config.artifacts_dir.exists() and any(config.artifacts_dir.iterdir()):
        raise SeedCaptureError(
            f"artifacts directory is not empty: {config.artifacts_dir}"
        )
    config.attempt_dir.mkdir(parents=True, exist_ok=True)
    config.artifacts_dir.mkdir(parents=True, exist_ok=True)


def tree_manifest(root: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        entries.append(
            {
                "path": relative.as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    canonical = json.dumps(
        entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return {
        "schema_version": 1,
        "algorithm": "sha256(canonical-json[path,bytes,sha256])",
        "root": str(root),
        "file_count": len(entries),
        "tree_sha256": hashlib.sha256(canonical).hexdigest(),
        "files": entries,
    }


def zip_manifest(path: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    with zipfile.ZipFile(path, "r") as archive:
        for info in sorted(
            (candidate for candidate in archive.infolist() if not candidate.is_dir()),
            key=lambda candidate: candidate.filename,
        ):
            digest = hashlib.sha256()
            with archive.open(info, "r") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            entries.append(
                {
                    "path": info.filename.replace("\\", "/"),
                    "bytes": info.file_size,
                    "sha256": digest.hexdigest(),
                }
            )
    canonical = json.dumps(
        entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    path_counts: dict[str, int] = {}
    for entry in entries:
        entry_path = str(entry["path"])
        path_counts[entry_path] = path_counts.get(entry_path, 0) + 1
    return {
        "schema_version": 1,
        "algorithm": "sha256(canonical-json[path,bytes,sha256])",
        "archive": str(path),
        "file_count": len(entries),
        "duplicate_paths": sorted(
            entry_path for entry_path, count in path_counts.items() if count > 1
        ),
        "logical_tree_sha256": hashlib.sha256(canonical).hexdigest(),
        "files": entries,
    }


def compare_zip_to_source(
    archive: dict[str, Any], source: dict[str, Any]
) -> dict[str, Any]:
    archive_rows = archive.get("files")
    source_rows = source.get("files")
    if not isinstance(archive_rows, list) or not isinstance(source_rows, list):
        raise SeedCaptureError("source/archive manifests are malformed")
    source_map = {
        str(row["path"]): (row["bytes"], row["sha256"])
        for row in source_rows
        if isinstance(row, dict)
    }
    raw_archive_map = {
        str(row["path"]): (row["bytes"], row["sha256"])
        for row in archive_rows
        if isinstance(row, dict)
    }
    mapping = "exact-relative-paths"
    archive_map = raw_archive_map
    if set(archive_map) != set(source_map) and archive_map:
        first_components = {
            path.split("/", 1)[0] for path in archive_map if "/" in path
        }
        if len(first_components) == 1:
            prefix = next(iter(first_components)) + "/"
            stripped = {
                path[len(prefix) :]: identity
                for path, identity in archive_map.items()
                if path.startswith(prefix)
            }
            if len(stripped) == len(archive_map):
                archive_map = stripped
                mapping = "single-top-level-directory-stripped"
    missing_from_archive = sorted(set(source_map) - set(archive_map))
    extra_in_archive = sorted(set(archive_map) - set(source_map))
    changed = sorted(
        path
        for path in set(source_map) & set(archive_map)
        if source_map[path] != archive_map[path]
    )
    return {
        "mapping": mapping,
        "equivalent": not archive.get("duplicate_paths")
        and not missing_from_archive
        and not extra_in_archive
        and not changed,
        "missing_from_archive": missing_from_archive,
        "extra_in_archive": extra_in_archive,
        "content_mismatches": changed,
    }


def git_identity(config: CaptureConfig) -> dict[str, Any]:
    identity: dict[str, Any] = {
        "declared_sha": config.frozen_git_sha,
        "verification": "clean-export-without-git-metadata",
        "observed_sha": None,
    }
    if (config.clean_source / ".git").exists():
        completed = subprocess.run(
            ["git", "-C", str(config.clean_source), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        observed = completed.stdout.strip().lower()
        identity.update(
            {"verification": "git-rev-parse-head", "observed_sha": observed}
        )
        if observed != config.frozen_git_sha:
            raise SeedCaptureError(
                f"clean source git SHA drifted: {observed} != {config.frozen_git_sha}"
            )
    return identity


def _require_module_origin(module: ModuleType, clean_source: Path) -> None:
    raw = getattr(module, "__file__", None)
    if not isinstance(raw, str):
        raise SeedCaptureError(f"module lacks an origin: {module.__name__}")
    origin = Path(raw).resolve()
    if not _is_relative_to(origin, clean_source):
        raise SeedCaptureError(
            f"module escaped the clean source: {module.__name__} -> {origin}"
        )


def load_runtime(config: CaptureConfig) -> RuntimeBindings:
    """Import all CK3 tooling from the explicit clean source, never this tree."""

    tools = config.clean_source / "tools"
    autoplayer = config.clean_source / "ck3_autonomous_player" / "src"
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    sys.dont_write_bytecode = True
    os.environ["XAR_CK3_EXE"] = str(config.game_executable)
    os.environ["XAR_CK3_GAME_DIR"] = str(config.game_dir)
    for import_root in reversed((tools, autoplayer)):
        while str(import_root) in sys.path:
            sys.path.remove(str(import_root))
        sys.path.insert(0, str(import_root))
    importlib.invalidate_caches()
    module_names = (
        "run_acceptance",
        "run_zhongguo_acceptance",
        "zg361_phase2_seed_bootstrap",
        "zg361_phase2_loader_stage",
    )
    for name in module_names:
        existing = sys.modules.get(name)
        if existing is not None:
            _require_module_origin(existing, config.clean_source)
    acceptance = importlib.import_module("run_acceptance")
    zgrun = importlib.import_module("run_zhongguo_acceptance")
    seed = importlib.import_module("zg361_phase2_seed_bootstrap")
    loader = importlib.import_module("zg361_phase2_loader_stage")
    driver_module = importlib.import_module("xar_autoplayer.bridge.native_driver")
    service_module = importlib.import_module("xar_autoplayer.bridge.service")
    bridge_driver = importlib.import_module("xar_autoplayer.bridge.driver")
    for module in (
        acceptance,
        zgrun,
        seed,
        loader,
        driver_module,
        service_module,
        bridge_driver,
    ):
        _require_module_origin(module, config.clean_source)

    original_defaults = acceptance.declared_vanilla_rule_defaults

    def declared_vanilla_rule_defaults(path: Path | None = None):
        return original_defaults(config.vanilla_game_rules if path is None else path)

    acceptance.VANILLA_GAME_RULES = config.vanilla_game_rules
    acceptance.declared_vanilla_rule_defaults = declared_vanilla_rule_defaults
    zgrun.FIXTURE_SOURCE = config.fixture_source
    return RuntimeBindings(
        acceptance=acceptance,
        zgrun=zgrun,
        seed=seed,
        driver_factory=driver_module.NativeHeadlessGameplayDriver,
        service_factory=service_module.GameplayBridgeService,
        bridge_unavailable_error=bridge_driver.BridgeUnavailableError,
        pre_submission_revision_mismatch_error=(
            bridge_driver.PreSubmissionRevisionMismatchError
        ),
        loader_stage_error=loader.LoaderStageError,
        wait_for_loader_stage=loader.wait_for_phase2_seed_loader_stage,
        keyboard_layout_attestor=attest_ck3_us_english_hkl,
    )


def _positive_revision(snapshot: dict[str, Any]) -> int:
    revision = snapshot.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision <= 0:
        raise SeedCaptureError("MCP snapshot lacks a positive public revision")
    return revision


def _typed_character_id(scope: object) -> int | None:
    if not isinstance(scope, dict):
        return None
    identity = scope.get("typed_identity")
    if not isinstance(identity, dict):
        return None
    character_id = identity.get("character_id")
    if (
        identity.get("status") != "available"
        or identity.get("kind") != "character"
        or not isinstance(character_id, int)
        or isinstance(character_id, bool)
        or character_id <= 0
    ):
        return None
    return character_id


def _known_pre_bootstrap_event_checks(
    *,
    source_save_sha256: str | None,
    snapshot: dict[str, Any],
    context: dict[str, Any],
    event_instance_id: int,
) -> dict[str, bool]:
    expected = KNOWN_PRE_BOOTSTRAP_EVENT
    active = snapshot.get("active_event")
    active_event = active if isinstance(active, dict) else {}
    options = context.get("options")
    option_rows = options if isinstance(options, list) else []
    authored_options_exact = len(option_rows) == expected["option_count"]
    if authored_options_exact:
        for index, row in enumerate(option_rows):
            if not isinstance(row, dict) or not (
                row.get("rendered_index") == index
                and row.get("native_option_index") == index
                and row.get("shown") is True
                and row.get("enabled") is True
                and row.get("fallback") is False
                and row.get("cancel") is False
            ):
                authored_options_exact = False
                break

    saved_scopes = context.get("saved_scopes")
    saved_scope_rows = saved_scopes if isinstance(saved_scopes, list) else []
    reviewing_superior_ids = {
        character_id
        for row in saved_scope_rows
        if isinstance(row, dict)
        and row.get("name") == "zg361_reviewing_superior"
        and (character_id := _typed_character_id(row.get("scope"))) is not None
    }
    return {
        "source_save_sha256": source_save_sha256
        == expected["source_save_sha256"],
        "context_schema": context.get("schema")
        == "current-event-window-context-v1",
        "context_schema_version": context.get("schema_version") == 1,
        "context_available": context.get("status") == "available",
        "unique_window": context.get("window_match_count") == 1,
        "event_definition_key": context.get("event_definition_key")
        == expected["event_definition_key"],
        "event_instance_id": context.get("current_event_instance_id")
        == event_instance_id,
        "snapshot_date_raw": snapshot.get("date_raw") == expected["date_raw"],
        "context_date_raw": context.get("date_raw") == expected["date_raw"],
        "root_character_id": _typed_character_id(context.get("root_scope"))
        == expected["root_character_id"],
        "reviewing_superior_character_id": reviewing_superior_ids
        == {expected["reviewing_superior_character_id"]},
        "snapshot_option_count": active_event.get("option_count")
        == expected["option_count"],
        "authored_options_exact": authored_options_exact,
    }


def _known_pre_bootstrap_vanilla_event_checks(
    *,
    source_save_sha256: str | None,
    snapshot: dict[str, Any],
    context: dict[str, Any],
    event_instance_id: int,
) -> dict[str, bool]:
    """Bind the one observed vanilla interruption; never classify by namespace."""

    expected = KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT
    active = snapshot.get("active_event")
    active_event = active if isinstance(active, dict) else {}
    options = context.get("options")
    option_rows = options if isinstance(options, list) else []
    authored_options_exact = len(option_rows) == expected["option_count"]
    if authored_options_exact:
        for index, row in enumerate(option_rows):
            if not isinstance(row, dict) or not (
                row.get("rendered_index") == index
                and row.get("native_option_index") == index
                and row.get("shown") is True
                and row.get("enabled") is True
                and row.get("fallback") is False
                and row.get("cancel") is False
            ):
                authored_options_exact = False
                break

    saved_scopes = context.get("saved_scopes")
    saved_scope_rows = saved_scopes if isinstance(saved_scopes, list) else []
    character_to_hook_ids = {
        character_id
        for row in saved_scope_rows
        if isinstance(row, dict)
        and row.get("name") == "character_to_hook"
        and (character_id := _typed_character_id(row.get("scope"))) is not None
    }
    excluded_character_ids = set(expected["excluded_character_to_hook_ids"])
    return {
        "source_save_sha256": source_save_sha256
        == expected["source_save_sha256"],
        "context_schema": context.get("schema")
        == "current-event-window-context-v1",
        "context_schema_version": context.get("schema_version") == 1,
        "context_available": context.get("status") == "available",
        "unique_window": context.get("window_match_count") == 1,
        "native_active_event": active_event.get("source") == "native",
        "event_definition_key": context.get("event_definition_key")
        == expected["event_definition_key"],
        "event_instance_id": context.get("current_event_instance_id")
        == event_instance_id,
        "snapshot_date_raw": snapshot.get("date_raw") == expected["date_raw"],
        "context_date_raw": context.get("date_raw") == expected["date_raw"],
        "root_character_id": _typed_character_id(context.get("root_scope"))
        == expected["root_character_id"],
        "character_to_hook_unique_typed_character": len(character_to_hook_ids) == 1,
        "character_to_hook_excludes_known_principals": bool(character_to_hook_ids)
        and character_to_hook_ids.isdisjoint(excluded_character_ids),
        "snapshot_option_count": active_event.get("option_count")
        == expected["option_count"],
        "authored_options_exact": authored_options_exact,
    }


def _known_pre_bootstrap_selection_checks(
    selection: object,
    *,
    event_instance_id: int,
    expected: dict[str, Any] = KNOWN_PRE_BOOTSTRAP_EVENT,
) -> dict[str, bool]:
    submission = selection if isinstance(selection, dict) else {}
    event_selection_value = submission.get("event_selection")
    event_selection = (
        event_selection_value if isinstance(event_selection_value, dict) else {}
    )
    return {
        "selection_object": isinstance(selection, dict),
        "step": submission.get("step")
        == f"select-event-option-{expected['selected_option_number']}",
        "accepted": submission.get("accepted") is True,
        "status": submission.get("status") == "submitted",
        "option_number": submission.get("option_number")
        == expected["selected_option_number"],
        "option_index": submission.get("option_index")
        == expected["selected_native_option_index"],
        "postcondition_verified": event_selection.get("postcondition_verified")
        is True,
        "old_event_instance_id": event_selection.get("old_event_instance_id")
        == event_instance_id,
        "selected_option_number": event_selection.get("selected_option_number")
        == expected["selected_option_number"],
        "selected_native_option_index": event_selection.get(
            "selected_native_option_index"
        )
        == expected["selected_native_option_index"],
        "old_instance_not_retained": event_selection.get("new_event_instance_id")
        != event_instance_id,
    }


def _drain_known_pre_bootstrap_event(
    service: Any,
    artifacts: Path,
    *,
    source_save_sha256: str | None,
    snapshot: dict[str, Any],
    query: object,
    context: dict[str, Any],
    event_instance_id: int,
    expected: dict[str, Any],
    identity_checks: dict[str, bool],
    evidence_path: Path,
    artifact_name: str,
    state_prefix: str,
) -> dict[str, Any]:
    """Drain one explicit event contract after identity and typed ACK checks."""

    event_key = context.get("event_definition_key")
    drain_evidence: dict[str, Any] = {
        "schema_version": 1,
        "state": f"{state_prefix}_observed",
        "source_save_sha256": source_save_sha256,
        "event_instance_id": event_instance_id,
        "event_definition_key": event_key,
        # Live evidence from repeated launches of the same frozen
        # save/product/build proves this engine-local value is not stable
        # across processes.  Preserve it for diagnosis, not identity.
        "observed_calculated_event_id": context.get("calculated_event_id"),
        "identity_checks": identity_checks,
        "query": query,
        "selection": None,
        "selection_checks": None,
        "result": None,
    }
    artifact_path = artifacts / artifact_name
    if not all(identity_checks.values()):
        drain_evidence["state"] = f"{state_prefix}_identity_mismatch"
        drain_evidence["result"] = "RED"
        write_json(artifact_path, drain_evidence)
        append_jsonl(evidence_path, drain_evidence)
        raise SeedCaptureError(
            f"known pre-bootstrap event identity drifted: {event_key!r}",
            drain_evidence,
        )

    selection_snapshot = service.snapshot()
    if not isinstance(selection_snapshot, dict):
        raise SeedCaptureError(
            "pre-bootstrap pre-selection snapshot is not an object"
        )
    selection_active_value = selection_snapshot.get("active_event")
    selection_active = (
        selection_active_value if isinstance(selection_active_value, dict) else {}
    )
    selection_revision = _positive_revision(selection_snapshot)
    pre_selection_checks = {
        "paused": selection_snapshot.get("paused") is True,
        "date_raw": selection_snapshot.get("date_raw") == expected["date_raw"],
        "event_instance_id": selection_active.get("instance_id")
        == event_instance_id,
        "option_count": selection_active.get("option_count")
        == expected["option_count"],
    }
    drain_evidence["pre_selection_snapshot"] = selection_snapshot
    drain_evidence["pre_selection_checks"] = pre_selection_checks
    if not all(pre_selection_checks.values()):
        drain_evidence["state"] = f"{state_prefix}_changed_before_selection"
        drain_evidence["result"] = "RED"
        write_json(artifact_path, drain_evidence)
        append_jsonl(evidence_path, drain_evidence)
        raise SeedCaptureError(
            f"known pre-bootstrap event changed before selection: {event_key!r}",
            drain_evidence,
        )

    selection = service.select_event_option(
        expected["selected_option_number"],
        event_instance_id=event_instance_id,
        expected_revision=selection_revision,
    )
    selection_checks = _known_pre_bootstrap_selection_checks(
        selection,
        event_instance_id=event_instance_id,
        expected=expected,
    )
    drain_evidence["selection"] = selection
    drain_evidence["selection_checks"] = selection_checks
    if not all(selection_checks.values()):
        drain_evidence["state"] = f"{state_prefix}_selection_red"
        drain_evidence["result"] = "RED"
        write_json(artifact_path, drain_evidence)
        append_jsonl(evidence_path, drain_evidence)
        raise SeedCaptureError(
            "known pre-bootstrap event option "
            f"{expected['selected_option_number']} did not close cleanly: "
            f"{event_key!r}",
            drain_evidence,
        )

    drain_evidence["state"] = f"{state_prefix}_drained"
    drain_evidence["result"] = "GREEN"
    drain_evidence["wait_policy"] = "continue_under_original_total_deadline"
    write_json(artifact_path, drain_evidence)
    append_jsonl(evidence_path, drain_evidence)
    return drain_evidence


def wait_for_bootstrap_event(
    service: Any,
    artifacts: Path,
    *,
    bridge_unavailable_error: type[BaseException],
    pre_submission_revision_mismatch_error: type[BaseException] | None = None,
    timeout_seconds: float,
    source_save_sha256: str | None = None,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
    logger: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Use one total deadline to reach exactly the visible seed event."""

    if timeout_seconds <= 0:
        raise ValueError("bootstrap event timeout must be positive")
    started = clock()
    deadline = started + timeout_seconds
    evidence_path = artifacts / "bootstrap-event-wait.jsonl"
    sequence = 0
    next_progress_log = 60.0
    resumed = False
    drained_pre_bootstrap_events: list[str] = []
    while clock() < deadline:
        now = clock()
        try:
            snapshot = service.snapshot()
        except bridge_unavailable_error as error:
            sequence += 1
            elapsed = max(0.0, now - started)
            append_jsonl(
                evidence_path,
                {
                    "schema_version": 1,
                    "sequence": sequence,
                    "elapsed_seconds": round(elapsed, 3),
                    "state": "semantic_snapshot_temporarily_unavailable",
                    "error_type": type(error).__name__,
                    "error": str(error),
                },
            )
            if logger is not None and elapsed >= next_progress_log:
                logger(f"semantic snapshot unavailable at {elapsed:.1f}s")
                while next_progress_log <= elapsed:
                    next_progress_log += 60.0
            sleeper(0.1)
            continue
        if not isinstance(snapshot, dict):
            raise SeedCaptureError("MCP snapshot is not an object")
        sequence += 1
        active = snapshot.get("active_event")
        append_jsonl(
            evidence_path,
            {
                "schema_version": 1,
                "sequence": sequence,
                "elapsed_seconds": round(max(0.0, now - started), 3),
                "state": "semantic_snapshot_available",
                "revision": snapshot.get("revision"),
                "date_raw": snapshot.get("date_raw"),
                "paused": snapshot.get("paused"),
                "map_ready": snapshot.get("map_ready"),
                "active_event": active,
            },
        )
        if isinstance(active, dict):
            revision = _positive_revision(snapshot)
            if snapshot.get("paused") is not True:
                try:
                    service.execute_step("pause-map", expected_revision=revision)
                except BaseException as error:
                    if (
                        pre_submission_revision_mismatch_error is None
                        or not isinstance(
                            error, pre_submission_revision_mismatch_error
                        )
                    ):
                        raise
                    sequence += 1
                    append_jsonl(
                        evidence_path,
                        {
                            "schema_version": 1,
                            "sequence": sequence,
                            "elapsed_seconds": round(
                                max(0.0, clock() - started), 3
                            ),
                            "state": "pause_revision_changed_before_submission",
                            "expected_revision": revision,
                            "error_type": type(error).__name__,
                            "error": str(error),
                        },
                    )
                sleeper(0.1)
                continue
            event_id = active.get("instance_id")
            if (
                not isinstance(event_id, int)
                or isinstance(event_id, bool)
                or event_id <= 0
            ):
                raise SeedCaptureError("active event lacks a positive instance ID")
            query = service.query_current_event_window_context_v1(
                event_id, expected_revision=revision
            )
            context = (
                query.get("current_event_window_context")
                if isinstance(query, dict)
                else None
            )
            key = (
                context.get("event_definition_key")
                if isinstance(context, dict)
                else None
            )
            if key != SEED_EVENT_DEFINITION_KEY:
                if isinstance(context, dict) and key not in drained_pre_bootstrap_events:
                    if key == KNOWN_PRE_BOOTSTRAP_EVENT["event_definition_key"]:
                        expected = KNOWN_PRE_BOOTSTRAP_EVENT
                        identity_checks = _known_pre_bootstrap_event_checks(
                            source_save_sha256=source_save_sha256,
                            snapshot=snapshot,
                            context=context,
                            event_instance_id=event_id,
                        )
                        artifact_name = "known-pre-bootstrap-event-drain.json"
                        state_prefix = "known_pre_bootstrap_event"
                    elif key == KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT[
                        "event_definition_key"
                    ]:
                        expected = KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT
                        identity_checks = (
                            _known_pre_bootstrap_vanilla_event_checks(
                                source_save_sha256=source_save_sha256,
                                snapshot=snapshot,
                                context=context,
                                event_instance_id=event_id,
                            )
                        )
                        artifact_name = (
                            "known-pre-bootstrap-vanilla-event-drain.json"
                        )
                        state_prefix = "known_pre_bootstrap_vanilla_event"
                    else:
                        expected = None
                    if expected is not None:
                        _drain_known_pre_bootstrap_event(
                            service,
                            artifacts,
                            source_save_sha256=source_save_sha256,
                            snapshot=snapshot,
                            query=query,
                            context=context,
                            event_instance_id=event_id,
                            expected=expected,
                            identity_checks=identity_checks,
                            evidence_path=evidence_path,
                            artifact_name=artifact_name,
                            state_prefix=state_prefix,
                        )
                        drained_pre_bootstrap_events.append(key)
                        sleeper(0.1)
                        continue
                evidence = {
                    "state": "unexpected_visible_event",
                    "expected_event_definition_key": SEED_EVENT_DEFINITION_KEY,
                    "observed_event_definition_key": key,
                    "event_instance_id": event_id,
                    "drained_pre_bootstrap_events": drained_pre_bootstrap_events,
                }
                append_jsonl(evidence_path, evidence)
                raise SeedCaptureError(
                    f"unexpected visible event before bootstrap: {key!r}", evidence
                )
            terminal = {
                "schema_version": 1,
                "sequence": sequence + 1,
                "elapsed_seconds": round(max(0.0, clock() - started), 3),
                "state": "bootstrap_event_ready",
                "result": "GREEN",
                "event_definition_key": key,
                "event_instance_id": event_id,
            }
            append_jsonl(evidence_path, terminal)
            return snapshot
        if snapshot.get("map_ready") is True:
            revision = _positive_revision(snapshot)
            if snapshot.get("speed") != 1:
                service.execute_step("set-speed-1", expected_revision=revision)
            elif snapshot.get("paused") is True:
                service.execute_step("resume-map", expected_revision=revision)
                resumed = True
        sleeper(0.1)
    evidence = {
        "schema_version": 1,
        "sequence": sequence + 1,
        "elapsed_seconds": round(max(0.0, clock() - started), 3),
        "state": (
            "bootstrap_event_timeout_after_known_prebootstrap_events"
            if drained_pre_bootstrap_events
            else "bootstrap_event_timeout"
        ),
        "result": "RED",
        "timeout_seconds": timeout_seconds,
        "timeline_resumed": resumed,
        "known_pre_bootstrap_event_drained": (
            KNOWN_PRE_BOOTSTRAP_EVENT["event_definition_key"]
            in drained_pre_bootstrap_events
        ),
        "known_pre_bootstrap_vanilla_event_drained": (
            KNOWN_PRE_BOOTSTRAP_VANILLA_EVENT["event_definition_key"]
            in drained_pre_bootstrap_events
        ),
        "drained_pre_bootstrap_events": drained_pre_bootstrap_events,
        "wait_policy": "original_total_deadline_not_reset_by_drains",
    }
    append_jsonl(evidence_path, evidence)
    raise SeedCaptureError(
        f"timed out before exact {SEED_EVENT_DEFINITION_KEY}", evidence
    )


def provider_probe(
    service: Any, matrix: dict[str, Any], artifacts: Path
) -> dict[str, Any]:
    """Preserve every phase-two provider response on paused MCP revisions."""

    snapshot = service.snapshot()
    if not isinstance(snapshot, dict) or snapshot.get("paused") is not True:
        raise SeedCaptureError("provider probe lacks a paused MCP snapshot")
    _positive_revision(snapshot)
    output: dict[str, Any] = {
        "schema_version": 1,
        "result": "captured",
        "mcp_only": True,
        "gameplay_control_transport": "MCP-only",
        "non_gameplay_platform_operation": "US-English HKL watchdog",
        "ocr_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "snapshot": snapshot,
        "selectors": matrix,
        "responses": {},
        "readiness": {},
    }
    responses: dict[str, Any] = output["responses"]

    def revision() -> int:
        current = service.snapshot()
        if not isinstance(current, dict):
            raise SeedCaptureError("provider revision snapshot is not an object")
        return _positive_revision(current)

    def capture(label: str, operation: Callable[[], Any]) -> None:
        try:
            responses[label] = {"response": operation()}
        except BaseException as error:
            responses[label] = {
                "error": f"{type(error).__name__}: {error}",
                "traceback": traceback.format_exc(),
            }
        write_json(artifacts / "provider-probes.json", output)

    capture(
        "loaded_feature_manifest",
        lambda: service.query_loaded_feature_manifest_v1(
            expected_revision=revision()
        ),
    )
    capture(
        "b2_pip",
        lambda: service.query_zhongguo_b2_pip_snapshot_v1(
            "zg361.seed.live.b2.01",
            expected_revision=revision(),
            owner_character_id=int(matrix["b2_pip_owner_character_id"]),
        ),
    )
    for profile in ("x", "y", "z"):
        capture(
            f"incident_{profile}",
            lambda profile=profile: service.query_zhongguo_incident_snapshot_v1(
                f"zg361.seed.live.incident.{profile}.01",
                expected_revision=revision(),
                owner_character_id=int(matrix["incident_owner_character_id"]),
                profile=profile,
            ),
        )
    capture(
        "workforce_collective",
        lambda: service.query_zhongguo_workforce_collective_snapshot_v1(
            "zg361.seed.live.workforce.01",
            expected_revision=revision(),
            owner_character_id=int(matrix["workforce_owner_character_id"]),
        ),
    )
    capture(
        "ai_owned_case",
        lambda: service.query_zhongguo_ai_owned_case_snapshot_v1(
            int(matrix["ai_owned_case_owner_character_id"]),
            int(matrix["ai_owned_case_subject_character_id"]),
            "zg361.seed.live.ai-owned.01",
            expected_revision=revision(),
        ),
    )

    def response(label: str) -> dict[str, Any]:
        row = responses.get(label)
        value = row.get("response") if isinstance(row, dict) else None
        return value if isinstance(value, dict) else {}

    b2 = response("b2_pip")
    workforce = response("workforce_collective")
    ai_owned = response("ai_owned_case")
    incidents = [response(f"incident_{profile}") for profile in ("x", "y", "z")]
    incident_kinds = {
        item.get("terminal", {}).get("kind")
        for item in incidents
        if isinstance(item.get("terminal"), dict)
    }
    readiness = {
        "b2_pip_ready": b2.get("status") == "available"
        and isinstance(b2.get("readiness"), dict)
        and b2["readiness"].get("ready") is True,
        "incident_profiles_ready": all(
            item.get("status") == "available"
            and isinstance(item.get("readiness"), dict)
            and item["readiness"].get("ready") is True
            for item in incidents
        ),
        "incident_mixed_na_positive": incident_kinds == {"na", "incident"},
        "workforce_collective_ready": workforce.get("status") == "available"
        and isinstance(workforce.get("readiness"), dict)
        and workforce["readiness"].get("ready") is True,
        "ai_owned_case_ready": ai_owned.get("status") == "available"
        and isinstance(ai_owned.get("readiness"), dict)
        and ai_owned["readiness"].get("ready") is True,
    }
    output["readiness"] = readiness
    output["all_product_providers_ready"] = all(readiness.values())
    write_json(artifacts / "provider-probes.json", output)
    return output


def _copy_logs(profile: Path, artifacts: Path) -> dict[str, Any]:
    source = profile / "logs"
    destination = artifacts / "ck3-logs"
    copied: list[dict[str, Any]] = []
    if source.is_dir():
        destination.mkdir(parents=True, exist_ok=True)
        for path in sorted(item for item in source.iterdir() if item.is_file()):
            target = destination / path.name
            shutil.copy2(path, target)
            copied.append(
                {
                    "name": path.name,
                    "bytes": target.stat().st_size,
                    "sha256": sha256_file(target),
                }
            )
    return {"source": str(source), "destination": str(destination), "files": copied}


def _ck3_is_running(acceptance: Any) -> bool:
    """Return the runtime's CK3 process state without starting any process."""

    checker = getattr(acceptance, "ck3_is_running", None)
    if not callable(checker):
        raise SeedCaptureError(
            "no-launch preflight cannot prove the CK3 process inventory: "
            "runtime checker is unavailable"
        )
    return bool(checker())


def _preflight_setup_failure(
    config: CaptureConfig, error: BaseException
) -> dict[str, Any] | None:
    """Persist a setup RED when doing so cannot overwrite prior evidence."""

    try:
        if _is_relative_to(config.attempt_dir, config.clean_source) or _is_relative_to(
            config.artifacts_dir, config.clean_source
        ):
            return None
        if config.artifacts_dir.exists() and any(config.artifacts_dir.iterdir()):
            # A non-empty artifact directory is immutable evidence from an
            # earlier attempt; never replace it just to report a retry error.
            return None
        config.artifacts_dir.mkdir(parents=True, exist_ok=True)
        report: dict[str, Any] = {
            "schema_version": 1,
            "kind": "zg361_phase2_seed_preflight",
            "mode": "preflight-only",
            "result": "RED",
            "status": "preflight-blocked",
            "ok": False,
            "readiness_scope": "frozen_inputs_and_projection_only",
            "seed_ready": False,
            "seed_contract_status": "unknown",
            "started_at_utc": utc_now(),
            "finished_at_utc": utc_now(),
            "report_path": str((config.artifacts_dir / "preflight.json").resolve()),
            "frozen_git_commit": config.frozen_git_sha,
            "paths": {
                "clean_source": str(config.clean_source),
                "source_zip": str(config.source_zip),
                "attempt": str(config.attempt_dir),
                "artifacts": str(config.artifacts_dir),
                "state": str(config.state_dir),
                "profile": str(config.profile_dir),
                "seed_contract": str(config.seed_contract),
            },
            "desktop_interaction": False,
            "mcp_only": True,
            "ocr_used": False,
            "image_used": False,
            "coordinates_used": False,
            "test_decision_used": False,
            "ck3_launch_attempted": False,
            "launch_boundary": "not-crossed",
            "native_session_started": False,
            "driver_opened": False,
            "checks": {},
            "failure_reason": f"{type(error).__name__}: {error}",
            "failure_evidence": None,
        }
        write_json(config.artifacts_dir / "preflight.json", report)
        append_jsonl(
            config.artifacts_dir / "preflight-failures.jsonl",
            {
                "schema_version": 1,
                "state": "seed_preflight_setup_failed",
                "error_type": type(error).__name__,
                "error": str(error),
            },
        )
        return report
    except BaseException:
        return None


def _run_seed_static_preflight(
    config: CaptureConfig,
    artifacts: Path,
    *,
    allow_missing_for_fixture: bool = False,
) -> dict[str, Any]:
    """Run the seed-specific offline gates without invoking CK3 or desktop IO."""

    commands = (
        ("validate_static", config.clean_source / "tools" / "validate_static.py", False),
        (
            "validate_local",
            config.clean_source / "mod_zhongguo_style" / "tools" / "validate_local.py",
            False,
        ),
        (
            "seed_loader_test",
            config.clean_source / "tools" / "test_zg361_phase2_loader_stage.py",
            False,
        ),
        (
            "seed_loader_test_optimized",
            config.clean_source / "tools" / "test_zg361_phase2_loader_stage.py",
            True,
        ),
        (
            "seed_bootstrap_test",
            config.clean_source / "tools" / "test_zg361_phase2_seed_bootstrap.py",
            False,
        ),
        (
            "seed_bootstrap_test_optimized",
            config.clean_source / "tools" / "test_zg361_phase2_seed_bootstrap.py",
            True,
        ),
        (
            "seed_fixture_test",
            config.clean_source / "tools" / "test_zg361_phase2_seed_fixture.py",
            False,
        ),
        (
            "seed_fixture_test_optimized",
            config.clean_source / "tools" / "test_zg361_phase2_seed_fixture.py",
            True,
        ),
        (
            "seed_capture_test",
            config.clean_source / "tools" / "test_run_zg361_phase2_seed_capture.py",
            False,
        ),
        (
            "seed_capture_test_optimized",
            config.clean_source / "tools" / "test_run_zg361_phase2_seed_capture.py",
            True,
        ),
    )
    missing = [
        name
        for name, path, _optimized in commands
        if not path.is_file()
    ]
    if missing:
        # The tiny fake runtimes used by the CK3-free unit tests intentionally
        # contain only the minimum fixture files.  They still exercise the
        # preflight ordering.  This escape is private and explicit; the real
        # CLI must never turn a missing seed gate into a false GREEN.
        evidence = {
            "result": "SKIPPED" if allow_missing_for_fixture else "RED",
            "reason": (
                "seed-specific offline gate scripts are absent in injected fixture runtime"
                if allow_missing_for_fixture
                else "required seed-specific offline gate scripts are missing"
            ),
            "missing_scripts": missing,
            "commands": [],
        }
        write_json(artifacts / "static-preflight.json", evidence)
        if allow_missing_for_fixture:
            return evidence
        raise SeedCaptureError(
            "seed static preflight cannot be skipped for the real CLI",
            evidence,
        )
    rows: list[dict[str, Any]] = []
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    for name, script, optimized in commands:
        # ``-B`` protects imports before the fixture code runs; the explicit
        # environment guard also propagates through any nested child process.
        command = [sys.executable, "-B"]
        if optimized:
            command.append("-O")
        command.append(str(script))
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=config.clean_source,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120.0,
                check=False,
            )
            row = {
                "name": name,
                "command": command,
                "returncode": completed.returncode,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "stdout": completed.stdout[-4000:],
                "stderr": completed.stderr[-4000:],
            }
        except BaseException as error:
            row = {
                "name": name,
                "command": command,
                "returncode": None,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "error": f"{type(error).__name__}: {error}",
            }
        rows.append(row)
        if row.get("returncode") != 0:
            evidence = {"result": "RED", "commands": rows}
            write_json(artifacts / "static-preflight.json", evidence)
            raise SeedCaptureError(
                f"seed static preflight failed: {name}", evidence
            )
    evidence = {"result": "GREEN", "commands": rows}
    write_json(artifacts / "static-preflight.json", evidence)
    return evidence


def _run_list_domain_observer_gate(
    config: CaptureConfig,
    artifacts: Path,
    *,
    game_version: str,
    dependency_hashes: dict[str, str],
    clean_source_tree_sha256: str,
) -> dict[str, Any] | None:
    """Freeze the next observer seam without selecting a native address here."""

    enabled = (
        config.list_domain_observer_gate
        or config.acceptance_observer_manifest is not None
    )
    if not enabled:
        return None
    gate = evaluate_observer_gate(
        contract_path=config.acceptance_observer_contract,
        observer_manifest_path=config.acceptance_observer_manifest,
        clean_source=config.clean_source,
        frozen_git_commit=config.frozen_git_sha,
        game_version=game_version,
        game_executable_sha256=dependency_hashes["game_executable"],
        bridge_dll_sha256=dependency_hashes["bridge_dll"],
        bridge_injector_sha256=dependency_hashes["bridge_injector"],
        source_zip_sha256=dependency_hashes["source_zip"],
        clean_source_tree_sha256=clean_source_tree_sha256,
        pipe_name=config.pipe_name,
    )
    write_json(artifacts / "list-domain-observer-gate.json", gate)
    return gate


def run_preflight(
    raw_config: CaptureConfig,
    *,
    runtime: RuntimeBindings | None = None,
    _allow_fixture_static_skip: bool = False,
) -> dict[str, Any]:
    """Validate one frozen seed attempt without crossing the CK3 launch boundary.

    This deliberately stops after source/dependency verification and the
    product+fixture projection.  It never starts ``native_session``, opens a
    bridge driver, sends HKL messages, or waits for a loader/event.  A fresh
    attempt directory is required and the machine-readable ``preflight.json``
    artifact is written for both GREEN and RED outcomes.
    """

    config = raw_config.resolved()
    try:
        prepare_output_paths(config)
    except BaseException as error:
        setup_report = _preflight_setup_failure(config, error)
        if setup_report is not None:
            return setup_report
        raise
    artifacts = config.artifacts_dir
    report: dict[str, Any] = {
        "schema_version": 1,
        "kind": "zg361_phase2_seed_preflight",
        "mode": "preflight-only",
        "result": "RED",
        "status": "checking",
        "ok": False,
        "readiness_scope": "frozen_inputs_and_projection_only",
        "seed_ready": False,
        "seed_contract_status": None,
        "started_at_utc": utc_now(),
        "finished_at_utc": None,
        "report_path": str((artifacts / "preflight.json").resolve()),
        "frozen_git_commit": config.frozen_git_sha,
        "game_dir": {
            "selected": str(config.game_dir),
            "source": config.game_dir_source,
            "candidates": list(config.game_dir_candidates),
        },
        "paths": {
            "clean_source": str(config.clean_source),
            "product_source": str(config.product_source),
            "product_projection": config.product_projection,
            "product_projection_manifest": (
                str(config.product_projection_manifest)
                if config.product_projection_manifest is not None
                else None
            ),
            "source_zip": str(config.source_zip),
            "attempt": str(config.attempt_dir),
            "artifacts": str(artifacts),
            "state": str(config.state_dir),
            "profile": str(config.profile_dir),
            "seed_contract": str(config.seed_contract),
            "acceptance_observer_contract": (
                str(config.acceptance_observer_contract)
                if config.list_domain_observer_gate
                or config.acceptance_observer_manifest is not None
                else None
            ),
            "acceptance_observer_manifest": (
                str(config.acceptance_observer_manifest)
                if config.acceptance_observer_manifest is not None
                else None
            ),
            "bridge_bundle_manifest": (
                str(config.bridge_bundle_manifest)
                if config.bridge_bundle_manifest is not None
                else None
            ),
        },
        "desktop_interaction": False,
        "mcp_only": True,
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "ck3_launch_attempted": False,
        "launch_boundary": "not-crossed",
        "native_session_started": False,
        "driver_opened": False,
        "checks": {},
        "source_identity": None,
        "critical_b2_product_byte_equivalence": None,
        "external_dependencies": None,
        "bootstrap": None,
        "profile_settings": {
            "result": "NOT_RUN",
            "strategy": "explicit-full-settings-template-only",
            "reason": "no-launch preflight does not mutate the isolated profile",
        },
        "bridge": None,
        "list_domain_observer_gate": None,
        "static_preflight": None,
        "failure_reason": None,
        "failure_evidence": None,
    }
    active_runtime = runtime
    source_manifest_before: dict[str, Any] | None = None
    dependency_paths: dict[str, Path] | None = None
    dependency_hashes_before: dict[str, str] | None = None
    initial_runtime_trees: dict[str, Any] | None = None
    bootstrap_targets: dict[str, Path] | None = None

    try:
        validate_config(config)
        report["open_kaishek_preflight"] = _run_open_kaishek_seed_preflight(
            config, artifacts, runtime=runtime
        )
        report["checks"]["config"] = "GREEN"
        if active_runtime is None:
            active_runtime = load_runtime(config)
        acceptance = active_runtime.acceptance
        zgrun = active_runtime.zgrun

        if _ck3_is_running(acceptance):
            raise SeedCaptureError(
                "no-launch preflight requires zero running ck3.exe processes"
            )
        report["checks"]["ck3_process_inventory"] = {
            "result": "GREEN",
            "running": False,
        }

        source_manifest_before = tree_manifest(config.clean_source)
        write_json(
            artifacts / "source-tree-manifest.before.json", source_manifest_before
        )
        source_zip_manifest = zip_manifest(config.source_zip)
        write_json(artifacts / "source-zip-manifest.json", source_zip_manifest)
        bytecode_paths = sorted(
            str(row["path"])
            for row in source_manifest_before["files"]
            if isinstance(row, dict)
            and (
                "__pycache__" in Path(str(row["path"])).parts
                or Path(str(row["path"])).suffix.lower() in {".pyc", ".pyo"}
            )
        )
        if bytecode_paths:
            raise SeedCaptureError(
                "clean source contains generated Python bytecode",
                {"bytecode_paths": bytecode_paths},
            )
        archive_equivalence = compare_zip_to_source(
            source_zip_manifest, source_manifest_before
        )
        if archive_equivalence["equivalent"] is not True:
            raise SeedCaptureError(
                "clean source is not byte-equivalent to the explicit source ZIP",
                archive_equivalence,
            )
        source_identity = {
            "git": git_identity(config),
            "source_zip": {
                "path": str(config.source_zip),
                "bytes": config.source_zip.stat().st_size,
                "sha256": sha256_file(config.source_zip),
                "logical_tree_sha256": source_zip_manifest["logical_tree_sha256"],
            },
            "clean_source_tree": {
                key: source_manifest_before[key]
                for key in ("algorithm", "file_count", "tree_sha256")
            },
            "archive_source_equivalence": archive_equivalence,
        }
        report["source_identity"] = source_identity
        report["checks"]["source_archive_equivalence"] = "GREEN"

        try:
            report["critical_b2_product_byte_equivalence"] = (
                enforce_critical_b2_product_bytes(config, artifacts)
            )
        except SeedCaptureError as error:
            report["critical_b2_product_byte_equivalence"] = error.evidence
            report["checks"]["critical_b2_product_byte_equivalence"] = "RED"
            raise
        report["checks"]["critical_b2_product_byte_equivalence"] = "GREEN"

        base_contract = json.loads(config.seed_contract.read_text(encoding="utf-8"))
        report["seed_contract_status"] = base_contract.get("status")
        source_row = base_contract.get("source")
        if not isinstance(source_row, dict):
            raise SeedCaptureError("seed contract source is not an object")
        raw_old_save = source_row.get("absolute_save")
        if not isinstance(raw_old_save, str) or not raw_old_save:
            raise SeedCaptureError("seed contract absolute_save is missing")
        old_save_path = Path(raw_old_save)
        if not old_save_path.is_absolute():
            raise SeedCaptureError("seed contract absolute_save must be absolute")
        old_save = old_save_path.resolve()
        expected_save_sha = source_row.get("sha256")
        if not old_save.is_file():
            raise SeedCaptureError(f"old real seed source is missing: {old_save}")
        observed_save_sha = sha256_file(old_save)
        if observed_save_sha != expected_save_sha:
            raise SeedCaptureError(
                f"old real seed source hash drifted: {observed_save_sha}"
            )

        dependency_paths = {
            "source_zip": config.source_zip,
            "old_save": old_save,
            "game_executable": config.game_executable,
            "vanilla_game_rules": config.vanilla_game_rules,
            "bridge_dll": config.bridge_dll,
            "bridge_injector": config.bridge_injector,
        }
        if config.product_projection_manifest is not None:
            dependency_paths["product_projection_manifest"] = (
                config.product_projection_manifest
            )
        if config.acceptance_observer_manifest is not None:
            dependency_paths["acceptance_observer_manifest"] = (
                config.acceptance_observer_manifest
            )
        if config.bridge_bundle_manifest is not None:
            dependency_paths["bridge_bundle_manifest"] = (
                config.bridge_bundle_manifest
            )
        dependency_hashes_before = {
            name: sha256_file(path) for name, path in dependency_paths.items()
        }
        expected_executable_sha = getattr(zgrun, "EXPECTED_EXE_SHA256", None)
        expected_game_version = getattr(zgrun, "EXPECTED_GAME_VERSION", None)
        if dependency_hashes_before["game_executable"] != expected_executable_sha:
            raise SeedCaptureError(
                "CK3 executable does not match the exact supported build: "
                f"{dependency_hashes_before['game_executable']}"
            )
        observed_game_version = zgrun.isolated.installed_game_version()
        if observed_game_version != expected_game_version:
            raise SeedCaptureError(
                "CK3 version does not match the exact supported build: "
                f"{observed_game_version!r}"
            )
        report["external_dependencies"] = {
            "paths": {name: str(path) for name, path in dependency_paths.items()},
            "sha256_before": dependency_hashes_before,
            "sha256_after": None,
            "unchanged": None,
            "game_version": observed_game_version,
            "expected_game_version": expected_game_version,
            "expected_executable_sha256": expected_executable_sha,
            "old_save": {
                "path": str(old_save),
                "bytes": old_save.stat().st_size,
                "sha256": observed_save_sha,
            },
        }
        report["checks"]["external_dependencies"] = "GREEN"

        report["list_domain_observer_gate"] = _run_list_domain_observer_gate(
            config,
            artifacts,
            game_version=observed_game_version,
            dependency_hashes=dependency_hashes_before,
            clean_source_tree_sha256=source_manifest_before["tree_sha256"],
        )
        if report["list_domain_observer_gate"] is not None:
            report["checks"]["list_domain_observer_gate"] = report[
                "list_domain_observer_gate"
            ]["result"]
            if report["list_domain_observer_gate"]["result"] != "GREEN":
                raise SeedCaptureError(
                    "list-domain observer gate blocked: "
                    f"{report['list_domain_observer_gate'].get('failure_reason')}",
                    report["list_domain_observer_gate"],
                )

        bridge = zgrun.resolve_native_bridge_config(
            config.bridge_dll, config.bridge_injector, config.pipe_name
        )
        bridge_identity = {
            "mode": getattr(bridge, "mode", None),
            "pipe": getattr(bridge, "pipe_name", config.pipe_name),
            "dll": str(config.bridge_dll),
            "dll_sha256": sha256_file(config.bridge_dll),
            "injector": str(config.bridge_injector),
            "injector_sha256": sha256_file(config.bridge_injector),
            "visual_fallback": False,
        }
        bridge_identity["release_bundle"] = bridge_bundle_provenance(config)
        identity_fn = getattr(zgrun, "native_bridge_preflight_identity", None)
        if callable(identity_fn):
            bridge_identity["runtime_identity"] = identity_fn(bridge)
        report["bridge"] = bridge_identity
        report["checks"]["bridge"] = "GREEN"

        report["static_preflight"] = _run_seed_static_preflight(
            config,
            artifacts,
            # The skip escape is a unit-test seam, never a real-runtime mode.
            # Even if a caller reaches this private flag directly, a missing
            # gate must remain RED unless an injected runtime is present.
            allow_missing_for_fixture=(
                _allow_fixture_static_skip and runtime is not None
            ),
        )
        report["checks"]["static_preflight"] = report["static_preflight"][
            "result"
        ]

        bootstrap = _bootstrap_product_projection(zgrun, config)
        enabled_mods = tuple(bootstrap.get("enabled_mods", ()))
        if enabled_mods != EXPECTED_ENABLED_MODS:
            raise SeedCaptureError(
                "seed profile must enable exactly product+fixture once: "
                f"{enabled_mods}"
            )
        raw_targets = bootstrap.get("targets")
        if not isinstance(raw_targets, dict) or set(raw_targets) != {
            "product",
            "fixture",
        }:
            raise SeedCaptureError("bootstrap targets are not exactly product+fixture")
        bootstrap_targets = {
            name: Path(path).resolve() for name, path in raw_targets.items()
        }
        try:
            report["critical_b2_product_byte_equivalence"] = (
                enforce_critical_b2_product_bytes(
                    config,
                    artifacts,
                    mounted_product=bootstrap_targets["product"],
                )
            )
        except SeedCaptureError as error:
            report["critical_b2_product_byte_equivalence"] = error.evidence
            report["checks"]["critical_b2_product_byte_equivalence"] = "RED"
            raise
        report["checks"]["critical_b2_product_byte_equivalence"] = "GREEN"
        initial_runtime_trees = {
            name: zgrun.isolated.tree_snapshot(path)
            for name, path in bootstrap_targets.items()
        }
        initial_runtime_tree_sha256 = {
            name: zgrun.isolated.snapshot_digest(tree)
            for name, tree in initial_runtime_trees.items()
        }
        declared_runtime_tree_sha256 = bootstrap.get("tree_sha256")
        if declared_runtime_tree_sha256 != initial_runtime_tree_sha256:
            raise SeedCaptureError(
                "bootstrap runtime tree hashes disagree with the projected trees",
                {
                    "declared_tree_sha256": declared_runtime_tree_sha256,
                    "observed_tree_sha256": initial_runtime_tree_sha256,
                },
            )
        report["bootstrap"] = {
            "targets": {name: str(path) for name, path in bootstrap_targets.items()},
            "tree_sha256": initial_runtime_tree_sha256,
            "enabled_mods": list(enabled_mods),
            "manifest": bootstrap.get("manifest"),
            "single_mount_contract": True,
            "projection_only": True,
            "mounted": False,
        }
        report["checks"]["product_fixture_projection"] = "GREEN"

        if _ck3_is_running(acceptance):
            raise SeedCaptureError(
                "ck3.exe appeared during no-launch preflight; launch boundary remains closed"
            )
        report["checks"]["ck3_process_inventory_after"] = {
            "result": "GREEN",
            "running": False,
        }
        report["result"] = "GREEN"
        report["status"] = "preflight-ready"
        report["ok"] = True
    except BaseException as error:
        report["result"] = "RED"
        report["status"] = "preflight-blocked"
        report["ok"] = False
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        report["traceback"] = traceback.format_exc()
        if isinstance(error, SeedCaptureError):
            report["failure_evidence"] = error.evidence
        append_jsonl(
            artifacts / "preflight-failures.jsonl",
            {
                "schema_version": 1,
                "state": "seed_preflight_failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "failure_evidence": report.get("failure_evidence"),
                "traceback": report["traceback"],
            },
        )
    finally:
        # Hashes are checked again before the report can claim readiness.  A
        # preflight never owns a native process, so projection immutability is
        # the only runtime after-check needed here.
        if source_manifest_before is not None:
            try:
                source_manifest_after = tree_manifest(config.clean_source)
                write_json(
                    artifacts / "source-tree-manifest.after.json",
                    source_manifest_after,
                )
                unchanged = (
                    source_manifest_after["tree_sha256"]
                    == source_manifest_before["tree_sha256"]
                )
                source_identity = report.get("source_identity")
                if not isinstance(source_identity, dict):
                    source_identity = {}
                    report["source_identity"] = source_identity
                source_identity["clean_source_tree_after"] = {
                    key: source_manifest_after[key]
                    for key in ("algorithm", "file_count", "tree_sha256")
                }
                report["checks"]["clean_source_unchanged"] = (
                    "GREEN" if unchanged else "RED"
                )
                if not unchanged:
                    _flip_red(report, "clean source tree changed during preflight")
            except BaseException as error:
                _flip_red(report, f"source immutability check failed: {error}")
        if dependency_paths is not None and dependency_hashes_before is not None:
            dependency_row = report.get("external_dependencies")
            try:
                dependency_hashes_after = {
                    name: sha256_file(path)
                    for name, path in dependency_paths.items()
                }
                if not isinstance(dependency_row, dict):
                    dependency_row = {
                        "paths": {
                            name: str(path)
                            for name, path in dependency_paths.items()
                        },
                        "sha256_before": dependency_hashes_before,
                    }
                    report["external_dependencies"] = dependency_row
                dependency_row["sha256_after"] = dependency_hashes_after
                dependency_row["unchanged"] = (
                    dependency_hashes_after == dependency_hashes_before
                )
                report["checks"]["external_dependencies_unchanged"] = (
                    "GREEN" if dependency_row["unchanged"] else "RED"
                )
                if dependency_row["unchanged"] is not True:
                    _flip_red(
                        report, "external runtime dependency changed during preflight"
                    )
            except BaseException as error:
                _flip_red(report, f"dependency immutability check failed: {error}")
        if initial_runtime_trees is not None and bootstrap_targets is not None:
            try:
                final_trees = {
                    name: active_runtime.zgrun.isolated.tree_snapshot(path)
                    for name, path in bootstrap_targets.items()
                }
                unchanged = final_trees == initial_runtime_trees
                report["runtime_projection_unchanged"] = unchanged
                report["checks"]["runtime_projection_unchanged"] = (
                    "GREEN" if unchanged else "RED"
                )
                if not unchanged:
                    _flip_red(
                        report, "projected product/fixture tree changed during preflight"
                    )
            except BaseException as error:
                _flip_red(report, f"projection immutability check failed: {error}")
        report["finished_at_utc"] = utc_now()
        # These fields are invariants, not claims inferred from a successful
        # return.  Keep them explicit so a reviewer can verify the boundary.
        report["ck3_launch_attempted"] = False
        report["launch_boundary"] = "not-crossed"
        report["native_session_started"] = False
        report["driver_opened"] = False
        if report.get("result") == "GREEN":
            report["status"] = "preflight-ready"
            report["ok"] = True
        else:
            report["status"] = "preflight-blocked"
            report["ok"] = False
        write_json(artifacts / "preflight.json", report)
    return report


def _flip_red(report: dict[str, Any], reason: str) -> None:
    report["result"] = "RED"
    if report.get("failure_reason") is None:
        report["failure_reason"] = reason


def _phase2_native_session_probe(
    supervisor: object,
) -> dict[str, Any] | None:
    """Return a terminal supervisor snapshot without touching CK3 directly.

    The managed native-session thread publishes its report/error before
    setting ``session_done``.  The loader gate polls this boundary while it
    waits for append-only CK3 logs; once the event is set, returning the
    snapshot lets the gate emit a typed process-exit RED immediately instead
    of waiting for its generic 300-second timeout.
    """

    if not isinstance(supervisor, dict):
        raise TypeError("phase-two supervisor handle is not an object")
    session_done = supervisor.get("session_done")
    session_state = supervisor.get("session_state")
    session_thread = supervisor.get("session_thread")
    if not (
        isinstance(session_done, threading.Event)
        and isinstance(session_state, dict)
        and isinstance(session_thread, threading.Thread)
    ):
        raise TypeError("phase-two supervisor handle is malformed")
    if not session_done.is_set():
        return None
    report = session_state.get("report")
    error = session_state.get("error")
    return {
        "terminal": True,
        "session_thread_alive": session_thread.is_alive(),
        "session_report": report if isinstance(report, dict) else None,
        "session_error": error,
    }


def _phase2_wrapper_edge_decision(
    edge: dict[str, Any], correlation: dict[str, Any]
) -> tuple[str, str]:
    if edge.get("private_build") is not True:
        return "RED", "observer_not_private"
    if edge.get("failure_flags") != 0:
        return "RED", "observer_install_or_runtime_failure"
    if edge.get("installed") is not True:
        return "RED", "observer_not_installed"
    selected = correlation.get("producer_selected_count", 0)
    wrapper_post_publish = edge.get("wrapper_post_publish_entry_count", 0)
    exact_edges = edge.get("selected_after_publish_edge_0x3B9E10B_count", 0) + edge.get(
        "selected_after_publish_edge_0x3B9E175_count", 0
    )
    other_callers = edge.get("selected_after_publish_other_caller_count", 0)
    identity_matches = edge.get("consumer_identity_match_count", 0)
    if selected == 0:
        return "NO-GO", "producer_selected_task_not_observed"
    if wrapper_post_publish == 0:
        return "NO-GO", "selected_task_wrapper_never_rescheduled"
    if exact_edges == 0:
        return (
            "NO-GO",
            "wrapper_entered_consumer_other_caller"
            if other_callers > 0
            else "wrapper_entered_other_branch",
        )
    if identity_matches == 0:
        return "NO-GO", "consumer_edge_without_retained_task_identity"
    return "GREEN", "selected_task_reached_completion_consumer"


def observe_phase2_wrapper_consumer_edge(
    service: Any,
    artifacts: Path,
    *,
    timeout_seconds: float,
    clock: Callable[[], float] = time.monotonic,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    """Sample only bridge heartbeats; never inspect or operate the desktop."""

    if timeout_seconds <= 0:
        raise ValueError("native observer timeout must be positive")
    progress = artifacts / "phase2-wrapper-consumer-edge-heartbeats.jsonl"
    deadline = clock() + timeout_seconds
    samples: list[dict[str, Any]] = []
    seen: set[tuple[object, object]] = set()
    final_status = "RED"
    final_decision = "heartbeat_not_observed"
    final_edge: dict[str, Any] | None = None
    final_correlation: dict[str, Any] | None = None
    while True:
        capabilities = service.capabilities()
        diagnostics = (
            capabilities.get("diagnostics")
            if isinstance(capabilities, dict)
            else None
        )
        heartbeat = (
            diagnostics.get("last_heartbeat")
            if isinstance(diagnostics, dict)
            else None
        )
        if isinstance(heartbeat, dict):
            identity = (heartbeat.get("pid"), heartbeat.get("sequence"))
            edge = heartbeat.get(PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_KEY)
            correlation = heartbeat.get(PHASE2_PRODUCER_CORRELATION_OBSERVER_KEY)
            if isinstance(edge, dict) and isinstance(correlation, dict):
                final_edge = dict(edge)
                final_correlation = dict(correlation)
                final_status, final_decision = _phase2_wrapper_edge_decision(
                    final_edge, final_correlation
                )
                if identity not in seen:
                    seen.add(identity)
                    row = {
                        "schema_version": 1,
                        "pid": heartbeat.get("pid"),
                        "sequence": heartbeat.get("sequence"),
                        "status": final_status,
                        "decision": final_decision,
                        "producer_selected_count": final_correlation.get(
                            "producer_selected_count"
                        ),
                        "observer": final_edge,
                    }
                    samples.append(row)
                    append_jsonl(progress, row)
                if final_status == "GREEN" or final_edge.get("failure_flags") != 0:
                    break
        now = clock()
        if now >= deadline:
            break
        sleeper(min(0.25, max(0.0, deadline - now)))
    return {
        "schema_version": 1,
        "result": final_status,
        "decision": final_decision,
        "observer_key": PHASE2_WRAPPER_CONSUMER_EDGE_OBSERVER_KEY,
        "correlation_key": PHASE2_PRODUCER_CORRELATION_OBSERVER_KEY,
        "heartbeat_only": True,
        "image_used": False,
        "ocr_used": False,
        "ui_input_sent": False,
        "gameplay_commands": [],
        "sample_count": len(samples),
        "samples": samples,
        "final_observer": final_edge,
        "final_correlation": final_correlation,
    }


def run_capture(
    raw_config: CaptureConfig,
    *,
    runtime: RuntimeBindings | None = None,
) -> dict[str, Any]:
    """Run one capture attempt; dependency injection keeps static tests CK3-free."""

    config = raw_config.resolved()
    prepare_output_paths(config)
    artifacts = config.artifacts_dir
    report: dict[str, Any] = {
        "schema_version": 1,
        "result": "RED",
        "started_at_utc": utc_now(),
        "frozen_git_commit": config.frozen_git_sha,
        "game_dir": {
            "selected": str(config.game_dir),
            "source": config.game_dir_source,
            "candidates": list(config.game_dir_candidates),
        },
        "paths": {
            "clean_source": str(config.clean_source),
            "product_source": str(config.product_source),
            "product_projection": config.product_projection,
            "product_projection_manifest": (
                str(config.product_projection_manifest)
                if config.product_projection_manifest is not None
                else None
            ),
            "source_zip": str(config.source_zip),
            "attempt": str(config.attempt_dir),
            "artifacts": str(artifacts),
            "state": str(config.state_dir),
            "profile": str(config.profile_dir),
            "seed_contract": str(config.seed_contract),
            "acceptance_observer_contract": (
                str(config.acceptance_observer_contract)
                if config.list_domain_observer_gate
                or config.acceptance_observer_manifest is not None
                else None
            ),
            "acceptance_observer_manifest": (
                str(config.acceptance_observer_manifest)
                if config.acceptance_observer_manifest is not None
                else None
            ),
            "bridge_bundle_manifest": (
                str(config.bridge_bundle_manifest)
                if config.bridge_bundle_manifest is not None
                else None
            ),
        },
        "mcp_only": True,
        "native_observer_only": config.native_observer_only,
        "gameplay_control_transport": "MCP-only",
        "non_gameplay_platform_operation": (
            "none"
            if config.native_observer_only
            else "US-English HKL watchdog + optional legal-agreement gate"
        ),
        "ocr_used": False,
        "image_used": False,
        "coordinates_used": False,
        "test_decision_used": False,
        "fixture_kind": "acceptance-only phase2 seed bootstrap",
        "timeouts": {
            "binding_seconds": config.binding_timeout_seconds,
            "loader_seconds": config.loader_timeout_seconds,
            "loader_fatal_stall_seconds": LOADER_FATAL_STALL_SECONDS,
            "native_readiness_seconds": config.native_readiness_timeout_seconds,
            "total_event_wait_seconds": config.event_timeout_seconds,
            "frontend_first_seconds": (
                config.frontend_first_timeout_seconds
                if config.frontend_first_load_save_name is not None
                else None
            ),
        },
        "source_identity": None,
        "critical_b2_product_byte_equivalence": None,
        "external_dependencies": None,
        "list_domain_observer_gate": None,
        "bridge": None,
        "bootstrap": None,
        "binding": None,
        "legal_consent": None,
        "loader_stage": None,
        "runtime_mount_inventory": None,
        "native_readiness": None,
        "loader_error_log_scan": None,
        "bootstrap_event": None,
        "capture": None,
        "native_observer": None,
        "provider_probes": None,
        "candidate": None,
        "keyboard_watchdog": None,
        "cleanup": None,
        "driver_closed": None,
        "runtime_unchanged": None,
        "clean_source_unchanged": None,
        "logs_copy": None,
        "open_kaishek_preflight": None,
        "profile_settings": None,
        "frontend_first_warmup": {
            "enabled": config.frontend_first_load_save_name is not None,
            "load_save_name": config.frontend_first_load_save_name,
            "timeout_seconds": (
                config.frontend_first_timeout_seconds
                if config.frontend_first_load_save_name is not None
                else None
            ),
        },
        "failure_reason": None,
        "failure_evidence": None,
    }
    supervisor: Any = None
    driver: Any = None
    service: Any = None
    binding: dict[str, Any] | None = None
    initial_runtime_trees: dict[str, Any] | None = None
    initial_runtime_tree_sha256: dict[str, str] | None = None
    bootstrap_targets: dict[str, Path] | None = None
    source_manifest_before: dict[str, Any] | None = None
    dependency_hashes_before: dict[str, str] | None = None
    keyboard_stop = threading.Event()
    keyboard_thread: threading.Thread | None = None
    keyboard_started = False
    keyboard_rows: list[dict[str, Any]] = []
    keyboard_lock = threading.Lock()
    keyboard_first_row = threading.Event()
    active_runtime = runtime

    def runner_log(message: str) -> None:
        log(artifacts, message)

    try:
        validate_config(config)
        report["open_kaishek_preflight"] = _run_open_kaishek_seed_preflight(
            config, artifacts, runtime=runtime
        )
        source_manifest_before = tree_manifest(config.clean_source)
        write_json(artifacts / "source-tree-manifest.before.json", source_manifest_before)
        source_zip_manifest = zip_manifest(config.source_zip)
        write_json(artifacts / "source-zip-manifest.json", source_zip_manifest)
        bytecode_paths = sorted(
            str(row["path"])
            for row in source_manifest_before["files"]
            if isinstance(row, dict)
            and (
                "__pycache__" in Path(str(row["path"])).parts
                or Path(str(row["path"])).suffix.lower() in {".pyc", ".pyo"}
            )
        )
        if bytecode_paths:
            raise SeedCaptureError(
                "clean source contains generated Python bytecode",
                {"bytecode_paths": bytecode_paths},
            )
        archive_equivalence = compare_zip_to_source(
            source_zip_manifest, source_manifest_before
        )
        if archive_equivalence["equivalent"] is not True:
            raise SeedCaptureError(
                "clean source is not byte-equivalent to the explicit source ZIP",
                archive_equivalence,
            )
        source_identity = {
            "git": git_identity(config),
            "source_zip": {
                "path": str(config.source_zip),
                "bytes": config.source_zip.stat().st_size,
                "sha256": sha256_file(config.source_zip),
                "logical_tree_sha256": source_zip_manifest[
                    "logical_tree_sha256"
                ],
            },
            "clean_source_tree": {
                key: source_manifest_before[key]
                for key in ("algorithm", "file_count", "tree_sha256")
            },
            "archive_source_equivalence": archive_equivalence,
        }
        report["source_identity"] = source_identity
        try:
            report["critical_b2_product_byte_equivalence"] = (
                enforce_critical_b2_product_bytes(config, artifacts)
            )
        except SeedCaptureError as error:
            report["critical_b2_product_byte_equivalence"] = error.evidence
            raise
        active_runtime = active_runtime or load_runtime(config)
        acceptance = active_runtime.acceptance
        zgrun = active_runtime.zgrun
        seed = active_runtime.seed

        base_contract = json.loads(config.seed_contract.read_text(encoding="utf-8"))
        source_row = base_contract.get("source")
        if not isinstance(source_row, dict):
            raise SeedCaptureError("seed contract source is not an object")
        raw_old_save = source_row.get("absolute_save")
        if not isinstance(raw_old_save, str) or not raw_old_save:
            raise SeedCaptureError("seed contract absolute_save is missing")
        old_save_path = Path(raw_old_save)
        if not old_save_path.is_absolute():
            raise SeedCaptureError("seed contract absolute_save must be absolute")
        old_save = old_save_path.resolve()
        expected_save_sha = source_row.get("sha256")
        if not old_save.is_file():
            raise SeedCaptureError(f"old real seed source is missing: {old_save}")
        observed_save_sha = sha256_file(old_save)
        if observed_save_sha != expected_save_sha:
            raise SeedCaptureError(
                f"old real seed source hash drifted: {observed_save_sha}"
            )
        dependency_paths = {
            "source_zip": config.source_zip,
            "old_save": old_save,
            "game_executable": config.game_executable,
            "vanilla_game_rules": config.vanilla_game_rules,
            "bridge_dll": config.bridge_dll,
            "bridge_injector": config.bridge_injector,
        }
        if config.product_projection_manifest is not None:
            dependency_paths["product_projection_manifest"] = (
                config.product_projection_manifest
            )
        if config.acceptance_observer_manifest is not None:
            dependency_paths["acceptance_observer_manifest"] = (
                config.acceptance_observer_manifest
            )
        if config.bridge_bundle_manifest is not None:
            dependency_paths["bridge_bundle_manifest"] = (
                config.bridge_bundle_manifest
            )
        dependency_hashes_before = {
            name: sha256_file(path) for name, path in dependency_paths.items()
        }
        expected_executable_sha = getattr(zgrun, "EXPECTED_EXE_SHA256", None)
        if dependency_hashes_before["game_executable"] != expected_executable_sha:
            raise SeedCaptureError(
                "CK3 executable does not match the exact supported build: "
                f"{dependency_hashes_before['game_executable']}"
            )
        observed_game_version = zgrun.isolated.installed_game_version()
        expected_game_version = getattr(zgrun, "EXPECTED_GAME_VERSION", None)
        if observed_game_version != expected_game_version:
            raise SeedCaptureError(
                "CK3 version does not match the exact supported build: "
                f"{observed_game_version!r}"
            )
        report["external_dependencies"] = {
            "paths": {name: str(path) for name, path in dependency_paths.items()},
            "sha256_before": dependency_hashes_before,
            "sha256_after": None,
            "unchanged": None,
            "game_version": observed_game_version,
            "expected_game_version": expected_game_version,
            "expected_executable_sha256": expected_executable_sha,
        }

        report["list_domain_observer_gate"] = _run_list_domain_observer_gate(
            config,
            artifacts,
            game_version=observed_game_version,
            dependency_hashes=dependency_hashes_before,
            clean_source_tree_sha256=source_manifest_before["tree_sha256"],
        )
        if (
            report["list_domain_observer_gate"] is not None
            and report["list_domain_observer_gate"]["result"] != "GREEN"
        ):
            raise SeedCaptureError(
                "list-domain observer gate blocked: "
                f"{report['list_domain_observer_gate'].get('failure_reason')}",
                report["list_domain_observer_gate"],
            )

        bootstrap = _bootstrap_product_projection(zgrun, config)
        enabled_mods = tuple(bootstrap.get("enabled_mods", ()))
        if enabled_mods != EXPECTED_ENABLED_MODS:
            raise SeedCaptureError(
                f"seed profile must enable exactly product+fixture once: {enabled_mods}"
            )
        raw_targets = bootstrap.get("targets")
        if not isinstance(raw_targets, dict) or set(raw_targets) != {
            "product",
            "fixture",
        }:
            raise SeedCaptureError("bootstrap targets are not exactly product+fixture")
        bootstrap_targets = {
            name: Path(path).resolve() for name, path in raw_targets.items()
        }
        try:
            report["critical_b2_product_byte_equivalence"] = (
                enforce_critical_b2_product_bytes(
                    config,
                    artifacts,
                    mounted_product=bootstrap_targets["product"],
                )
            )
        except SeedCaptureError as error:
            report["critical_b2_product_byte_equivalence"] = error.evidence
            raise
        initial_runtime_trees = {
            name: zgrun.isolated.tree_snapshot(path)
            for name, path in bootstrap_targets.items()
        }
        initial_runtime_tree_sha256 = {
            name: zgrun.isolated.snapshot_digest(tree)
            for name, tree in initial_runtime_trees.items()
        }
        declared_runtime_tree_sha256 = bootstrap.get("tree_sha256")
        if declared_runtime_tree_sha256 != initial_runtime_tree_sha256:
            raise SeedCaptureError(
                "bootstrap runtime tree hashes disagree with the mounted projections",
                {
                    "declared_tree_sha256": declared_runtime_tree_sha256,
                    "observed_tree_sha256": initial_runtime_tree_sha256,
                },
            )
        report["bootstrap"] = {
            "targets": {name: str(path) for name, path in bootstrap_targets.items()},
            "tree_sha256": initial_runtime_tree_sha256,
            "enabled_mods": list(enabled_mods),
            "manifest": bootstrap.get("manifest"),
            "single_mount_contract": True,
        }
        try:
            report["profile_settings"] = prepare_profile_settings(config)
        except SeedCaptureError as error:
            # Preserve the typed profile evidence in the durable report before
            # the outer failure/cleanup path runs.  In particular, an invalid
            # or missing warm cache must be distinguishable from a CK3 loader
            # failure; neither case may cross the native launch boundary.
            if isinstance(error.evidence, dict) and error.evidence:
                report["profile_settings"] = error.evidence
            raise
        profile_settings = report["profile_settings"]
        if (
            not isinstance(profile_settings, dict)
            or profile_settings.get("profile_ready") is not True
            or profile_settings.get("result") not in {"GREEN", "PRESERVED"}
        ):
            evidence = (
                profile_settings
                if isinstance(profile_settings, dict)
                else {"value": profile_settings}
            )
            reason = str(
                evidence.get("failure_reason")
                or "pinned full settings and warm shadercache were not prepared"
            )
            raise _profile_startup_assets_error(evidence, reason)
        shutil.copy2(old_save, config.profile_dir / "save games" / "autosave.ck3")
        shutil.copy2(old_save, config.profile_dir / "last_save.ck3")
        report["frontend_first_warmup"]["save_materialization"] = (
            prepare_frontend_first_save(config, old_save)
        )
        acceptance.configure_runtime_userdir(config.profile_dir)
        spec = zgrun.make_spec(config.state_dir, config.game_dir)
        bridge = zgrun.resolve_native_bridge_config(
            config.bridge_dll, config.bridge_injector, config.pipe_name
        )
        report["bridge"] = {
            "dll": str(config.bridge_dll),
            "dll_sha256": sha256_file(config.bridge_dll),
            "injector": str(config.bridge_injector),
            "injector_sha256": sha256_file(config.bridge_injector),
            "pipe": config.pipe_name,
            "release_bundle": bridge_bundle_provenance(config),
        }
        write_json(
            artifacts / "preflight.json",
            {
                "schema_version": 1,
                "result": "GREEN",
                "source_identity": source_identity,
                "old_save": {
                    "path": str(old_save),
                    "bytes": old_save.stat().st_size,
                    "sha256": observed_save_sha,
                },
                "runtime_tree_sha256": initial_runtime_tree_sha256,
                "enabled_mods": list(enabled_mods),
                "bridge": report["bridge"],
                "mcp_only": True,
                "ocr_used": False,
                "coordinates_used": False,
                "test_decision_used": False,
            },
        )

        supervisor_options: dict[str, object] = {}
        if config.frontend_first_load_save_name is not None:
            supervisor_options = {
                "frontend_first_load_save_name": (
                    config.frontend_first_load_save_name
                ),
                "frontend_first_timeout_seconds": (
                    config.frontend_first_timeout_seconds
                ),
            }
        supervisor = zgrun.start_phase2_native_session_supervisor(
            spec, bridge, **supervisor_options
        )
        driver = active_runtime.driver_factory(
            bridge.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
            command_timeout_seconds=zgrun.NATIVE_TITLE_COMMAND_TIMEOUT_S,
        )
        service = active_runtime.service_factory(driver)
        binding = zgrun.wait_for_phase2_native_session_binding(
            service,
            supervisor,
            artifacts,
            timeout_s=config.binding_timeout_seconds,
        )
        report["binding"] = binding
        acceptance.ACTIVE_CK3_PID = int(binding["bridge_pid"])
        runner_log(
            f"CK3 PID {binding['bridge_pid']} bound on explicit pipe {config.pipe_name}"
        )
        if config.native_observer_only:
            report["legal_consent"] = {
                "schema_version": 1,
                "result": "NOT_APPLICABLE",
                "state": "not_inspected_no_input",
                "reason": (
                    "native-observer-only mode does not inspect the desktop or "
                    "send legal, UI, or gameplay input"
                ),
                "image_used": False,
                "ocr_used": False,
                "authorized_click_count": 0,
                "real_money_click_count": 0,
                "real_profile_read": False,
                "real_profile_modified": False,
            }
            observer = observe_phase2_wrapper_consumer_edge(
                service,
                artifacts,
                timeout_seconds=config.event_timeout_seconds,
                clock=active_runtime.clock,
                sleeper=active_runtime.sleep,
            )
            report["native_observer"] = observer
            report["result"] = observer["result"]
            report["live_verdict"] = observer["decision"]
            return report
        try:
            legal_evidence = zgrun.handle_phase2_optional_legal_consent(
                config.profile_dir, artifacts
            )
            report["legal_consent"] = legal_evidence
            report["ocr_used"] = legal_evidence.get("ocr_used") is True
            report["image_used"] = legal_evidence.get("image_used") is True
        except BaseException as error:
            legal_evidence = getattr(error, "evidence", None)
            if isinstance(legal_evidence, dict):
                report["legal_consent"] = legal_evidence
            raise SeedCaptureError(
                "phase-two seed legal-consent gate blocked: " + str(error),
                legal_evidence if isinstance(legal_evidence, dict) else {},
            ) from error

        def keep_english() -> None:
            serial = 0
            while not keyboard_stop.is_set():
                serial += 1
                try:
                    evidence = active_runtime.keyboard_layout_attestor(
                        int(binding["bridge_pid"]),
                        artifacts,
                        f"keyboard_watchdog_{serial:03d}",
                    )
                    row = {
                        "schema_version": 1,
                        "sequence": serial,
                        "state": "keyboard_layout_attestation",
                        "evidence": evidence,
                    }
                except BaseException as error:
                    row = {
                        "schema_version": 1,
                        "sequence": serial,
                        "state": "keyboard_layout_retry",
                        "error": f"{type(error).__name__}: {error}",
                        "traceback": traceback.format_exc(),
                    }
                with keyboard_lock:
                    keyboard_rows.append(row)
                append_jsonl(artifacts / "keyboard-watchdog.jsonl", row)
                keyboard_first_row.set()
                keyboard_stop.wait(config.keyboard_watchdog_interval_seconds)

        keyboard_thread = threading.Thread(
            target=keep_english,
            name="zg361-seed-us-english-hkl",
            daemon=False,
        )
        keyboard_thread.start()
        keyboard_started = True
        if not keyboard_first_row.wait(timeout=5.0):
            raise SeedCaptureError(
                "US English HKL watchdog did not publish its first attestation"
            )

        try:
            loader_stage = active_runtime.wait_for_loader_stage(
                config.profile_dir / "logs",
                artifacts / "01_phase2_loader_stage_progress.jsonl",
                timeout_seconds=config.loader_timeout_seconds,
                fatal_stall_seconds=LOADER_FATAL_STALL_SECONDS,
                native_session_probe=lambda: _phase2_native_session_probe(
                    supervisor
                ),
            )
        except active_runtime.loader_stage_error as error:
            evidence = getattr(error, "evidence", {})
            report["loader_stage"] = evidence
            raise
        report["loader_stage"] = loader_stage
        if loader_stage.get("result") != "GREEN":
            raise SeedCaptureError("loader stage returned without a GREEN terminal")

        mount_inventory = zgrun.verify_runtime_load_order(config.profile_dir, bootstrap)
        if len(mount_inventory) != 2 or len(set(mount_inventory)) != 2:
            raise SeedCaptureError(
                f"runtime did not mount product+fixture exactly once: {mount_inventory}"
            )
        report["runtime_mount_inventory"] = mount_inventory
        native_readiness = zgrun.native_loader_smoke_readiness(
            service,
            artifacts,
            tracked_ck3_pid=int(binding["bridge_pid"]),
            timeout_s=config.native_readiness_timeout_seconds,
        )
        report["native_readiness"] = native_readiness
        if native_readiness.get("result") != "GREEN":
            raise SeedCaptureError("native loader readiness returned non-GREEN")
        loader_error_scan = zgrun.scan_loader_error_log(
            config.profile_dir, artifacts
        )
        report["loader_error_log_scan"] = loader_error_scan
        if loader_error_scan.get("result") != "GREEN":
            raise SeedCaptureError("loader error.log scan returned non-GREEN")

        event_snapshot = wait_for_bootstrap_event(
            service,
            artifacts,
            bridge_unavailable_error=active_runtime.bridge_unavailable_error,
            pre_submission_revision_mismatch_error=(
                active_runtime.pre_submission_revision_mismatch_error
            ),
            timeout_seconds=config.event_timeout_seconds,
            source_save_sha256=observed_save_sha,
            clock=active_runtime.clock,
            sleeper=active_runtime.sleep,
            logger=runner_log,
        )
        write_json(artifacts / "bootstrap-event-snapshot.json", event_snapshot)
        report["bootstrap_event"] = {
            "result": "GREEN",
            "event_definition_key": SEED_EVENT_DEFINITION_KEY,
            "date_raw": event_snapshot.get("date_raw"),
            "revision": event_snapshot.get("revision"),
        }
        capture_dir = artifacts / "capture"
        candidate_dir = artifacts / "candidate"
        capture_result = seed.capture_mcp_evidence(service, capture_dir)
        report["capture"] = capture_result
        matrix = capture_result.get("domain_query_matrix")
        if not isinstance(matrix, dict):
            raise SeedCaptureError("seed capture did not return a domain query matrix")
        probes = provider_probe(service, matrix, artifacts)
        report["provider_probes"] = probes
        candidate = seed.materialize_candidate(
            event_context_path=Path(capture_result["event_context_path"]),
            paused_snapshot_path=Path(capture_result["paused_snapshot_path"]),
            event_close_path=Path(capture_result["event_close_path"]),
            checkpoint_response_path=Path(
                capture_result["checkpoint_response_path"]
            ),
            profile=config.profile_dir,
            output_dir=candidate_dir,
            base_contract_path=config.seed_contract,
            source_git_commit=config.frozen_git_sha,
            product_tree_sha256=initial_runtime_tree_sha256["product"],
            fixture_tree_sha256=initial_runtime_tree_sha256["fixture"],
            provider_probes_path=artifacts / "provider-probes.json",
        )
        report["candidate"] = candidate
        report["result"] = "GREEN"
        report["live_verdict"] = "paused_seed_ready"
        report["provider_baseline_verdict"] = (
            "ready_provider_matrix_captured"
            if candidate.get("provider_baseline_ready") is True
            else "blocked_provider_matrix_captured"
        )
    except BaseException as error:
        report["failure_reason"] = f"{type(error).__name__}: {error}"
        report["traceback"] = traceback.format_exc()
        if isinstance(error, SeedCaptureError):
            report["failure_evidence"] = error.evidence
        if active_runtime is not None and isinstance(
            error, active_runtime.loader_stage_error
        ):
            report["loader_stage"] = getattr(error, "evidence", {})
        append_jsonl(
            artifacts / "runner-failures.jsonl",
            {
                "schema_version": 1,
                "state": "seed_capture_failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "failure_evidence": report.get("failure_evidence"),
                "loader_stage": report.get("loader_stage"),
                "traceback": report["traceback"],
            },
        )
        runner_log(f"RED: {report['failure_reason']}")
    finally:
        keyboard_stop.set()
        if keyboard_thread is not None and keyboard_started:
            try:
                keyboard_thread.join(timeout=20.0)
            except BaseException as error:
                report["keyboard_join_error"] = f"{type(error).__name__}: {error}"
                _flip_red(report, str(report["keyboard_join_error"]))
        with keyboard_lock:
            keyboard_evidence = list(keyboard_rows)
        green_keyboard_rows = [
            row
            for row in keyboard_evidence
            if isinstance(row.get("evidence"), dict)
            and row["evidence"].get("result") == "GREEN"
        ]
        report["keyboard_watchdog"] = {
            "policy": "keep_us_english_hkl",
            "thread_stopped": (
                keyboard_thread is None
                or not keyboard_started
                or not keyboard_thread.is_alive()
            ),
            "attestation_count": len(keyboard_evidence),
            "green_attestation_count": len(green_keyboard_rows),
            "evidence": keyboard_evidence,
        }
        if (
            keyboard_thread is not None
            and keyboard_started
            and keyboard_thread.is_alive()
        ):
            _flip_red(report, "US English HKL watchdog did not stop")
        if supervisor is not None and active_runtime is not None:
            final_capabilities: dict[str, Any] = {}
            if service is not None:
                try:
                    candidate_capabilities = service.capabilities()
                    if isinstance(candidate_capabilities, dict):
                        final_capabilities = candidate_capabilities
                except BaseException as error:
                    report["final_capabilities_error"] = (
                        f"{type(error).__name__}: {error}"
                    )
            try:
                report["cleanup"] = (
                    active_runtime.zgrun.stop_phase2_native_session_supervisor(
                        supervisor,
                        artifacts,
                        initial_pid=(int(binding["bridge_pid"]) if binding else None),
                        initial_generation=(
                            int(binding["connection_generation"])
                            if binding
                            else None
                        ),
                        expected_pipe=config.pipe_name,
                        scenario_evidence={},
                        final_capabilities=final_capabilities,
                    )
                )
            except BaseException as error:
                report["cleanup_error"] = f"{type(error).__name__}: {error}"
                _flip_red(report, str(report["cleanup_error"]))
            session_state = supervisor.get("session_state")
            session_report = (
                session_state.get("report")
                if isinstance(session_state, dict)
                else None
            )
            if isinstance(session_report, dict):
                warmup = session_report.get("frontend_first_warmup")
                if isinstance(report.get("frontend_first_warmup"), dict):
                    report["frontend_first_warmup"]["session_report"] = warmup
        if driver is not None:
            try:
                driver.close()
                report["driver_closed"] = True
            except BaseException as error:
                report["driver_closed"] = False
                report["driver_close_error"] = f"{type(error).__name__}: {error}"
                _flip_red(report, str(report["driver_close_error"]))
        if active_runtime is not None:
            active_runtime.acceptance.ACTIVE_CK3_PID = None
        try:
            report["logs_copy"] = _copy_logs(config.profile_dir, artifacts)
        except BaseException as error:
            report["logs_copy_error"] = f"{type(error).__name__}: {error}"
            _flip_red(report, str(report["logs_copy_error"]))
        if (
            initial_runtime_trees is not None
            and bootstrap_targets is not None
            and active_runtime is not None
        ):
            try:
                final_trees = {
                    name: active_runtime.zgrun.isolated.tree_snapshot(path)
                    for name, path in bootstrap_targets.items()
                }
                report["runtime_unchanged"] = final_trees == initial_runtime_trees
                report["runtime_tree_after_sha256"] = {
                    name: active_runtime.zgrun.isolated.snapshot_digest(tree)
                    for name, tree in final_trees.items()
                }
                if report["runtime_unchanged"] is not True:
                    _flip_red(report, "CK3 rewrote a mounted runtime tree")
            except BaseException as error:
                report["runtime_immutability_error"] = (
                    f"{type(error).__name__}: {error}"
                )
                _flip_red(report, str(report["runtime_immutability_error"]))
        if source_manifest_before is not None:
            try:
                source_manifest_after = tree_manifest(config.clean_source)
                write_json(
                    artifacts / "source-tree-manifest.after.json",
                    source_manifest_after,
                )
                report["clean_source_unchanged"] = (
                    source_manifest_after["tree_sha256"]
                    == source_manifest_before["tree_sha256"]
                )
                report["clean_source_tree_after_sha256"] = source_manifest_after[
                    "tree_sha256"
                ]
                if report["clean_source_unchanged"] is not True:
                    _flip_red(report, "clean source tree changed during capture")
            except BaseException as error:
                report["clean_source_immutability_error"] = (
                    f"{type(error).__name__}: {error}"
                )
                _flip_red(report, str(report["clean_source_immutability_error"]))
        if dependency_hashes_before is not None:
            dependency_row = report.get("external_dependencies")
            if isinstance(dependency_row, dict):
                paths = dependency_row.get("paths")
                if isinstance(paths, dict):
                    try:
                        dependency_hashes_after = {
                            name: sha256_file(Path(path))
                            for name, path in paths.items()
                        }
                        dependency_row["sha256_after"] = dependency_hashes_after
                        dependency_row["unchanged"] = (
                            dependency_hashes_after == dependency_hashes_before
                        )
                        if dependency_row["unchanged"] is not True:
                            _flip_red(report, "external runtime dependency changed")
                    except BaseException as error:
                        dependency_row["after_hash_error"] = (
                            f"{type(error).__name__}: {error}"
                        )
                        _flip_red(report, str(dependency_row["after_hash_error"]))
        if report.get("result") == "GREEN":
            cleanup_row = report.get("cleanup")
            if not isinstance(cleanup_row, dict) or cleanup_row.get(
                "result"
            ) != "GREEN":
                _flip_red(report, "GREEN capture lacks native cleanup proof")
            if report.get("driver_closed") is not True:
                _flip_red(report, "GREEN capture lacks driver-close proof")
            if report.get("runtime_unchanged") is not True:
                _flip_red(report, "GREEN capture lacks runtime immutability proof")
            if report.get("clean_source_unchanged") is not True:
                _flip_red(report, "GREEN capture lacks clean-source immutability proof")
            dependency_row = report.get("external_dependencies")
            if not isinstance(dependency_row, dict) or dependency_row.get(
                "unchanged"
            ) is not True:
                _flip_red(report, "GREEN capture lacks dependency immutability proof")
            if not config.native_observer_only and len(green_keyboard_rows) < 1:
                _flip_red(report, "GREEN capture lacks a US English HKL attestation")
            logs_row = report.get("logs_copy")
            if not isinstance(logs_row, dict) or not logs_row.get("files"):
                _flip_red(report, "GREEN capture lacks copied CK3 logs")
        report["finished_at_utc"] = utc_now()
        write_json(artifacts / "runner-report.json", report)
    return report


def parse_args(argv: list[str] | None = None) -> CaptureConfig:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean-source", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    parser.add_argument("--artifacts-dir", type=Path, required=True)
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--git-sha", required=True)
    parser.add_argument(
        "--game-dir",
        type=Path,
        help=(
            "explicit CK3 install; when omitted, discover the actual Steam "
            "library install and retain its provenance"
        ),
    )
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--injector", type=Path, required=True)
    parser.add_argument(
        "--bridge-bundle-manifest",
        type=Path,
        help=(
            "optional Release bridge bundle-manifest.json; when supplied, "
            "build/source/feature provenance and artifact hashes are verified"
        ),
    )
    parser.add_argument("--pipe", required=True)
    parser.add_argument("--seed-contract", type=Path)
    parser.add_argument(
        "--product-projection",
        default="broad",
        help=(
            "product runtime projection to mount: broad (default), core "
            "(the byte-authoritative 51-file baseline), or a named group "
            "defined by --product-projection-manifest"
        ),
    )
    parser.add_argument(
        "--product-projection-manifest",
        type=Path,
        help=(
            "hash-bound product projection manifest/catalog; required for "
            "named groups other than broad/core"
        ),
    )
    parser.add_argument(
        "--product-source",
        type=Path,
        help=(
            "explicit product root for projection replay (for example an "
            "offline Phase2 bisect tree); defaults to clean-source/mod_zhongguo_style"
        ),
    )
    parser.add_argument(
        "--loader-timeout-seconds",
        type=float,
        default=DEFAULT_LOADER_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--native-readiness-timeout-seconds",
        type=float,
        default=DEFAULT_NATIVE_READINESS_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--event-timeout-seconds",
        type=float,
        default=DEFAULT_EVENT_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--binding-timeout-seconds",
        type=float,
        default=DEFAULT_BINDING_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--keyboard-watchdog-interval-seconds",
        type=float,
        default=DEFAULT_KEYBOARD_WATCHDOG_INTERVAL_SECONDS,
    )
    parser.add_argument(
        "--profile-settings-template",
        type=Path,
        help=(
            "full pdx_settings.txt template for a formal isolated profile; "
            "source is read-only and its sibling shadercache is required"
        ),
    )
    parser.add_argument(
        "--frontend-first-load-save-name",
        help=(
            "opt-in Phase2 startup: launch without a save argument, wait for "
            "Frontend, stop, then load this save basename on the same pipe"
        ),
    )
    parser.add_argument(
        "--frontend-first-timeout-seconds",
        type=float,
        default=180.0,
        help="bounded Frontend marker wait for --frontend-first-load-save-name",
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="validate frozen inputs and projections without launching CK3",
    )
    parser.add_argument(
        "--native-observer-only",
        action="store_true",
        help=(
            "after exact bridge binding, sample only the private Phase-2 "
            "wrapper/consumer heartbeat; do not inspect the desktop or send "
            "legal, UI, or gameplay input"
        ),
    )
    parser.add_argument(
        "--list-domain-observer-gate",
        action="store_true",
        help=(
            "require the frozen 0x817C20 list-domain observer handshake; "
            "without a native seam manifest this produces a typed no-launch RED"
        ),
    )
    parser.add_argument(
        "--acceptance-observer-manifest",
        type=Path,
        help="native-team seam manifest bound to this source and bridge build",
    )
    args = parser.parse_args(argv)
    selected_game_dir, game_dir_source, game_dir_candidates = resolve_ck3_game_dir(
        args.game_dir
    )
    return CaptureConfig(
        clean_source=args.clean_source,
        attempt_dir=args.attempt_dir,
        artifacts_dir=args.artifacts_dir,
        source_zip=args.source_zip,
        frozen_git_sha=args.git_sha,
        game_dir=selected_game_dir,
        bridge_dll=args.bridge_dll,
        bridge_injector=args.injector,
        pipe_name=args.pipe,
        bridge_bundle_manifest=args.bridge_bundle_manifest,
        product_projection=args.product_projection,
        product_projection_manifest=args.product_projection_manifest,
        product_source_override=args.product_source,
        game_dir_source=game_dir_source,
        game_dir_candidates=game_dir_candidates,
        seed_contract=args.seed_contract,
        loader_timeout_seconds=args.loader_timeout_seconds,
        native_readiness_timeout_seconds=(
            args.native_readiness_timeout_seconds
        ),
        event_timeout_seconds=args.event_timeout_seconds,
        binding_timeout_seconds=args.binding_timeout_seconds,
        keyboard_watchdog_interval_seconds=(
            args.keyboard_watchdog_interval_seconds
        ),
        list_domain_observer_gate=args.list_domain_observer_gate,
        acceptance_observer_manifest=args.acceptance_observer_manifest,
        preflight_only=args.preflight_only,
        native_observer_only=args.native_observer_only,
        profile_settings_template=args.profile_settings_template,
        frontend_first_load_save_name=args.frontend_first_load_save_name,
        frontend_first_timeout_seconds=args.frontend_first_timeout_seconds,
    )


def main(argv: list[str] | None = None) -> int:
    try:
        # Automatic game-directory discovery intentionally raises before a
        # CaptureConfig can be built when no Steam install is present.  Keep
        # that typed RED concise for CLI callers (argparse's own SystemExit
        # behaviour for --help/invalid syntax remains unchanged).
        config = parse_args(argv)
        report = run_preflight(config) if config.preflight_only else run_capture(config)
    except SeedCaptureError as error:
        print(f"seed capture preflight failed: {type(error).__name__}: {error}")
        return 2
    except BaseException as error:
        print(f"seed capture preflight failed: {type(error).__name__}: {error}")
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0 if report.get("result") == "GREEN" else 2


if __name__ == "__main__":
    raise SystemExit(main())

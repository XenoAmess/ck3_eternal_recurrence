#!/usr/bin/env python3
"""Materialize and query one deterministic generic current event window.

The immutable CK3 1.19.0.6 source save is never launched in place.  A
disposable seed clone mounts the production native bridge, the repository
``mod_bridge``, and one event-definition/localization fixture.  While paused,
``mod_bridge`` triggers the fixture character event for the local human.  The
seed process verifies its typed presentation and saves it without selecting an
option.

The checkpoint enters a fresh clone with the production native bridge and the
byte-identical fixture, but no ``mod_bridge`` or run inbox.  A distinct
supervised CK3 process cold-loads the event and performs exactly two adjacent
same-revision ``current-event-window-context-v1`` queries.  GREEN binds the
full event instance ID, canonical definition key, both signed definition
integers, materialized option order and presentation, exact EXE/DLL/fixture
bytes, immutable source bytes, and managed cleanup.

This is a generic nonreligious fixture-definition playset, not stock or
production-only event evidence.  It never selects an option.  Root/saved
scopes and full effect previews remain unavailable, and semantic decision
readiness remains false.  It is outside both owner-authorized narrow religion
exceptions (minimum holy-war OODA and minimum marriage legality/acceptance).
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
import uuid


RUNNER_RESEARCH_ROOT = Path(__file__).resolve().parent
RUNNER_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
ISOLATED_SOURCE_ROOT_ENV = "XAR_EVENT_WINDOW_ISOLATED_SOURCE_ROOT"
_isolated_source_value = os.environ.get(ISOLATED_SOURCE_ROOT_ENV)
ISOLATED_SOURCE_ROOT = (
    Path(_isolated_source_value).expanduser().resolve()
    if _isolated_source_value
    else None
)
RESEARCH_ROOT = (
    ISOLATED_SOURCE_ROOT
    / "ck3_autonomous_player"
    / "native_bridge"
    / "research"
    if ISOLATED_SOURCE_ROOT is not None
    else RUNNER_RESEARCH_ROOT
)
PACKAGE_ROOT = (
    ISOLATED_SOURCE_ROOT / "ck3_autonomous_player" / "src"
    if ISOLATED_SOURCE_ROOT is not None
    else Path(__file__).resolve().parents[2] / "src"
)
sys.path.insert(0, str(RESEARCH_ROOT))
sys.path.insert(0, str(PACKAGE_ROOT))

import run_loaded_feature_manifest_live_acceptance as manifest_live  # noqa: E402
import run_owner_subset_retreat_live_acceptance as owner_live  # noqa: E402
import run_pending_character_interaction_context_live_acceptance as pending_live  # noqa: E402,E501
from xar_autoplayer.bridge.event_window_context_contract import (  # noqa: E402
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY,
    QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    OUTER_DESCRIPTOR_REF,
    ensure_state_path_safe,
    is_relative_to,
    paths_overlap,
    write_json_atomic,
)
from xar_autoplayer.errors import AgentError  # noqa: E402
from xar_autoplayer.native_auto_run import (  # noqa: E402
    _cleanup_report,
    _compact_session_report,
    _wait_for_readiness,
)
from xar_autoplayer.runtime import (  # noqa: E402
    NativeBridgeLaunchConfig,
    ck3_processes,
    utc_now,
)


PURE_NATIVE_MODE = "native-headless"
EXPECTED_ADAPTER_ID = "ck3-1.19.0.6-msvc-x64"
EXPECTED_GAME_VERSION = "1.19.0.6"
EXPECTED_EXECUTABLE_SHA256 = (
    "2D00FF3101EF70B566F2FCBAE292F09263199C80E9DC8F139B82D7D96F83DB86"
)
FROZEN_SOURCE_COMMIT = "cea30a067b1e112596d70532b98fa068b2102ebf"
FROZEN_BRIDGE_DLL_SHA256 = (
    "52398435F8AA5177D6D507BFAA38CD2578EB988F0629F1C5E13360CC91FB3BB0"
)
FROZEN_BRIDGE_INJECTOR_SHA256 = (
    "1618840EC108F688B3EBECC6D7F8963038BA64C8D4A3E10DDE2E29E3F443B4DF"
)
EXPECTED_SOURCE_SAVE_SHA256 = pending_live.EXPECTED_SOURCE_SAVE_SHA256
DEFAULT_SOURCE_PROFILE = pending_live.DEFAULT_SOURCE_PROFILE
DEFAULT_SOURCE_SAVE = pending_live.DEFAULT_SOURCE_SAVE
CONTINUE_SAVE_NAME = owner_live.CONTINUE_SAVE_NAME
PLAYER_CHARACTER_ID = pending_live.SOURCE_CHARACTER_ID

EXPECTED_EVENT_KEY = "xar_event_window_live_fixture.1"
FIXTURE_NAMESPACE = "xar_event_window_live_fixture"
FIXTURE_MOD_TARGET_NAME = "xar-event-window-context-live-fixture"
FIXTURE_MOD_OUTER_NAME = "xar_event_window_context_live_fixture.mod"
FIXTURE_MOD_OUTER_REF = f"mod/{FIXTURE_MOD_OUTER_NAME}"
FIXTURE_EVENT_RELATIVE = Path(
    "events/zz_xar_event_window_context_live_fixture.txt"
)
FIXTURE_EVENT_SOURCE = """namespace = xar_event_window_live_fixture

xar_event_window_live_fixture.1 = {
	type = character_event
	title = XAR_EVENT_WINDOW_LIVE_FIXTURE_TITLE
	desc = XAR_EVENT_WINDOW_LIVE_FIXTURE_DESC
	theme = default
	left_portrait = root

	option = {
		name = XAR_EVENT_WINDOW_LIVE_FIXTURE_ENABLED
	}
	option = {
		name = XAR_EVENT_WINDOW_LIVE_FIXTURE_DISABLED
		trigger = { is_ai = yes }
		show_as_unavailable = { always = yes }
	}
	option = {
		name = XAR_EVENT_WINDOW_LIVE_FIXTURE_HIDDEN
		trigger = { always = no }
	}
	option = {
		name = XAR_EVENT_WINDOW_LIVE_FIXTURE_CANCEL
		is_cancel_option = yes
	}
	option = {
		name = XAR_EVENT_WINDOW_LIVE_FIXTURE_FALLBACK
		trigger = { always = no }
		fallback = yes
	}
}
"""
FIXTURE_EVENT_SHA256 = (
    "CE5416E0BB2D508F5A3445B73EAEEA7D1383727FC465D18486467B4CD58D972E"
)
FIXTURE_CONTENT_MANIFEST_SHA256 = (
    "D2B6AC3D39D6362BA905299912BBF91EACF2C90A58DA00D0423E10F237BF3C7A"
)

_LOCALES = {
    "english": "l_english",
    "french": "l_french",
    "german": "l_german",
    "japanese": "l_japanese",
    "korean": "l_korean",
    "polish": "l_polish",
    "russian": "l_russian",
    "simp_chinese": "l_simp_chinese",
    "spanish": "l_spanish",
}
EXPECTED_OPTION_NAMES = (
    "XAR enabled fixture option",
    "XAR disabled fixture option",
    "XAR cancel fixture option",
)
EXPECTED_EFFECT_INDICATOR_COVERAGE = (
    "played-character-event-icon-indicators-1.19.0.6-v1"
)
_LOCALIZATION_ROWS = (
    ("XAR_EVENT_WINDOW_LIVE_FIXTURE_TITLE", "XAR event-window fixture"),
    (
        "XAR_EVENT_WINDOW_LIVE_FIXTURE_DESC",
        "A deterministic generic event for paused native observation.",
    ),
    (
        "XAR_EVENT_WINDOW_LIVE_FIXTURE_ENABLED",
        EXPECTED_OPTION_NAMES[0],
    ),
    (
        "XAR_EVENT_WINDOW_LIVE_FIXTURE_DISABLED",
        EXPECTED_OPTION_NAMES[1],
    ),
    (
        "XAR_EVENT_WINDOW_LIVE_FIXTURE_HIDDEN",
        "XAR hidden fixture option",
    ),
    (
        "XAR_EVENT_WINDOW_LIVE_FIXTURE_CANCEL",
        EXPECTED_OPTION_NAMES[2],
    ),
    (
        "XAR_EVENT_WINDOW_LIVE_FIXTURE_FALLBACK",
        "XAR fallback fixture option",
    ),
)

GENERATE_GUARD = "xar_event_window_live_fixture_generated"
GENERATE_MARKER = (
    "XAR_FIXTURE:EVENT_WINDOW_CONTEXT_GENERATE|"
    f"event={EXPECTED_EVENT_KEY}"
)
SEED_NOOP_INBOX = "# XAR event-window fixture inbox: no effects.\n"

_ROOT_MARKER_NAME = ".xar-current-event-window-context-live.json"
_ROOT_KIND = "xar_current_event_window_context_live_acceptance"
_ROOT_PREFIX = "xew-"
_CK3_PHYSFS_PATH_LIMIT = 250
_SEED_STAGE_NAME = "seed-trigger-query-save-event"
_COLD_STAGE_NAME = "fresh-fixture-cold-double-query"
_FORBIDDEN_ACTION_PREFIXES = ("select-event-option-",)
_RELIGION_TOKENS = frozenset(
    {
        "faith",
        "doctrine",
        "tenet",
        "fervor",
        "conversion",
        "reformation",
        "holy_war",
        "great_holy_war",
    }
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-profile", type=Path, default=DEFAULT_SOURCE_PROFILE
    )
    parser.add_argument("--source-save", type=Path, default=DEFAULT_SOURCE_SAVE)
    parser.add_argument(
        "--expected-source-save-sha256",
        default=EXPECTED_SOURCE_SAVE_SHA256,
    )
    parser.add_argument("--state-dir", type=Path)
    parser.add_argument("--game-dir", type=Path, required=True)
    parser.add_argument("--bridge-pipe", required=True)
    parser.add_argument("--bridge-dll", type=Path, required=True)
    parser.add_argument("--expected-bridge-dll-sha256", required=True)
    parser.add_argument("--bridge-injector", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=900.0)
    parser.add_argument("--readiness-timeout", type=float, default=240.0)
    parser.add_argument("--seed-timeout", type=float, default=45.0)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--retain-state", action="store_true")
    return parser


def _mapping(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _sha256_file(path: Path) -> str:
    return pending_live._sha256_file(path)


def _canonical_sha256(value: object, name: str) -> str:
    return pending_live._canonical_sha256(value, name)


def _canonical_json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest().upper()


def _positive_seconds(value: object, name: str) -> float:
    return pending_live._positive_seconds(value, name)


def _target_root(requested: Path | None) -> Path:
    if requested is not None:
        return requested.expanduser().resolve()
    return Path(tempfile.gettempdir()).resolve() / (
        _ROOT_PREFIX + uuid.uuid4().hex
    )


def _dependency_source_contract() -> dict[str, object]:
    root = ISOLATED_SOURCE_ROOT
    checks: dict[str, bool] = {
        "isolated_root_explicit": root is not None,
        "outside_shared_workspace": root is not None
        and not paths_overlap(root, RUNNER_WORKSPACE_ROOT),
        "required_sources_present": False,
        "exact_commit": False,
    }
    commit: str | None = None
    files: dict[str, object] = {}
    error: str | None = None
    if root is not None:
        required = {
            "event_contract": root
            / "ck3_autonomous_player/src/xar_autoplayer/bridge"
            / "event_window_context_contract.py",
            "service": root
            / "ck3_autonomous_player/src/xar_autoplayer/bridge/service.py",
            "native_driver": root
            / "ck3_autonomous_player/src/xar_autoplayer/bridge/native_driver.py",
            "mod_bridge_descriptor": root
            / "ck3_autonomous_player/mod_bridge/descriptor.mod",
        }
        checks["required_sources_present"] = all(
            path.is_file() for path in required.values()
        )
        for key, path in required.items():
            if path.is_file():
                files[key] = {
                    "path": str(path.resolve()),
                    "size": path.stat().st_size,
                    "sha256": _sha256_file(path),
                }
        try:
            result = subprocess.run(
                ["git", "-C", str(root), "rev-parse", "HEAD"],
                check=True,
                capture_output=True,
                text=True,
                timeout=15.0,
            )
            commit = result.stdout.strip().lower()
            checks["exact_commit"] = commit == FROZEN_SOURCE_COMMIT
        except (OSError, subprocess.SubprocessError) as caught:
            error = f"{type(caught).__name__}: {caught}"
    return {
        "environment_variable": ISOLATED_SOURCE_ROOT_ENV,
        "runner_path": str(Path(__file__).resolve()),
        "runner_workspace_root": str(RUNNER_WORKSPACE_ROOT),
        "isolated_source_root": str(root) if root is not None else None,
        "commit": commit,
        "expected_commit": FROZEN_SOURCE_COMMIT,
        "files": files,
        "checks": checks,
        "ok": all(checks.values()),
        "error": error,
    }


def _bom(source: str) -> bytes:
    return b"\xef\xbb\xbf" + source.lstrip("\ufeff").encode("utf-8")


def _localization_source(header: str) -> str:
    rows = "".join(f' {key}:0 "{value}"\n' for key, value in _LOCALIZATION_ROWS)
    return f"{header}:\n{rows}"


def _fixture_content() -> dict[Path, bytes]:
    files = {FIXTURE_EVENT_RELATIVE: _bom(FIXTURE_EVENT_SOURCE)}
    for directory, header in _LOCALES.items():
        relative = Path(
            f"localization/{directory}/"
            f"xar_event_window_context_live_fixture_l_{directory}.yml"
        )
        files[relative] = _bom(_localization_source(header))
    return files


def _generated_fixture_path_length_contract(
    root: Path,
) -> dict[str, object]:
    root_path = PureWindowsPath(str(root.expanduser().resolve()))
    fixture_content = _fixture_content()
    rows: list[dict[str, object]] = []
    for stage in (_SEED_STAGE_NAME, _COLD_STAGE_NAME):
        profile_relative = PureWindowsPath(stage) / "profile"
        fixture_relative = (
            profile_relative / "mod-content" / FIXTURE_MOD_TARGET_NAME
        )
        generated = [
            fixture_relative / "descriptor.mod",
            *(
                fixture_relative / PureWindowsPath(relative.as_posix())
                for relative in fixture_content
            ),
            profile_relative / "mod" / FIXTURE_MOD_OUTER_NAME,
        ]
        for relative in generated:
            path = root_path / relative
            rows.append(
                {
                    "stage": stage,
                    "relative_path": str(relative),
                    "path": str(path),
                    "characters": len(str(path)),
                }
            )
    rows.sort(key=lambda row: (int(row["characters"]), str(row["path"])))
    maximum = max(int(row["characters"]) for row in rows)
    longest = [row for row in rows if row["characters"] == maximum]
    checks = {
        "ck3_physfs_limit_is_250": _CK3_PHYSFS_PATH_LIMIT == 250,
        "both_stage_fixture_paths_covered": {
            str(row["stage"]) for row in rows
        }
        == {_SEED_STAGE_NAME, _COLD_STAGE_NAME}
        and len(rows) == 2 * (len(fixture_content) + 2),
        "maximum_generated_path_within_limit": maximum
        < _CK3_PHYSFS_PATH_LIMIT,
    }
    return {
        "root": str(root_path),
        "root_characters": len(str(root_path)),
        "ck3_physfs_path_limit": _CK3_PHYSFS_PATH_LIMIT,
        "maximum_generated_path_characters": maximum,
        "longest_paths": longest,
        "paths": rows,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _content_manifest(files: dict[Path, bytes]) -> dict[str, object]:
    rows = [
        {
            "path": path.as_posix(),
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
        }
        for path, raw in sorted(files.items(), key=lambda row: row[0].as_posix())
    ]
    return {"files": rows, "sha256": _canonical_json_sha256(rows)}


def _fixture_definition_contract() -> dict[str, object]:
    files = _fixture_content()
    event_raw = files[FIXTURE_EVENT_RELATIVE]
    event_text = FIXTURE_EVENT_SOURCE
    folded = "\n".join(
        raw.decode("utf-8-sig") for raw in files.values()
    ).casefold()
    manifest = _content_manifest(files)
    checks = {
        "utf8_bom_every_file": all(raw.startswith(b"\xef\xbb\xbf") for raw in files.values()),
        "exact_event_sha256": hashlib.sha256(event_raw).hexdigest().upper()
        == FIXTURE_EVENT_SHA256,
        "exact_content_manifest_sha256": manifest["sha256"]
        == FIXTURE_CONTENT_MANIFEST_SHA256,
        "canonical_character_event": (
            event_text.startswith(f"namespace = {FIXTURE_NAMESPACE}\n")
            and f"{EXPECTED_EVENT_KEY} = {{" in event_text
            and "\ttype = character_event\n" in event_text
        ),
        "five_authored_options": event_text.count("\toption = {\n") == 5,
        "enabled_option": (
            "name = XAR_EVENT_WINDOW_LIVE_FIXTURE_ENABLED" in event_text
        ),
        "shown_disabled_option": (
            "name = XAR_EVENT_WINDOW_LIVE_FIXTURE_DISABLED\n"
            "\t\ttrigger = { is_ai = yes }\n"
            "\t\tshow_as_unavailable = { always = yes }" in event_text
        ),
        "hidden_option": (
            "name = XAR_EVENT_WINDOW_LIVE_FIXTURE_HIDDEN\n"
            "\t\ttrigger = { always = no }" in event_text
        ),
        "one_cancel_option": event_text.count("is_cancel_option = yes") == 1,
        "fallback_only_if_regular_empty": (
            event_text.count("fallback = yes") == 1
            and "name = XAR_EVENT_WINDOW_LIVE_FIXTURE_FALLBACK\n"
            "\t\ttrigger = { always = no }\n"
            "\t\tfallback = yes" in event_text
        ),
        "no_event_gameplay_effects": all(
            token not in event_text
            for token in (
                "\timmediate =",
                "\tafter =",
                "trigger_event =",
                "add_",
                "remove_",
                "set_",
            )
        ),
        "all_locales_have_exact_keys": all(
            raw.decode("utf-8-sig").count(":0 ") == len(_LOCALIZATION_ROWS)
            for path, raw in files.items()
            if path != FIXTURE_EVENT_RELATIVE
        ),
        "no_religion_semantics": all(
            token not in folded for token in _RELIGION_TOKENS
        ),
    }
    return {
        "classification": "generic-nonreligious-definition-and-localization-fixture",
        "canonical_key": EXPECTED_EVENT_KEY,
        "event_definition_relative_path": FIXTURE_EVENT_RELATIVE.as_posix(),
        "event_definition_size": len(event_raw),
        "event_definition_sha256": hashlib.sha256(event_raw).hexdigest().upper(),
        "expected_event_definition_sha256": FIXTURE_EVENT_SHA256,
        "content_manifest": manifest,
        "expected_content_manifest_sha256": FIXTURE_CONTENT_MANIFEST_SHA256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _fixture_descriptor(*, outer: bool, target: Path) -> str:
    path = f'path="{target.resolve().as_posix()}"\n' if outer else ""
    return (
        '\ufeffversion="0.1.0"\n'
        'tags={\n\t"Utilities"\n}\n'
        'name="XAR Event Window Context Live Fixture"\n'
        'supported_version="1.19.0.6"\n'
        f"{path}"
    )


def _install_fixture_definition(spec: Any) -> dict[str, object]:
    target = (
        spec.profile_dir / "mod-content" / FIXTURE_MOD_TARGET_NAME
    ).resolve()
    if target.exists():
        raise AgentError(f"fixture definition mod already exists: {target}")
    target.mkdir(parents=True, exist_ok=False)
    inner = target / "descriptor.mod"
    owner_live.write_text_atomic(
        inner, _fixture_descriptor(outer=False, target=target), encoding="utf-8"
    )
    identities: dict[str, object] = {}
    for relative, raw in _fixture_content().items():
        path = target / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        identity = owner_live._write_seed_inbox(
            path, raw.decode("utf-8-sig")
        )
        identities[relative.as_posix()] = identity
    outer = spec.profile_dir / "mod" / FIXTURE_MOD_OUTER_NAME
    owner_live.write_text_atomic(
        outer, _fixture_descriptor(outer=True, target=target), encoding="utf-8"
    )
    load_path = spec.profile_dir / "dlc_load.json"
    payload = json.loads(load_path.read_text(encoding="utf-8-sig"))
    enabled = payload.get("enabled_mods")
    if not isinstance(enabled, list) or FIXTURE_MOD_OUTER_REF in enabled:
        raise AgentError("fixture definition playset cannot be extended safely")
    enabled.append(FIXTURE_MOD_OUTER_REF)
    owner_live.write_json_atomic(load_path, payload)
    return {
        "mod_root": str(target),
        "outer_descriptor": str(outer.resolve()),
        "inner_descriptor": str(inner.resolve()),
        "content": identities,
        "content_manifest": _content_manifest(_fixture_content()),
        "enabled_mods": list(enabled),
    }


def _fixture_projection_proof(
    spec: Any, *, seed_stage: bool
) -> dict[str, object]:
    load_path = spec.profile_dir / "dlc_load.json"
    fixture_root = (
        spec.profile_dir / "mod-content" / FIXTURE_MOD_TARGET_NAME
    ).resolve()
    mod_bridge_root = (
        spec.profile_dir / "mod-content" / owner_live.MOD_BRIDGE_TARGET_NAME
    ).resolve()
    mod_bridge_outer = (
        spec.profile_dir / "mod" / owner_live.MOD_BRIDGE_OUTER_NAME
    ).resolve()
    expected_enabled = [OUTER_DESCRIPTOR_REF]
    if seed_stage:
        expected_enabled.append(f"mod/{owner_live.MOD_BRIDGE_OUTER_NAME}")
    expected_enabled.append(FIXTURE_MOD_OUTER_REF)
    expected_content = _fixture_content()
    try:
        payload = json.loads(load_path.read_text(encoding="utf-8-sig"))
        actual_content = {
            relative: (fixture_root / relative).read_bytes()
            for relative in expected_content
        }
        inner_raw = (fixture_root / "descriptor.mod").read_text(
            encoding="utf-8-sig"
        )
        outer_raw = (
            spec.profile_dir / "mod" / FIXTURE_MOD_OUTER_NAME
        ).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        return {
            "checks": {},
            "ok": False,
            "error": f"{type(error).__name__}: {error}",
        }
    files = sorted(
        path.relative_to(fixture_root).as_posix()
        for path in fixture_root.rglob("*")
        if path.is_file()
    )
    expected_files = sorted(
        ["descriptor.mod", *(path.as_posix() for path in expected_content)]
    )
    manifest = _content_manifest(actual_content)
    checks = {
        "inside_disposable_profile": is_relative_to(
            fixture_root, spec.profile_dir.resolve()
        ),
        "exact_fixture_playset": payload
        == {"enabled_mods": expected_enabled, "disabled_dlcs": []},
        "production_native_tree_present": spec.production_dir.is_dir(),
        "fixture_files_exact": files == expected_files,
        "fixture_content_bytes_exact": actual_content == expected_content,
        "fixture_manifest_exact": manifest["sha256"]
        == FIXTURE_CONTENT_MANIFEST_SHA256,
        "inner_descriptor_exact": inner_raw.lstrip("\ufeff")
        == _fixture_descriptor(outer=False, target=fixture_root).lstrip("\ufeff"),
        "outer_descriptor_exact": outer_raw.lstrip("\ufeff")
        == _fixture_descriptor(outer=True, target=fixture_root).lstrip("\ufeff"),
        "mod_bridge_presence_matches_stage": (
            mod_bridge_root.is_dir()
            and mod_bridge_outer.is_file()
            and owner_live._seed_inbox_path(spec).is_file()
            if seed_stage
            else not mod_bridge_root.exists()
            and not mod_bridge_outer.exists()
            and not owner_live._seed_inbox_path(spec).exists()
        ),
    }
    return {
        "stage_kind": "seed" if seed_stage else "cold-double-query",
        "dlc_load": payload,
        "expected_enabled_mods": expected_enabled,
        "fixture_root": str(fixture_root),
        "files": files,
        "content_manifest": manifest,
        "mod_bridge_root": str(mod_bridge_root),
        "checks": checks,
        "ok": all(checks.values()),
        "error": None,
    }


def _fixture_definition_native_session(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    timeout: float,
    stop_event: threading.Event,
    seed_stage: bool,
) -> dict[str, object]:
    """Use the existing supervised fixture seam after exact projection."""
    projection = _fixture_projection_proof(spec, seed_stage=seed_stage)
    if projection.get("ok") is not True:
        stage = "seed" if seed_stage else "cold-double-query"
        raise AgentError(f"{stage} exact fixture projection differs")
    report = owner_live._fixture_native_session(
        spec=spec,
        config=config,
        timeout=timeout,
        stop_event=stop_event,
    )
    result = copy.deepcopy(report)
    result["kind"] = "ck3_current_event_window_context_fixture_session"
    result["fixture_stage"] = (
        "seed" if seed_stage else "cold-double-query"
    )
    result["exact_fixture_projection"] = projection
    return result


def _generate_effect() -> str:
    return (
        "if = {\n"
        "\tlimit = {\n"
        "\t\tis_ai = no\n"
        f"\t\tNOT = {{ global_var:{GENERATE_GUARD} = 1 }}\n"
        "\t}\n"
        "\tset_global_variable = {\n"
        f"\t\tname = {GENERATE_GUARD}\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        f'\tdebug_log = "{GENERATE_MARKER}"\n'
        f"\ttrigger_event = {{ id = {EXPECTED_EVENT_KEY} }}\n"
        "}\n"
    )


def _effect_contract() -> dict[str, object]:
    source = _generate_effect()
    folded = source.casefold()
    checks = {
        "human_local_scope_gate": "\t\tis_ai = no\n" in source,
        "single_use_guard": (
            f"NOT = {{ global_var:{GENERATE_GUARD} = 1 }}" in source
            and f"name = {GENERATE_GUARD}" in source
        ),
        "exact_generic_event_trigger": source.count("trigger_event =") == 1
        and f"trigger_event = {{ id = {EXPECTED_EVENT_KEY} }}" in source,
        "diagnostic_marker": source.count(GENERATE_MARKER) == 1,
        "no_option_selection": not any(
            prefix in source for prefix in _FORBIDDEN_ACTION_PREFIXES
        ),
        "no_religion_semantics": all(
            token not in folded for token in _RELIGION_TOKENS
        ),
    }
    return {"source": source, "checks": checks, "ok": all(checks.values())}


def _played_character_id(snapshot: object) -> int | None:
    return owner_live._played_character_id(snapshot)


def _snapshot_revision(snapshot: dict[str, object]) -> int:
    return pending_live._snapshot_revision(snapshot)


def _snapshot_native_revision(snapshot: dict[str, object]) -> int:
    return pending_live._snapshot_native_revision(snapshot)


def _snapshot_date(snapshot: dict[str, object]) -> int:
    return pending_live._snapshot_date(snapshot)


def _assert_paused_map_ready(snapshot: dict[str, object]) -> None:
    if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
        raise RuntimeError("event-window fixture requires paused map-ready state")


def _active_event_id(snapshot: object) -> int | None:
    if not isinstance(snapshot, dict):
        return None
    event = snapshot.get("active_event")
    if not isinstance(event, dict):
        return None
    value = event.get("instance_id")
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or not 1 <= value <= 2**31 - 1
    ):
        return None
    return value


def _compact_snapshot(snapshot: object) -> object:
    if not isinstance(snapshot, dict):
        return snapshot
    return {
        key: copy.deepcopy(snapshot.get(key))
        for key in (
            "snapshot_id",
            "revision",
            "native_revision",
            "date_raw",
            "paused",
            "map_ready",
            "episode_run_id",
            "backend_id",
            "active_event",
        )
    } | {"played_character_id": _played_character_id(snapshot)}


def _same_paused_event_binding(
    before: dict[str, object], after: dict[str, object]
) -> bool:
    return bool(
        before.get("paused") is True
        and after.get("paused") is True
        and before.get("map_ready") is True
        and after.get("map_ready") is True
        and all(
            before.get(key) == after.get(key)
            for key in (
                "snapshot_id",
                "revision",
                "native_revision",
                "date_raw",
                "episode_run_id",
            )
        )
        and _played_character_id(before) == _played_character_id(after)
        and _active_event_id(before) == _active_event_id(after)
    )


def _wait_for_event(
    service: GameplayBridgeService,
    *,
    debug_log: Path,
    log_offset: int,
    expected_date_raw: int,
    deadline: float,
    session_done: threading.Event,
    session_state: dict[str, object],
) -> tuple[dict[str, object], bool]:
    marker_observed = False
    while time.monotonic() < deadline:
        marker_observed = owner_live._debug_marker_observed(
            debug_log, GENERATE_MARKER, offset=log_offset
        )
        candidate = service.snapshot()
        if (
            marker_observed
            and _played_character_id(candidate) == PLAYER_CHARACTER_ID
            and candidate.get("date_raw") == expected_date_raw
            and candidate.get("paused") is True
            and candidate.get("map_ready") is True
            and _active_event_id(candidate) is not None
        ):
            return candidate, True
        if session_done.is_set():
            raise AgentError(
                str(
                    session_state.get("error")
                    or "seed session ended before fixture event appeared"
                )
            )
        time.sleep(0.05)
    raise AgentError("seed fixture did not materialize a current event window")


def _diagnostics(capabilities: object) -> dict[str, object]:
    return manifest_live._diagnostics(capabilities)


def _capability_proof(
    capabilities: object, *, event_present: bool
) -> dict[str, object]:
    raw = _mapping(capabilities)
    advertised_value = raw.get("bridge_capabilities")
    advertised = advertised_value if isinstance(advertised_value, list) else []
    hello = _mapping(_diagnostics(raw).get("hello"))
    hello_caps_value = hello.get("capabilities")
    hello_caps = hello_caps_value if isinstance(hello_caps_value, list) else []
    action_value = raw.get("action_steps")
    actions = action_value if isinstance(action_value, list) else []
    checks = {
        "bridge_capability": (
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY in advertised
        ),
        "hello_capability": (
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY in hello_caps
        ),
        "driver_query_surface": raw.get(
            "current_event_window_context_v1_query_supported"
        )
        is True,
        "query_action_identity_gate": (
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP in actions
        )
        is event_present,
    }
    return {
        "event_present": event_present,
        "required_bridge_capability": (
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_CAPABILITY
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _exact_binary_proof(
    capabilities: object,
    *,
    executable_sha256: str,
    dll_sha256: str,
    expected_dll_sha256: str,
) -> dict[str, object]:
    result = manifest_live._exact_binary_proof(
        capabilities,
        managed_executable_sha256=executable_sha256,
        production_dll_sha256=dll_sha256,
        expected_production_dll_sha256=expected_dll_sha256,
    )
    checks = _mapping(result.get("checks"))
    checks["event_contract_game_version"] = (
        result.get("expected_game_version") == EXPECTED_GAME_VERSION
    )
    checks["event_contract_executable_sha256"] = (
        result.get("expected_executable_sha256")
        == EXPECTED_EXECUTABLE_SHA256
    )
    checks["event_contract_adapter"] = (
        result.get("expected_adapter_id") == EXPECTED_ADAPTER_ID
    )
    result["checks"] = checks
    result["ok"] = all(checks.values())
    return result


def _same_process_proof(before: object, after: object) -> dict[str, object]:
    return manifest_live._same_process_proof(before, after)


def _signed_int32(value: object) -> bool:
    return bool(
        isinstance(value, int)
        and not isinstance(value, bool)
        and -(2**31) <= value <= 2**31 - 1
    )


def _expected_option_shape(options: object) -> bool:
    if not isinstance(options, list) or len(options) != 3:
        return False
    expected = (
        (0, 0, True, False, False, EXPECTED_OPTION_NAMES[0]),
        (1, 1, False, False, False, EXPECTED_OPTION_NAMES[1]),
        (2, 3, True, False, True, EXPECTED_OPTION_NAMES[2]),
    )
    for row, values in zip(options, expected, strict=True):
        if not isinstance(row, dict):
            return False
        rendered, native, enabled, fallback, cancel, name = values
        if not (
            row.get("rendered_index") == rendered
            and row.get("native_option_index") == native
            and row.get("shown") is True
            and row.get("enabled") is enabled
            and row.get("fallback") is fallback
            and row.get("cancel") is cancel
            and row.get("resolved_name") == name
            and isinstance(row.get("unavailable_reason"), str)
            and row.get("effect_indicators")
            == {
                "status": "available",
                "coverage": EXPECTED_EFFECT_INDICATOR_COVERAGE,
                "complete_effect_set": False,
                "rows": [],
            }
            and row.get("effect_preview")
            == {
                "status": "unavailable",
                "reason": "indicator_subset_has_no_completeness_signal",
            }
            and row.get("resource_deltas") == {"status": "unavailable"}
            and row.get("relationship_deltas") == {"status": "unavailable"}
        ):
            return False
    return bool(
        options[0]["unavailable_reason"] == ""
        and options[1]["unavailable_reason"] != ""
        and options[2]["unavailable_reason"] == ""
    )


def _context_proof(
    result: object,
    *,
    event_id: int,
    snapshot_id: str,
    public_revision: int,
    native_revision: int,
    date_raw: int,
) -> dict[str, object]:
    envelope = _mapping(result)
    frame = _mapping(envelope.get("current_event_window_context"))
    binding = _mapping(envelope.get("binding"))
    source = _mapping(envelope.get("source"))
    readiness = _mapping(frame.get("readiness"))
    options = frame.get("options")
    mirror_keys = (
        "schema",
        "schema_version",
        "date_raw",
        "current_event_instance_id",
        "window_match_count",
        "unavailable_reason",
        "event_definition_key",
        "calculated_event_id",
        "runtime_stats_ordinal",
        "root_scope",
        "saved_scopes",
        "options",
        "readiness",
        "provenance",
    )
    checks = {
        "typed_available": envelope.get("status") == "available"
        and frame.get("status") == "available"
        and frame.get("unavailable_reason") is None,
        "exact_scope": envelope.get("step")
        == QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP
        and envelope.get("accepted") is True
        and envelope.get("scope") == "exact-current-event-window",
        "full_instance_binding": frame.get("current_event_instance_id")
        == event_id
        and binding.get("event_instance_id") == event_id,
        "same_snapshot_binding": frame.get("snapshot_revision")
        == native_revision
        and envelope.get("snapshot_revision") == native_revision
        and envelope.get("queried_native_revision") == native_revision
        and binding.get("native_revision") == native_revision
        and envelope.get("queried_revision") == public_revision
        and binding.get("revision") == public_revision
        and binding.get("expected_revision") == public_revision
        and frame.get("date_raw") == date_raw
        and binding.get("date_raw") == date_raw
        and envelope.get("queried_snapshot_id") == snapshot_id
        and binding.get("snapshot_id") == snapshot_id
        and source.get("snapshot_id") == snapshot_id
        and source.get("revision") == public_revision
        and source.get("native_revision") == native_revision
        and source.get("date_raw") == date_raw
        and source.get("paused") is True,
        "one_exact_window": frame.get("window_match_count") == 1,
        "canonical_definition_key": frame.get("event_definition_key")
        == EXPECTED_EVENT_KEY,
        "calculated_event_id_is_signed_int32": _signed_int32(
            frame.get("calculated_event_id")
        ),
        "runtime_stats_ordinal_is_signed_int32": _signed_int32(
            frame.get("runtime_stats_ordinal")
        ),
        "materialized_option_shape": _expected_option_shape(options),
        "hidden_native_index_absent": isinstance(options, list)
        and all(row.get("native_option_index") != 2 for row in options),
        "fallback_native_index_absent": isinstance(options, list)
        and all(row.get("native_option_index") != 4 for row in options),
        "root_and_saved_scopes_unavailable": frame.get("root_scope") is None
        and frame.get("saved_scopes") is None,
        "readiness_truthful": readiness
        == {
            "event_definition_identity_ready": True,
            "option_presentation_ready": True,
            "effect_indicators_ready": True,
            "effect_preview_ready": False,
            "semantic_decision_ready": False,
        }
        and envelope.get("current_event_window_context_ready") is True
        and envelope.get("current_event_effect_indicators_ready") is True,
        "exact_provenance": frame.get("provenance")
        == {
            "root": "module+0x570F7B8->+0x10",
            "idler_vtable_rva": "0x40B1D30",
            "manager_offset": "+0x28",
            "backend_id": "ck3-1.19.0.6-native-event-window-v1",
        },
        "strict_mirrors": all(
            envelope.get(key) == frame.get(key) for key in mirror_keys
        ),
    }
    return {
        "event_instance_id": event_id,
        "event_definition_key": frame.get("event_definition_key"),
        "calculated_event_id": frame.get("calculated_event_id"),
        "runtime_stats_ordinal": frame.get("runtime_stats_ordinal"),
        "options": copy.deepcopy(options),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _without_query_sequence(result: object) -> object:
    normalized = copy.deepcopy(result)
    if isinstance(normalized, dict):
        normalized.pop("query_sequence", None)
    return normalized


def _mutation_boundary_proof(
    commands: object, *, seed_stage: bool
) -> dict[str, object]:
    rows = commands if isinstance(commands, list) else []
    expected = (
        [QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP, "save-checkpoint"]
        if seed_stage
        else [
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
            QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP,
        ]
    )
    forbidden = [
        step
        for step in rows
        if isinstance(step, str)
        and any(step.startswith(prefix) for prefix in _FORBIDDEN_ACTION_PREFIXES)
    ]
    checks = {
        "exact_commands": rows == expected,
        "no_event_option_selection": forbidden == [],
        "no_auto_turn": "auto-turn" not in rows,
        "cold_is_read_only": seed_stage
        or all(step.startswith("query-") for step in rows),
    }
    return {
        "seed_stage": seed_stage,
        "commands": list(rows),
        "expected_commands": expected,
        "forbidden_event_actions_observed": forbidden,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_double_query_sequence(
    service: GameplayBridgeService,
    *,
    expected_event_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    commands: list[str] = []
    before = service.snapshot()
    _assert_paused_map_ready(before)
    if _played_character_id(before) != PLAYER_CHARACTER_ID:
        raise RuntimeError("cold query did not bind the fixture player")
    if _active_event_id(before) != expected_event_id:
        raise RuntimeError("cold query did not restore the full event ID")
    revision = _snapshot_revision(before)
    native_revision = _snapshot_native_revision(before)
    date_raw = _snapshot_date(before)
    snapshot_id = before.get("snapshot_id")
    if not isinstance(snapshot_id, str) or not snapshot_id:
        raise RuntimeError("cold query lacks a stable snapshot ID")
    if date_raw != expected_date_raw:
        raise RuntimeError("cold query changed the fixture date")

    first = service.query_current_event_window_context_v1(
        expected_event_id, expected_revision=revision
    )
    commands.append(QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP)
    between = service.snapshot()
    second = service.query_current_event_window_context_v1(
        expected_event_id, expected_revision=revision
    )
    commands.append(QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP)
    after = service.snapshot()

    first_proof = _context_proof(
        first,
        event_id=expected_event_id,
        snapshot_id=snapshot_id,
        public_revision=revision,
        native_revision=native_revision,
        date_raw=date_raw,
    )
    second_proof = _context_proof(
        second,
        event_id=expected_event_id,
        snapshot_id=snapshot_id,
        public_revision=revision,
        native_revision=native_revision,
        date_raw=date_raw,
    )
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    first_frame = first.get("current_event_window_context")
    second_frame = second.get("current_event_window_context")
    mutation = _mutation_boundary_proof(commands, seed_stage=False)
    checks = {
        "initial_paused_map_ready": before.get("paused") is True
        and before.get("map_ready") is True,
        "between_same_paused_binding": _same_paused_event_binding(
            before, between
        ),
        "after_same_paused_binding": _same_paused_event_binding(before, after),
        "first_context_valid": first_proof.get("ok") is True,
        "second_context_valid": second_proof.get("ok") is True,
        "query_sequence_exact_successor": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and first_sequence > 0
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence == first_sequence + 1,
        "adjacent_context_frames_strictly_equal": isinstance(first_frame, dict)
        and first_frame == second_frame,
        "only_query_sequence_changed": _without_query_sequence(first)
        == _without_query_sequence(second),
        "exact_two_read_only_commands": mutation.get("ok") is True,
    }
    return {
        "expected_revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "current_event_instance_id": expected_event_id,
        "before": _compact_snapshot(before),
        "between": _compact_snapshot(between),
        "after": _compact_snapshot(after),
        "first_query": copy.deepcopy(first),
        "second_query": copy.deepcopy(second),
        "first_context_proof": first_proof,
        "second_context_proof": second_proof,
        "context_sha256": _canonical_json_sha256(first_frame),
        "mutation_boundary": mutation,
        "commands": commands,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _prepare_root(
    root: Path,
    *,
    source_profile: Path,
    source_save_sha256: str,
    nonce: str,
) -> dict[str, object]:
    target = root.resolve()
    source = source_profile.resolve()
    if target.exists():
        raise AgentError(f"disposable root already exists: {target}")
    ensure_state_path_safe(target)
    if paths_overlap(source, target):
        raise AgentError("immutable source and disposable root overlap")
    target.mkdir(parents=True, exist_ok=False)
    marker = target / _ROOT_MARKER_NAME
    write_json_atomic(
        marker,
        {
            "kind": _ROOT_KIND,
            "nonce": nonce,
            "source_profile": str(source),
            "source_save_sha256": source_save_sha256,
        },
    )
    return {
        "path": str(target),
        "marker": str(marker),
        "nonce": nonce,
    }


def _cleanup_root(
    root: Path,
    *,
    nonce: str,
    retain: bool,
    stages: list[object],
) -> dict[str, object]:
    target = root.resolve()
    if retain:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "--retain-state prevents cleanup qualification",
        }
    unclean: list[object] = []
    for value in stages:
        stage = _mapping(value)
        cleanup = _mapping(stage.get("cleanup"))
        if stage.get("session_started") is True and cleanup.get("ok") is not True:
            unclean.append(stage.get("stage"))
    if unclean:
        return {
            "attempted": False,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": "managed cleanup unproven for: "
            + ", ".join(str(value) for value in unclean),
        }
    marker = target / _ROOT_MARKER_NAME
    try:
        payload = json.loads(marker.read_text(encoding="utf-8"))
        if not (
            payload.get("kind") == _ROOT_KIND
            and payload.get("nonce") == nonce
        ):
            raise AgentError("disposable root marker differs")
        ensure_state_path_safe(target)
        shutil.rmtree(target)
        removed = not target.exists()
        return {
            "attempted": True,
            "removed": removed,
            "path": str(target),
            "ok": removed,
            "reason": None if removed else "disposable root still exists",
        }
    except BaseException as error:
        return {
            "attempted": True,
            "removed": False,
            "path": str(target),
            "ok": False,
            "reason": f"{type(error).__name__}: {error}",
        }


def _capture_log_evidence(spec: Any) -> dict[str, object]:
    evidence: dict[str, object] = {}
    for name in ("debug.log", "error.log"):
        path = spec.profile_dir / "logs" / name
        if not path.is_file():
            evidence[name] = {
                "path": str(path.resolve()),
                "present": False,
                "size": None,
                "sha256": None,
                "selected_lines": [],
            }
            continue
        raw = path.read_bytes()
        decoded = raw.decode("utf-8", errors="replace")
        selected = [
            line
            for line in decoded.splitlines()
            if GENERATE_MARKER in line
            or EXPECTED_EVENT_KEY.casefold() in line.casefold()
            or "duplicate" in line.casefold()
        ]
        evidence[name] = {
            "path": str(path.resolve()),
            "present": True,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "selected_lines": selected[-200:],
        }
    rows = _mapping(evidence.get("debug.log")).get("selected_lines")
    lines = rows if isinstance(rows, list) else []
    evidence["marker_observed"] = any(
        isinstance(line, str) and GENERATE_MARKER in line for line in lines
    )
    return evidence


def _checkpoint_transfer_proof(
    seed_checkpoint: Path, cold_spec: Any
) -> dict[str, object]:
    return pending_live._checkpoint_transfer_proof(seed_checkpoint, cold_spec)


def _run_seed_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    expected_dll_sha256: str,
    timeout: float,
    readiness_timeout: float,
    seed_timeout: float,
) -> dict[str, object]:
    started = time.monotonic()
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    primary_error: str | None = None
    readiness: dict[str, object] | None = None
    initial: dict[str, object] | None = None
    materialized: dict[str, object] | None = None
    stable: dict[str, object] | None = None
    after_save: dict[str, object] | None = None
    seed_query: dict[str, object] | None = None
    seed_query_proof: dict[str, object] | None = None
    save_result: dict[str, object] | None = None
    checkpoint: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    capability_before: dict[str, object] | None = None
    capability_after: dict[str, object] | None = None
    exact_binary: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    generation_write: dict[str, object] | None = None
    final_noop: dict[str, object] | None = None
    marker_observed = False
    log_evidence: dict[str, object] | None = None
    executable_sha256: str | None = None
    dll_sha256: str | None = None
    injector_sha256: str | None = None
    commands: list[str] = []
    projection = _fixture_projection_proof(spec, seed_stage=True)

    def supervise() -> None:
        try:
            session_state["report"] = _fixture_definition_native_session(
                spec=spec,
                config=config,
                timeout=timeout + 90.0,
                stop_event=stop_event,
                seed_stage=True,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        if projection.get("ok") is not True:
            raise AgentError("seed clone lacks the exact fixture playset")
        executable_sha256 = _sha256_file(spec.game_exe)
        dll_sha256 = _sha256_file(config.dll_path)
        injector_sha256 = _sha256_file(config.injector_path)
        if executable_sha256 != EXPECTED_EXECUTABLE_SHA256:
            raise RuntimeError("managed CK3 executable SHA-256 differs")
        if dll_sha256 != expected_dll_sha256:
            raise RuntimeError("production bridge DLL SHA-256 differs")
        if injector_sha256 != FROZEN_BRIDGE_INJECTOR_SHA256:
            raise RuntimeError("frozen bridge injector SHA-256 differs")
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-event-window-seed-session",
            daemon=False,
        )
        thread.start()
        session_started = True
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        initial = service.snapshot()
        _assert_paused_map_ready(initial)
        if _played_character_id(initial) != PLAYER_CHARACTER_ID:
            raise AgentError("immutable fixture player identity differs")
        if _active_event_id(initial) is not None:
            raise AgentError("immutable source unexpectedly has an active event")

        capabilities_before = driver.capabilities()
        exact_binary = _exact_binary_proof(
            capabilities_before,
            executable_sha256=executable_sha256,
            dll_sha256=dll_sha256,
            expected_dll_sha256=expected_dll_sha256,
        )
        capability_before = _capability_proof(
            capabilities_before, event_present=False
        )
        if exact_binary.get("ok") is not True:
            raise RuntimeError("seed exact EXE/DLL proof failed")
        if capability_before.get("ok") is not True:
            raise RuntimeError("seed event-window capability proof failed")

        initial_date = _snapshot_date(initial)
        debug_log = spec.profile_dir / "logs" / "debug.log"
        log_offset = owner_live._debug_log_offset(debug_log)
        generation_write = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), _generate_effect()
        )
        materialized, marker_observed = _wait_for_event(
            service,
            debug_log=debug_log,
            log_offset=log_offset,
            expected_date_raw=initial_date,
            deadline=time.monotonic() + seed_timeout,
            session_done=session_done,
            session_state=session_state,
        )
        event_id = _active_event_id(materialized)
        if event_id is None:
            raise AgentError("materialized event lacks a positive full ID")
        final_noop = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), SEED_NOOP_INBOX
        )

        revision = _snapshot_revision(materialized)
        native_revision = _snapshot_native_revision(materialized)
        snapshot_id = materialized.get("snapshot_id")
        if not isinstance(snapshot_id, str) or not snapshot_id:
            raise AgentError("materialized event lacks a stable snapshot ID")
        seed_query = service.query_current_event_window_context_v1(
            event_id, expected_revision=revision
        )
        commands.append(QUERY_CURRENT_EVENT_WINDOW_CONTEXT_V1_STEP)
        seed_query_proof = _context_proof(
            seed_query,
            event_id=event_id,
            snapshot_id=snapshot_id,
            public_revision=revision,
            native_revision=native_revision,
            date_raw=initial_date,
        )
        if seed_query_proof.get("ok") is not True:
            raise AgentError("seed event-window context differs from fixture")
        stable = service.snapshot()
        if not _same_paused_event_binding(materialized, stable):
            raise AgentError("fixture event binding drifted before checkpoint")

        save_result = service.save_checkpoint(
            expected_revision=_snapshot_revision(stable)
        )
        commands.append("save-checkpoint")
        checkpoint_path = owner_live._checkpoint_path(spec)
        checkpoint = owner_live._checkpoint_identity(checkpoint_path)
        after_save = service.snapshot()
        if (
            _played_character_id(after_save) != PLAYER_CHARACTER_ID
            or _snapshot_date(after_save) != initial_date
            or _active_event_id(after_save) != event_id
        ):
            raise AgentError("checkpoint save changed the active event")

        capabilities_after = driver.capabilities()
        capability_after = _capability_proof(
            capabilities_after, event_present=True
        )
        same_process = _same_process_proof(
            capabilities_before, capabilities_after
        )
        if capability_after.get("ok") is not True:
            raise RuntimeError("seed active event did not publish query action")
        if same_process.get("ok") is not True:
            raise RuntimeError("seed fixture crossed bridge process")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        try:
            final_noop = owner_live._write_seed_inbox(
                owner_live._seed_inbox_path(spec), SEED_NOOP_INBOX
            )
        except BaseException as error:
            detail = f"{type(error).__name__}: {error}"
            primary_error = (
                detail
                if primary_error is None
                else f"{primary_error}; final inbox reset failed: {detail}"
            )
        stop_started = time.monotonic()
        stop_event.set()
        if thread is not None and session_started:
            thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )
        try:
            log_evidence = _capture_log_evidence(spec)
            marker_observed = bool(
                marker_observed
                or _mapping(log_evidence).get("marker_observed") is True
            )
        except BaseException as error:
            detail = f"{type(error).__name__}: {error}"
            primary_error = (
                detail
                if primary_error is None
                else f"{primary_error}; log capture failed: {detail}"
            )
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    mutation = _mutation_boundary_proof(commands, seed_stage=True)
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "seed managed cleanup was not proven"
        )
    event_id = _active_event_id(stable if stable is not None else materialized)
    return {
        "stage": "seed-trigger-query-save-event",
        "session_started": session_started,
        "production_native_bridge": True,
        "fixture_definition_playset": True,
        "seed_only_mod_bridge": True,
        "debug_mode": False,
        "ok": bool(
            primary_error is None
            and projection.get("ok") is True
            and exact_binary
            and exact_binary.get("ok") is True
            and capability_before
            and capability_before.get("ok") is True
            and capability_after
            and capability_after.get("ok") is True
            and marker_observed
            and event_id is not None
            and seed_query_proof
            and seed_query_proof.get("ok") is True
            and checkpoint is not None
            and mutation.get("ok") is True
            and same_process
            and same_process.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path.resolve()),
            "bridge_dll_sha256": dll_sha256,
            "expected_bridge_dll_sha256": expected_dll_sha256,
            "bridge_injector": str(config.injector_path.resolve()),
            "bridge_injector_sha256": injector_sha256,
        },
        "fixture_projection_proof": projection,
        "readiness": readiness,
        "exact_binary_proof": exact_binary,
        "capability_before": capability_before,
        "capability_after": capability_after,
        "same_process_proof": same_process,
        "initial_snapshot": _compact_snapshot(initial),
        "materialized_snapshot": _compact_snapshot(materialized),
        "stable_pre_save_snapshot": _compact_snapshot(stable),
        "post_save_snapshot": _compact_snapshot(after_save),
        "event_instance_id": event_id,
        "seed_query": seed_query,
        "seed_query_proof": seed_query_proof,
        "save_result": save_result,
        "checkpoint": checkpoint,
        "seed_protocol": {
            "generation_marker": GENERATE_MARKER,
            "generation_marker_observed": marker_observed,
            "generation_write": generation_write,
            "final_noop": final_noop,
            "guard_persists_in_fixture_checkpoint": True,
        },
        "mutation_boundary": mutation,
        "log_evidence": log_evidence,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _run_cold_query_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    expected_dll_sha256: str,
    expected_event_id: int,
    expected_date_raw: int,
    timeout: float,
    readiness_timeout: float,
) -> dict[str, object]:
    started = time.monotonic()
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    primary_error: str | None = None
    readiness: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    exact_binary: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    sequence: dict[str, object] | None = None
    executable_sha256: str | None = None
    dll_sha256: str | None = None
    injector_sha256: str | None = None
    projection = _fixture_projection_proof(spec, seed_stage=False)

    def supervise() -> None:
        try:
            session_state["report"] = _fixture_definition_native_session(
                spec=spec,
                config=config,
                timeout=timeout + 90.0,
                stop_event=stop_event,
                seed_stage=False,
            )
        except BaseException as error:
            session_state["error"] = f"{type(error).__name__}: {error}"
        finally:
            session_done.set()

    try:
        if projection.get("ok") is not True:
            raise AgentError("cold clone lacks the exact fixture playset")
        executable_sha256 = _sha256_file(spec.game_exe)
        dll_sha256 = _sha256_file(config.dll_path)
        injector_sha256 = _sha256_file(config.injector_path)
        if executable_sha256 != EXPECTED_EXECUTABLE_SHA256:
            raise RuntimeError("managed CK3 executable SHA-256 differs")
        if dll_sha256 != expected_dll_sha256:
            raise RuntimeError("production bridge DLL SHA-256 differs")
        if injector_sha256 != FROZEN_BRIDGE_INJECTOR_SHA256:
            raise RuntimeError("frozen bridge injector SHA-256 differs")
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-event-window-cold-query-session",
            daemon=False,
        )
        thread.start()
        session_started = True
        readiness = _wait_for_readiness(
            driver,
            session_done=session_done,
            session_state=session_state,
            timeout_seconds=readiness_timeout,
            stable_seconds=0.5,
            poll_interval_seconds=0.05,
            cold_start_checkpoint=False,
            allow_terminal=False,
        )
        capabilities_before = driver.capabilities()
        exact_binary = _exact_binary_proof(
            capabilities_before,
            executable_sha256=executable_sha256,
            dll_sha256=dll_sha256,
            expected_dll_sha256=expected_dll_sha256,
        )
        capability = _capability_proof(
            capabilities_before, event_present=True
        )
        if exact_binary.get("ok") is not True:
            raise RuntimeError("cold exact EXE/DLL proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("cold event-window capability proof failed")
        sequence = _run_double_query_sequence(
            service,
            expected_event_id=expected_event_id,
            expected_date_raw=expected_date_raw,
        )
        if sequence.get("ok") is not True:
            raise RuntimeError("adjacent current-event queries failed")
        capabilities_after = driver.capabilities()
        same_process = _same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("cold event queries crossed bridge process")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"
    finally:
        stop_started = time.monotonic()
        stop_event.set()
        if thread is not None and session_started:
            thread.join()
        stop_elapsed = round(max(0.0, time.monotonic() - stop_started), 3)
        if driver is not None:
            try:
                driver.close()
                driver_closed = True
            except BaseException as error:
                detail = f"{type(error).__name__}: {error}"
                primary_error = (
                    detail
                    if primary_error is None
                    else f"{primary_error}; driver close failed: {detail}"
                )
    cleanup = _cleanup_report(
        session_state.get("report"),
        session_error=session_state.get("error"),
        driver_closed=driver_closed,
        elapsed_seconds=stop_elapsed,
    )
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "cold managed cleanup was not proven"
        )
    return {
        "stage": "fresh-fixture-cold-double-query",
        "session_started": session_started,
        "fresh_process_cold_reload": True,
        "production_native_bridge": True,
        "fixture_definition_playset": True,
        "production_only_playset": False,
        "mod_bridge_loaded": False,
        "debug_mode": False,
        "ok": bool(
            primary_error is None
            and projection.get("ok") is True
            and exact_binary
            and exact_binary.get("ok") is True
            and capability
            and capability.get("ok") is True
            and sequence
            and sequence.get("ok") is True
            and same_process
            and same_process.get("ok") is True
            and cleanup.get("ok") is True
        ),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "identity": {
            "pipe": config.pipe_name,
            "game_executable": str(spec.game_exe.resolve()),
            "game_executable_sha256": executable_sha256,
            "bridge_dll": str(config.dll_path.resolve()),
            "bridge_dll_sha256": dll_sha256,
            "expected_bridge_dll_sha256": expected_dll_sha256,
            "bridge_injector": str(config.injector_path.resolve()),
            "bridge_injector_sha256": injector_sha256,
        },
        "fixture_projection_proof": projection,
        "readiness": readiness,
        "exact_binary_proof": exact_binary,
        "capability_proof": capability,
        "same_process_proof": same_process,
        "sequence": sequence,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _cross_stage_proof(
    seed_stage: object,
    cold_stage: object,
    transfer: object,
) -> dict[str, object]:
    seed = _mapping(seed_stage)
    cold = _mapping(cold_stage)
    sequence = _mapping(cold.get("sequence"))
    seed_query = _mapping(seed.get("seed_query"))
    seed_frame = _mapping(seed_query.get("current_event_window_context"))
    first = _mapping(sequence.get("first_query"))
    cold_frame = _mapping(first.get("current_event_window_context"))
    seed_process = _mapping(seed.get("same_process_proof"))
    cold_process = _mapping(cold.get("same_process_proof"))
    seed_pid = seed_process.get("bridge_pid")
    cold_pid = cold_process.get("bridge_pid")
    seed_projection = _mapping(seed.get("fixture_projection_proof"))
    cold_projection = _mapping(cold.get("fixture_projection_proof"))
    seed_manifest = _mapping(seed_projection.get("content_manifest"))
    cold_manifest = _mapping(cold_projection.get("content_manifest"))
    seed_snapshot = _mapping(seed.get("stable_pre_save_snapshot"))
    checks = {
        "both_stages_green": seed.get("ok") is True and cold.get("ok") is True,
        "checkpoint_bytes_transferred": _mapping(transfer).get("ok") is True,
        "distinct_positive_pids": isinstance(seed_pid, int)
        and not isinstance(seed_pid, bool)
        and seed_pid > 0
        and isinstance(cold_pid, int)
        and not isinstance(cold_pid, bool)
        and cold_pid > 0
        and seed_pid != cold_pid,
        "same_full_event_instance_id": seed.get("event_instance_id")
        == sequence.get("current_event_instance_id")
        == seed_frame.get("current_event_instance_id")
        == cold_frame.get("current_event_instance_id"),
        "same_game_date": seed_snapshot.get("date_raw")
        == sequence.get("date_raw")
        == seed_frame.get("date_raw")
        == cold_frame.get("date_raw"),
        "same_canonical_definition_key": seed_frame.get(
            "event_definition_key"
        )
        == cold_frame.get("event_definition_key")
        == EXPECTED_EVENT_KEY,
        "process_local_calculated_event_ids_are_signed_int32": _signed_int32(
            seed_frame.get("calculated_event_id")
        )
        and _signed_int32(cold_frame.get("calculated_event_id")),
        "process_local_runtime_stats_ordinals_are_signed_int32": _signed_int32(
            seed_frame.get("runtime_stats_ordinal")
        )
        and _signed_int32(cold_frame.get("runtime_stats_ordinal")),
        "same_materialized_options": seed_frame.get("options")
        == cold_frame.get("options")
        and _expected_option_shape(cold_frame.get("options")),
        "byte_identical_fixture_content": seed_manifest.get("sha256")
        == cold_manifest.get("sha256")
        == FIXTURE_CONTENT_MANIFEST_SHA256,
        "cold_has_no_mod_bridge": _mapping(
            cold_projection.get("checks")
        ).get("mod_bridge_presence_matches_stage")
        is True
        and cold.get("mod_bridge_loaded") is False,
        "no_option_selection": _mapping(seed.get("mutation_boundary")).get(
            "ok"
        )
        is True
        and _mapping(sequence.get("mutation_boundary")).get("ok") is True,
        "unclosed_semantics_stay_false": _mapping(seed_frame.get("readiness"))
        == _mapping(cold_frame.get("readiness"))
        == {
            "event_definition_identity_ready": True,
            "option_presentation_ready": True,
            "effect_indicators_ready": True,
            "effect_preview_ready": False,
            "semantic_decision_ready": False,
        }
        and seed_query.get("current_event_effect_indicators_ready") is True
        and first.get("current_event_effect_indicators_ready") is True
        and cold_frame.get("root_scope") is None
        and cold_frame.get("saved_scopes") is None,
    }
    return {
        "seed_bridge_pid": seed_pid,
        "cold_bridge_pid": cold_pid,
        "current_event_instance_id": seed.get("event_instance_id"),
        "date_raw": seed_snapshot.get("date_raw"),
        "event_definition_key": cold_frame.get("event_definition_key"),
        "seed_calculated_event_id": seed_frame.get("calculated_event_id"),
        "cold_calculated_event_id": cold_frame.get("calculated_event_id"),
        "seed_runtime_stats_ordinal": seed_frame.get(
            "runtime_stats_ordinal"
        ),
        "cold_runtime_stats_ordinal": cold_frame.get(
            "runtime_stats_ordinal"
        ),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run(args: argparse.Namespace) -> tuple[dict[str, object], int]:
    started = time.monotonic()
    started_wall = utc_now()
    timeout = _positive_seconds(args.timeout, "timeout")
    readiness_timeout = _positive_seconds(
        args.readiness_timeout, "readiness_timeout"
    )
    seed_timeout = _positive_seconds(args.seed_timeout, "seed_timeout")
    expected_source_sha = _canonical_sha256(
        args.expected_source_save_sha256,
        "expected source save SHA-256",
    )
    expected_dll_sha = _canonical_sha256(
        args.expected_bridge_dll_sha256,
        "expected bridge DLL SHA-256",
    )
    if expected_dll_sha != FROZEN_BRIDGE_DLL_SHA256:
        raise AgentError(
            "event-window live acceptance must use the reviewed cea30a0 DLL: "
            f"{FROZEN_BRIDGE_DLL_SHA256}"
        )
    source_profile = args.source_profile.expanduser().resolve()
    root = _target_root(args.state_dir)
    output = args.output.expanduser().resolve()
    game_dir = args.game_dir.expanduser().resolve()
    if output.exists():
        raise AgentError(f"artifact output already exists: {output}")
    if is_relative_to(output, root):
        raise AgentError("artifact output must be outside disposable root")
    if is_relative_to(output, source_profile):
        raise AgentError("artifact output must be outside immutable source")
    if paths_overlap(source_profile, root):
        raise AgentError("immutable source and disposable root overlap")

    config = NativeBridgeLaunchConfig(
        mode=PURE_NATIVE_MODE,
        pipe_name=args.bridge_pipe,
        dll_path=args.bridge_dll.expanduser().resolve(),
        injector_path=args.bridge_injector.expanduser().resolve(),
    )
    dependency_source = _dependency_source_contract()
    fixture_definition = _fixture_definition_contract()
    fixture_effect = _effect_contract()
    generated_path_lengths = _generated_fixture_path_length_contract(root)
    source_save: Path | None = None
    source_identity: dict[str, object] | None = None
    source_before: dict[str, object] | None = None
    source_after: dict[str, object] | None = None
    disposable: dict[str, object] | None = None
    seed_materialization: dict[str, object] | None = None
    cold_materialization: dict[str, object] | None = None
    seed_stage: dict[str, object] | None = None
    cold_stage: dict[str, object] | None = None
    transfer: dict[str, object] | None = None
    cross_stage: dict[str, object] | None = None
    primary_error: str | None = None
    nonce = uuid.uuid4().hex

    try:
        if dependency_source.get("ok") is not True:
            raise AgentError(
                "live event-window acceptance requires an isolated exact-commit "
                f"dependency tree: set {ISOLATED_SOURCE_ROOT_ENV} to commit "
                f"{FROZEN_SOURCE_COMMIT}"
            )
        if fixture_definition.get("ok") is not True:
            raise AgentError("fixture definition/localization contract differs")
        if fixture_effect.get("ok") is not True:
            raise AgentError("fixture generation effect contract differs")
        if generated_path_lengths.get("ok") is not True:
            raise AgentError(
                "generated fixture path is not below the CK3 PhysFS "
                "250-character boundary; use a shorter explicit --state-dir"
            )
        source_save, source_identity = pending_live._resolve_source_save(
            source_profile,
            args.source_save,
            expected_source_sha,
        )
        source_before = {
            "sha256": _sha256_file(source_save),
            "size": source_save.stat().st_size,
            "mtime_ns": source_save.stat().st_mtime_ns,
        }
        disposable = _prepare_root(
            root,
            source_profile=source_profile,
            source_save_sha256=expected_source_sha,
            nonce=nonce,
        )
        seed_spec, seed_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / _SEED_STAGE_NAME,
            game_dir=game_dir,
            save_source=source_save,
            save_name=CONTINUE_SAVE_NAME,
        )
        seed_materialization["fixture_bridge"] = (
            owner_live._install_seed_bridge(seed_spec)
        )
        seed_materialization["fixture_definition"] = (
            _install_fixture_definition(seed_spec)
        )
        seed_stage = _run_seed_stage(
            spec=seed_spec,
            config=config,
            expected_dll_sha256=expected_dll_sha,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            seed_timeout=seed_timeout,
        )
        if seed_stage.get("ok") is not True:
            raise AgentError(str(seed_stage.get("error") or "seed stage failed"))
        event_id = seed_stage.get("event_instance_id")
        if (
            isinstance(event_id, bool)
            or not isinstance(event_id, int)
            or not 1 <= event_id <= 2**31 - 1
        ):
            raise AgentError("seed stage lacks a positive full event ID")
        seed_snapshot = _mapping(seed_stage.get("stable_pre_save_snapshot"))
        expected_date_raw = seed_snapshot.get("date_raw")
        if isinstance(expected_date_raw, bool) or not isinstance(
            expected_date_raw, int
        ):
            raise AgentError("seed stage lacks a signed game date")
        seed_checkpoint = owner_live._checkpoint_path(seed_spec)

        cold_spec, cold_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / _COLD_STAGE_NAME,
            game_dir=game_dir,
            save_source=seed_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        cold_materialization["fixture_definition"] = (
            _install_fixture_definition(cold_spec)
        )
        transfer = _checkpoint_transfer_proof(seed_checkpoint, cold_spec)
        if transfer.get("ok") is not True:
            raise AgentError("event checkpoint transfer differs")
        cold_stage = _run_cold_query_stage(
            spec=cold_spec,
            config=config,
            expected_dll_sha256=expected_dll_sha,
            expected_event_id=event_id,
            expected_date_raw=expected_date_raw,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
        )
        if cold_stage.get("ok") is not True:
            raise AgentError(
                str(cold_stage.get("error") or "cold query stage failed")
            )
        cross_stage = _cross_stage_proof(seed_stage, cold_stage, transfer)
        if cross_stage.get("ok") is not True:
            raise AgentError("fixture event changed across cold reload")
    except BaseException as error:
        primary_error = f"{type(error).__name__}: {error}"

    if source_save is not None:
        try:
            source_after = {
                "sha256": _sha256_file(source_save),
                "size": source_save.stat().st_size,
                "mtime_ns": source_save.stat().st_mtime_ns,
            }
        except BaseException as error:
            if primary_error is None:
                primary_error = f"{type(error).__name__}: {error}"
    source_unchanged = bool(
        source_before is not None
        and source_after is not None
        and source_before == source_after
    )
    if not source_unchanged and source_save is not None and primary_error is None:
        primary_error = "immutable source save changed"

    stages: list[object] = [seed_stage, cold_stage]
    no_ck3_processes = not ck3_processes()
    if root.exists():
        cleanup = _cleanup_root(
            root,
            nonce=nonce,
            retain=bool(args.retain_state),
            stages=stages,
        )
    else:
        cleanup = {
            "attempted": False,
            "removed": True,
            "path": str(root),
            "ok": True,
            "reason": "disposable root was not created",
        }
    if not no_ck3_processes and primary_error is None:
        primary_error = "a CK3 process remains after managed stages"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            cleanup.get("reason") or "disposable root cleanup failed"
        )

    seed = _mapping(seed_stage)
    cold = _mapping(cold_stage)
    sequence = _mapping(cold.get("sequence"))
    sequence_checks = _mapping(sequence.get("checks"))
    context_proof = _mapping(sequence.get("first_context_proof"))
    context_checks = _mapping(context_proof.get("checks"))
    cross_checks = _mapping(_mapping(cross_stage).get("checks"))
    seed_binary = _mapping(seed.get("exact_binary_proof"))
    cold_binary = _mapping(cold.get("exact_binary_proof"))
    readiness_gates = {
        "generated_fixture_paths_within_ck3_physfs_limit": (
            generated_path_lengths.get("ok") is True
        ),
        "generic_nonreligious_fixture_contract": fixture_definition.get("ok")
        is True
        and fixture_effect.get("ok") is True,
        "fixture_event_materialized_while_paused": seed.get("event_instance_id")
        is not None
        and _mapping(seed.get("seed_query_proof")).get("ok") is True,
        "stable_full_instance_id_across_cold_reload": cross_checks.get(
            "same_full_event_instance_id"
        )
        is True,
        "byte_identical_fixture_definition_both_stages": cross_checks.get(
            "byte_identical_fixture_content"
        )
        is True,
        "cold_fixture_playset_has_no_mod_bridge": cross_checks.get(
            "cold_has_no_mod_bridge"
        )
        is True,
        "canonical_key_and_stage_local_registration_metadata": all(
            context_checks.get(key) is True
            for key in (
                "canonical_definition_key",
                "calculated_event_id_is_signed_int32",
                "runtime_stats_ordinal_is_signed_int32",
            )
        )
        and cross_checks.get(
            "process_local_calculated_event_ids_are_signed_int32"
        )
        is True
        and cross_checks.get(
            "process_local_runtime_stats_ordinals_are_signed_int32"
        )
        is True,
        "rendered_native_presentation_exact": all(
            context_checks.get(key) is True
            for key in (
                "materialized_option_shape",
                "hidden_native_index_absent",
                "fallback_native_index_absent",
            )
        ),
        "adjacent_same_revision_double_query": all(
            sequence_checks.get(key) is True
            for key in (
                "between_same_paused_binding",
                "after_same_paused_binding",
                "query_sequence_exact_successor",
                "adjacent_context_frames_strictly_equal",
                "only_query_sequence_changed",
            )
        ),
        "effect_scopes_and_semantic_readiness_remain_unclosed": all(
            context_checks.get(key) is True
            for key in (
                "root_and_saved_scopes_unavailable",
                "readiness_truthful",
            )
        ),
        "no_event_option_selected": cross_checks.get("no_option_selection")
        is True,
        "exact_exe_dll_and_injector": seed_binary.get("ok") is True
        and cold_binary.get("ok") is True
        and _mapping(seed.get("identity")).get("bridge_injector_sha256")
        == FROZEN_BRIDGE_INJECTOR_SHA256
        and _mapping(cold.get("identity")).get("bridge_injector_sha256")
        == FROZEN_BRIDGE_INJECTOR_SHA256,
        "immutable_source_bytes_and_metadata": source_unchanged,
        "managed_process_cleanup": no_ck3_processes
        and all(
            isinstance(stage, dict)
            and _mapping(stage.get("cleanup")).get("ok") is True
            for stage in stages
        ),
        "nonce_disposable_cleanup": cleanup.get("ok") is True,
    }
    ok = bool(primary_error is None and all(readiness_gates.values()))
    payload: dict[str, object] = {
        "format_version": 1,
        "kind": "ck3_current_event_window_context_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "evidence_classification": (
            "fixture-scoped-live-confirmed" if ok else "not-qualified"
        ),
        "fixed_scenario": {
            "player_character_id": PLAYER_CHARACTER_ID,
            "event_definition_key": EXPECTED_EVENT_KEY,
            "authored_option_count": 5,
            "expected_rendered_native_indices": [0, 1, 3],
            "expected_hidden_native_index": 2,
            "expected_unmaterialized_fallback_native_index": 4,
        },
        "policy": {
            "fixture_definition_and_localization_loaded_in_both_stages": True,
            "fixture_definition_is_stock": False,
            "fixture_playset_is_production_only": False,
            "production_native_bridge_in_both_stages": True,
            "cold_stage_has_no_mod_bridge_or_run_inbox": True,
            "event_option_selection_allowed": False,
            "event_option_selection_invoked": False,
            "root_scope_ready_expected": False,
            "saved_scopes_ready_expected": False,
            "full_effect_preview_ready_expected": False,
            "semantic_decision_ready_expected": False,
            "religion_specific_semantics_read": False,
            "religion_nonwar_deep_domains_owner_deferred": True,
            "minimal_holy_war_observation_action_exception_relevant": False,
            "minimal_marriage_faith_legality_exception_relevant": False,
        },
        "frozen_source_contract": {
            "commit": FROZEN_SOURCE_COMMIT,
            "bridge_dll_sha256": FROZEN_BRIDGE_DLL_SHA256,
            "bridge_injector_sha256": FROZEN_BRIDGE_INJECTOR_SHA256,
            "shared_dirty_source_used_for_runtime_dependencies": False,
            "fixture_content_manifest_sha256": (
                FIXTURE_CONTENT_MANIFEST_SHA256
            ),
        },
        "isolated_dependency_source": dependency_source,
        "generated_fixture_path_length_contract": generated_path_lengths,
        "fixture_definition_contract": fixture_definition,
        "fixture_effect_contract": fixture_effect,
        "source_save": source_identity,
        "source_save_invariant": {
            "before": source_before,
            "after": source_after,
            "unchanged": source_unchanged,
        },
        "disposable": disposable,
        "seed_materialization": seed_materialization,
        "cold_materialization": cold_materialization,
        "checkpoint_transfer": transfer,
        "seed_stage": seed_stage,
        "cold_stage": cold_stage,
        "cross_stage_proof": cross_stage,
        "readiness_gates": readiness_gates,
        "no_ck3_processes_after": no_ck3_processes,
        "disposable_cleanup": cleanup,
        "error": primary_error,
    }
    return payload, 0 if ok else 1


def main() -> int:
    args = _parser().parse_args()
    payload, exit_code = _run(args)
    cross = _mapping(payload.get("cross_stage_proof"))
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "ok": payload.get("ok"),
                "event_instance_id": cross.get("current_event_instance_id"),
                "event_definition_key": cross.get("event_definition_key"),
                "seed_calculated_event_id": cross.get(
                    "seed_calculated_event_id"
                ),
                "cold_calculated_event_id": cross.get(
                    "cold_calculated_event_id"
                ),
                "seed_runtime_stats_ordinal": cross.get(
                    "seed_runtime_stats_ordinal"
                ),
                "cold_runtime_stats_ordinal": cross.get(
                    "cold_runtime_stats_ordinal"
                ),
                "output": str(output),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

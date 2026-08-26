#!/usr/bin/env python3
"""Generate and ACK one deterministic nonreligious interaction notification.

The immutable CK3 1.19.0.6 source save is never launched in place.  A first
disposable seed clone mounts the production native bridge, the repository
``mod_bridge``, and one definition-only fixture mod.  While paused,
``mod_bridge`` first switches the local player to CharacterID 36108 and then
sends the fixture interaction from NPC CharacterID 29829.  The fixture owns
``auto_accept = yes`` and ``force_notification = yes`` and its two handlers
only emit diagnostic log markers.  The resulting generation-bearing
``auto_accept_notification`` is saved without accepting, rejecting, blocking,
or acknowledging it in the seed process.

The checkpoint enters a fresh clone that mounts the production native bridge
and the byte-identical definition-only fixture mod, but not ``mod_bridge`` or
its run inbox.  This is deliberately described as a fixture-definition
playset, not as a stock or production-only playset.  A distinct supervised CK3
process cold-loads the notification, performs two adjacent same-revision typed
context queries, submits exactly one fixed ACK through the public service, and
proves that the old full pending ID disappears or advances while the game
remains paused on the same date.  GREEN also binds the exact EXE/DLL, fixture
definition bytes, immutable source bytes, and managed cleanup.

This fixture exercises only the generic character-interaction notification
channel.  It does not inspect or implement faith, doctrine, tenet, fervor,
conversion, reformation, holy-war, or any other religion-specific semantics.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
import uuid


RUNNER_RESEARCH_ROOT = Path(__file__).resolve().parent
RUNNER_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
ISOLATED_SOURCE_ROOT_ENV = "XAR_ACK_ISOLATED_SOURCE_ROOT"
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

import run_pending_character_interaction_context_live_acceptance as pending_live  # noqa: E402,E501
import run_owner_subset_retreat_live_acceptance as owner_live  # noqa: E402
from xar_autoplayer.bridge.mod_driver import DataModGameplayDriver  # noqa: E402
from xar_autoplayer.bridge.native_driver import (  # noqa: E402
    NativeHeadlessGameplayDriver,
)
from xar_autoplayer.bridge.pending_character_interaction_context_contract import (  # noqa: E402,E501
    ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_CAPABILITY,
    ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256,
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
    QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
)
from xar_autoplayer.bridge.service import GameplayBridgeService  # noqa: E402
from xar_autoplayer.environment import (  # noqa: E402
    OUTER_DESCRIPTOR_REF,
    is_relative_to,
    paths_overlap,
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
EXPECTED_ADAPTER_ID = pending_live.EXPECTED_ADAPTER_ID
EXPECTED_SOURCE_SAVE_SHA256 = pending_live.EXPECTED_SOURCE_SAVE_SHA256
DEFAULT_SOURCE_PROFILE = pending_live.DEFAULT_SOURCE_PROFILE
DEFAULT_SOURCE_SAVE = pending_live.DEFAULT_SOURCE_SAVE
CONTINUE_SAVE_NAME = owner_live.CONTINUE_SAVE_NAME
FROZEN_ACK_SOURCE_COMMIT = "70bf8e6b689780b459b361af5edf57c0f7521fca"
FROZEN_ACK_DLL_SHA256 = (
    "BFB1E38FCA879681074C4AB64C077F0111A7A828EA3E5284D21E0B362F40D9A9"
)
FROZEN_ACK_INJECTOR_SHA256 = (
    "1F418FFD2D765278C4EF749D3C389447FC0141FD52BDEBF79D536F1DEBAACD5C"
)
PRIOR_EXECUTE_THRESHOLD_RED_ARTIFACT_SHA256 = (
    "76CF9670B38F0B80018E3C384C0AA61663FB454301C0F810227BFBA60C143343"
)
PRIOR_OVERRIDE_COLD_RELOAD_RED_ARTIFACT_SHA256 = (
    "E640F9ED431EB4C071805BA5B9306E420A57121BC1A9D3264753FEA116F3B3AB"
)
PRIOR_STOCK_VALIDITY_RED_ARTIFACT_SHA256 = (
    "F7A07CE8A6FD84519A2AA3723AA46BA908AEBE2306412F051E447FBC103EAB3B"
)
PRIOR_STOCK_ROOT_SCOPE_RED_ARTIFACT_SHA256 = (
    "7B42CCDD1F4C4FFACD21BC93D2F224C323AEFFB1DEB2D8282F6516DD4EFB4AAF"
)
PRIOR_STOCK_ACTOR_SCOPE_RED_ARTIFACT_SHA256 = (
    "C8EE5E2C1F354DA38D137260FB28DF2C895D3A872E0F8ADDDF3EEBA46FA39E74"
)
PRIOR_STOCK_REMOVE_GUARDIAN_RED_ARTIFACT_SHA256 = (
    "726F468A46C39462370A8422B7CBC15093310A7F34E769AE7D78C01E1E9DC607"
)

PROFILE_PLAYER_CHARACTER_ID = pending_live.SOURCE_CHARACTER_ID
SOURCE_CHARACTER_ID = pending_live.SOURCE_CHARACTER_ID
RECIPIENT_CHARACTER_ID = pending_live.RECIPIENT_CHARACTER_ID
RECIPIENT_ANCHOR_PROVINCE_ID = pending_live.RECIPIENT_ANCHOR_PROVINCE_ID
SOURCE_ANCHOR_PROVINCE_ID = 2_619
EXPECTED_INTERACTION_KEY = "xar_notification_ack_fixture_interaction"
FIXTURE_MOD_TARGET_NAME = "xar-notification-ack-fixture"
FIXTURE_MOD_OUTER_NAME = "xar_notification_ack_fixture.mod"
FIXTURE_MOD_OUTER_REF = f"mod/{FIXTURE_MOD_OUTER_NAME}"
FIXTURE_DEFINITION_RELATIVE = Path(
    "common/character_interactions/zz_xar_notification_ack_fixture.txt"
)
FIXTURE_ON_AUTO_ACCEPT_MARKER = (
    "XAR_FIXTURE:NOTIFICATION_ACK_ON_AUTO_ACCEPT|"
    f"interaction={EXPECTED_INTERACTION_KEY}"
)
FIXTURE_ON_ACCEPT_MARKER = (
    "XAR_FIXTURE:NOTIFICATION_ACK_ON_ACCEPT|"
    f"interaction={EXPECTED_INTERACTION_KEY}"
)
FIXTURE_DEFINITION_SOURCE = (
    f"{EXPECTED_INTERACTION_KEY} = {{\n"
    "\tcategory = interaction_category_friendly\n"
    "\thidden = yes\n"
    "\tuse_diplomatic_range = no\n"
    "\tignores_pending_interaction_block = yes\n"
    "\tgreeting = positive\n"
    "\tnotification_text = XAR_NOTIFICATION_ACK_FIXTURE_NOTIFICATION\n"
    "\tforce_notification = yes\n"
    "\tis_shown = { always = yes }\n"
    "\tis_valid_showing_failures_only = { always = yes }\n"
    "\tauto_accept = yes\n"
    "\ton_auto_accept = {\n"
    f'\t\tdebug_log = "{FIXTURE_ON_AUTO_ACCEPT_MARKER}"\n'
    "\t}\n"
    "\ton_accept = {\n"
    f'\t\tdebug_log = "{FIXTURE_ON_ACCEPT_MARKER}"\n'
    "\t}\n"
    "}\n"
)
FIXTURE_DEFINITION_SHA256 = (
    "76AD6E5337366E86851F1A51B6EED2A910B85BD3181B492059DC37362B637501"
)

SWITCH_GUARD = "xar_fixture_notification_ack_switch_consumed"
GENERATE_GUARD = "xar_fixture_notification_ack_generated"
SOURCE_SCOPE = "xar_fixture_notification_ack_source"
RECIPIENT_SCOPE = "xar_fixture_notification_ack_recipient"
SWITCH_MARKER = "XAR_FIXTURE:NOTIFICATION_ACK_SWITCH|recipient=36108"
GENERATE_MARKER = (
    "XAR_FIXTURE:NOTIFICATION_ACK_GENERATE|"
    f"interaction={EXPECTED_INTERACTION_KEY}"
)
SEED_NOOP_INBOX = "# XAR notification-ACK fixture inbox: no effects.\n"

_ROOT_PREFIX = "xar-pending-notification-ack-"
_FORBIDDEN_NORMAL_REPLY_STEPS = frozenset(
    {
        "accept-pending-character-interaction",
        "reject-pending-character-interaction",
        "block-pending-character-interaction",
    }
)
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
    parser.add_argument("--postcondition-timeout", type=float, default=15.0)
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
            "pending_contract": root
            / "ck3_autonomous_player"
            / "src"
            / "xar_autoplayer"
            / "bridge"
            / "pending_character_interaction_context_contract.py",
            "service": root
            / "ck3_autonomous_player"
            / "src"
            / "xar_autoplayer"
            / "bridge"
            / "service.py",
            "native_driver": root
            / "ck3_autonomous_player"
            / "src"
            / "xar_autoplayer"
            / "bridge"
            / "native_driver.py",
            "mod_bridge_descriptor": root
            / "ck3_autonomous_player"
            / "mod_bridge"
            / "descriptor.mod",
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
            checks["exact_commit"] = commit == FROZEN_ACK_SOURCE_COMMIT
        except (OSError, subprocess.SubprocessError) as caught:
            error = f"{type(caught).__name__}: {caught}"
    return {
        "environment_variable": ISOLATED_SOURCE_ROOT_ENV,
        "runner_path": str(Path(__file__).resolve()),
        "runner_workspace_root": str(RUNNER_WORKSPACE_ROOT),
        "isolated_source_root": str(root) if root is not None else None,
        "commit": commit,
        "expected_commit": FROZEN_ACK_SOURCE_COMMIT,
        "files": files,
        "checks": checks,
        "ok": all(checks.values()),
        "error": error,
    }


def _extract_definition_block(
    source: str, key: str
) -> tuple[str, int, int] | None:
    """Return one top-level scripted definition without guessing its end."""

    match = re.search(rf"(?m)^{re.escape(key)}\s*=\s*\{{", source)
    if match is None:
        return None
    opening = source.find("{", match.start())
    depth = 0
    quoted = False
    escaped = False
    in_comment = False
    for index in range(opening, len(source)):
        character = source[index]
        if in_comment:
            if character in "\r\n":
                in_comment = False
            continue
        if quoted:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                quoted = False
            continue
        if character == "#":
            in_comment = True
        elif character == '"':
            quoted = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                return (
                    source[match.start() : end],
                    source.count("\n", 0, match.start()) + 1,
                    source.count("\n", 0, end) + 1,
                )
    return None


def _fixture_definition_raw() -> bytes:
    return b"\xef\xbb\xbf" + FIXTURE_DEFINITION_SOURCE.encode("utf-8")


def _fixture_definition_contract() -> dict[str, object]:
    raw = _fixture_definition_raw()
    extracted = _extract_definition_block(
        FIXTURE_DEFINITION_SOURCE, EXPECTED_INTERACTION_KEY
    )
    block = extracted[0] if extracted is not None else ""
    folded = block.casefold()
    checks = {
        "canonical_definition_only": extracted is not None
        and extracted[1] == 1
        and extracted[2] == len(FIXTURE_DEFINITION_SOURCE.splitlines()),
        "utf8_bom": raw.startswith(b"\xef\xbb\xbf"),
        "exact_source_sha256": hashlib.sha256(raw).hexdigest().upper()
        == FIXTURE_DEFINITION_SHA256,
        "auto_accept": "auto_accept = yes" in block,
        "force_notification": "force_notification = yes" in block,
        "hidden": "hidden = yes" in block,
        "no_diplomatic_range": "use_diplomatic_range = no" in block,
        "always_shown_and_valid": block.count("always = yes") == 2,
        "diagnostic_handlers_only": (
            "on_auto_accept = {" in block
            and "on_accept = {" in block
            and block.count("debug_log =") == 2
            and FIXTURE_ON_AUTO_ACCEPT_MARKER in block
            and FIXTURE_ON_ACCEPT_MARKER in block
        ),
        "no_gameplay_mutator_tokens": all(
            token not in folded
            for token in (
                "add_",
                "remove_",
                "set_",
                "change_",
                "trigger_event",
                "run_interaction",
                "send_interface",
            )
        ),
        "no_religion_semantics": all(
            token not in folded for token in _RELIGION_TOKENS
        ),
    }
    return {
        "canonical_key": EXPECTED_INTERACTION_KEY,
        "relative_path": FIXTURE_DEFINITION_RELATIVE.as_posix(),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest().upper(),
        "expected_sha256": FIXTURE_DEFINITION_SHA256,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _fixture_descriptor(*, outer: bool, target: Path) -> str:
    path = f'path="{target.resolve().as_posix()}"\n' if outer else ""
    return (
        '\ufeffversion="0.1.0"\n'
        'tags={\n\t"Utilities"\n}\n'
        'name="XAR Notification ACK Acceptance Fixture"\n'
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
    definition = target / FIXTURE_DEFINITION_RELATIVE
    definition.parent.mkdir(parents=True, exist_ok=False)
    definition_identity = owner_live._write_seed_inbox(
        definition, FIXTURE_DEFINITION_SOURCE
    )
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
        "definition": definition_identity,
        "enabled_mods": list(enabled),
    }


def _fixture_projection_proof(
    spec: Any, *, seed_stage: bool
) -> dict[str, object]:
    load_path = spec.profile_dir / "dlc_load.json"
    fixture_root = (
        spec.profile_dir / "mod-content" / FIXTURE_MOD_TARGET_NAME
    ).resolve()
    definition = fixture_root / FIXTURE_DEFINITION_RELATIVE
    mod_bridge_root = (
        spec.profile_dir
        / "mod-content"
        / owner_live.MOD_BRIDGE_TARGET_NAME
    ).resolve()
    mod_bridge_outer = (
        spec.profile_dir / "mod" / owner_live.MOD_BRIDGE_OUTER_NAME
    ).resolve()
    expected_enabled = [OUTER_DESCRIPTOR_REF]
    if seed_stage:
        expected_enabled.append(f"mod/{owner_live.MOD_BRIDGE_OUTER_NAME}")
    expected_enabled.append(FIXTURE_MOD_OUTER_REF)
    try:
        payload = json.loads(load_path.read_text(encoding="utf-8-sig"))
        raw = definition.read_bytes()
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
    checks = {
        "inside_disposable_profile": is_relative_to(
            fixture_root, spec.profile_dir.resolve()
        ),
        "exact_fixture_playset": payload
        == {"enabled_mods": expected_enabled, "disabled_dlcs": []},
        "production_native_tree_present": spec.production_dir.is_dir(),
        "fixture_files_exact": files
        == sorted(
            ["descriptor.mod", FIXTURE_DEFINITION_RELATIVE.as_posix()]
        ),
        "definition_bytes_exact": raw == _fixture_definition_raw(),
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
        "stage_kind": "seed" if seed_stage else "cold-query-ack",
        "dlc_load": payload,
        "expected_enabled_mods": expected_enabled,
        "fixture_root": str(fixture_root),
        "definition_path": str(definition.resolve()),
        "definition_size": len(raw),
        "definition_sha256": hashlib.sha256(raw).hexdigest().upper(),
        "files": files,
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
    """Launch only after the exact stage-specific fixture projection passes.

    The production singleton verifier remains unchanged.  This acceptance-only
    seam reuses the existing supervised fixture launcher only after proving the
    exact production+fixture playset and the stage-specific mod_bridge boundary.
    """

    projection = _fixture_projection_proof(spec, seed_stage=seed_stage)
    if projection.get("ok") is not True:
        stage = "seed" if seed_stage else "cold-query-ack"
        raise AgentError(f"{stage} exact fixture projection differs")
    report = owner_live._fixture_native_session(
        spec=spec,
        config=config,
        timeout=timeout,
        stop_event=stop_event,
    )
    result = copy.deepcopy(report)
    result["kind"] = (
        "ck3_pending_character_interaction_notification_ack_fixture_session"
    )
    result["fixture_stage"] = "seed" if seed_stage else "cold-query-ack"
    result["exact_fixture_projection"] = projection
    return result


def _switch_effect() -> str:
    return (
        f"province:{RECIPIENT_ANCHOR_PROVINCE_ID} = {{\n"
        "\tprovince_owner = {\n"
        f"\t\tsave_temporary_scope_as = {RECIPIENT_SCOPE}\n"
        "\t}\n"
        "}\n"
        "if = {\n"
        "\tlimit = {\n"
        f"\t\texists = scope:{RECIPIENT_SCOPE}\n"
        f"\t\tNOT = {{ global_var:{SWITCH_GUARD} = 1 }}\n"
        "\t}\n"
        "\tset_global_variable = {\n"
        f"\t\tname = {SWITCH_GUARD}\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        f"\tset_player_character = scope:{RECIPIENT_SCOPE}\n"
        f'\tdebug_log = "{SWITCH_MARKER}"\n'
        "}\n"
    )


def _generate_effect() -> str:
    return (
        f"province:{SOURCE_ANCHOR_PROVINCE_ID} = {{\n"
        "\tprovince_owner = {\n"
        f"\t\tsave_temporary_scope_as = {SOURCE_SCOPE}\n"
        "\t}\n"
        "}\n"
        f"province:{RECIPIENT_ANCHOR_PROVINCE_ID} = {{\n"
        "\tprovince_owner = {\n"
        f"\t\tsave_temporary_scope_as = {RECIPIENT_SCOPE}\n"
        "\t}\n"
        "}\n"
        "if = {\n"
        "\tlimit = {\n"
        f"\t\texists = scope:{SOURCE_SCOPE}\n"
        f"\t\texists = scope:{RECIPIENT_SCOPE}\n"
        f"\t\tscope:{SOURCE_SCOPE} = {{ is_ai = yes }}\n"
        f"\t\tscope:{RECIPIENT_SCOPE} = {{ is_ai = no }}\n"
        f"\t\tscope:{SOURCE_SCOPE} != scope:{RECIPIENT_SCOPE}\n"
        f"\t\tNOT = {{ global_var:{GENERATE_GUARD} = 1 }}\n"
        "\t}\n"
        "\tset_global_variable = {\n"
        f"\t\tname = {GENERATE_GUARD}\n"
        "\t\tvalue = 1\n"
        "\t}\n"
        f"\tscope:{SOURCE_SCOPE} = {{\n"
        "\t\trun_interaction = {\n"
        f"\t\t\tinteraction = {EXPECTED_INTERACTION_KEY}\n"
        f"\t\t\tactor = scope:{SOURCE_SCOPE}\n"
        f"\t\t\trecipient = scope:{RECIPIENT_SCOPE}\n"
        "\t\t\tsend_threshold = decline\n"
        "\t\t}\n"
        "\t}\n"
        f'\tdebug_log = "{GENERATE_MARKER}"\n'
        "}\n"
    )


def _effect_contract() -> dict[str, object]:
    switch = _switch_effect()
    generate = _generate_effect()
    folded = (switch + generate).casefold()
    checks = {
        "switch_before_generation_is_separate": (
            "set_player_character" in switch
            and "run_interaction" not in switch
            and "set_player_character" not in generate
        ),
        "live_source_anchor": (
            f"province:{SOURCE_ANCHOR_PROVINCE_ID}" in generate
            and f"save_temporary_scope_as = {SOURCE_SCOPE}" in generate
            and f"character:{SOURCE_CHARACTER_ID}" not in generate
        ),
        "live_recipient_anchor": (
            f"province:{RECIPIENT_ANCHOR_PROVINCE_ID}" in generate
            and f"character:{RECIPIENT_CHARACTER_ID}" not in generate
        ),
        "npc_actor_and_human_recipient_before_send": (
            f"scope:{SOURCE_SCOPE} = {{ is_ai = yes }}" in generate
            and f"scope:{RECIPIENT_SCOPE} = {{ is_ai = no }}" in generate
        ),
        "fixture_run_interaction": (
            "run_interaction = {" in generate
            and f"scope:{SOURCE_SCOPE} = {{\n\t\trun_interaction = {{"
            in generate
            and f"interaction = {EXPECTED_INTERACTION_KEY}" in generate
            and "send_threshold = decline" in generate
        ),
        "no_fixture_gameplay_mutation": all(
            token not in folded
            for token in (
                "set_employer",
                "set_relation",
                "remove_guardian_effect",
                "grant_independence",
                "trigger_event",
                "send_interface",
            )
        ),
        "definition_contract_ready": (
            _fixture_definition_contract().get("ok") is True
        ),
        "no_religion_semantics": all(
            token not in folded for token in _RELIGION_TOKENS
        ),
    }
    return {"checks": checks, "ok": all(checks.values())}



def _capture_log_evidence(spec: Any) -> dict[str, object]:
    evidence: dict[str, object] = {}
    marker_names = (
        SWITCH_MARKER,
        GENERATE_MARKER,
        FIXTURE_ON_AUTO_ACCEPT_MARKER,
        FIXTURE_ON_ACCEPT_MARKER,
    )
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
        text = raw.decode("utf-8", errors="replace")
        selected: list[str] = []
        for line in text.splitlines():
            folded = line.casefold()
            if any(marker in line for marker in marker_names) or any(
                token in folded
                for token in (
                    EXPECTED_INTERACTION_KEY.casefold(),
                    "duplicate",
                    "run_interaction",
                )
            ):
                selected.append(line)
        evidence[name] = {
            "path": str(path.resolve()),
            "present": True,
            "size": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest().upper(),
            "selected_lines": selected[-200:],
        }
    debug_lines = _mapping(evidence.get("debug.log")).get("selected_lines")
    rows = debug_lines if isinstance(debug_lines, list) else []
    evidence["marker_observations"] = {
        marker: any(isinstance(line, str) and marker in line for line in rows)
        for marker in marker_names
    }
    return evidence


def _played_character_id(snapshot: object) -> int | None:
    return pending_live._played_character_id(snapshot)


def _pending_identity(snapshot: object) -> dict[str, object] | None:
    return pending_live._pending_identity(snapshot)


def _snapshot_revision(snapshot: dict[str, object]) -> int:
    return pending_live._snapshot_revision(snapshot)


def _snapshot_native_revision(snapshot: dict[str, object]) -> int:
    return pending_live._snapshot_native_revision(snapshot)


def _snapshot_date(snapshot: dict[str, object]) -> int:
    return pending_live._snapshot_date(snapshot)


def _assert_paused_map_ready(snapshot: dict[str, object]) -> None:
    pending_live._assert_paused_map_ready(snapshot)


def _compact_snapshot(snapshot: object) -> object:
    compact = pending_live._compact_snapshot(snapshot)
    if isinstance(compact, dict):
        compact.pop("fixed_war", None)
    return compact


def _wait_for_switch(
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
            debug_log, SWITCH_MARKER, offset=log_offset
        )
        candidate = service.snapshot()
        if marker_observed and _pending_identity(candidate) is not None:
            raise AgentError(
                "recipient already had a pending interaction before generation"
            )
        if (
            marker_observed
            and _played_character_id(candidate) == RECIPIENT_CHARACTER_ID
            and candidate.get("date_raw") == expected_date_raw
            and candidate.get("paused") is True
            and candidate.get("map_ready") is True
        ):
            return candidate, True
        if session_done.is_set():
            raise AgentError(
                str(
                    session_state.get("error")
                    or "seed session ended before recipient switch"
                )
            )
        time.sleep(0.05)
    raise AgentError("mod_bridge did not switch the recipient on the same day")


def _wait_for_notification(
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
        pending = _pending_identity(candidate)
        if pending is not None and pending.get("auto_accept_notification") is False:
            raise AgentError(
                "ordinary pending appeared; it cannot stand in for notification"
            )
        if (
            marker_observed
            and _played_character_id(candidate) == RECIPIENT_CHARACTER_ID
            and candidate.get("date_raw") == expected_date_raw
            and candidate.get("paused") is True
            and candidate.get("map_ready") is True
            and pending is not None
            and pending.get("sender_character_id") == SOURCE_CHARACTER_ID
            and pending.get("auto_accept_notification") is True
        ):
            return candidate, True
        if session_done.is_set():
            raise AgentError(
                str(
                    session_state.get("error")
                    or "seed session ended before notification appeared"
                )
            )
        time.sleep(0.05)
    raise AgentError(
        "seed interaction did not materialize an auto_accept_notification"
    )


def _capability_proof(
    capabilities: object,
    *,
    notification_present: bool,
) -> dict[str, object]:
    raw = _mapping(capabilities)
    advertised_value = raw.get("bridge_capabilities")
    advertised = advertised_value if isinstance(advertised_value, list) else []
    diagnostics = pending_live._diagnostics(raw)
    hello_value = diagnostics.get("hello")
    hello = hello_value if isinstance(hello_value, dict) else {}
    hello_caps_value = hello.get("capabilities")
    hello_caps = hello_caps_value if isinstance(hello_caps_value, list) else []
    action_value = raw.get("action_steps")
    actions = action_value if isinstance(action_value, list) else []
    required = {
        QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_CAPABILITY,
        ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_CAPABILITY,
    }
    checks = {
        "bridge_capabilities": required.issubset(set(advertised)),
        "hello_capabilities": required.issubset(set(hello_caps)),
        "query_surface": raw.get(
            "pending_character_interaction_context_v1_query_supported"
        )
        is True,
        "notification_action_projection": (
            ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP in actions
            and QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP in actions
            and not any(
                step in actions for step in _FORBIDDEN_NORMAL_REPLY_STEPS
            )
            if notification_present
            else ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP not in actions
        ),
    }
    return {
        "notification_present": notification_present,
        "required_bridge_capabilities": sorted(required),
        "checks": checks,
        "ok": all(checks.values()),
    }


def _structured_terms_proof(terms: object) -> dict[str, object]:
    raw = _mapping(terms)
    costs = _mapping(raw.get("structured_costs"))
    other_keys = (
        "structured_exchanges",
        "structured_effect_preview",
        "recipient_ai_acceptance_score",
        "recipient_ai_final_decision",
    )
    other_unavailable = all(
        isinstance(raw.get(key), dict)
        and _mapping(raw[key]).get("status") == "unavailable"
        and _mapping(raw[key]).get("value") is None
        for key in other_keys
    )
    costs_status = costs.get("status")
    costs_truthful = bool(
        costs_status == "unavailable" and costs.get("value") is None
        or costs_status == "available" and costs.get("value") is not None
    )
    checks = {
        "special_data_presence_is_typed": isinstance(
            raw.get("special_data_present"), bool
        ),
        "generic_costs_are_explicit": costs_truthful,
        "unclosed_terms_remain_unavailable": other_unavailable,
    }
    return {
        "structured_costs_status": costs_status,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _notification_context_proof(
    result: object,
    *,
    pending_id: int,
    native_revision: int,
    date_raw: int,
) -> dict[str, object]:
    envelope = _mapping(result)
    frame = _mapping(envelope.get("pending_character_interaction_context"))
    definition = _mapping(frame.get("definition"))
    roles = _mapping(frame.get("roles"))
    target = _mapping(frame.get("target"))
    options = _mapping(frame.get("send_options"))
    rows_value = options.get("rows")
    rows = rows_value if isinstance(rows_value, list) else []
    routing = _mapping(frame.get("routing"))
    deadline = _mapping(frame.get("deadline"))
    auto_accept = _mapping(frame.get("auto_accept"))
    legality = _mapping(frame.get("legality"))
    terms = _mapping(frame.get("terms"))
    readiness = _mapping(frame.get("readiness"))
    binding = _mapping(envelope.get("binding"))
    terms_proof = _structured_terms_proof(terms)

    legality_available = all(
        isinstance(legality.get(key), dict)
        and _mapping(legality[key]).get("status") == "available"
        for key in ("accept", "reject", "block", "acknowledge")
    )
    normal_replies_closed = all(
        _mapping(legality.get(key)).get("allowed") is False
        and _mapping(legality.get(key)).get("reason")
        == "auto_accept_notification_channel"
        for key in ("accept", "reject", "block")
    )
    acknowledge_open = bool(
        _mapping(legality.get("acknowledge")).get("allowed") is True
        and _mapping(legality.get("acknowledge")).get("reason") is None
    )
    ready_keys = (
        "stable_definition_ready",
        "roles_ready",
        "target_type_key_ready",
        "send_options_ready",
        "routing_ready",
        "deadline_ready",
        "auto_accept_ready",
        "reply_legality_ready",
        "same_frame_ready",
    )
    costs_status = terms_proof.get("structured_costs_status")
    generic_costs_gate = readiness.get("generic_costs_ready")
    generic_costs_consistent = (
        generic_costs_gate is None
        or generic_costs_gate is (costs_status == "available")
    )
    checks = {
        "typed_available": envelope.get("status") == "available"
        and frame.get("status") == "available"
        and frame.get("reason") is None,
        "exact_scope": envelope.get("step")
        == QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP
        and envelope.get("accepted") is True
        and envelope.get("scope")
        == "exact-pending-character-interaction-context",
        "snapshot_binding": frame.get("snapshot_revision")
        == native_revision
        and frame.get("date_raw") == date_raw
        and frame.get("pending_interaction_id") == pending_id
        and envelope.get("snapshot_revision") == native_revision
        and binding.get("native_revision") == native_revision
        and binding.get("date_raw") == date_raw
        and binding.get("pending_interaction_id") == pending_id,
        "exact_build": frame.get("build")
        == {
            "version": PENDING_CHARACTER_INTERACTION_CONTEXT_V1_GAME_VERSION,
            "exe_sha256": (
                PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
            ),
        },
        "canonical_nonreligious_definition": definition.get("canonical_key")
        == EXPECTED_INTERACTION_KEY
        and isinstance(definition.get("deterministic_key_hash"), int)
        and not isinstance(definition.get("deterministic_key_hash"), bool)
        and isinstance(definition.get("runtime_ordinal"), int)
        and not isinstance(definition.get("runtime_ordinal"), bool),
        "exact_roles": roles
        == {
            "actor_character_id": SOURCE_CHARACTER_ID,
            "recipient_character_id": RECIPIENT_CHARACTER_ID,
            "secondary_actor_character_id": -1,
            "secondary_recipient_character_id": -1,
            "intermediary_character_id": -1,
        },
        "no_target": target.get("present") is False
        and target.get("type_key_status") == "absent"
        and target.get("typed_identity_status") == "absent",
        "zero_send_options": options.get("exclusive") is True
        and options.get("definition_count") == 0
        and options.get("context_count") == 0
        and rows == [],
        "recipient_notification_route": routing
        == {
            "kind": 0,
            "played_character_id": RECIPIENT_CHARACTER_ID,
            "current_responder_role": "recipient",
            "reply_execution_channel": "recipient",
            "local_route": True,
            "auto_accept_notification": True,
        },
        "fresh_deadline": deadline.get("age_days") == 0
        and isinstance(deadline.get("expiration_days"), int)
        and not isinstance(deadline.get("expiration_days"), bool)
        and deadline.get("expiration_days", 0) > 0
        and deadline.get("remaining_days") == deadline.get("expiration_days")
        and deadline.get("expiry_boundary_status") == "not_reached",
        "auto_accept_true": auto_accept
        == {"status": "available", "value": True, "reason": None},
        "acknowledge_only_legality": legality_available
        and normal_replies_closed
        and acknowledge_open,
        "terms_are_truthful": terms_proof.get("ok") is True,
        "partial_readiness": all(
            readiness.get(key) is True for key in ready_keys
        )
        and readiness.get("interaction_semantic_decision_ready") is False
        and envelope.get("pending_character_interaction_context_ready")
        is False
        and generic_costs_consistent,
    }
    return {
        "definition": copy.deepcopy(definition),
        "roles": copy.deepcopy(roles),
        "target": copy.deepcopy(target),
        "send_options": copy.deepcopy(options),
        "routing": copy.deepcopy(routing),
        "deadline": copy.deepcopy(deadline),
        "auto_accept": copy.deepcopy(auto_accept),
        "legality": copy.deepcopy(legality),
        "terms": copy.deepcopy(terms),
        "readiness": copy.deepcopy(readiness),
        "terms_proof": terms_proof,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _without_query_sequence(result: object) -> object:
    normalized = copy.deepcopy(result)
    if isinstance(normalized, dict):
        normalized.pop("query_sequence", None)
    return normalized


def _mutation_boundary_proof(commands: object) -> dict[str, object]:
    rows = commands if isinstance(commands, list) else []
    expected = [
        QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
        QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP,
        ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP,
    ]
    normal_replies = [
        step for step in rows if step in _FORBIDDEN_NORMAL_REPLY_STEPS
    ]
    checks = {
        "exact_query_query_ack": rows == expected,
        "one_fixed_ack": rows.count(
            ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP
        )
        == 1,
        "no_normal_reply": normal_replies == [],
        "no_auto_turn": "auto-turn" not in rows,
    }
    return {
        "commands": list(rows),
        "expected_commands": expected,
        "forbidden_normal_reply_steps_observed": normal_replies,
        "checks": checks,
        "ok": all(checks.values()),
    }


def _run_query_ack_sequence(
    service: GameplayBridgeService,
    *,
    expected_pending_id: int,
    expected_date_raw: int,
) -> dict[str, object]:
    commands: list[str] = []
    before = service.snapshot()
    _assert_paused_map_ready(before)
    pending = _pending_identity(before)
    if _played_character_id(before) != RECIPIENT_CHARACTER_ID:
        raise RuntimeError("production ACK did not bind recipient CharacterID")
    if pending is None or pending.get("instance_id") != expected_pending_id:
        raise RuntimeError("production ACK did not restore the full pending ID")
    if pending.get("sender_character_id") != SOURCE_CHARACTER_ID:
        raise RuntimeError("production ACK restored a different sender")
    if pending.get("auto_accept_notification") is not True:
        raise RuntimeError("production ACK restored an ordinary pending request")
    revision = _snapshot_revision(before)
    native_revision = _snapshot_native_revision(before)
    date_raw = _snapshot_date(before)
    if date_raw != expected_date_raw:
        raise RuntimeError("production cold reload changed the fixture date")

    first = service.query_pending_character_interaction_context_v1(
        expected_pending_id,
        expected_revision=revision,
    )
    commands.append(QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP)
    between = service.snapshot()
    second = service.query_pending_character_interaction_context_v1(
        expected_pending_id,
        expected_revision=revision,
    )
    commands.append(QUERY_PENDING_CHARACTER_INTERACTION_CONTEXT_V1_STEP)
    after_queries = service.snapshot()

    first_proof = _notification_context_proof(
        first,
        pending_id=expected_pending_id,
        native_revision=native_revision,
        date_raw=date_raw,
    )
    second_proof = _notification_context_proof(
        second,
        pending_id=expected_pending_id,
        native_revision=native_revision,
        date_raw=date_raw,
    )
    if first_proof.get("ok") is not True or second_proof.get("ok") is not True:
        raise RuntimeError("notification typed context proof failed")

    ack = service.acknowledge_pending_character_interaction(
        interaction_instance_id=expected_pending_id,
        expected_revision=revision,
    )
    commands.append(ACKNOWLEDGE_PENDING_CHARACTER_INTERACTION_STEP)
    after_ack = service.snapshot()
    remaining = _pending_identity(after_ack)
    interaction_result = _mapping(ack.get("interaction_result"))
    result_remaining = ack.get("remaining_pending_character_interaction")
    result_remaining_id = (
        result_remaining.get("instance_id")
        if isinstance(result_remaining, dict)
        else None
    )
    mutation = _mutation_boundary_proof(commands)
    first_sequence = first.get("query_sequence")
    second_sequence = second.get("query_sequence")
    first_frame = first.get("pending_character_interaction_context")
    second_frame = second.get("pending_character_interaction_context")
    old_id_gone = bool(
        remaining is None or remaining.get("instance_id") != expected_pending_id
    )
    result_old_id_gone = bool(
        result_remaining_id is None
        or result_remaining_id != expected_pending_id
    )
    checks = {
        "initial_notification_exact": pending
        == {
            "instance_id": expected_pending_id,
            "sender_character_id": SOURCE_CHARACTER_ID,
            "auto_accept_notification": True,
        },
        "between_same_paused_binding": pending_live._same_paused_binding(
            before, between
        ),
        "after_queries_same_paused_binding": pending_live._same_paused_binding(
            before, after_queries
        ),
        "two_contexts_valid": first_proof.get("ok") is True
        and second_proof.get("ok") is True,
        "query_sequence_exact_successor": isinstance(first_sequence, int)
        and not isinstance(first_sequence, bool)
        and first_sequence > 0
        and isinstance(second_sequence, int)
        and not isinstance(second_sequence, bool)
        and second_sequence == first_sequence + 1,
        "adjacent_frames_equal": isinstance(first_frame, dict)
        and first_frame == second_frame,
        "only_query_sequence_changed": _without_query_sequence(first)
        == _without_query_sequence(second),
        "fixed_ack_result": ack.get("acknowledged") is True
        and ack.get("interaction_instance_id") == expected_pending_id
        and interaction_result.get("status") == "acknowledged"
        and interaction_result.get("instance_id") == expected_pending_id,
        "old_full_id_gone_from_driver_result": result_old_id_gone,
        "old_full_id_gone_from_fresh_snapshot": old_id_gone,
        "post_ack_paused_same_day_recipient": after_ack.get("paused") is True
        and after_ack.get("map_ready") is True
        and _played_character_id(after_ack) == RECIPIENT_CHARACTER_ID
        and _snapshot_date(after_ack) == date_raw,
        "post_ack_snapshot_advanced": after_ack.get("snapshot_id")
        != before.get("snapshot_id")
        or after_ack.get("native_revision") != native_revision,
        "exact_mutation_boundary": mutation.get("ok") is True,
    }
    return {
        "expected_revision": revision,
        "native_revision": native_revision,
        "date_raw": date_raw,
        "pending_interaction_id": expected_pending_id,
        "pending_slot": expected_pending_id & 0x00FF_FFFF,
        "pending_generation": expected_pending_id >> 24,
        "before": _compact_snapshot(before),
        "between": _compact_snapshot(between),
        "after_queries": _compact_snapshot(after_queries),
        "after_ack": _compact_snapshot(after_ack),
        "first_query": copy.deepcopy(first),
        "second_query": copy.deepcopy(second),
        "first_context_proof": first_proof,
        "second_context_proof": second_proof,
        "context_sha256": _canonical_json_sha256(first_frame),
        "ack_result": copy.deepcopy(ack),
        "mutation_boundary": mutation,
        "commands": commands,
        "checks": checks,
        "ok": all(checks.values()),
    }


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
    readiness: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    exact_binary: dict[str, object] | None = None
    capability_before: dict[str, object] | None = None
    capability_after: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    initial: dict[str, object] | None = None
    switched: dict[str, object] | None = None
    generated: dict[str, object] | None = None
    stable: dict[str, object] | None = None
    after_save: dict[str, object] | None = None
    save_result: dict[str, object] | None = None
    checkpoint: dict[str, object] | None = None
    switch_write: dict[str, object] | None = None
    switch_noop: dict[str, object] | None = None
    generate_write: dict[str, object] | None = None
    final_noop: dict[str, object] | None = None
    switch_marker_observed = False
    generate_marker_observed = False
    on_auto_accept_marker_observed = False
    on_accept_marker_observed = False
    switch_polls: list[dict[str, object]] = []
    notification_polls: list[dict[str, object]] = []
    log_evidence: dict[str, object] | None = None
    primary_error: str | None = None
    executable_sha256: str | None = None
    dll_sha256: str | None = None
    injector_sha256: str | None = None
    fixture_projection = _fixture_projection_proof(spec, seed_stage=True)

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
        if fixture_projection.get("ok") is not True:
            raise AgentError("seed clone lacks the exact fixture playset")
        executable_sha256 = _sha256_file(spec.game_exe)
        dll_sha256 = _sha256_file(config.dll_path)
        injector_sha256 = _sha256_file(config.injector_path)
        if (
            executable_sha256
            != PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
        ):
            raise RuntimeError("managed CK3 executable SHA-256 differs")
        if dll_sha256 != expected_dll_sha256:
            raise RuntimeError("production bridge DLL SHA-256 differs")
        if injector_sha256 != FROZEN_ACK_INJECTOR_SHA256:
            raise RuntimeError("frozen ACK injector SHA-256 differs")
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-notification-ack-seed-session",
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
        source_war = pending_live._source_war_proof(initial)
        if source_war.get("ok") is not True:
            raise AgentError("immutable source scenario identity differs")
        if _pending_identity(initial) is not None:
            raise AgentError("immutable source unexpectedly has a pending request")

        capabilities_before = driver.capabilities()
        exact_binary = pending_live._exact_binary_proof(
            capabilities_before,
            executable_sha256=executable_sha256,
            dll_sha256=dll_sha256,
            expected_dll_sha256=expected_dll_sha256,
        )
        capability_before = _capability_proof(
            capabilities_before, notification_present=False
        )
        if exact_binary.get("ok") is not True:
            raise RuntimeError("seed exact EXE/DLL proof failed")
        if capability_before.get("ok") is not True:
            raise RuntimeError("seed bridge ACK capabilities are incomplete")

        initial_date = _snapshot_date(initial)
        debug_log = spec.profile_dir / "logs" / "debug.log"
        switch_offset = owner_live._debug_log_offset(debug_log)
        switch_write = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), _switch_effect()
        )
        switched, switch_marker_observed = _wait_for_switch(
            service,
            debug_log=debug_log,
            log_offset=switch_offset,
            expected_date_raw=initial_date,
            deadline=time.monotonic() + seed_timeout,
            session_done=session_done,
            session_state=session_state,
        )
        switch_noop = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), SEED_NOOP_INBOX
        )
        poll_driver = DataModGameplayDriver(
            spec.profile_dir,
            request_timeout_seconds=seed_timeout,
            poll_interval_seconds=0.05,
        )
        switch_polls = [
            poll_driver.take_snapshot(),
            poll_driver.take_snapshot(),
        ]
        if (
            len({row.get("request_id") for row in switch_polls}) != 2
            or any(
                row.get("player_id") != RECIPIENT_CHARACTER_ID
                for row in switch_polls
            )
            or switch_polls[0].get("total_days")
            != switch_polls[1].get("total_days")
        ):
            raise AgentError("post-switch mod_bridge polls were not stable")
        switched = service.snapshot()
        if (
            _played_character_id(switched) != RECIPIENT_CHARACTER_ID
            or _snapshot_date(switched) != initial_date
            or _pending_identity(switched) is not None
        ):
            raise AgentError("recipient binding drifted before generation")

        generate_offset = owner_live._debug_log_offset(debug_log)
        generate_write = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), _generate_effect()
        )
        generated, generate_marker_observed = _wait_for_notification(
            service,
            debug_log=debug_log,
            log_offset=generate_offset,
            expected_date_raw=initial_date,
            deadline=time.monotonic() + seed_timeout,
            session_done=session_done,
            session_state=session_state,
        )
        on_auto_accept_marker_observed = owner_live._debug_marker_observed(
            debug_log, FIXTURE_ON_AUTO_ACCEPT_MARKER, offset=generate_offset
        )
        on_accept_marker_observed = owner_live._debug_marker_observed(
            debug_log, FIXTURE_ON_ACCEPT_MARKER, offset=generate_offset
        )
        if not (on_auto_accept_marker_observed and on_accept_marker_observed):
            raise AgentError(
                "fixture diagnostic handlers did not both execute"
            )
        pending_before = _pending_identity(generated)
        if pending_before is None:
            raise AgentError("generated notification lacks a full pending ID")
        final_noop = owner_live._write_seed_inbox(
            owner_live._seed_inbox_path(spec), SEED_NOOP_INBOX
        )
        notification_polls = [
            poll_driver.take_snapshot(),
            poll_driver.take_snapshot(),
        ]
        if (
            len({row.get("request_id") for row in notification_polls}) != 2
            or any(
                row.get("player_id") != RECIPIENT_CHARACTER_ID
                for row in notification_polls
            )
            or notification_polls[0].get("total_days")
            != notification_polls[1].get("total_days")
        ):
            raise AgentError("post-notification mod_bridge polls were not stable")
        stable = service.snapshot()
        if (
            _played_character_id(stable) != RECIPIENT_CHARACTER_ID
            or _snapshot_date(stable) != initial_date
            or _pending_identity(stable) != pending_before
        ):
            raise AgentError("notification identity drifted before checkpoint")

        save_result = service.save_checkpoint(
            expected_revision=_snapshot_revision(stable)
        )
        checkpoint = owner_live._checkpoint_identity(
            owner_live._checkpoint_path(spec)
        )
        after_save = service.snapshot()
        if (
            _played_character_id(after_save) != RECIPIENT_CHARACTER_ID
            or _snapshot_date(after_save) != initial_date
            or _pending_identity(after_save) != pending_before
        ):
            raise AgentError("checkpoint save changed the notification")

        capabilities_after = driver.capabilities()
        capability_after = _capability_proof(
            capabilities_after, notification_present=True
        )
        same_process = pending_live._same_process_proof(
            capabilities_before, capabilities_after
        )
        if capability_after.get("ok") is not True:
            raise RuntimeError("seed notification did not publish ACK action")
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
            final_markers = _mapping(
                _mapping(log_evidence).get("marker_observations")
            )
            switch_marker_observed = bool(
                switch_marker_observed
                or final_markers.get(SWITCH_MARKER) is True
            )
            generate_marker_observed = bool(
                generate_marker_observed
                or final_markers.get(GENERATE_MARKER) is True
            )
            on_auto_accept_marker_observed = bool(
                on_auto_accept_marker_observed
                or final_markers.get(FIXTURE_ON_AUTO_ACCEPT_MARKER) is True
            )
            on_accept_marker_observed = bool(
                on_accept_marker_observed
                or final_markers.get(FIXTURE_ON_ACCEPT_MARKER) is True
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
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            session_state.get("error")
            or cleanup.get("reason")
            or "seed managed cleanup was not proven"
        )
    pending = _pending_identity(stable if stable is not None else generated)
    return {
        "stage": "seed-switch-generate-save-notification",
        "session_started": session_started,
        "production_native_bridge": True,
        "stock_or_production_only_playset": False,
        "fixture_definition_playset": True,
        "seed_only_mod_bridge": True,
        "fixture_definition_loaded": True,
        "debug_mode": False,
        "ok": bool(
            primary_error is None
            and fixture_projection.get("ok") is True
            and exact_binary
            and exact_binary.get("ok") is True
            and capability_before
            and capability_before.get("ok") is True
            and capability_after
            and capability_after.get("ok") is True
            and switch_marker_observed
            and generate_marker_observed
            and on_auto_accept_marker_observed
            and on_accept_marker_observed
            and pending is not None
            and pending.get("auto_accept_notification") is True
            and pending.get("sender_character_id") == SOURCE_CHARACTER_ID
            and checkpoint is not None
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
        "fixture_projection_proof": fixture_projection,
        "readiness": readiness,
        "exact_binary_proof": exact_binary,
        "capability_before": capability_before,
        "capability_after": capability_after,
        "same_process_proof": same_process,
        "initial_snapshot": _compact_snapshot(initial),
        "switched_snapshot": _compact_snapshot(switched),
        "generated_snapshot": _compact_snapshot(generated),
        "stable_pre_save_snapshot": _compact_snapshot(stable),
        "post_save_snapshot": _compact_snapshot(after_save),
        "pending_identity": pending,
        "fixture_handler_diagnostics": {
            "on_auto_accept_marker": FIXTURE_ON_AUTO_ACCEPT_MARKER,
            "on_auto_accept_observed": on_auto_accept_marker_observed,
            "on_accept_marker": FIXTURE_ON_ACCEPT_MARKER,
            "on_accept_observed": on_accept_marker_observed,
            "gameplay_state_mutators_authored": False,
            "ok": on_auto_accept_marker_observed
            and on_accept_marker_observed,
        },
        "save_result": save_result,
        "checkpoint": checkpoint,
        "seed_protocol": {
            "switch_marker": SWITCH_MARKER,
            "switch_marker_observed": switch_marker_observed,
            "generation_marker": GENERATE_MARKER,
            "generation_marker_observed": generate_marker_observed,
            "on_auto_accept_marker": FIXTURE_ON_AUTO_ACCEPT_MARKER,
            "on_auto_accept_marker_observed": (
                on_auto_accept_marker_observed
            ),
            "on_accept_marker": FIXTURE_ON_ACCEPT_MARKER,
            "on_accept_marker_observed": on_accept_marker_observed,
            "switch_write": switch_write,
            "switch_noop": switch_noop,
            "generate_write": generate_write,
            "final_noop": final_noop,
            "post_switch_frames": switch_polls,
            "post_notification_frames": notification_polls,
        },
        "log_evidence": log_evidence,
        "session": _compact_session_report(session_state.get("report")),
        "cleanup": cleanup,
        "error": primary_error,
    }


def _run_production_ack_stage(
    *,
    spec: Any,
    config: NativeBridgeLaunchConfig,
    expected_dll_sha256: str,
    expected_pending_id: int,
    expected_date_raw: int,
    timeout: float,
    readiness_timeout: float,
    postcondition_timeout: float,
) -> dict[str, object]:
    stop_event = threading.Event()
    session_done = threading.Event()
    session_state: dict[str, object] = {"report": None, "error": None}
    driver: NativeHeadlessGameplayDriver | None = None
    thread: threading.Thread | None = None
    session_started = False
    driver_closed = False
    readiness: dict[str, object] | None = None
    capabilities_before: dict[str, object] | None = None
    capabilities_after: dict[str, object] | None = None
    exact_binary: dict[str, object] | None = None
    capability: dict[str, object] | None = None
    same_process: dict[str, object] | None = None
    sequence: dict[str, object] | None = None
    projection = _fixture_projection_proof(spec, seed_stage=False)
    primary_error: str | None = None
    executable_sha256: str | None = None
    dll_sha256: str | None = None
    injector_sha256: str | None = None

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
            raise AgentError(
                "fresh ACK clone lacks the exact definition-only fixture playset"
            )
        executable_sha256 = _sha256_file(spec.game_exe)
        dll_sha256 = _sha256_file(config.dll_path)
        injector_sha256 = _sha256_file(config.injector_path)
        if (
            executable_sha256
            != PENDING_CHARACTER_INTERACTION_CONTEXT_V1_EXECUTABLE_SHA256
        ):
            raise RuntimeError("managed CK3 executable SHA-256 differs")
        if dll_sha256 != expected_dll_sha256:
            raise RuntimeError("production bridge DLL SHA-256 differs")
        if injector_sha256 != FROZEN_ACK_INJECTOR_SHA256:
            raise RuntimeError("frozen ACK injector SHA-256 differs")
        driver = NativeHeadlessGameplayDriver(
            config.pipe_name,
            command_timeout_seconds=postcondition_timeout,
            state_dir=spec.state_dir,
            save_dir=spec.profile_dir / "save games",
        )
        service = GameplayBridgeService(driver)
        thread = threading.Thread(
            target=supervise,
            name="xar-notification-fixture-query-ack",
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
        exact_binary = pending_live._exact_binary_proof(
            capabilities_before,
            executable_sha256=executable_sha256,
            dll_sha256=dll_sha256,
            expected_dll_sha256=expected_dll_sha256,
        )
        capability = _capability_proof(
            capabilities_before, notification_present=True
        )
        if exact_binary.get("ok") is not True:
            raise RuntimeError("production exact EXE/DLL proof failed")
        if capability.get("ok") is not True:
            raise RuntimeError("production query/ACK capabilities are incomplete")
        sequence = _run_query_ack_sequence(
            service,
            expected_pending_id=expected_pending_id,
            expected_date_raw=expected_date_raw,
        )
        if sequence.get("ok") is not True:
            raise RuntimeError("production query-query-ACK sequence failed")
        capabilities_after = driver.capabilities()
        same_process = pending_live._same_process_proof(
            capabilities_before, capabilities_after
        )
        if same_process.get("ok") is not True:
            raise RuntimeError("production sequence crossed bridge process")
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
            or "production managed cleanup was not proven"
        )
    return {
        "stage": "fresh-fixture-definition-cold-query-query-ack",
        "session_started": session_started,
        "fresh_process_cold_reload": True,
        "production_native_bridge": True,
        "production_only_playset": False,
        "fixture_definition_playset": True,
        "seed_mod_bridge_absent": True,
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
    production_stage: object,
    transfer: object,
) -> dict[str, object]:
    seed = _mapping(seed_stage)
    production = _mapping(production_stage)
    sequence = _mapping(production.get("sequence"))
    first = _mapping(sequence.get("first_query"))
    frame = _mapping(first.get("pending_character_interaction_context"))
    seed_pending = _mapping(seed.get("pending_identity"))
    seed_snapshot = _mapping(seed.get("stable_pre_save_snapshot"))
    seed_process = _mapping(seed.get("same_process_proof"))
    production_process = _mapping(production.get("same_process_proof"))
    seed_pid = seed_process.get("bridge_pid")
    production_pid = production_process.get("bridge_pid")
    checks = {
        "both_stages_green": seed.get("ok") is True
        and production.get("ok") is True,
        "checkpoint_bytes_transferred": _mapping(transfer).get("ok") is True,
        "distinct_positive_pids": isinstance(seed_pid, int)
        and not isinstance(seed_pid, bool)
        and seed_pid > 0
        and isinstance(production_pid, int)
        and not isinstance(production_pid, bool)
        and production_pid > 0
        and seed_pid != production_pid,
        "same_full_pending_id": seed_pending.get("instance_id")
        == sequence.get("pending_interaction_id")
        == frame.get("pending_interaction_id"),
        "notification_survived_cold_reload": seed_pending.get(
            "auto_accept_notification"
        )
        is True
        and _mapping(frame.get("routing")).get("auto_accept_notification")
        is True,
        "same_roles": seed_pending.get("sender_character_id")
        == SOURCE_CHARACTER_ID
        and _mapping(frame.get("roles")).get("actor_character_id")
        == SOURCE_CHARACTER_ID
        and _mapping(frame.get("roles")).get("recipient_character_id")
        == RECIPIENT_CHARACTER_ID,
        "same_game_date": seed_snapshot.get("date_raw")
        == sequence.get("date_raw")
        == frame.get("date_raw"),
        "canonical_nonreligious_fixture_key": _mapping(
            frame.get("definition")
        ).get("canonical_key")
        == EXPECTED_INTERACTION_KEY,
        "byte_identical_fixture_definition": _mapping(
            seed.get("fixture_projection_proof")
        ).get("definition_sha256")
        == _mapping(production.get("fixture_projection_proof")).get(
            "definition_sha256"
        )
        == _fixture_definition_contract().get("sha256"),
        "fixture_definition_ack_playset": _mapping(
            production.get("fixture_projection_proof")
        ).get("ok") is True,
        "old_full_id_gone": _mapping(sequence.get("checks")).get(
            "old_full_id_gone_from_driver_result"
        )
        is True
        and _mapping(sequence.get("checks")).get(
            "old_full_id_gone_from_fresh_snapshot"
        )
        is True,
    }
    return {
        "seed_bridge_pid": seed_pid,
        "production_bridge_pid": production_pid,
        "pending_interaction_id": seed_pending.get("instance_id"),
        "pending_slot": (
            int(seed_pending["instance_id"]) & 0x00FF_FFFF
            if isinstance(seed_pending.get("instance_id"), int)
            else None
        ),
        "pending_generation": (
            int(seed_pending["instance_id"]) >> 24
            if isinstance(seed_pending.get("instance_id"), int)
            else None
        ),
        "date_raw": seed_snapshot.get("date_raw"),
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
    postcondition_timeout = _positive_seconds(
        args.postcondition_timeout, "postcondition_timeout"
    )
    expected_source_sha = _canonical_sha256(
        args.expected_source_save_sha256,
        "expected source save SHA-256",
    )
    expected_dll_sha = _canonical_sha256(
        args.expected_bridge_dll_sha256,
        "expected bridge DLL SHA-256",
    )
    if expected_dll_sha != FROZEN_ACK_DLL_SHA256:
        raise AgentError(
            "live ACK must use the reviewed commit 70bf8e6 DLL: "
            f"{FROZEN_ACK_DLL_SHA256}"
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
    source_save: Path | None = None
    source_identity: dict[str, object] | None = None
    source_before: dict[str, object] | None = None
    source_after: dict[str, object] | None = None
    disposable: dict[str, object] | None = None
    seed_materialization: dict[str, object] | None = None
    production_materialization: dict[str, object] | None = None
    seed_stage: dict[str, object] | None = None
    production_stage: dict[str, object] | None = None
    transfer: dict[str, object] | None = None
    cross_stage: dict[str, object] | None = None
    primary_error: str | None = None
    nonce = uuid.uuid4().hex
    dependency_source = _dependency_source_contract()
    fixture_definition = _fixture_definition_contract()

    try:
        if dependency_source.get("ok") is not True:
            raise AgentError(
                "live ACK requires an isolated exact-commit dependency tree: "
                f"set {ISOLATED_SOURCE_ROOT_ENV} to commit "
                f"{FROZEN_ACK_SOURCE_COMMIT}"
            )
        if fixture_definition.get("ok") is not True:
            raise AgentError("fixture definition source contract differs")
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
        disposable = pending_live._prepare_root(
            root,
            source_profile=source_profile,
            source_save_sha256=expected_source_sha,
            nonce=nonce,
        )
        seed_spec, seed_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "seed-switch-generate-save-notification",
            game_dir=game_dir,
            save_source=source_save,
            save_name=CONTINUE_SAVE_NAME,
        )
        seed_materialization["fixture_bridge"] = owner_live._install_seed_bridge(
            seed_spec
        )
        seed_materialization["fixture_definition"] = (
            _install_fixture_definition(seed_spec)
        )
        if _effect_contract().get("ok") is not True:
            raise AgentError("seed notification source contract failed")
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
        seed_pending = _mapping(seed_stage.get("pending_identity"))
        pending_id = seed_pending.get("instance_id")
        if (
            isinstance(pending_id, bool)
            or not isinstance(pending_id, int)
            or not 1 <= pending_id <= 2**31 - 1
        ):
            raise AgentError("seed stage lacks a positive full pending ID")
        seed_snapshot = _mapping(seed_stage.get("stable_pre_save_snapshot"))
        expected_date_raw = seed_snapshot.get("date_raw")
        if isinstance(expected_date_raw, bool) or not isinstance(
            expected_date_raw, int
        ):
            raise AgentError("seed stage lacks a signed game date")
        seed_checkpoint = owner_live._checkpoint_path(seed_spec)

        production_spec, production_materialization = owner_live._prepare_stage(
            source_profile=source_profile,
            target_state=root / "fresh-fixture-cold-query-query-ack",
            game_dir=game_dir,
            save_source=seed_checkpoint,
            save_name=CONTINUE_SAVE_NAME,
        )
        production_materialization["fixture_definition"] = (
            _install_fixture_definition(production_spec)
        )
        transfer = pending_live._checkpoint_transfer_proof(
            seed_checkpoint, production_spec
        )
        if transfer.get("ok") is not True:
            raise AgentError("notification checkpoint transfer differs")
        production_stage = _run_production_ack_stage(
            spec=production_spec,
            config=config,
            expected_dll_sha256=expected_dll_sha,
            expected_pending_id=pending_id,
            expected_date_raw=expected_date_raw,
            timeout=timeout,
            readiness_timeout=readiness_timeout,
            postcondition_timeout=postcondition_timeout,
        )
        if production_stage.get("ok") is not True:
            raise AgentError(
                str(production_stage.get("error") or "production ACK stage failed")
            )
        cross_stage = _cross_stage_proof(
            seed_stage, production_stage, transfer
        )
        if cross_stage.get("ok") is not True:
            raise AgentError("notification changed across fixture cold reload")
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
    if not source_unchanged and primary_error is None:
        primary_error = "immutable source save changed"

    stages: list[object] = [seed_stage, production_stage]
    no_ck3_processes = not ck3_processes()
    cleanup = pending_live._cleanup_root(
        root,
        nonce=nonce,
        retain=bool(args.retain_state),
        stages=stages,
    )
    if not no_ck3_processes and primary_error is None:
        primary_error = "a CK3 process remains after managed stages"
    if cleanup.get("ok") is not True and primary_error is None:
        primary_error = str(
            cleanup.get("reason") or "disposable root cleanup failed"
        )

    production = _mapping(production_stage)
    sequence = _mapping(production.get("sequence"))
    sequence_checks = _mapping(sequence.get("checks"))
    first_proof = _mapping(sequence.get("first_context_proof"))
    context_checks = _mapping(first_proof.get("checks"))
    cross_checks = _mapping(_mapping(cross_stage).get("checks"))
    seed = _mapping(seed_stage)
    seed_protocol = _mapping(seed.get("seed_protocol"))
    seed_log_markers = _mapping(
        _mapping(seed.get("log_evidence")).get("marker_observations")
    )
    seed_binary = _mapping(seed.get("exact_binary_proof"))
    production_binary = _mapping(production.get("exact_binary_proof"))
    readiness_gates = {
        "fixture_definition_is_nonreligious_auto_notification": (
            fixture_definition.get("ok") is True
            and _effect_contract().get("ok") is True
        ),
        "recipient_human_before_send": seed_protocol.get(
            "switch_marker_observed"
        )
        is True
        and _mapping(seed.get("switched_snapshot")).get(
            "played_character_id"
        )
        == RECIPIENT_CHARACTER_ID,
        "generation_effect_reached_post_send_marker": seed_log_markers.get(
            GENERATE_MARKER
        )
        is True,
        "fixture_handlers_executed_without_gameplay_mutation": (
            seed_log_markers.get(FIXTURE_ON_AUTO_ACCEPT_MARKER) is True
            and seed_log_markers.get(FIXTURE_ON_ACCEPT_MARKER) is True
            and _mapping(seed.get("fixture_handler_diagnostics")).get("ok")
            is True
        ),
        "real_notification_materialized": _mapping(
            seed.get("pending_identity")
        ).get("auto_accept_notification")
        is True,
        "stable_full_id_across_fixture_cold_reload": cross_checks.get(
            "same_full_pending_id"
        )
        is True
        and cross_checks.get("notification_survived_cold_reload") is True,
        "byte_identical_fixture_definition_both_stages": cross_checks.get(
            "byte_identical_fixture_definition"
        ) is True,
        "fixture_definition_ack_stage": cross_checks.get(
            "fixture_definition_ack_playset"
        ) is True,
        "canonical_nonreligious_fixture_key": context_checks.get(
            "canonical_nonreligious_definition"
        )
        is True,
        "roles_routing_options_deadline_legalities": all(
            context_checks.get(key) is True
            for key in (
                "exact_roles",
                "no_target",
                "zero_send_options",
                "recipient_notification_route",
                "fresh_deadline",
                "auto_accept_true",
                "acknowledge_only_legality",
            )
        ),
        "adjacent_same_revision_double_query": all(
            sequence_checks.get(key) is True
            for key in (
                "between_same_paused_binding",
                "after_queries_same_paused_binding",
                "query_sequence_exact_successor",
                "adjacent_frames_equal",
                "only_query_sequence_changed",
            )
        ),
        "fixed_ack_old_full_id_gone": sequence_checks.get(
            "fixed_ack_result"
        )
        is True
        and sequence_checks.get("old_full_id_gone_from_driver_result") is True
        and sequence_checks.get("old_full_id_gone_from_fresh_snapshot") is True,
        "no_default_accept_reject_or_block": _mapping(
            sequence.get("mutation_boundary")
        ).get("ok")
        is True,
        "exact_exe_and_dll": seed_binary.get("ok") is True
        and production_binary.get("ok") is True,
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
        "kind": "ck3_pending_character_interaction_notification_ack_live_acceptance",
        "started_at": started_wall,
        "finished_at": utc_now(),
        "elapsed_seconds": round(max(0.0, time.monotonic() - started), 3),
        "ok": ok,
        "fixed_scenario": {
            "immutable_profile_player_character_id": (
                PROFILE_PLAYER_CHARACTER_ID
            ),
            "source_character_id": SOURCE_CHARACTER_ID,
            "source_anchor_province_id": SOURCE_ANCHOR_PROVINCE_ID,
            "recipient_character_id": RECIPIENT_CHARACTER_ID,
            "recipient_anchor_province_id": RECIPIENT_ANCHOR_PROVINCE_ID,
            "source_relation": "province:2619.owner before recipient switch",
            "interaction_key": EXPECTED_INTERACTION_KEY,
        },
        "policy": {
            "seed_native_bridge_is_production": True,
            "stock_definition_override_present": False,
            "fixture_definition_loaded_in_both_stages": True,
            "fixture_handlers_are_debug_log_only": True,
            "fixture_gameplay_side_effects_authored": False,
            "recipient_switch_precedes_interaction_send": True,
            "run_interaction_current_scope_is_actor": True,
            "run_interaction_uses_send_threshold_decline": True,
            "cold_ack_stage_has_no_mod_bridge_or_inbox": True,
            "cold_ack_playset_is_production_only": False,
            "production_native_bridge_in_both_stages": True,
            "normal_pending_cannot_substitute_for_notification": True,
            "fixed_ack_only": True,
            "religion_domain_deferred": True,
            "religion_specific_semantics_read": False,
        },
        "prior_red_attempts": [
            {
                "artifact": "artifacts/pending-notification-ack-70bf8e6-live.json",
                "artifact_sha256": (
                    PRIOR_EXECUTE_THRESHOLD_RED_ARTIFACT_SHA256
                ),
                "generation_threshold": "execute_threshold = accept",
                "result": "no pending notification materialized",
                "managed_cleanup": True,
            },
            {
                "artifact": (
                    "artifacts/pending-notification-ack-70bf8e6-live-attempt2.json"
                ),
                "artifact_sha256": (
                    PRIOR_OVERRIDE_COLD_RELOAD_RED_ARTIFACT_SHA256
                ),
                "generation_threshold": "send_threshold = decline",
                "result": (
                    "override notification materialized but did not survive "
                    "production-only cold reload"
                ),
                "seed_pending_interaction_id": 738_197_506,
                "managed_cleanup": True,
            },
            {
                "artifact": (
                    "artifacts/pending-notification-ack-70bf8e6-live-attempt3-stock.json"
                ),
                "artifact_sha256": PRIOR_STOCK_VALIDITY_RED_ARTIFACT_SHA256,
                "generation_threshold": "send_threshold = decline",
                "result": (
                    "stock relation was present but the full validity path "
                    "did not execute independence or materialize notification"
                ),
                "managed_cleanup": True,
            },
            {
                "artifact": (
                    "artifacts/pending-notification-ack-70bf8e6-live-attempt4-stock-validity.json"
                ),
                "artifact_sha256": PRIOR_STOCK_ROOT_SCOPE_RED_ARTIFACT_SHA256,
                "generation_threshold": "send_threshold = decline",
                "result": (
                    "all stock validity gates passed but recipient-root "
                    "run_interaction did not execute on_accept"
                ),
                "managed_cleanup": True,
            },
            {
                "artifact": (
                    "artifacts/pending-notification-ack-70bf8e6-live-attempt5-stock-actor-scope.json"
                ),
                "artifact_sha256": (
                    PRIOR_STOCK_ACTOR_SCOPE_RED_ARTIFACT_SHA256
                ),
                "generation_threshold": "send_threshold = decline",
                "result": (
                    "all validity gates passed; actor-scope send remained "
                    "blocked by stock ai_will_do base = 0"
                ),
                "managed_cleanup": True,
            },
            {
                "artifact": (
                    "artifacts/pending-notification-ack-70bf8e6-live-attempt6-stock-remove-guardian.json"
                ),
                "artifact_sha256": (
                    PRIOR_STOCK_REMOVE_GUARDIAN_RED_ARTIFACT_SHA256
                ),
                "generation_threshold": "send_threshold = decline",
                "result": (
                    "stock total and authored gates passed and on_accept "
                    "removed the guardian relation, but no notification "
                    "pending was observed"
                ),
                "managed_cleanup": True,
            },
        ],
        "frozen_ack_source_contract": {
            "commit": FROZEN_ACK_SOURCE_COMMIT,
            "bridge_dll_sha256": FROZEN_ACK_DLL_SHA256,
            "bridge_injector_sha256": FROZEN_ACK_INJECTOR_SHA256,
            "shared_dirty_source_used_for_build": False,
            "seed_and_cold_stage_use_same_fixture_definition": True,
            "fixture_definition_sha256": fixture_definition.get("sha256"),
            "fixture_definition_is_stock": False,
            "cold_playset_is_production_only": False,
        },
        "isolated_dependency_source": dependency_source,
        "fixture_definition_contract": fixture_definition,
        "fixture_effect_contract": _effect_contract(),
        "source_save": source_identity,
        "source_save_invariant": {
            "before": source_before,
            "after": source_after,
            "unchanged": source_unchanged,
        },
        "disposable": disposable,
        "seed_materialization": seed_materialization,
        "production_materialization": production_materialization,
        "checkpoint_transfer": transfer,
        "seed_stage": seed_stage,
        "production_stage": production_stage,
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
    cross_stage = _mapping(payload.get("cross_stage_proof"))
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
                "output": str(output),
                "artifact_sha256": _sha256_file(output),
                "pending_interaction_id": cross_stage.get(
                    "pending_interaction_id"
                ),
                "readiness_gates": payload.get("readiness_gates"),
                "cleanup": payload.get("disposable_cleanup"),
                "error": payload.get("error"),
            },
            ensure_ascii=False,
        )
    )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

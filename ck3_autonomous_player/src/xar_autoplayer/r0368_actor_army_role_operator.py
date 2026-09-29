"""R0368 role-only source gate and disabled same-session read-only collector.

The no-launch command only checks immutable source bytes. A future managed
session owner must explicitly open the live gate, provide a fresh paused frame,
and prove its own CK3 process cleanup before treating an inner result as live
evidence. This module has no CK3 launch or gameplay entry point.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Protocol

from .bridge.actor_army_role_private_transport import _binding
from .errors import AgentError


ROLE_ONLY_LIVE_AUTHORIZED = False
_SOURCE_COMMIT = "7457ef060cdfa1c943c86be619df02dbbb247dd0"
_PAIR_SHA256 = "798A3E8ADC055C39B170D2F37F2BC2074A7994882D078DFDACB74C73CF71149C"
_CANDIDATE_SHA256 = "1F0BB07ED5FABF89EA8E82CE8CC178388F22DC8BB35590AA045846E06FE89E25"
_ASSET_SHA256 = {
    "xar_checkpoint.ck3": "92A06F540E98A767D3E1DB95A6F3870674E0A7F084C2A14BD2D04D354E53DAF6",
    "driver-state.json": "2F0673EC4D0AFA2A77DE59FE9405EC032CF00F79D9484BBD3DC4361EC1311722",
    "player-child-matrilineal-formal-v1.json": "798F16F572FB83399CC9AB7ABD16561E87C47CEF7109CF23D255DAE660A8D8A7",
    "xar_ck3_bridge.dll": "F360FA9F55F1628A03CE111458983A67E769BB9E78BA85EA202CB819BA805425",
    "xar_ck3_bridge_injector.exe": "6EB871817A6861F431DB50759B2EC607B80E0DAE269A8B1B2610F98212355C01",
}
_NATIVE_PATHS = (
    "ck3_autonomous_player/native_bridge",
    "ck3_autonomous_player/src/xar_autoplayer/bridge/actor_army_role_private_transport.py",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _read_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise AgentError(f"R0368 expected JSON object: {path}")
    return value


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, text=True,
        check=True, timeout=30,
    )
    return completed.stdout.strip()


def verify_no_launch_source_pair(
    *, candidate_manifest: Path, release_pair_manifest: Path,
    checkout: Path,
) -> dict[str, object]:
    """Rehash the frozen checkpoint/driver/sidecar and Release DLL pair."""
    if ROLE_ONLY_LIVE_AUTHORIZED:
        raise AgentError("R0368 no-launch gate requires live authorization closed")
    candidate_sha = _sha256(candidate_manifest)
    pair_sha = _sha256(release_pair_manifest)
    if candidate_sha != _CANDIDATE_SHA256 or pair_sha != _PAIR_SHA256:
        raise AgentError("R0368 frozen candidate or Release pair manifest changed")
    candidate = _read_json(candidate_manifest)
    pair = _read_json(release_pair_manifest)
    if (candidate.get("status") != "SOURCE_BYTES_READY_SAME_FRAME_PENDING"
            or candidate.get("candidate_head") != _SOURCE_COMMIT
            or candidate.get("pair_manifest_sha256") != pair_sha
            or Path(str(candidate.get("pair_manifest_path"))).resolve()
            != release_pair_manifest.resolve()
            or candidate.get("candidate_army_id_is_current_same_frame") is not False
            or candidate.get("native_revision") is not None
            or candidate.get("public_army_row") is not None
            or candidate.get("allied_army_row") is not None
            or candidate.get("operator_enabled") is not False
            or pair.get("status") != "STATIC_GREEN_LIVE_PENDING"
            or pair.get("source_commit") != _SOURCE_COMMIT
            or pair.get("configuration") != "Release"
            or pair.get("cmake_option")
            != "XAR_CK3_ENABLE_WAR_ACTOR_ARMY_ROLE_PRIVATE_V1=ON"
            or pair.get("ctest", {}).get("junit_tests") != 173
            or pair.get("ctest", {}).get("junit_failures") != 0):
        raise AgentError("R0368 frozen source pair contract changed")
    files = candidate.get("files")
    if not isinstance(files, dict) or set(files) != set(_ASSET_SHA256):
        raise AgentError("R0368 frozen asset set changed")
    actual: dict[str, dict[str, object]] = {}
    for name, expected in _ASSET_SHA256.items():
        row = files[name]
        if not isinstance(row, dict):
            raise AgentError(f"R0368 asset manifest malformed: {name}")
        path = Path(str(row.get("path")))
        digest = _sha256(path)
        size = path.stat().st_size
        if digest != expected or row.get("sha256") != expected or row.get("bytes") != size:
            raise AgentError(f"R0368 source asset changed: {name}")
        actual[name] = {"path": str(path), "bytes": size, "sha256": digest}
    for name, key in (("xar_ck3_bridge.dll", "dll"),
                      ("xar_ck3_bridge_injector.exe", "injector")):
        release_row = pair.get(key)
        if (not isinstance(release_row, dict)
                or release_row.get("sha256") != actual[name]["sha256"]
                or _sha256(Path(str(release_row.get("path"))))
                != actual[name]["sha256"]):
            raise AgentError(f"R0368 Release {key} differs from frozen copy")
    exe = pair.get("ck3_executable")
    if (not isinstance(exe, dict) or exe.get("launched") is not False
            or _sha256(Path(str(exe.get("path")))) != exe.get("sha256")):
        raise AgentError("R0368 exact CK3 executable identity changed")
    root = checkout.resolve()
    head = _git(root, "rev-parse", "HEAD")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise AgentError("R0368 operator checkout is dirty")
    if _git(root, "diff", "--name-only", _SOURCE_COMMIT, head,
            "--", *_NATIVE_PATHS):
        raise AgentError("R0368 native source differs from Release pair")
    return {
        "schema": "xar.war.r0368.role-only-no-launch.v1",
        "status": "SOURCE_BYTES_READY_SAME_FRAME_PENDING",
        "candidate_manifest_sha256": candidate_sha,
        "release_pair_manifest_sha256": pair_sha,
        "checkout_head": head,
        "release_native_source_commit": _SOURCE_COMMIT,
        "exact_ck3_exe_sha256": exe["sha256"],
        "assets": actual,
        "candidate_episode_run_id": candidate.get("episode_run_id"),
        "candidate_actor_character_id": candidate.get("actor_character_id"),
        "candidate_war_id": candidate.get("candidate_war_id"),
        "candidate_army_id": candidate.get("candidate_public_army_id"),
        "current_paused_frame": None,
        "operator_enabled": False,
        "screen_acquired": False,
        "ck3_started": False,
        "query_attempts": 0,
        "gameplay_actions": 0,
        "date_advance_actions": 0,
    }


class RoleOnlyDriver(Protocol):
    allow_private_actor_army_role_query: bool

    def take_snapshot(self) -> dict[str, object]: ...

    def query_actor_army_role_private_v1(
        self, *, actor_character_id: int, public_army_id: int,
        expected_war_id: int, expected_episode_run_id: str,
        expected_revision: int,
    ) -> dict[str, object]: ...


def _fresh_target(
    frame: dict[str, object], *, actor: int, episode: str,
    war_id: int, army_id: int,
) -> bool:
    diagnostics = frame.get("diagnostics")
    player = frame.get("played_character")
    armies = frame.get("player_armies")
    wars = frame.get("active_wars")
    if not all(type(value) is int and 0 < value <= 2**31 - 1
               for value in (actor, war_id, army_id)):
        return False
    if not (isinstance(episode, str) and episode
            and isinstance(diagnostics, dict)
            and diagnostics.get("connected") is True
            and type(diagnostics.get("connection_generation")) is int
            and diagnostics["connection_generation"] > 0
            and type(diagnostics.get("bridge_pid")) is int
            and diagnostics["bridge_pid"] > 0
            and isinstance(diagnostics.get("hello"), dict)
            and frame.get("paused") is True
            and frame.get("map_ready") is True
            and frame.get("episode_run_id") == episode
            and frame.get("episode_character_id") == actor
            and type(frame.get("revision")) is int
            and type(frame.get("native_revision")) is int
            and frame["native_revision"] > 0
            and type(frame.get("date_raw")) is int
            and isinstance(player, dict)
            and player.get("character_id") == actor
            and player.get("alive") is True
            and isinstance(armies, list) and isinstance(wars, list)):
        return False
    own = [row for row in armies if isinstance(row, dict)
           and row.get("army_id") == army_id]
    war = [row for row in wars if isinstance(row, dict)
           and row.get("war_id") == war_id]
    if len(own) != 1 or own[0].get("owner_character_id") != actor or len(war) != 1:
        return False
    allies = war[0].get("allied_armies")
    if not isinstance(allies, list):
        return False
    allied = [row for row in allies if isinstance(row, dict)
              and row.get("army_id") == army_id]
    return len(allied) == 1 and allied[0].get("owner_character_id") == actor


def collect_role_only_in_managed_session(
    driver: RoleOnlyDriver, *, actor_character_id: int,
    episode_run_id: str, war_id: int, public_army_id: int,
) -> dict[str, object]:
    """One private query in an already owned session; never grants outer GREEN."""
    if ROLE_ONLY_LIVE_AUTHORIZED is not True:
        raise AgentError("R0368 role-only live gate is closed")
    if driver.allow_private_actor_army_role_query is not True:
        raise AgentError("R0368 private role query is disabled on this driver")
    before = driver.take_snapshot()
    if not _fresh_target(before, actor=actor_character_id,
                         episode=episode_run_id, war_id=war_id,
                         army_id=public_army_id):
        raise AgentError("R0368 fresh paused actor/war/owned allied army binding absent")
    result = driver.query_actor_army_role_private_v1(
        actor_character_id=actor_character_id,
        public_army_id=public_army_id,
        expected_war_id=war_id,
        expected_episode_run_id=episode_run_id,
        expected_revision=before["revision"],
    )
    after = driver.take_snapshot()
    if (not _fresh_target(after, actor=actor_character_id,
                          episode=episode_run_id, war_id=war_id,
                          army_id=public_army_id)
            or _binding(before) != _binding(after)
            or result.get("queried_snapshot_id") != before.get("snapshot_id")
            or result.get("queried_revision") != before.get("revision")
            or result.get("queried_native_revision") != before.get("native_revision")
            or result.get("queried_episode_run_id") != episode_run_id
            or result.get("queried_war_id") != war_id
            or result.get("queried_connection_generation")
            != before["diagnostics"]["connection_generation"]
            or result.get("queried_bridge_pid") != before["diagnostics"]["bridge_pid"]
            or result.get("date_raw") != before.get("date_raw")
            or result.get("private_build") is not True
            or result.get("read_only") is not True
            or result.get("advertised") is not False
            or result.get("global_role_ready") is not False
            or result.get("safe_role_release_ready") is not False
            or result.get("date_advance_ready") is not False):
        raise AgentError("R0368 role query crossed or changed its paused source frame")
    status = result.get("status")
    if status not in {"available", "partial", "unavailable"}:
        raise AgentError("R0368 role result lacks typed status")
    return {
        "schema": "xar.war.r0368.role-only-inner.v1",
        "status": f"READ_ONLY_INNER_{status.upper()}",
        "outer_session_cleanup_verified": False,
        "role_observed": status == "available",
        "before": copy.deepcopy(before),
        "after": copy.deepcopy(after),
        "role_result": copy.deepcopy(result),
        "query_attempts": 1,
        "gameplay_actions": 0,
        "date_advance_actions": 0,
        "action_authorized": False,
        "date_advance_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R0368 no-launch source-pair gate")
    parser.add_argument("--no-launch", action="store_true", required=True)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--release-pair-manifest", type=Path, required=True)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--attempt-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    args.attempt_dir.mkdir(parents=True, exist_ok=False)
    report_path = args.attempt_dir / "no-launch.json"
    try:
        report = verify_no_launch_source_pair(
            candidate_manifest=args.candidate_manifest,
            release_pair_manifest=args.release_pair_manifest,
            checkout=args.checkout,
        )
        code = 0
    except Exception as error:
        report = {"schema": "xar.war.r0368.role-only-no-launch.v1",
                  "status": "RED", "error": f"{type(error).__name__}: {error}",
                  "operator_enabled": False, "screen_acquired": False,
                  "ck3_started": False, "query_attempts": 0,
                  "gameplay_actions": 0, "date_advance_actions": 0}
        code = 2
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(report_path, _sha256(report_path), report["status"])
    return code


if __name__ == "__main__":
    raise SystemExit(main())

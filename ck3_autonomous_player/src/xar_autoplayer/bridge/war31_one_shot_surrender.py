"""One exact-source, owner-authorized WAR31 research action gate.

This is not a campaign surrender policy.  An operator must explicitly supply
an external receipt, both immutable R0197 files, and a durable fence path.
No ordinary driver constructs this gate.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


REQUEST_ID = "WAR-INPUT-R0221-WAR31-20260927"
STEP = "surrender-war-16777231"
WAR_ID = 16777231
EPISODE = "native-29829-2bc2d599f7f9"
DATE_RAW = 53215920
CHARACTER_ID = 29829
OPPONENT_ID = 30097
TITLE_IDS = [2128]
SCORE = -15
DURATION_DAYS = 1045
CHECKPOINT_SHA256 = "1AF4055F978AF60267FB3A0D8658224047CD6BFDA884C66886A13B74EE34A90A"
DRIVER_SHA256 = "1DE61CF0AC47EDD1D63FE1F3D77668D5F499EA6CA06B90BC83B068CF35F16336"
AUTHORIZATION_TEXT = "授权这一次匹配检查点的投降动作"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


class War31OneShotSurrenderGate:
    """Fail closed before dispatch, including across process restarts."""

    def __init__(
        self,
        *,
        authorization_receipt: str | os.PathLike[str],
        source_checkpoint: str | os.PathLike[str],
        source_driver: str | os.PathLike[str],
        submission_fence: str | os.PathLike[str],
    ) -> None:
        self.authorization_receipt = Path(authorization_receipt).resolve(strict=True)
        self.source_checkpoint = Path(source_checkpoint).resolve(strict=True)
        self.source_driver = Path(source_driver).resolve(strict=True)
        self.submission_fence = Path(submission_fence).resolve()
        if self.submission_fence != (
            self.authorization_receipt.parent
            / "war31-one-shot-submission-reservation.json"
        ):
            raise ValueError("WAR31 fence must use the authorization receipt directory")
        if self.submission_fence.exists():
            raise ValueError("WAR31 one-shot surrender fence already exists")
        if not self.submission_fence.parent.is_dir():
            raise ValueError("WAR31 one-shot fence parent must already exist")
        if self.submission_fence in {
            self.authorization_receipt,
            self.source_checkpoint,
            self.source_driver,
        }:
            raise ValueError("WAR31 one-shot fence must be a separate file")
        receipt_bytes = self.authorization_receipt.read_bytes()
        receipt = json.loads(receipt_bytes)
        if not isinstance(receipt, dict) or receipt != {
            "schema": "xar.ck3.war31-one-shot-user-authorization/v1",
            "request_id": REQUEST_ID,
            "action_step": STEP,
            "source_checkpoint_sha256": CHECKPOINT_SHA256,
            "source_driver_sha256": DRIVER_SHA256,
            "episode_run_id": EPISODE,
            "date_raw": DATE_RAW,
            "authorization_text": AUTHORIZATION_TEXT,
            "scope": "one matching checkpoint surrender action only",
        }:
            raise ValueError("WAR31 one-shot authorization receipt does not match")
        if _sha256_file(self.source_checkpoint) != CHECKPOINT_SHA256:
            raise ValueError("WAR31 source checkpoint SHA-256 mismatch")
        if _sha256_file(self.source_driver) != DRIVER_SHA256:
            raise ValueError("WAR31 source driver SHA-256 mismatch")
        self.receipt_sha256 = hashlib.sha256(receipt_bytes).hexdigest().upper()

    def readiness(
        self, snapshot: dict[str, object]
    ) -> tuple[bool, str, dict[str, object]]:
        if self.submission_fence.exists():
            return False, "one_shot_submission_fence_exists", {}
        if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
            return False, "snapshot_not_paused", {}
        if (
            snapshot.get("episode_run_id") != EPISODE
            or snapshot.get("date_raw") != DATE_RAW
        ):
            return False, "checkpoint_episode_or_date_mismatch", {}
        played = snapshot.get("played_character")
        if not isinstance(played, dict) or played.get("character_id") != CHARACTER_ID:
            return False, "played_character_mismatch", {}
        wars = snapshot.get("active_wars")
        matches = [
            row for row in wars if isinstance(row, dict) and row.get("war_id") == WAR_ID
        ] if isinstance(wars, list) else []
        if len(matches) != 1:
            return False, "war_identity_missing_or_ambiguous", {}
        war = matches[0]
        if not (
            war.get("player_side") == "defender"
            and war.get("player_is_primary_war_leader") is True
            and war.get("primary_opponent_character_id") == OPPONENT_ID
            and war.get("targeted_title_ids") == TITLE_IDS
            and war.get("player_relative_war_score") == SCORE
        ):
            return False, "war_identity_mismatch", {}
        rows = snapshot.get("war_termination_options")
        matches = [
            row for row in rows if isinstance(row, dict) and row.get("war_id") == WAR_ID
        ] if isinstance(rows, list) else []
        if len(matches) != 1:
            return False, "same_frame_termination_query_missing", {}
        options = matches[0]
        diagnostics = snapshot.get("diagnostics")
        generation = diagnostics.get("connection_generation") if isinstance(diagnostics, dict) else None
        if not (
            isinstance(generation, int)
            and not isinstance(generation, bool)
            and generation > 0
            and options.get("queried_snapshot_id") == snapshot.get("snapshot_id")
            and options.get("queried_revision") == snapshot.get("revision")
            and options.get("queried_native_revision") == snapshot.get("native_revision")
            and options.get("queried_connection_generation") == generation
            and options.get("episode_run_id") == EPISODE
        ):
            return False, "termination_query_not_same_frame", {}
        cb = options.get("active_casus_belli_identity")
        choices = options.get("options")
        surrender = choices.get("surrender") if isinstance(choices, dict) else None
        response = surrender.get("recipient_response") if isinstance(surrender, dict) else None
        if not (
            options.get("player_side") == "defender"
            and options.get("player_is_primary_war_leader") is True
            and options.get("player_relative_war_score") == SCORE
            and options.get("war_duration_days") == DURATION_DAYS
            and options.get("absolute_war_scores_observable") is True
            and options.get("attacker_war_score") == 15
            and options.get("defender_war_score") == -15
            and options.get("war_score_breakdown") == {
                "battles": 0,
                "imprisonment": 0,
                "occupation": 39,
                "ticking": -24,
            }
            and options.get("active_casus_belli_present") is True
            and cb == {"database_index": 17, "canonical_key": "individual_county_de_jure_cb"}
            and isinstance(surrender, dict)
            and surrender.get("outcome") == "attacker_victory"
            and surrender.get("hostage_variant") == "none"
            and surrender.get("context_constructed") is True
            and surrender.get("native_validator_passed") is True
            and surrender.get("available") is True
            and surrender.get("auto_accept_observable") is True
            and surrender.get("auto_accept") is True
            and isinstance(response, dict)
            and response.get("status") == "available"
            and response.get("decision_status_raw") == 0
            and response.get("would_accept_now") is True
        ):
            return False, "defender_surrender_legality_or_acceptance_failed", {}
        return True, "ready", {"war": war, "options": options, "surrender": surrender}

    def reserve(self, snapshot: dict[str, object], *, query_sequence: object) -> dict[str, object]:
        ready, reason, _ = self.readiness(snapshot)
        if not ready:
            raise ValueError("WAR31 one-shot surrender is not ready: " + reason)
        if isinstance(query_sequence, bool) or not isinstance(query_sequence, int) or query_sequence < 1:
            raise ValueError("WAR31 one-shot surrender lacks native query sequence")
        if hashlib.sha256(self.authorization_receipt.read_bytes()).hexdigest().upper() != self.receipt_sha256:
            raise ValueError("WAR31 authorization receipt changed after gate creation")
        if _sha256_file(self.source_checkpoint) != CHECKPOINT_SHA256:
            raise ValueError("WAR31 source checkpoint changed after gate creation")
        if _sha256_file(self.source_driver) != DRIVER_SHA256:
            raise ValueError("WAR31 source driver changed after gate creation")
        marker = {
            "schema": "xar.ck3.war31-one-shot-submission-reservation/v1",
            "request_id": REQUEST_ID,
            "action_step": STEP,
            "authorization_receipt_sha256": self.receipt_sha256,
            "source_checkpoint_sha256": CHECKPOINT_SHA256,
            "source_driver_sha256": DRIVER_SHA256,
            "episode_run_id": EPISODE,
            "date_raw": DATE_RAW,
            "snapshot_id": snapshot.get("snapshot_id"),
            "revision": snapshot.get("revision"),
            "native_revision": snapshot.get("native_revision"),
            "query_sequence": query_sequence,
            "status": "reserved_before_native_dispatch",
        }
        with self.submission_fence.open("x", encoding="utf-8") as stream:
            json.dump(marker, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        return {"fence_path": str(self.submission_fence), **marker}

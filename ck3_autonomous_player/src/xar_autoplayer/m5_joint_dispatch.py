"""Single-writer M5 frame dispatcher for fully assessed legal alternatives.

This module reserves one analytic choice and its shared resources.  It does
not create native values, submit a CK3 action, or persist a campaign promise.
The caller must first provide complete same-frame readbacks and policy values.
"""

from __future__ import annotations

from copy import deepcopy
from threading import Lock

from .m5_joint_budget_selector import select_m5_assessed_candidate
from .m5_observed_opportunity_selector import select_observed_m5_opportunity


_CLAIM_FIELDS = ("army_ids", "ally_character_ids", "character_ids", "commitment_keys")
_FRAME_FIELDS = (
    "played_character_id", "native_revision", "date_raw", "snapshot_id",
    "revision", "episode_run_id",
)


def summarize_m5_alliance_readback(
    *, legality: dict[str, object], projection: dict[str, object],
) -> dict[str, object]:
    """Keep the existing private five-row projection distinct from payoff."""
    if (
        legality.get("schema") != "xar.ck3.observed-first-heir-marriage-legality.v1"
        or legality.get("status") != "available"
        or legality.get("read_only") is not True
        or legality.get("advertised") is not False
        or legality.get("exact_ck3_build") != "1.19.0.6"
        or projection.get("schema") != "xar.ck3.first-heir-candidate-alliance-projection.v1"
        or projection.get("status") != "available"
        or projection.get("read_only") is not True
        or projection.get("advertised") is not False
        or projection.get("exact_ck3_build") != "1.19.0.6"
        or projection.get("native_revision") != legality.get("native_revision")
        or projection.get("legality_query_sequence") != legality.get("query_sequence")
    ):
        raise ValueError("M5 alliance readback lacks one native legal frame")
    legal_rows = legality.get("native_legal_candidates")
    projected_rows = projection.get("rows")
    if not isinstance(legal_rows, list) or not isinstance(projected_rows, list) or len(projected_rows) != 5:
        raise ValueError("M5 five current legal projection rows are required")
    legal = {
        row.get("candidate_character_id"): row for row in legal_rows
        if isinstance(row, dict) and row.get("complete_can_send") is True
        and row.get("recipient_answer_allows_send") is True
    }
    if len(legal) != len(legal_rows):
        raise ValueError("M5 final-legal candidate identities are not distinct")
    candidate_ids: list[int] = []
    attempted = 0
    pairs_count = 0
    heir = legality.get("observed_first_heir_character_id")
    for row in projected_rows:
        if not isinstance(row, dict):
            raise ValueError("M5 alliance projection row is malformed")
        candidate = row.get("candidate_character_id")
        pairs = row.get("possible_alliance_pairs")
        if (
            type(candidate) is not int or candidate not in legal
            or candidate in candidate_ids or row.get("heir_character_id") != heir
            or row.get("actor_character_id") != legal[candidate]["played_character_id"]
            or legal[candidate].get("subject_character_id") != heir
            or row.get("status") != "available" or not isinstance(pairs, list)
        ):
            raise ValueError("M5 alliance projection is not five final-legal rows")
        candidate_ids.append(candidate)
        for pair in pairs:
            if (
                not isinstance(pair, dict)
                or type(pair.get("first_character_id")) is not int
                or type(pair.get("second_character_id")) is not int
                or any(type(pair.get(key)) is not bool for key in (
                    "already_allied", "both_have_realm_data", "would_attempt_if_accepted"))
            ):
                raise ValueError("M5 alliance pair has an unreadable native result")
            pairs_count += 1
            attempted += int(pair["would_attempt_if_accepted"])
    return {
        "policy": "g2-m5-alliance-readback-summary-v1",
        "native_revision": projection["native_revision"],
        "legality_query_sequence": projection["legality_query_sequence"],
        "candidate_character_ids": candidate_ids,
        "possible_pair_count": pairs_count,
        "would_attempt_pair_count": attempted,
        "alliance_payoff_ready": False,
        "long_term_commitment_ready": False,
        "next_readonly_inputs": [
            "candidate_marriage_or_betrothal_outcome_and_lineality",
            "actual_alliance_value_duration_and_cancellation_cost",
        ],
    }


def _frame(value: object) -> tuple[int, int, int, str, int, str]:
    if not isinstance(value, dict):
        raise ValueError("M5 full paused frame is required")
    player = value.get("played_character_id")
    if player is None and isinstance(value.get("played_character"), dict):
        player = value["played_character"].get("character_id")
    native = value.get("native_revision")
    date = value.get("date_raw")
    snapshot = value.get("snapshot_id")
    revision = value.get("revision")
    episode = value.get("episode_run_id")
    if (
        type(player) is not int or player <= 0
        or type(native) is not int or native <= 0
        or type(date) is not int or date < 0
        or type(snapshot) is not str or not snapshot
        or type(revision) is not int or revision <= 0
        or type(episode) is not str or not episode
    ):
        raise ValueError("M5 full paused frame identity is incomplete")
    return player, native, date, snapshot, revision, episode


def _frame_dict(frame: tuple[int, int, int, str, int, str]) -> dict[str, object]:
    return dict(zip(_FRAME_FIELDS, frame))


def _commitments(
    value: object, frame: tuple[int, int, int, str, int, str],
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ValueError("M5 observed commitments are required")
    if _frame(value.get("frame")) != frame:
        raise ValueError("M5 commitments crossed an episode or paused frame")
    gold = value.get("gold_raw")
    pending_wars = value.get("pending_war_slots")
    if type(gold) is not int or gold < 0 or type(pending_wars) is not int or pending_wars < 0:
        raise ValueError("M5 gold and pending-war commitments must be explicit")
    result: dict[str, object] = {
        "frame": _frame_dict(frame), "gold_raw": gold,
        "pending_war_slots": pending_wars,
    }
    for key in _CLAIM_FIELDS:
        items = value.get(key)
        kind = str if key == "commitment_keys" else int
        if (
            not isinstance(items, list)
            or any(type(item) is not kind or (not item if kind is str else item <= 0)
                   for item in items)
            or len(items) != len(set(items))
        ):
            raise ValueError(f"M5 {key} commitments must be distinct observed claims")
        result[key] = sorted(items)
    return result


class M5FrameDispatcher:
    """One frame, one analytic reservation, shared by cooperating subpolicies."""

    def __init__(
        self, *, snapshot: dict[str, object],
        existing_commitments: dict[str, object],
    ) -> None:
        if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
            raise ValueError("M5 dispatcher requires a paused map frame")
        self._frame = _frame(snapshot)
        self._commitments = _commitments(existing_commitments, self._frame)
        self._reservation: dict[str, object] | None = None
        self._lock = Lock()

    def choose(
        self, *, intake: dict[str, object], snapshot: dict[str, object],
        assessments: list[dict[str, object]], gold_reserve_raw: int,
        max_active_wars: int,
    ) -> dict[str, object]:
        """Reserve one complete assessed choice; never return a typed step."""
        with self._lock:
            if _frame(snapshot) != self._frame or _frame(intake) != self._frame:
                raise ValueError("M5 dispatch crossed an episode or paused frame")
            if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
                raise ValueError("M5 dispatch requires a paused map frame")
            if not isinstance(assessments, list) or any(
                _frame(row) != self._frame for row in assessments
            ):
                raise ValueError("M5 assessment crossed an episode or paused frame")
            if type(max_active_wars) is not int or max_active_wars < 0:
                raise ValueError("M5 maximum active wars must be explicit")
            pending = self._commitments["pending_war_slots"]
            if pending > max_active_wars:
                raise ValueError("M5 pending war slots exceed the declared budget")
            if self._reservation is not None:
                return self._result("already_reserved_this_frame", None, None)
            if not assessments:
                return self._result("missing_assessments", None, None)
            analysis = select_m5_assessed_candidate(
                intake=intake, snapshot=snapshot, assessments=deepcopy(assessments),
                commitments=deepcopy(self._commitments),
                gold_reserve_raw=gold_reserve_raw,
                max_active_wars=max_active_wars,
            )
            candidate_id = analysis["selected_candidate_id"]
            if candidate_id is None:
                return self._result("wait", None, analysis)
            selected = next(row for row in analysis["evaluated"]
                            if row["candidate_id"] == candidate_id)
            commitments = deepcopy(self._commitments)
            commitments["gold_raw"] += selected["gold_raw"]
            for key in _CLAIM_FIELDS:
                commitments[key] = sorted(set(commitments[key]) | set(selected["claims"][key]))
            commitments["pending_war_slots"] += selected["war_slot_claim"]
            self._reservation = {
                "schema": "xar.ck3.m5-frame-reservation.v1",
                "frame": _frame_dict(self._frame),
                "candidate_id": candidate_id,
                "domain": selected["domain"],
                "commitments_after": commitments,
                "status": "analytic_only_pending_formal_action",
            }
            return self._result("reserved_analytic", candidate_id, analysis)

    def choose_observed(
        self, *, snapshot: dict[str, object],
        proposals: list[dict[str, object]], gold_reserve_raw: int,
        max_active_wars: int,
    ) -> dict[str, object]:
        """Reserve one domain-approved proposal using observed shared costs.

        This is the reusable M5 dispatch entry for council, construction and
        diplomacy proposals already produced by their formal policies. War
        and marriage enter only after their supply/commitment observations
        are complete. No typed action is returned here.
        """
        with self._lock:
            if _frame(snapshot) != self._frame:
                raise ValueError("M5 observed dispatch crossed an episode or paused frame")
            if snapshot.get("paused") is not True or snapshot.get("map_ready") is not True:
                raise ValueError("M5 observed dispatch requires a paused map frame")
            if self._reservation is not None:
                return self._result("already_reserved_this_frame", None, None)
            analysis = select_observed_m5_opportunity(
                snapshot=snapshot, proposals=deepcopy(proposals),
                commitments=deepcopy(self._commitments),
                gold_reserve_raw=gold_reserve_raw,
                max_active_wars=max_active_wars,
            )
            candidate_id = analysis["selected_candidate_id"]
            if candidate_id is None:
                return self._result("wait", None, analysis)
            selected = next(
                row for row in analysis["evaluated"]
                if row["candidate_id"] == candidate_id
            )
            commitments = deepcopy(self._commitments)
            commitments["gold_raw"] += selected["gold_cost_raw"]
            for key in _CLAIM_FIELDS:
                commitments[key] = sorted(
                    set(commitments[key]) | set(selected[key])
                )
            commitments["pending_war_slots"] += selected["war_slot_claim"]
            self._reservation = {
                "schema": "xar.ck3.m5-frame-reservation.v1",
                "frame": _frame_dict(self._frame),
                "candidate_id": candidate_id,
                "domain": selected["domain"],
                "source_policy": selected["source_policy"],
                "commitments_after": commitments,
                "status": "analytic_only_pending_formal_action",
                "observed_opportunity_cost": {
                    "gold_cost_raw": selected["gold_cost_raw"],
                    "war_slot_claim": selected["war_slot_claim"],
                    "projected_supply_margin_raw": selected[
                        "projected_supply_margin_raw"
                    ],
                },
            }
            return self._result(
                "reserved_observed_analytic", candidate_id, analysis
            )

    def _result(
        self, status: str, candidate_id: str | None,
        analysis: dict[str, object] | None,
    ) -> dict[str, object]:
        return {
            "policy": "g2-m5-single-frame-dispatch-v1",
            "status": status,
            "frame": _frame_dict(self._frame),
            "selected_candidate_id": candidate_id,
            "reservation": deepcopy(self._reservation),
            "analysis": deepcopy(analysis),
            "selected_step": None,
            "formal_action_ready": False,
        }

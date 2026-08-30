#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 model for the phase-two 361 career/HC domains.

This module covers domains D, M, N, O, P, Q, U and V.  It is intentionally a
pure-Python reference model: passing its tests proves deterministic business
rules and conservation invariants only.  It is *not* CK3 script wiring,
fixture-live evidence, MCP evidence, or a player-visible loop.

The model is deliberately stricter than the generated policy-card receipts.
Every mutation is bound to a frozen owner/subject/cycle/case/state token,
duplicate action serials are idempotent no-ops, malformed commands fail with a
typed ``ModelRed``, and conserved slots/money/hours cannot silently appear.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
import random
from typing import Any, Callable, Final, Iterable, Mapping, Sequence


HONEST_RUNTIME_EVIDENCE: Final[str] = "python-l0-model"
HONEST_CK3_WIRING: Final[str] = "not-implemented"


class RedCode(str, Enum):
    """Stable machine-readable failures for invalid commands or invariants."""

    INVALID_TYPE = "invalid-type"
    INVALID_VALUE = "invalid-value"
    DUPLICATE_ID = "duplicate-id"
    ILLEGAL_TRANSITION = "illegal-transition"
    INVARIANT_BREACH = "invariant-breach"
    RESOURCE_EXHAUSTED = "resource-exhausted"
    PERMISSION_DENIED = "permission-denied"
    CONFLICT_OF_INTEREST = "conflict-of-interest"
    PRIVACY_BREACH = "privacy-breach"


class ModelRed(ValueError):
    """Typed RED result; callers never need to parse prose to classify it."""

    def __init__(self, code: RedCode, field_name: str, detail: str) -> None:
        self.code = RedCode(code)
        self.field_name = field_name
        self.detail = detail
        super().__init__(f"{self.code.value}:{field_name}:{detail}")


class NoOpCode(str, Enum):
    STALE_TOKEN = "stale-token"
    DUPLICATE_ACTION = "duplicate-action"


@dataclass(frozen=True)
class MutationOutcome:
    mechanism_id: int
    applied: bool
    code: str
    previous_state: str
    current_state: str


def _nonempty(name: str, value: object) -> str:
    if not isinstance(value, str):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be str")
    if not value.strip():
        raise ModelRed(RedCode.INVALID_VALUE, name, "must be non-empty")
    return value


def _integer(
    name: str,
    value: object,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be int, not bool")
    if minimum is not None and value < minimum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be <= {maximum}")
    return value


def _number(
    name: str,
    value: object,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be numeric, not bool")
    result = float(value)
    if minimum is not None and result < minimum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be >= {minimum}")
    if maximum is not None and result > maximum:
        raise ModelRed(RedCode.INVALID_VALUE, name, f"must be <= {maximum}")
    return result


def _boolean(name: str, value: object) -> bool:
    if not isinstance(value, bool):
        raise ModelRed(RedCode.INVALID_TYPE, name, "must be bool")
    return value


def _unique_nonempty(name: str, values: Iterable[str]) -> tuple[str, ...]:
    result = tuple(_nonempty(name, value) for value in values)
    if len(result) != len(set(result)):
        raise ModelRed(RedCode.DUPLICATE_ID, name, "values must be unique")
    return result


def _shares_100(name: str, shares: Mapping[str, int]) -> dict[str, int]:
    result = {
        _nonempty(f"{name}.key", key): _integer(
            f"{name}.{key}", value, minimum=0, maximum=100
        )
        for key, value in shares.items()
    }
    if not result or sum(result.values()) != 100:
        raise ModelRed(RedCode.INVARIANT_BREACH, name, "shares must sum to 100")
    return result


@dataclass(frozen=True)
class CaseIdentity:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int

    def __post_init__(self) -> None:
        _nonempty("owner_id", self.owner_id)
        _nonempty("subject_id", self.subject_id)
        _integer("cycle_serial", self.cycle_serial, minimum=1)
        _integer("case_serial", self.case_serial, minimum=1)


@dataclass(frozen=True)
class CaseToken:
    owner_id: str
    subject_id: str
    cycle_serial: int
    case_serial: int
    expected_state: str


@dataclass
class GuardedCase:
    """Owner/cycle/case-bound aggregate with stale/idempotent no-op semantics."""

    identity: CaseIdentity
    state: str = "OPEN"
    _applied_serials: set[str] = field(default_factory=set, init=False, repr=False)

    def __post_init__(self) -> None:
        _nonempty("state", self.state)

    def token(self) -> CaseToken:
        return CaseToken(
            self.identity.owner_id,
            self.identity.subject_id,
            self.identity.cycle_serial,
            self.identity.case_serial,
            self.state,
        )

    def mutate(
        self,
        mechanism_id: int,
        token: CaseToken,
        action_serial: str,
        operation: Callable[[], None],
        *,
        next_state: str | None = None,
    ) -> MutationOutcome:
        previous = self.state
        action_serial = _nonempty("action_serial", action_serial)
        if action_serial in self._applied_serials:
            return MutationOutcome(
                mechanism_id,
                False,
                NoOpCode.DUPLICATE_ACTION.value,
                previous,
                self.state,
            )
        if token != self.token():
            return MutationOutcome(
                mechanism_id,
                False,
                NoOpCode.STALE_TOKEN.value,
                previous,
                self.state,
            )
        operation()
        self._applied_serials.add(action_serial)
        if next_state is not None:
            self.state = _nonempty("next_state", next_state)
        return MutationOutcome(mechanism_id, True, "applied", previous, self.state)


class TitleRank(IntEnum):
    BARON = 0
    COUNT = 1
    DUKE = 2
    KING = 3
    EMPEROR = 4


@dataclass(frozen=True)
class ManagerBoundary:
    rank: TitleRank
    landed: bool
    celestial_government: bool

    @property
    def can_manage(self) -> bool:
        return self.landed and self.celestial_government and self.rank >= TitleRank.DUKE

    def require_manager(self) -> None:
        if not self.can_manage:
            raise ModelRed(
                RedCode.PERMISSION_DENIED,
                "manager",
                "only landed celestial dukes-or-higher may manage",
            )


@dataclass(frozen=True)
class MechanismBehavior:
    mechanism_id: int
    domain: str
    title_cn: str
    behavior_key: str
    invariant_key: str
    runtime_evidence: str = HONEST_RUNTIME_EVIDENCE
    ck3_wiring: str = HONEST_CK3_WIRING


def _behavior(
    mechanism_id: int,
    domain: str,
    title_cn: str,
    behavior_key: str,
    invariant_key: str,
) -> MechanismBehavior:
    return MechanismBehavior(
        mechanism_id,
        domain,
        title_cn,
        behavior_key,
        invariant_key,
    )


MECHANISM_BEHAVIORS: Final[dict[int, MechanismBehavior]] = {
    19: _behavior(19, "D", "晋升资格门槛", "promotion_eligibility_gate", "separate_career_channels"),
    20: _behavior(20, "D", "晋升包与跨部门答辩", "promotion_package_panel", "single_packet_terminal"),
    21: _behavior(21, "D", "奖金—调薪矩阵", "bonus_salary_matrix", "money_conservation"),
    22: _behavior(22, "D", "软 HC / 编制预算", "soft_headcount_budget", "hc_conservation"),
    23: _behavior(23, "D", "HC 答辩与团队投入产出", "headcount_business_review", "one_defense_per_year"),
    24: _behavior(24, "D", "内部活水与转岗博弈", "internal_mobility_transfer", "one_cohort_per_cycle"),
    25: _behavior(25, "D", "高绩效人才被挖与反 offer", "talent_poaching_counteroffer", "one_offer_terminal"),
    92: _behavior(92, "M", "专业 / 管理双通道", "dual_career_tracks", "track_authority_separation"),
    93: _behavior(93, "M", "失败经理回归专家岗", "manager_return_to_expert", "titles_immutable"),
    94: _behavior(94, "M", "微职级与“升半级”缓冲", "micro_level_progression", "finite_level_table"),
    95: _behavior(95, "M", "高级管理任命年度复审", "annual_management_authority_review", "one_review_per_year"),
    96: _behavior(96, "M", "破格晋升包", "exceptional_promotion_packet", "promotion_slot_conservation"),
    97: _behavior(97, "M", "跨团队晋升校准", "cross_team_promotion_calibration", "promotion_slot_conservation"),
    98: _behavior(98, "N", "增长、补缺、项目三类 HC", "hc_type_ledger", "hc_conservation"),
    99: _behavior(99, "N", "HC 到期、结转与年底突击招募", "hc_expiry_carryover", "one_slot_one_outcome"),
    100: _behavior(100, "N", "冻结期与关键岗位特批", "hc_freeze_exception", "one_slot_one_role"),
    101: _behavior(101, "N", "一个资深 / 两个普通 / 学徒梯队", "hc_workforce_mix", "hire_cost_slot_character_conservation"),
    102: _behavior(102, "N", "零基编制重审", "zero_based_hc_review", "organization_hc_conservation"),
    103: _behavior(103, "N", "空编占坑审计", "vacant_hc_hoarding_audit", "exclusive_slot_owner"),
    104: _behavior(104, "N", "新人池 / 成熟人才池之争", "talent_source_mix", "external_only_character_growth"),
    105: _behavior(105, "N", "离任后的 backfill 归属", "backfill_ownership", "one_departure_one_backfill"),
    106: _behavior(106, "O", "关键岗位与关键人才分离", "critical_role_talent_split", "role_person_labels_separate"),
    107: _behavior(107, "O", "继任准备度阶梯", "succession_readiness_ladder", "one_candidate_one_band"),
    108: _behavior(108, "O", "代理任职试炼", "acting_role_trial", "authority_resource_goal_bound"),
    109: _behavior(109, "O", "高潜标签的公开层级", "high_potential_visibility", "need_to_know_visibility"),
    110: _behavior(110, "O", "潜力校准与绩效校准分会", "potential_performance_separation", "performance_frozen_first"),
    111: _behavior(111, "O", "遗憾流失与健康流失分类", "attrition_classification", "one_attrition_case"),
    112: _behavior(112, "O", "留任访谈（Stay Interview）", "stay_interview", "one_funded_promise"),
    113: _behavior(113, "O", "关键人依赖与知识移交", "key_person_dependency", "knowledge_coverage_no_duplication"),
    114: _behavior(114, "P", "经理“人才输出”积分", "manager_talent_export_credit", "reward_after_transfer"),
    115: _behavior(115, "P", "匿名内部应聘", "anonymous_internal_application", "privacy_until_final"),
    116: _behavior(116, "P", "放人时限与一次交接延期", "transfer_release_deadline", "one_extension"),
    117: _behavior(117, "P", "转岗爬坡保护期", "transfer_ramp_protection", "one_protection_lifetime"),
    118: _behavior(118, "P", "试用期绝对门槛，不占末位配额", "probation_outside_bottom_quota", "probation_quota_separate"),
    119: _behavior(119, "P", "招聘质量回写", "hiring_quality_writeback", "one_quality_outcome"),
    120: _behavior(120, "P", "导师与 onboarding 绩效", "mentor_onboarding_performance", "milestone_once"),
    121: _behavior(121, "Q", "首次任经理试运行", "manager_trial_assignment", "eligible_manager_owner"),
    122: _behavior(122, "Q", "管理者 4-3-3 记分卡", "manager_scorecard", "weights_40_30_30"),
    123: _behavior(123, "Q", "下属评经理专表", "manager_subordinate_review", "credible_six_factor_feedback"),
    124: _behavior(124, "Q", "“先有接班人，才升经理”", "manager_successor_gate", "successor_before_promotion"),
    125: _behavior(125, "Q", "亲自救火与授权取舍", "manager_delegation_crisis", "crisis_hours_conservation"),
    126: _behavior(126, "Q", "绩效 × 价值观处置矩阵", "manager_performance_values_matrix", "one_of_four_quadrants"),
    127: _behavior(127, "Q", "管理幅度与评分失真", "manager_span_of_control", "span_snapshot_frozen"),
    128: _behavior(128, "Q", "强制分布气候指标", "manager_forced_ranking_climate", "next_cycle_only"),
    157: _behavior(157, "U", "自荐权与主管提名权", "promotion_nomination_access", "one_candidate_one_packet"),
    158: _behavior(158, "U", "主管提名额度", "promotion_nomination_quota", "nomination_quota_conservation"),
    159: _behavior(159, "U", "雪藏明星不提名", "promotion_shelved_star", "shelving_due_once"),
    160: _behavior(160, "U", "部门预审淘汰赛", "promotion_department_prescreen", "one_prescreen_result"),
    161: _behavior(161, "U", "“陪跑包”与虚假竞争", "promotion_sham_competition", "real_quota_and_hours"),
    162: _behavior(162, "U", "资历门槛例外申请", "promotion_tenure_exception", "exception_before_merit_review"),
    163: _behavior(163, "U", "晋升绩效观察窗", "promotion_performance_window", "one_window_per_cohort"),
    164: _behavior(164, "U", "跨团队成果进入晋升包", "promotion_cross_team_evidence", "contribution_shares_bounded"),
    165: _behavior(165, "U", "“先干到下一级”试岗证据", "promotion_next_level_trial", "authority_compensation_deadline_bound"),
    166: _behavior(166, "U", "候选主动撤包", "promotion_packet_withdrawal", "withdraw_before_prescreen"),
    167: _behavior(167, "U", "Sponsor 的晋升信用债", "promotion_sponsor_credit", "settle_after_observation"),
    168: _behavior(168, "U", "经理提名命中率", "promotion_manager_hit_rate", "mature_cases_only"),
    169: _behavior(169, "V", "评委专业匹配", "promotion_panel_expertise", "panel_weights_100"),
    170: _behavior(170, "V", "随机评委与熟人评委", "promotion_panel_selection", "reproducible_unique_panel"),
    171: _behavior(171, "V", "答辩评委利益回避", "promotion_panel_recusal", "conflicted_votes_void"),
    172: _behavior(172, "V", "一票否决 / 多数票 / 平均分", "promotion_panel_decision_rule", "rule_frozen_before_vote"),
    173: _behavior(173, "V", "盲材料审查与现场答辩", "promotion_blind_live_review", "blind_score_immutable"),
    174: _behavior(174, "V", "答辩时间预算", "promotion_defense_time_budget", "defense_hours_conservation"),
    175: _behavior(175, "V", "模拟答辩与辅导资源", "promotion_coaching_allocation", "coaching_hours_conservation"),
    176: _behavior(176, "V", "团队成绩的个人归因质询", "promotion_individual_attribution", "attribution_shares_100"),
    177: _behavior(177, "V", "项目规模与个人杠杆分离", "promotion_scale_leverage_split", "scale_leverage_separate"),
    178: _behavior(178, "V", "可复核工件与故事表达双证据", "promotion_artifact_narrative_evidence", "dual_evidence_gate"),
    179: _behavior(179, "V", "失败答辩的具体反馈 owner", "promotion_rejection_feedback_owner", "one_feedback_owner"),
    180: _behavior(180, "V", "晋升冷却与材料刷新", "promotion_retry_cooldown", "cooldown_preserves_versions"),
}


EXPECTED_MECHANISM_IDS: Final[frozenset[int]] = frozenset(
    (*range(19, 26), *range(92, 129), *range(157, 181))
)


def validate_behavior_registry() -> None:
    if set(MECHANISM_BEHAVIORS) != EXPECTED_MECHANISM_IDS:
        missing = sorted(EXPECTED_MECHANISM_IDS - set(MECHANISM_BEHAVIORS))
        extra = sorted(set(MECHANISM_BEHAVIORS) - EXPECTED_MECHANISM_IDS)
        raise ModelRed(
            RedCode.INVARIANT_BREACH,
            "MECHANISM_BEHAVIORS",
            f"missing={missing}, extra={extra}",
        )
    keys = [row.behavior_key for row in MECHANISM_BEHAVIORS.values()]
    if len(keys) != len(set(keys)):
        raise ModelRed(RedCode.DUPLICATE_ID, "behavior_key", "must be unique")
    for mechanism_id, row in MECHANISM_BEHAVIORS.items():
        if mechanism_id != row.mechanism_id:
            raise ModelRed(RedCode.INVARIANT_BREACH, "mechanism_id", "key mismatch")
        if row.runtime_evidence != HONEST_RUNTIME_EVIDENCE or row.ck3_wiring != HONEST_CK3_WIRING:
            raise ModelRed(RedCode.INVARIANT_BREACH, "readiness", "readiness inflation")


@dataclass
class MoneyLedger:
    """A payer-side budget with explicit reservations and recipient credits."""

    opening: int
    available: int = field(init=False)
    reserved: dict[str, int] = field(default_factory=dict)
    credits: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.opening = _integer("opening", self.opening, minimum=0)
        self.available = self.opening

    @property
    def spent(self) -> int:
        return sum(self.credits.values())

    def reserve(self, reservation_id: str, amount: int) -> None:
        reservation_id = _nonempty("reservation_id", reservation_id)
        amount = _integer("amount", amount, minimum=0)
        if reservation_id in self.reserved or reservation_id in self.credits:
            raise ModelRed(RedCode.DUPLICATE_ID, "reservation_id", reservation_id)
        if amount > self.available:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "available", "insufficient money")
        self.available -= amount
        self.reserved[reservation_id] = amount
        self.assert_conserved()

    def settle(self, reservation_id: str, recipient_id: str) -> int:
        reservation_id = _nonempty("reservation_id", reservation_id)
        recipient_id = _nonempty("recipient_id", recipient_id)
        if reservation_id not in self.reserved:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "reservation_id", "not reserved")
        amount = self.reserved.pop(reservation_id)
        self.credits[recipient_id] = self.credits.get(recipient_id, 0) + amount
        self.assert_conserved()
        return amount

    def release(self, reservation_id: str) -> int:
        reservation_id = _nonempty("reservation_id", reservation_id)
        if reservation_id not in self.reserved:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "reservation_id", "not reserved")
        amount = self.reserved.pop(reservation_id)
        self.available += amount
        self.assert_conserved()
        return amount

    def assert_conserved(self) -> None:
        if self.opening != self.available + sum(self.reserved.values()) + self.spent:
            raise ModelRed(RedCode.INVARIANT_BREACH, "money", "opening != available+reserved+spent")


class SlotKind(str, Enum):
    PROMOTION = "promotion"
    NOMINATION = "nomination"
    GROWTH = "growth"
    BACKFILL = "backfill"
    PROJECT = "project"
    TRANSFER = "transfer"


class SlotState(str, Enum):
    VACANT = "vacant"
    RESERVED = "reserved"
    OCCUPIED = "occupied"
    FROZEN = "frozen"
    RECLAIMED = "reclaimed"


@dataclass
class Slot:
    slot_id: str
    kind: SlotKind
    owner_id: str
    state: SlotState = SlotState.VACANT
    reservation_id: str | None = None
    occupant_id: str | None = None
    carryovers: int = 0
    source_slot_id: str | None = None

    def __post_init__(self) -> None:
        _nonempty("slot_id", self.slot_id)
        _nonempty("owner_id", self.owner_id)
        self.kind = SlotKind(self.kind)
        self.state = SlotState(self.state)


@dataclass
class SlotLedger:
    slots: dict[str, Slot]
    _opening_ids: frozenset[str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.slots:
            raise ModelRed(RedCode.INVALID_VALUE, "slots", "at least one slot required")
        if set(self.slots) != {slot.slot_id for slot in self.slots.values()}:
            raise ModelRed(RedCode.INVARIANT_BREACH, "slots", "mapping key/id mismatch")
        self._opening_ids = frozenset(self.slots)
        self.assert_conserved()

    @classmethod
    def build(
        cls,
        rows: Iterable[tuple[str, SlotKind, str]],
    ) -> "SlotLedger":
        slots: dict[str, Slot] = {}
        for slot_id, kind, owner_id in rows:
            if slot_id in slots:
                raise ModelRed(RedCode.DUPLICATE_ID, "slot_id", slot_id)
            slots[slot_id] = Slot(slot_id, kind, owner_id)
        return cls(slots)

    def reserve(self, slot_id: str, reservation_id: str) -> None:
        slot = self._get(slot_id)
        reservation_id = _nonempty("reservation_id", reservation_id)
        if slot.state != SlotState.VACANT:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "slot", "must be vacant")
        if any(item.reservation_id == reservation_id for item in self.slots.values()):
            raise ModelRed(RedCode.DUPLICATE_ID, "reservation_id", reservation_id)
        slot.state = SlotState.RESERVED
        slot.reservation_id = reservation_id
        self.assert_conserved()

    def occupy(self, slot_id: str, reservation_id: str, occupant_id: str) -> None:
        slot = self._get(slot_id)
        occupant_id = _nonempty("occupant_id", occupant_id)
        if slot.state != SlotState.RESERVED or slot.reservation_id != reservation_id:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "slot", "reservation mismatch")
        if any(
            item.occupant_id == occupant_id and item.state == SlotState.OCCUPIED
            for item in self.slots.values()
        ):
            raise ModelRed(RedCode.DUPLICATE_ID, "occupant_id", occupant_id)
        slot.state = SlotState.OCCUPIED
        slot.occupant_id = occupant_id
        slot.reservation_id = None
        self.assert_conserved()

    def release_reservation(self, slot_id: str, reservation_id: str) -> None:
        slot = self._get(slot_id)
        if slot.state != SlotState.RESERVED or slot.reservation_id != reservation_id:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "slot", "reservation mismatch")
        slot.state = SlotState.VACANT
        slot.reservation_id = None
        self.assert_conserved()

    def freeze(self, slot_id: str) -> None:
        slot = self._get(slot_id)
        if slot.state != SlotState.VACANT:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "slot", "only vacant slot may freeze")
        slot.state = SlotState.FROZEN
        self.assert_conserved()

    def reclaim(self, slot_id: str) -> None:
        slot = self._get(slot_id)
        if slot.state not in (SlotState.VACANT, SlotState.FROZEN):
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "slot", "slot cannot be reclaimed")
        slot.state = SlotState.RECLAIMED
        slot.reservation_id = None
        slot.occupant_id = None
        self.assert_conserved()

    def transfer_owner(self, slot_id: str, new_owner_id: str) -> None:
        slot = self._get(slot_id)
        new_owner_id = _nonempty("new_owner_id", new_owner_id)
        if slot.state not in (SlotState.VACANT, SlotState.FROZEN):
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "slot", "occupied/reserved slot cannot transfer")
        slot.owner_id = new_owner_id
        slot.state = SlotState.VACANT
        self.assert_conserved()

    def carry_over_once(self, slot_id: str, *, has_final_candidate: bool) -> None:
        slot = self._get(slot_id)
        if slot.state != SlotState.VACANT or not has_final_candidate:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "carryover", "requires vacant slot and final candidate")
        if slot.carryovers >= 1:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "carryover", "may occur once")
        slot.carryovers += 1

    def count(self, state: SlotState) -> int:
        return sum(slot.state == state for slot in self.slots.values())

    def _get(self, slot_id: str) -> Slot:
        slot_id = _nonempty("slot_id", slot_id)
        try:
            return self.slots[slot_id]
        except KeyError as exc:
            raise ModelRed(RedCode.INVALID_VALUE, "slot_id", slot_id) from exc

    def assert_conserved(self) -> None:
        if frozenset(self.slots) != self._opening_ids:
            raise ModelRed(RedCode.INVARIANT_BREACH, "slots", "slot IDs changed")
        if len(self.slots) != sum(self.count(state) for state in SlotState):
            raise ModelRed(RedCode.INVARIANT_BREACH, "slots", "state partition does not conserve")
        reservations = [slot.reservation_id for slot in self.slots.values() if slot.reservation_id]
        occupants = [slot.occupant_id for slot in self.slots.values() if slot.occupant_id]
        if len(reservations) != len(set(reservations)) or len(occupants) != len(set(occupants)):
            raise ModelRed(RedCode.DUPLICATE_ID, "slots", "reservation/occupant duplicated")
        for slot in self.slots.values():
            if slot.state == SlotState.RESERVED and not slot.reservation_id:
                raise ModelRed(RedCode.INVARIANT_BREACH, "slot", "reserved slot lacks reservation")
            if slot.state == SlotState.OCCUPIED and not slot.occupant_id:
                raise ModelRed(RedCode.INVARIANT_BREACH, "slot", "occupied slot lacks occupant")


@dataclass(frozen=True)
class EligibilityEvidence:
    consecutive_top_cycles: int
    values_ok: bool
    active_pip: bool
    tenure_ok: bool
    legal_vacancy: bool

    def __post_init__(self) -> None:
        _integer("consecutive_top_cycles", self.consecutive_top_cycles, minimum=0)
        if not all(isinstance(value, bool) for value in (self.values_ok, self.active_pip, self.tenure_ok, self.legal_vacancy)):
            raise ModelRed(RedCode.INVALID_TYPE, "eligibility", "boolean gates required")

    def qualifying_gates(self, sponsor_soft_skips: Iterable[str] = ()) -> dict[str, bool]:
        skips = set(sponsor_soft_skips)
        unknown = skips - {"tenure"}
        if unknown:
            raise ModelRed(RedCode.PERMISSION_DENIED, "sponsor_soft_skips", f"hard/unknown={sorted(unknown)}")
        return {
            "two_top_cycles": self.consecutive_top_cycles >= 2,
            "values": self.values_ok,
            "no_active_pip": not self.active_pip,
            "tenure": self.tenure_ok or "tenure" in skips,
            "legal_vacancy": self.legal_vacancy,
        }

    def qualifies(self, sponsor_soft_skips: Iterable[str] = ()) -> bool:
        return all(self.qualifying_gates(sponsor_soft_skips).values())


@dataclass(frozen=True)
class PromotionPacket:
    packet_id: str
    evidence_ids: tuple[str, ...]
    hard_evidence_score: int
    expression_score: int
    reviewer_units: tuple[str, ...]
    sponsor_disclosure: str | None = None

    def __post_init__(self) -> None:
        _nonempty("packet_id", self.packet_id)
        _unique_nonempty("evidence_ids", self.evidence_ids)
        _integer("hard_evidence_score", self.hard_evidence_score, minimum=0, maximum=80)
        _integer("expression_score", self.expression_score, minimum=0, maximum=20)
        _unique_nonempty("reviewer_units", self.reviewer_units)
        if not self.reviewer_units:
            raise ModelRed(RedCode.INVALID_VALUE, "reviewer_units", "cross-unit reviewer required")

    @property
    def score(self) -> int:
        return self.hard_evidence_score + self.expression_score


class OfferState(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class TalentOffer:
    offer_id: str
    candidate_id: str
    payer_id: str
    position_id: str
    salary: int
    expires_day: int
    legal_vacancy: bool
    consecutive_top_cycles: int
    promotion_stalled: bool
    state: OfferState = OfferState.OPEN

    def __post_init__(self) -> None:
        for name in ("offer_id", "candidate_id", "payer_id", "position_id"):
            _nonempty(name, getattr(self, name))
        _integer("salary", self.salary, minimum=0)
        _integer("expires_day", self.expires_day, minimum=1)
        _integer("consecutive_top_cycles", self.consecutive_top_cycles, minimum=0)
        _boolean("legal_vacancy", self.legal_vacancy)
        _boolean("promotion_stalled", self.promotion_stalled)
        if not (self.legal_vacancy and self.consecutive_top_cycles >= 2 and self.promotion_stalled):
            raise ModelRed(RedCode.PERMISSION_DENIED, "offer", "candidate/vacancy gates failed")

    def resolve(self, state: OfferState) -> None:
        state = OfferState(state)
        if self.state != OfferState.OPEN or state == OfferState.OPEN:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "offer", "terminal outcome is single-use")
        self.state = state


@dataclass
class CareerAllocationCase(GuardedCase):
    """Domain D: eligibility, packet, money/HC reservations, mobility and offers."""

    titles: tuple[str, ...] = ()
    authority: frozenset[str] = frozenset()
    career_level: int = 0
    personal_gold: int = 0
    eligibility: EligibilityEvidence | None = None
    eligibility_reviewer_id: str | None = None
    eligibility_cycle_serial: int | None = None
    packet: PromotionPacket | None = None
    packet_terminal: str | None = None
    deferred_until: int | None = None
    salary_percent: int = 0
    cohort_by_cycle: dict[int, str] = field(default_factory=dict)
    hc_defense_years: set[int] = field(default_factory=set)

    def evaluate_eligibility(
        self,
        token: CaseToken,
        action_serial: str,
        evidence: EligibilityEvidence,
        *,
        sponsor_soft_skips: Iterable[str] = (),
    ) -> MutationOutcome:
        def operation() -> None:
            if not evidence.qualifies(sponsor_soft_skips):
                raise ModelRed(RedCode.PERMISSION_DENIED, "eligibility", "one or more gates failed")
            self.eligibility = evidence
            self.eligibility_reviewer_id = self.identity.owner_id
            self.eligibility_cycle_serial = self.identity.cycle_serial

        return self.mutate(19, token, action_serial, operation, next_state="ELIGIBLE")

    def open_packet(
        self,
        token: CaseToken,
        action_serial: str,
        packet: PromotionPacket,
        promotion_slots: SlotLedger,
        slot_id: str,
    ) -> MutationOutcome:
        def operation() -> None:
            if self.eligibility is None:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "packet", "eligibility not frozen")
            if packet.packet_id in (slot.reservation_id for slot in promotion_slots.slots.values()):
                raise ModelRed(RedCode.DUPLICATE_ID, "packet_id", packet.packet_id)
            promotion_slots.reserve(slot_id, packet.packet_id)
            self.packet = packet

        return self.mutate(20, token, action_serial, operation, next_state="PACKET_OPEN")

    def settle_packet(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        outcome: str,
        earliest_retry_day: int | None = None,
    ) -> MutationOutcome:
        def operation() -> None:
            if self.packet is None or self.packet_terminal is not None:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "packet", "no open packet")
            if outcome not in {"passed", "deferred", "failed"}:
                raise ModelRed(RedCode.INVALID_VALUE, "outcome", outcome)
            if outcome == "deferred":
                self.deferred_until = _integer("earliest_retry_day", earliest_retry_day, minimum=1)
            self.packet_terminal = outcome

        return self.mutate(20, token, action_serial, operation, next_state="PANEL_COMPLETE")

    def award_bonus_and_salary(
        self,
        token: CaseToken,
        action_serial: str,
        budget: MoneyLedger,
        *,
        reservation_id: str,
        bonus: int,
        salary_delta_percent: int,
    ) -> MutationOutcome:
        def operation() -> None:
            delta = _integer("salary_delta_percent", salary_delta_percent, minimum=-50, maximum=25)
            budget.reserve(reservation_id, bonus)
            paid = budget.settle(reservation_id, self.identity.subject_id)
            self.personal_gold += paid
            self.salary_percent = max(-50, min(25, self.salary_percent + delta))

        return self.mutate(21, token, action_serial, operation)

    def record_hc_defense(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        year: int,
        jingcha_treasury_delta: int,
        jingcha_personal_delta: int,
    ) -> MutationOutcome:
        def operation() -> None:
            year_value = _integer("year", year, minimum=1)
            if year_value in self.hc_defense_years:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "year", "defense already settled")
            if jingcha_treasury_delta != 0 or jingcha_personal_delta != 0:
                raise ModelRed(RedCode.INVARIANT_BREACH, "jingcha", "Jingcha itself is free")
            self.hc_defense_years.add(year_value)

        return self.mutate(23, token, action_serial, operation)

    def assign_cohort_once(self, cycle_serial: int, team_id: str) -> None:
        cycle_serial = _integer("cycle_serial", cycle_serial, minimum=1)
        team_id = _nonempty("team_id", team_id)
        existing = self.cohort_by_cycle.get(cycle_serial)
        if existing is not None and existing != team_id:
            raise ModelRed(RedCode.INVARIANT_BREACH, "cohort", "one team per cycle")
        self.cohort_by_cycle[cycle_serial] = team_id

    def accept_transfer_next_cycle(self, *, legal_position: bool, new_team_id: str) -> None:
        if not isinstance(legal_position, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "legal_position", "must be bool")
        if not legal_position:
            raise ModelRed(RedCode.PERMISSION_DENIED, "position", "native vacancy is not legal")
        self.assign_cohort_once(self.identity.cycle_serial + 1, new_team_id)


class CareerTrack(str, Enum):
    EXPERT = "expert"
    MANAGER = "manager"


MANAGER_AUTHORITIES: Final[frozenset[str]] = frozenset(
    {"assess_others", "allocate_hc", "sit_review_panel"}
)
MICRO_LEVELS: Final[tuple[str, ...]] = ("L1", "L1.5", "L2", "L2.5", "L3")


@dataclass
class CareerProfile:
    person_id: str
    titles: tuple[str, ...]
    professional_level: str = "L1"
    track: CareerTrack = CareerTrack.EXPERT
    management_level: int = 0
    authority: set[str] = field(default_factory=set)
    pay: int = 0
    delivery_capacity: int = 100
    manager_retry_day: int | None = None
    reviewed_years: set[int] = field(default_factory=set)
    title_inflation_debt: int = 0

    def __post_init__(self) -> None:
        _nonempty("person_id", self.person_id)
        self.titles = _unique_nonempty("titles", self.titles)
        if self.professional_level not in MICRO_LEVELS:
            raise ModelRed(RedCode.INVALID_VALUE, "professional_level", self.professional_level)
        _integer("pay", self.pay, minimum=0)
        _integer("delivery_capacity", self.delivery_capacity, minimum=0, maximum=100)

    def choose_track(self, track: CareerTrack, *, manager_training_cost: int = 0) -> None:
        track = CareerTrack(track)
        training_cost = _integer("manager_training_cost", manager_training_cost, minimum=0)
        self.track = track
        if track == CareerTrack.MANAGER:
            self.management_level = max(1, self.management_level)
            self.authority.update(MANAGER_AUTHORITIES)
            self.delivery_capacity = max(0, 100 - training_cost)
        else:
            self.management_level = 0
            self.authority.difference_update(MANAGER_AUTHORITIES)
            self.delivery_capacity = 100

    def return_to_expert(self, *, retry_day: int) -> None:
        self.choose_track(CareerTrack.EXPERT)
        self.manager_retry_day = _integer("retry_day", retry_day, minimum=1)

    def advance_micro_level(self, *, pay_delta: int, authority_grants: Iterable[str] = ()) -> None:
        index = MICRO_LEVELS.index(self.professional_level)
        if index == len(MICRO_LEVELS) - 1:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "professional_level", "already at table maximum")
        self.professional_level = MICRO_LEVELS[index + 1]
        self.pay += _integer("pay_delta", pay_delta, minimum=0)
        self.authority.update(_unique_nonempty("authority_grants", authority_grants))

    def grant_empty_micro_title(self) -> None:
        self.title_inflation_debt += 1

    def annual_management_review(
        self,
        boundary: ManagerBoundary,
        *,
        year: int,
        outcome: str,
    ) -> None:
        boundary.require_manager()
        year = _integer("year", year, minimum=1)
        if year in self.reviewed_years:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "year", "review already completed")
        if outcome not in {"confirm", "coach", "tighten_budget", "remove_management_authority"}:
            raise ModelRed(RedCode.INVALID_VALUE, "outcome", outcome)
        if outcome == "remove_management_authority":
            self.authority.difference_update(MANAGER_AUTHORITIES)
        elif outcome == "tighten_budget":
            self.authority.discard("allocate_hc")
        self.reviewed_years.add(year)


@dataclass
class PromotionSlotBook:
    slots: SlotLedger
    promoted_candidates: set[str] = field(default_factory=set)
    future_debt: int = 0

    def award(self, slot_id: str, candidate_id: str, packet_id: str, *, exceptional: bool = False) -> None:
        candidate_id = _nonempty("candidate_id", candidate_id)
        if candidate_id in self.promoted_candidates:
            raise ModelRed(RedCode.DUPLICATE_ID, "candidate_id", candidate_id)
        self.slots.reserve(slot_id, packet_id)
        self.slots.occupy(slot_id, packet_id, candidate_id)
        self.promoted_candidates.add(candidate_id)
        if exceptional:
            self.future_debt += 1

    def cross_team_calibrate(
        self,
        slot_id: str,
        candidates: Mapping[str, tuple[int, int]],
        packet_id: str,
    ) -> str:
        """Choose by target-level scope first, then local rank; consumes one slot."""

        if not candidates:
            raise ModelRed(RedCode.INVALID_VALUE, "candidates", "cannot be empty")
        normalized: list[tuple[int, int, str]] = []
        for candidate_id, (cross_team_results, local_rank_score) in candidates.items():
            normalized.append(
                (
                    _integer("cross_team_results", cross_team_results, minimum=0),
                    _integer("local_rank_score", local_rank_score, minimum=0),
                    _nonempty("candidate_id", candidate_id),
                )
            )
        winner = max(normalized)[2]
        self.award(slot_id, winner, packet_id)
        return winner


@dataclass(frozen=True)
class HireCandidate:
    candidate_id: str
    source: str
    cost: int
    mentor_capacity: int = 0

    def __post_init__(self) -> None:
        _nonempty("candidate_id", self.candidate_id)
        if self.source not in {"newcomer", "mature", "internal", "senior", "apprentice", "midlevel"}:
            raise ModelRed(RedCode.INVALID_VALUE, "source", self.source)
        _integer("cost", self.cost, minimum=0)
        _integer("mentor_capacity", self.mentor_capacity, minimum=0)

    @property
    def external(self) -> bool:
        return self.source != "internal"


@dataclass
class HcBoard:
    """Domain N and the HC portion of D: identity-preserving slot lifecycle."""

    ledger: SlotLedger
    budget: MoneyLedger
    mentor_capacity: int = 0
    hired_people: set[str] = field(default_factory=set)
    backfill_by_departure: dict[str, tuple[str, str]] = field(default_factory=dict)
    review_windows: set[str] = field(default_factory=set)
    audit_flags: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.mentor_capacity = _integer("mentor_capacity", self.mentor_capacity, minimum=0)
        for slot in self.ledger.slots.values():
            if slot.kind not in {SlotKind.GROWTH, SlotKind.BACKFILL, SlotKind.PROJECT}:
                raise ModelRed(RedCode.INVALID_VALUE, "slot.kind", "HC board requires HC slot kinds")

    @property
    def external_character_growth(self) -> int:
        return len(self.hired_people)

    def assert_hc_conserved(self) -> None:
        self.ledger.assert_conserved()
        self.budget.assert_conserved()
        if self.mentor_capacity < 0:
            raise ModelRed(RedCode.INVARIANT_BREACH, "mentor_capacity", "negative")

    def convert_project_to_growth(self, slot_id: str, *, defended: bool) -> None:
        slot = self.ledger._get(slot_id)
        if slot.kind != SlotKind.PROJECT:
            raise ModelRed(RedCode.INVALID_VALUE, "slot.kind", "not a project slot")
        if not _boolean("defended", defended):
            raise ModelRed(RedCode.PERMISSION_DENIED, "defended", "conversion requires new defense")
        slot.kind = SlotKind.GROWTH
        self.assert_hc_conserved()

    def recruit(self, slot_id: str, candidate: HireCandidate) -> None:
        if candidate.source == "internal":
            raise ModelRed(RedCode.INVALID_VALUE, "candidate.source", "internal move is not external recruitment")
        if candidate.candidate_id in self.hired_people:
            raise ModelRed(RedCode.DUPLICATE_ID, "candidate_id", candidate.candidate_id)
        reservation_id = f"hire:{candidate.candidate_id}"
        self.ledger.reserve(slot_id, reservation_id)
        self.budget.reserve(reservation_id, candidate.cost)
        if candidate.mentor_capacity > self.mentor_capacity:
            self.ledger.release_reservation(slot_id, reservation_id)
            self.budget.release(reservation_id)
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "mentor_capacity", "insufficient mentors")
        self.ledger.occupy(slot_id, reservation_id, candidate.candidate_id)
        self.budget.settle(reservation_id, candidate.candidate_id)
        self.mentor_capacity -= candidate.mentor_capacity
        self.hired_people.add(candidate.candidate_id)
        self.assert_hc_conserved()

    def recruit_workforce_mix(
        self,
        assignments: Sequence[tuple[str, HireCandidate]],
    ) -> None:
        candidate_ids = _unique_nonempty("candidate_ids", (candidate.candidate_id for _, candidate in assignments))
        if len(candidate_ids) != len(assignments):
            raise ModelRed(RedCode.DUPLICATE_ID, "candidate_ids", "duplicate candidate")
        total_cost = sum(candidate.cost for _, candidate in assignments)
        total_mentor = sum(candidate.mentor_capacity for _, candidate in assignments)
        if total_cost > self.budget.available:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "budget", "plan exceeds available")
        if total_mentor > self.mentor_capacity:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "mentor_capacity", "plan exceeds available")
        for slot_id, candidate in assignments:
            self.recruit(slot_id, candidate)

    def carryover_or_reclaim(self, slot_id: str, *, has_final_candidate: bool) -> str:
        if _boolean("has_final_candidate", has_final_candidate):
            self.ledger.carry_over_once(slot_id, has_final_candidate=True)
            return "carried-once"
        self.ledger.reclaim(slot_id)
        return "reclaimed"

    def freeze_except_critical(
        self,
        ordinary_slot_ids: Iterable[str],
        *,
        exception_slot_id: str,
        role_id: str,
        governance_evidence: bool,
    ) -> None:
        ordinary = _unique_nonempty("ordinary_slot_ids", ordinary_slot_ids)
        exception = self.ledger._get(exception_slot_id)
        if not _boolean("governance_evidence", governance_evidence):
            raise ModelRed(RedCode.PERMISSION_DENIED, "governance_evidence", "critical exception denied")
        if exception.state != SlotState.VACANT:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "exception_slot_id", "must be vacant")
        for slot_id in ordinary:
            slot = self.ledger._get(slot_id)
            if slot_id != exception_slot_id and slot.state != SlotState.VACANT:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "ordinary_slot_ids", "all must be vacant")
        for slot_id in ordinary:
            if slot_id != exception_slot_id:
                self.ledger.freeze(slot_id)
        self.ledger.reserve(exception_slot_id, f"critical:{_nonempty('role_id', role_id)}")

    def zero_based_reallocate(self, window_id: str, assignments: Mapping[str, str]) -> None:
        window_id = _nonempty("window_id", window_id)
        if window_id in self.review_windows:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "window_id", "already reviewed")
        if set(assignments) != set(self.ledger.slots):
            raise ModelRed(RedCode.INVARIANT_BREACH, "assignments", "must allocate every existing slot exactly once")
        normalized_owners = {
            slot_id: _nonempty("new_owner", new_owner)
            for slot_id, new_owner in assignments.items()
        }
        for slot_id in assignments:
            slot = self.ledger._get(slot_id)
            if slot.state not in (SlotState.OCCUPIED, SlotState.VACANT, SlotState.FROZEN):
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "slot", "reserved/reclaimed slot cannot reallocate")
        for slot_id, new_owner in normalized_owners.items():
            slot = self.ledger._get(slot_id)
            if slot.state == SlotState.OCCUPIED:
                slot.owner_id = new_owner
            else:
                self.ledger.transfer_owner(slot_id, new_owner)
        self.review_windows.add(window_id)
        self.assert_hc_conserved()

    def audit_hoarded_slot(self, slot_id: str, *, vacancy_months: int, real_candidate: bool) -> None:
        vacancy_months = _integer("vacancy_months", vacancy_months, minimum=0)
        if vacancy_months < 12:
            raise ModelRed(RedCode.INVALID_VALUE, "vacancy_months", "audit threshold not reached")
        if _boolean("real_candidate", real_candidate):
            return
        self.ledger.reclaim(slot_id)
        self.audit_flags.append(f"hoarding:{slot_id}")

    def source_mix(
        self,
        assignments: Sequence[tuple[str, HireCandidate]],
        *,
        internal_origin_team: str | None = None,
    ) -> int:
        external_growth_before = self.external_character_growth
        seen_slots: set[str] = set()
        for slot_id, candidate in assignments:
            if slot_id in seen_slots:
                raise ModelRed(RedCode.DUPLICATE_ID, "slot_id", slot_id)
            seen_slots.add(slot_id)
            if candidate.source == "internal":
                if internal_origin_team is None:
                    raise ModelRed(RedCode.INVALID_VALUE, "internal_origin_team", "required")
                reservation_id = f"move:{candidate.candidate_id}"
                self.ledger.reserve(slot_id, reservation_id)
                self.ledger.occupy(slot_id, reservation_id, candidate.candidate_id)
                self.assign_backfill(
                    departure_id=reservation_id,
                    slot_id=f"backfill:{candidate.candidate_id}",
                    owner_id=internal_origin_team,
                    virtual=True,
                )
            else:
                self.recruit(slot_id, candidate)
        return self.external_character_growth - external_growth_before

    def assign_backfill(
        self,
        *,
        departure_id: str,
        slot_id: str,
        owner_id: str,
        virtual: bool = False,
    ) -> None:
        departure_id = _nonempty("departure_id", departure_id)
        slot_id = _nonempty("slot_id", slot_id)
        owner_id = _nonempty("owner_id", owner_id)
        if departure_id in self.backfill_by_departure:
            raise ModelRed(RedCode.DUPLICATE_ID, "departure_id", "backfill already assigned")
        if not virtual:
            if slot_id not in self.ledger.slots:
                raise ModelRed(RedCode.INVALID_VALUE, "slot_id", "unknown physical slot")
            self.ledger.transfer_owner(slot_id, owner_id)
        self.backfill_by_departure[departure_id] = (slot_id, owner_id)


class ReadinessBand(str, Enum):
    READY_NOW = "ready-now"
    READY_TWO_YEARS = "ready-two-years"
    LONG_TERM = "long-term"
    NO_SUCCESSOR = "no-successor"


@dataclass
class SuccessionCandidate:
    candidate_id: str
    band: ReadinessBand
    mentor_id: str | None
    due_day: int | None
    evidence_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _nonempty("candidate_id", self.candidate_id)
        self.band = ReadinessBand(self.band)
        if self.band != ReadinessBand.NO_SUCCESSOR:
            if self.mentor_id is not None:
                _nonempty("mentor_id", self.mentor_id)
            if self.due_day is not None:
                _integer("due_day", self.due_day, minimum=1)
        self.evidence_ids = _unique_nonempty("evidence_ids", self.evidence_ids)


@dataclass
class ActingTrial:
    trial_id: str
    candidate_id: str
    authority: frozenset[str]
    resource_amount: int
    goal_id: str
    end_day: int
    settled: bool = False
    succeeded: bool | None = None

    def __post_init__(self) -> None:
        _nonempty("trial_id", self.trial_id)
        _nonempty("candidate_id", self.candidate_id)
        if not self.authority:
            raise ModelRed(RedCode.INVALID_VALUE, "authority", "acting trial requires real authority")
        _integer("resource_amount", self.resource_amount, minimum=1)
        _nonempty("goal_id", self.goal_id)
        _integer("end_day", self.end_day, minimum=1)

    def settle(self, *, current_day: int, succeeded: bool) -> None:
        current_day = _integer("current_day", current_day, minimum=1)
        if current_day < self.end_day:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "current_day", "trial not due")
        if self.settled:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "trial", "already settled")
        if not isinstance(succeeded, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "succeeded", "must be bool")
        self.settled = True
        self.succeeded = succeeded
        self.authority = frozenset()


class AttritionKind(str, Enum):
    REGRETTABLE = "regrettable"
    HEALTHY = "healthy"
    MISEVALUATED = "misevaluated"


@dataclass
class AttritionCase:
    case_id: str
    person_id: str
    kind: AttritionKind
    manager_id: str
    hc_released: bool = False
    history: list[AttritionKind] = field(default_factory=list)

    def __post_init__(self) -> None:
        for name in ("case_id", "person_id", "manager_id"):
            _nonempty(name, getattr(self, name))
        self.kind = AttritionKind(self.kind)
        self.history.append(self.kind)

    def revise_for_later_success(self) -> None:
        if self.kind == AttritionKind.MISEVALUATED:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "attrition", "already revised")
        self.kind = AttritionKind.MISEVALUATED
        self.history.append(self.kind)

    def release_hc_once(self) -> None:
        if self.hc_released:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "hc_released", "already released")
        self.hc_released = True


@dataclass
class StayPromise:
    promise_id: str
    kind: str
    amount: int
    due_day: int
    settled: bool = False
    debt: bool = False

    def __post_init__(self) -> None:
        _nonempty("promise_id", self.promise_id)
        if self.kind not in {"money", "opportunity", "authority", "mobility", "friction_relief"}:
            raise ModelRed(RedCode.INVALID_VALUE, "kind", self.kind)
        _integer("amount", self.amount, minimum=0)
        _integer("due_day", self.due_day, minimum=1)


@dataclass
class SuccessionPlan:
    """Domain O: role/person labels, readiness, trials, retention and knowledge."""

    role_id: str
    critical_role: bool = False
    key_talent: set[str] = field(default_factory=set)
    candidates: dict[str, SuccessionCandidate] = field(default_factory=dict)
    trials: dict[str, ActingTrial] = field(default_factory=dict)
    high_potential_readers: dict[str, frozenset[str]] = field(default_factory=dict)
    high_potential_expiry: dict[str, int] = field(default_factory=dict)
    frozen_performance: dict[str, str] = field(default_factory=dict)
    potential: dict[str, int] = field(default_factory=dict)
    attrition: dict[str, AttritionCase] = field(default_factory=dict)
    stay_promises: dict[str, StayPromise] = field(default_factory=dict)
    knowledge_holders: dict[str, set[str]] = field(default_factory=dict)
    teaching_milestones: set[tuple[str, str]] = field(default_factory=set)

    def __post_init__(self) -> None:
        _nonempty("role_id", self.role_id)

    def label_role_and_talent(self, *, role_critical: bool, person_id: str, person_key: bool) -> None:
        if not isinstance(role_critical, bool) or not isinstance(person_key, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "labels", "must be bool")
        person_id = _nonempty("person_id", person_id)
        self.critical_role = role_critical
        if person_key:
            self.key_talent.add(person_id)
        else:
            self.key_talent.discard(person_id)

    def set_readiness(self, candidate: SuccessionCandidate) -> None:
        self.candidates[candidate.candidate_id] = candidate

    def advance_readiness(
        self,
        candidate_id: str,
        *,
        current_day: int,
        goals_complete: bool,
    ) -> None:
        candidate_id = _nonempty("candidate_id", candidate_id)
        candidate = self.candidates.get(candidate_id)
        if candidate is None:
            raise ModelRed(RedCode.INVALID_VALUE, "candidate_id", "not in succession pool")
        if candidate.band != ReadinessBand.READY_TWO_YEARS:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "band", "candidate not in two-year band")
        if candidate.due_day is None or current_day < candidate.due_day or not _boolean("goals_complete", goals_complete):
            raise ModelRed(RedCode.PERMISSION_DENIED, "readiness", "due date/evidence incomplete")
        candidate.band = ReadinessBand.READY_NOW

    def start_trial(self, trial: ActingTrial) -> None:
        if trial.candidate_id not in self.candidates:
            raise ModelRed(RedCode.PERMISSION_DENIED, "candidate_id", "not in succession pool")
        if trial.candidate_id in (item.candidate_id for item in self.trials.values() if not item.settled):
            raise ModelRed(RedCode.DUPLICATE_ID, "candidate_id", "active trial already exists")
        if trial.trial_id in self.trials:
            raise ModelRed(RedCode.DUPLICATE_ID, "trial_id", trial.trial_id)
        self.trials[trial.trial_id] = trial

    def settle_trial(self, trial_id: str, *, current_day: int, succeeded: bool) -> None:
        trial_id = _nonempty("trial_id", trial_id)
        try:
            trial = self.trials[trial_id]
        except KeyError as exc:
            raise ModelRed(RedCode.INVALID_VALUE, "trial_id", trial_id) from exc
        trial.settle(current_day=current_day, succeeded=succeeded)
        if succeeded:
            self.candidates[trial.candidate_id].band = ReadinessBand.READY_NOW

    def mark_high_potential(
        self,
        person_id: str,
        *,
        readers: Iterable[str],
        expiry_day: int,
    ) -> None:
        person_id = _nonempty("person_id", person_id)
        reader_set = frozenset(_unique_nonempty("readers", readers))
        if person_id not in reader_set:
            raise ModelRed(RedCode.PRIVACY_BREACH, "readers", "subject must be able to read own label")
        self.high_potential_readers[person_id] = reader_set
        self.high_potential_expiry[person_id] = _integer("expiry_day", expiry_day, minimum=1)

    def can_read_high_potential(self, person_id: str, reader_id: str) -> bool:
        return reader_id in self.high_potential_readers.get(person_id, frozenset())

    def freeze_performance_before_potential(
        self,
        person_id: str,
        grade: str,
        potential_score: int,
    ) -> None:
        person_id = _nonempty("person_id", person_id)
        if grade not in {"3.25", "3.5", "3.75"}:
            raise ModelRed(RedCode.INVALID_VALUE, "grade", grade)
        self.frozen_performance[person_id] = grade
        self.potential[person_id] = _integer("potential_score", potential_score, minimum=0, maximum=100)

    def record_attrition(self, case: AttritionCase) -> None:
        if case.case_id in self.attrition:
            raise ModelRed(RedCode.DUPLICATE_ID, "case_id", case.case_id)
        self.attrition[case.case_id] = case

    def make_stay_promise(self, promise: StayPromise) -> None:
        if self.stay_promises:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "stay_promise", "one promise per interview")
        self.stay_promises[promise.promise_id] = promise

    def settle_stay_promise(self, promise_id: str, budget: MoneyLedger | None = None) -> None:
        promise_id = _nonempty("promise_id", promise_id)
        try:
            promise = self.stay_promises[promise_id]
        except KeyError as exc:
            raise ModelRed(RedCode.INVALID_VALUE, "promise_id", promise_id) from exc
        if promise.settled:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "promise", "already settled")
        if promise.kind == "money":
            if budget is None:
                raise ModelRed(RedCode.INVALID_VALUE, "budget", "money promise requires payer")
            budget.reserve(promise.promise_id, promise.amount)
            budget.settle(promise.promise_id, "retained-person")
        promise.settled = True
        promise.debt = False

    def mark_stay_promise_overdue(self, promise_id: str, *, current_day: int) -> None:
        promise = self.stay_promises[promise_id]
        if current_day <= promise.due_day or promise.settled:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "promise", "not overdue")
        promise.debt = True

    def register_knowledge(self, knowledge_id: str, holder_id: str) -> None:
        knowledge_id = _nonempty("knowledge_id", knowledge_id)
        holder_id = _nonempty("holder_id", holder_id)
        self.knowledge_holders.setdefault(knowledge_id, set()).add(holder_id)

    def transfer_knowledge(
        self,
        knowledge_id: str,
        *,
        teacher_id: str,
        deputy_id: str,
        milestone_id: str,
    ) -> None:
        knowledge_id = _nonempty("knowledge_id", knowledge_id)
        teacher_id = _nonempty("teacher_id", teacher_id)
        deputy_id = _nonempty("deputy_id", deputy_id)
        milestone_id = _nonempty("milestone_id", milestone_id)
        holders = self.knowledge_holders.get(knowledge_id, set())
        if teacher_id not in holders:
            raise ModelRed(RedCode.PERMISSION_DENIED, "teacher_id", "teacher lacks knowledge")
        receipt = (knowledge_id, milestone_id)
        if receipt in self.teaching_milestones:
            raise ModelRed(RedCode.DUPLICATE_ID, "milestone_id", "already credited")
        holders.add(deputy_id)
        self.knowledge_holders[knowledge_id] = holders
        self.teaching_milestones.add(receipt)

    @property
    def knowledge_coverage_percent(self) -> int:
        if not self.knowledge_holders:
            return 0
        covered = sum(len(holders) >= 2 for holders in self.knowledge_holders.values())
        return (covered * 100) // len(self.knowledge_holders)


class MobilityState(str, Enum):
    APPLIED = "applied"
    FINALIST = "finalist"
    ACCEPTED = "accepted"
    RELEASE_DUE = "release-due"
    TRANSFERRED = "transferred"
    PROTECTED = "protected"
    CLOSED = "closed"
    BLOCKED = "blocked"


class HiringQuality(str, Enum):
    SUCCESS = "success"
    MISPLACED = "misplaced"
    PROBATION_FAILED = "probation-failed"


@dataclass
class MentorPlan:
    mentor_id: str
    capacity_units: int
    teaching_hours: int
    milestones: dict[int, bool] = field(default_factory=lambda: {3: False, 6: False, 12: False})
    independent_delivery: bool = False
    credit_settled: bool = False

    def __post_init__(self) -> None:
        _nonempty("mentor_id", self.mentor_id)
        _integer("capacity_units", self.capacity_units, minimum=1)
        _integer("teaching_hours", self.teaching_hours, minimum=1)
        if set(self.milestones) != {3, 6, 12}:
            raise ModelRed(RedCode.INVALID_VALUE, "milestones", "must be 3/6/12 months")

    def complete_milestone(self, month: int) -> None:
        month = _integer("month", month, minimum=1)
        if month not in self.milestones:
            raise ModelRed(RedCode.INVALID_VALUE, "month", "not a frozen milestone")
        if self.milestones[month]:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "milestone", "already settled")
        self.milestones[month] = True

    def settle_credit(self, *, independent_delivery: bool) -> None:
        if self.credit_settled:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "mentor_credit", "already settled")
        if not independent_delivery:
            raise ModelRed(RedCode.PERMISSION_DENIED, "independent_delivery", "evidence required")
        self.independent_delivery = True
        self.credit_settled = True


@dataclass
class MobilityCase(GuardedCase):
    """Domain P: anonymous application through release, protection and writeback."""

    vacancy_id: str = "vacancy"
    origin_team_id: str = "origin"
    target_team_id: str = "target"
    applicant_id: str = "applicant"
    legal_vacancy: bool = True
    identity_visible_to_origin: bool = False
    origin_notified_count: int = 0
    accepted: bool = False
    release_start_day: int | None = None
    release_due_day: int | None = None
    extension_used: bool = False
    transferred: bool = False
    backfill_settled: bool = False
    protection_used_lifetime: bool = False
    participation_percent: int = 100
    old_review_ids: tuple[str, ...] = ()
    quality_outcome: HiringQuality | None = None
    quality_receivers: tuple[str, ...] = ()
    mentor_plan: MentorPlan | None = None
    export_credit_settled: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        for name in ("vacancy_id", "origin_team_id", "target_team_id", "applicant_id"):
            _nonempty(name, getattr(self, name))
        if not isinstance(self.legal_vacancy, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "legal_vacancy", "must be bool")
        self.old_review_ids = _unique_nonempty("old_review_ids", self.old_review_ids)

    def anonymous_origin_view(self) -> dict[str, object]:
        if not self.identity_visible_to_origin:
            return {"has_application": False, "applicant_id": None}
        return {"has_application": True, "applicant_id": self.applicant_id}

    def reach_finalist(
        self,
        token: CaseToken,
        action_serial: str,
    ) -> MutationOutcome:
        def operation() -> None:
            if not self.legal_vacancy:
                raise ModelRed(RedCode.PERMISSION_DENIED, "vacancy", "not legal")
            self.identity_visible_to_origin = True
            self.origin_notified_count += 1

        return self.mutate(115, token, action_serial, operation, next_state=MobilityState.FINALIST.value)

    def accept(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        start_day: int,
    ) -> MutationOutcome:
        def operation() -> None:
            if not self.legal_vacancy or not self.identity_visible_to_origin:
                raise ModelRed(RedCode.PERMISSION_DENIED, "accept", "not a legal notified finalist")
            self.accepted = True
            self.release_start_day = _integer("start_day", start_day, minimum=1)
            self.release_due_day = self.release_start_day + 90

        return self.mutate(116, token, action_serial, operation, next_state=MobilityState.RELEASE_DUE.value)

    def extend_release_once(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        critical_delivery: bool,
        succession_plan: bool,
    ) -> MutationOutcome:
        def operation() -> None:
            critical = _boolean("critical_delivery", critical_delivery)
            succession = _boolean("succession_plan", succession_plan)
            if not (critical and succession):
                raise ModelRed(RedCode.PERMISSION_DENIED, "extension", "delivery and succession evidence required")
            if self.extension_used or self.release_due_day is None:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "extension", "one extension only")
            self.extension_used = True
            self.release_due_day += 60

        return self.mutate(116, token, action_serial, operation)

    def transfer(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        current_day: int,
    ) -> MutationOutcome:
        def operation() -> None:
            if not self.accepted or self.release_due_day is None:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "transfer", "not accepted")
            _integer("current_day", current_day, minimum=1)
            if self.transferred:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "transfer", "already moved")
            self.transferred = True
            self.backfill_settled = True
            self.export_credit_settled = True

        return self.mutate(114, token, action_serial, operation, next_state=MobilityState.TRANSFERRED.value)

    def start_ramp_protection(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        participation_percent: int,
    ) -> MutationOutcome:
        def operation() -> None:
            if not self.transferred or self.protection_used_lifetime:
                raise ModelRed(RedCode.ILLEGAL_TRANSITION, "protection", "unavailable")
            self.participation_percent = _integer(
                "participation_percent", participation_percent, minimum=0, maximum=100
            )
            self.protection_used_lifetime = True

        return self.mutate(117, token, action_serial, operation, next_state=MobilityState.PROTECTED.value)

    def expire_ramp_protection(self) -> None:
        if not self.protection_used_lifetime:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "protection", "never started")
        self.participation_percent = 100

    @staticmethod
    def probation_and_bottom_quota(
        *,
        regular_count: int,
        probation_pass: Sequence[bool],
        bottom_quota: int,
    ) -> dict[str, int]:
        regular_count = _integer("regular_count", regular_count, minimum=0)
        bottom_quota = _integer("bottom_quota", bottom_quota, minimum=0, maximum=regular_count)
        if not all(isinstance(value, bool) for value in probation_pass):
            raise ModelRed(RedCode.INVALID_TYPE, "probation_pass", "booleans required")
        return {
            "regular_denominator": regular_count,
            "regular_bottom_slots": bottom_quota,
            "probation_failures": sum(not value for value in probation_pass),
        }

    def write_hiring_quality(
        self,
        outcome: HiringQuality,
        *,
        proposer_id: str,
        selector_id: str,
        approver_id: str,
    ) -> None:
        if self.quality_outcome is not None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "quality_outcome", "already settled")
        self.quality_outcome = HiringQuality(outcome)
        self.quality_receivers = _unique_nonempty(
            "quality_receivers", (proposer_id, selector_id, approver_id)
        )

    def assign_mentor(self, plan: MentorPlan) -> None:
        if self.mentor_plan is not None:
            raise ModelRed(RedCode.DUPLICATE_ID, "mentor_plan", "one formal mentor at a time")
        self.mentor_plan = plan


@dataclass(frozen=True)
class SubordinateSurvey:
    subordinate_id: str
    credibility: int
    goal_clarity: int
    resources: int
    feedback: int
    delegation: int
    fairness: int
    development: int

    def __post_init__(self) -> None:
        _nonempty("subordinate_id", self.subordinate_id)
        _integer("credibility", self.credibility, minimum=0, maximum=100)
        for name in ("goal_clarity", "resources", "feedback", "delegation", "fairness", "development"):
            _integer(name, getattr(self, name), minimum=0, maximum=100)

    @property
    def mean(self) -> float:
        return sum(
            (
                self.goal_clarity,
                self.resources,
                self.feedback,
                self.delegation,
                self.fairness,
                self.development,
            )
        ) / 6


class ValuesQuadrant(str, Enum):
    DOUBLE_HIGH = "double-high"
    WILD_DOG = "wild-dog"
    RABBIT = "rabbit"
    DOUBLE_LOW = "double-low"


@dataclass(frozen=True)
class ClimateSnapshot:
    cycle_serial: int
    pressure: int
    collaboration: int
    risk_reporting: int
    peer_credibility: int
    regrettable_attrition: int

    def __post_init__(self) -> None:
        _integer("cycle_serial", self.cycle_serial, minimum=1)
        for name in ("pressure", "collaboration", "risk_reporting", "peer_credibility", "regrettable_attrition"):
            _integer(name, getattr(self, name), minimum=0, maximum=100)


@dataclass
class ManagerCertification(GuardedCase):
    """Domain Q: manager trial, scorecard, feedback, successor and climate."""

    boundary: ManagerBoundary = ManagerBoundary(TitleRank.DUKE, True, True)
    trial_team: tuple[str, ...] = ()
    mentor_id: str | None = None
    skip_reviewer_id: str | None = None
    trial_due_day: int | None = None
    score_components: tuple[int, int, int] | None = None
    score_weights: tuple[int, int, int] | None = None
    surveys: dict[str, SubordinateSurvey] = field(default_factory=dict)
    successor_id: str | None = None
    successor_accepted: bool = False
    promotion_released: bool = False
    crisis_receipts: set[str] = field(default_factory=set)
    span_snapshot: tuple[str, ...] = ()
    climate: ClimateSnapshot | None = None
    next_cycle_policy: str | None = None

    def __post_init__(self) -> None:
        super().__post_init__()
        self.boundary.require_manager()

    def start_trial(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        team: Iterable[str],
        max_team_size: int,
        mentor_id: str,
        skip_reviewer_id: str,
        due_day: int,
    ) -> MutationOutcome:
        def operation() -> None:
            team_tuple = _unique_nonempty("team", team)
            maximum = _integer("max_team_size", max_team_size, minimum=1)
            if len(team_tuple) > maximum:
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "team", "trial span exceeds maximum")
            self.trial_team = team_tuple
            self.mentor_id = _nonempty("mentor_id", mentor_id)
            self.skip_reviewer_id = _nonempty("skip_reviewer_id", skip_reviewer_id)
            self.trial_due_day = _integer("due_day", due_day, minimum=1)

        return self.mutate(121, token, action_serial, operation, next_state="TRIAL")

    def freeze_scorecard(
        self,
        token: CaseToken,
        action_serial: str,
        *,
        hard_results: int,
        people_organization: int,
        values_process: int,
        weights: tuple[int, int, int] = (40, 30, 30),
    ) -> MutationOutcome:
        def operation() -> None:
            if weights != (40, 30, 30):
                raise ModelRed(RedCode.INVARIANT_BREACH, "weights", "must be 40/30/30")
            self.score_components = tuple(
                _integer(name, value, minimum=0, maximum=100)
                for name, value in zip(
                    ("hard_results", "people_organization", "values_process"),
                    (hard_results, people_organization, values_process),
                )
            )
            self.score_weights = weights

        return self.mutate(122, token, action_serial, operation)

    @property
    def scorecard_total(self) -> float:
        if self.score_components is None or self.score_weights is None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "scorecard", "not frozen")
        return sum(score * weight for score, weight in zip(self.score_components, self.score_weights)) / 100

    def add_subordinate_survey(self, survey: SubordinateSurvey) -> None:
        if survey.subordinate_id in self.surveys:
            raise ModelRed(RedCode.DUPLICATE_ID, "subordinate_id", "one survey per subordinate")
        self.surveys[survey.subordinate_id] = survey

    @property
    def credible_feedback_score(self) -> float:
        denominator = sum(survey.credibility for survey in self.surveys.values())
        if denominator == 0:
            return 0.0
        return sum(survey.mean * survey.credibility for survey in self.surveys.values()) / denominator

    def bind_successor(self, successor_id: str, *, accepted: bool) -> None:
        self.successor_id = _nonempty("successor_id", successor_id)
        if not isinstance(accepted, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "accepted", "must be bool")
        self.successor_accepted = accepted

    def release_promotion(self) -> None:
        if self.promotion_released:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "promotion", "already released")
        if not self.successor_id or not self.successor_accepted:
            raise ModelRed(RedCode.PERMISSION_DENIED, "successor", "accepted successor required")
        self.promotion_released = True

    def settle_crisis(
        self,
        incident_id: str,
        *,
        budget_hours: int,
        manager_hours: int,
        subordinate_hours: int,
        subordinate_led: bool,
        succeeded: bool,
    ) -> dict[str, bool]:
        incident_id = _nonempty("incident_id", incident_id)
        if incident_id in self.crisis_receipts:
            raise ModelRed(RedCode.DUPLICATE_ID, "incident_id", "already settled")
        budget = _integer("budget_hours", budget_hours, minimum=0)
        manager = _integer("manager_hours", manager_hours, minimum=0)
        subordinate = _integer("subordinate_hours", subordinate_hours, minimum=0)
        subordinate_led = _boolean("subordinate_led", subordinate_led)
        succeeded = _boolean("succeeded", succeeded)
        if manager + subordinate > budget:
            raise ModelRed(RedCode.INVARIANT_BREACH, "crisis_hours", "hours exceed budget")
        self.crisis_receipts.add(incident_id)
        return {
            "successor_evidence": bool(subordinate_led and succeeded),
            "hero_credit": bool((not subordinate_led) and succeeded),
            "opportunity_loss": bool(not subordinate_led),
        }

    @staticmethod
    def classify_quadrant(*, performance_high: bool, values_high: bool) -> ValuesQuadrant:
        if not isinstance(performance_high, bool) or not isinstance(values_high, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "quadrant", "booleans required")
        return {
            (True, True): ValuesQuadrant.DOUBLE_HIGH,
            (True, False): ValuesQuadrant.WILD_DOG,
            (False, True): ValuesQuadrant.RABBIT,
            (False, False): ValuesQuadrant.DOUBLE_LOW,
        }[(performance_high, values_high)]

    def freeze_span(self, reports: Iterable[str], *, maximum: int) -> int:
        self.span_snapshot = _unique_nonempty("reports", reports)
        maximum = _integer("maximum", maximum, minimum=1)
        return max(0, len(self.span_snapshot) - maximum)

    def record_climate(self, snapshot: ClimateSnapshot, *, policy: str) -> None:
        if self.climate is not None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "climate", "already frozen")
        if snapshot.cycle_serial != self.identity.cycle_serial:
            raise ModelRed(RedCode.INVARIANT_BREACH, "cycle_serial", "snapshot mismatch")
        self.climate = snapshot
        self.next_cycle_policy = _nonempty("policy", policy)


class PacketState(str, Enum):
    NOMINATED = "nominated"
    PRESCREENED = "prescreened"
    PASSED = "passed"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


@dataclass
class NominationPacket:
    packet_id: str
    candidate_id: str
    manager_id: str
    sponsor_id: str | None
    manager_opinion: str
    quota_id: str
    state: PacketState = PacketState.NOMINATED
    verified_artifacts: tuple[str, ...] = ()
    unverified_artifacts: tuple[str, ...] = ()
    rank: int | None = None
    reason: str | None = None
    is_filler: bool = False
    preparation_hours: int = 0

    def __post_init__(self) -> None:
        for name in ("packet_id", "candidate_id", "manager_id", "manager_opinion", "quota_id"):
            _nonempty(name, getattr(self, name))
        if self.sponsor_id is not None:
            _nonempty("sponsor_id", self.sponsor_id)
        self.state = PacketState(self.state)
        self.verified_artifacts = _unique_nonempty("verified_artifacts", self.verified_artifacts)
        self.unverified_artifacts = _unique_nonempty("unverified_artifacts", self.unverified_artifacts)
        _integer("preparation_hours", self.preparation_hours, minimum=0)


@dataclass
class ShelvedStar:
    candidate_id: str
    successor_id: str
    resource_amount: int
    due_day: int
    nominated: bool = False
    overdue_penalty_cycles: set[int] = field(default_factory=set)

    def __post_init__(self) -> None:
        _nonempty("candidate_id", self.candidate_id)
        _nonempty("successor_id", self.successor_id)
        _integer("resource_amount", self.resource_amount, minimum=1)
        _integer("due_day", self.due_day, minimum=1)


@dataclass(frozen=True)
class SponsorObservation:
    sponsor_id: str
    candidate_id: str
    strength: int
    competent: bool
    due_cycle: int

    def __post_init__(self) -> None:
        _nonempty("sponsor_id", self.sponsor_id)
        _nonempty("candidate_id", self.candidate_id)
        _integer("strength", self.strength, minimum=1, maximum=3)
        if not isinstance(self.competent, bool):
            raise ModelRed(RedCode.INVALID_TYPE, "competent", "must be bool")
        _integer("due_cycle", self.due_cycle, minimum=1)


@dataclass(frozen=True)
class NominationObservation:
    difficulty: int
    passed: bool
    competent: bool
    matured: bool

    def __post_init__(self) -> None:
        _integer("difficulty", self.difficulty, minimum=1, maximum=5)
        if not all(isinstance(value, bool) for value in (self.passed, self.competent, self.matured)):
            raise ModelRed(RedCode.INVALID_TYPE, "nomination_observation", "booleans required")


@dataclass
class NominationBook(GuardedCase):
    """Domain U: access, quota, prescreen, trials, withdrawal and sponsor debt."""

    quota_total: int = 0
    quota_remaining: int = field(init=False)
    quota_returned: int = 0
    packets: dict[str, NominationPacket] = field(default_factory=dict)
    candidate_packets: dict[str, str] = field(default_factory=dict)
    shelved: dict[str, ShelvedStar] = field(default_factory=dict)
    tenure_exception_total: int = 0
    tenure_exception_used: int = 0
    observation_window: tuple[int, ...] = ()
    cross_team_evidence: dict[str, dict[str, int]] = field(default_factory=dict)
    next_level_trials: dict[str, dict[str, object]] = field(default_factory=dict)
    sponsor_credit: dict[str, int] = field(default_factory=dict)
    sponsor_observations_settled: set[tuple[str, str, int]] = field(default_factory=set)
    manager_observations: list[NominationObservation] = field(default_factory=list)
    fairness_debt: int = 0
    readiness_risk: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        super().__post_init__()
        self.quota_total = _integer("quota_total", self.quota_total, minimum=0)
        self.quota_remaining = self.quota_total
        self.tenure_exception_total = _integer(
            "tenure_exception_total", self.tenure_exception_total, minimum=0
        )

    @property
    def quota_used(self) -> int:
        return sum(
            packet.state not in {PacketState.WITHDRAWN}
            for packet in self.packets.values()
        )

    def assert_quota_conserved(self) -> None:
        if self.quota_total != self.quota_used + self.quota_returned + self.quota_remaining:
            raise ModelRed(
                RedCode.INVARIANT_BREACH,
                "nomination_quota",
                "used+returned+remaining != initial",
            )
        if self.quota_remaining < 0:
            raise ModelRed(RedCode.INVARIANT_BREACH, "nomination_quota", "negative")

    def nominate(
        self,
        token: CaseToken,
        action_serial: str,
        packet: NominationPacket,
        *,
        self_nomination: bool,
    ) -> MutationOutcome:
        def operation() -> None:
            self_nomination_value = _boolean("self_nomination", self_nomination)
            if self_nomination_value and (not packet.sponsor_id or not packet.manager_opinion):
                raise ModelRed(RedCode.PERMISSION_DENIED, "self_nomination", "sponsor and manager opinion required")
            if packet.candidate_id in self.candidate_packets:
                raise ModelRed(RedCode.DUPLICATE_ID, "candidate_id", "one packet per cycle")
            if self.quota_remaining <= 0:
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "nomination_quota", "no remaining quota")
            self.packets[packet.packet_id] = packet
            self.candidate_packets[packet.candidate_id] = packet.packet_id
            self.quota_remaining -= 1
            self.assert_quota_conserved()

        return self.mutate(157, token, action_serial, operation, next_state="NOMINATED")

    def return_unused_quota(self, amount: int) -> None:
        amount = _integer("amount", amount, minimum=0)
        if amount > self.quota_remaining:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "quota_remaining", "cannot return more than remaining")
        self.quota_remaining -= amount
        self.quota_returned += amount
        self.assert_quota_conserved()

    def rank_packets(self, packet_ids: Sequence[str]) -> None:
        packet_ids = _unique_nonempty("packet_ids", packet_ids)
        if set(packet_ids) != set(self.packets):
            raise ModelRed(RedCode.INVARIANT_BREACH, "packet_ids", "rank every packet exactly once")
        for rank, packet_id in enumerate(packet_ids, start=1):
            self.packets[packet_id].rank = rank

    def shelve_star(self, record: ShelvedStar) -> None:
        if record.candidate_id in self.shelved:
            raise ModelRed(RedCode.DUPLICATE_ID, "candidate_id", "already shelved")
        self.shelved[record.candidate_id] = record

    def audit_shelving(self, candidate_id: str, *, current_day: int, cycle_serial: int) -> bool:
        record = self.shelved[candidate_id]
        if record.nominated or current_day <= record.due_day:
            return False
        if cycle_serial in record.overdue_penalty_cycles:
            return False
        record.overdue_penalty_cycles.add(cycle_serial)
        return True

    def prescreen(
        self,
        scores: Mapping[str, tuple[int, int, int]],
        *,
        seats: int,
    ) -> tuple[str, ...]:
        seats = _integer("seats", seats, minimum=0)
        if set(scores) != set(self.packets):
            raise ModelRed(RedCode.INVARIANT_BREACH, "scores", "every packet requires a score")
        ranked: list[tuple[int, str]] = []
        for packet_id, dimensions in scores.items():
            if len(dimensions) != 3:
                raise ModelRed(RedCode.INVALID_VALUE, "dimensions", "three rubric scores required")
            total = sum(_integer("rubric_score", value, minimum=0, maximum=100) for value in dimensions)
            ranked.append((total, packet_id))
        winners = tuple(packet_id for _, packet_id in sorted(ranked, reverse=True)[:seats])
        for packet_id, packet in self.packets.items():
            packet.state = PacketState.PRESCREENED if packet_id in winners else PacketState.REJECTED
            packet.reason = "rubric-pass" if packet_id in winners else "rubric-cut"
        return winners

    def mark_filler(self, packet_id: str, *, preparation_hours: int) -> None:
        packet = self.packets[packet_id]
        packet.is_filler = True
        packet.preparation_hours = _integer("preparation_hours", preparation_hours, minimum=1)

    def identify_sham(self, filler_packet_id: str, main_packet_id: str) -> None:
        if filler_packet_id == main_packet_id:
            raise ModelRed(RedCode.INVARIANT_BREACH, "sham", "filler and main must differ")
        filler = self.packets[filler_packet_id]
        if not filler.is_filler:
            raise ModelRed(RedCode.INVALID_VALUE, "filler_packet_id", "not marked filler")
        self.fairness_debt += 1

    def admit_tenure_exception(self, candidate_id: str, *, vote_passed: bool) -> bool:
        _nonempty("candidate_id", candidate_id)
        if self.tenure_exception_used >= self.tenure_exception_total:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "tenure_exception", "no quota")
        self.tenure_exception_used += 1
        return _boolean("vote_passed", vote_passed)

    def freeze_observation_window(
        self,
        cycle_serials: Iterable[int],
        *,
        candidate_histories: Mapping[str, Sequence[int]],
    ) -> None:
        window = tuple(_integer("cycle_serial", value, minimum=1) for value in cycle_serials)
        if not window:
            raise ModelRed(RedCode.INVALID_VALUE, "cycle_serials", "window required")
        if self.observation_window:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "observation_window", "already frozen")
        for candidate_id, history in candidate_histories.items():
            _nonempty("candidate_id", candidate_id)
            if not set(window).issubset(set(history)):
                raise ModelRed(RedCode.INVARIANT_BREACH, "candidate_histories", "window not present")
        self.observation_window = window

    def add_cross_team_evidence(
        self,
        result_id: str,
        shares: Mapping[str, int],
        *,
        owner_signed: bool,
        independently_reviewed: bool,
    ) -> None:
        result_id = _nonempty("result_id", result_id)
        normalized = {
            _nonempty("contributor_id", key): _integer("share", value, minimum=0, maximum=100)
            for key, value in shares.items()
        }
        if sum(normalized.values()) > 100:
            raise ModelRed(RedCode.INVARIANT_BREACH, "shares", "contribution exceeds 100")
        owner_signed = _boolean("owner_signed", owner_signed)
        independently_reviewed = _boolean("independently_reviewed", independently_reviewed)
        if not owner_signed and not independently_reviewed:
            raise ModelRed(RedCode.PERMISSION_DENIED, "evidence", "cosign or review required")
        if result_id in self.cross_team_evidence:
            raise ModelRed(RedCode.DUPLICATE_ID, "result_id", result_id)
        self.cross_team_evidence[result_id] = normalized

    def start_next_level_trial(
        self,
        candidate_id: str,
        *,
        authority: Iterable[str],
        compensation: int,
        due_day: int,
        exit_condition: str,
    ) -> None:
        candidate_id = _nonempty("candidate_id", candidate_id)
        authority_set = frozenset(_unique_nonempty("authority", authority))
        if not authority_set:
            raise ModelRed(RedCode.INVALID_VALUE, "authority", "required")
        _integer("compensation", compensation, minimum=0)
        _integer("due_day", due_day, minimum=1)
        _nonempty("exit_condition", exit_condition)
        if candidate_id in self.next_level_trials:
            raise ModelRed(RedCode.DUPLICATE_ID, "candidate_id", "trial already exists")
        self.next_level_trials[candidate_id] = {
            "authority": authority_set,
            "compensation": compensation,
            "due_day": due_day,
            "exit_condition": exit_condition,
            "settled": False,
        }

    def withdraw_packet(self, packet_id: str) -> tuple[str, ...]:
        packet = self.packets[packet_id]
        if packet.state != PacketState.NOMINATED:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "packet", "withdrawal only before prescreen")
        packet.state = PacketState.WITHDRAWN
        self.quota_remaining += 1
        self.candidate_packets.pop(packet.candidate_id, None)
        self.assert_quota_conserved()
        self.readiness_risk[packet.candidate_id] = self.readiness_risk.get(packet.candidate_id, 0) + 1
        return packet.verified_artifacts

    def settle_sponsor_observation(
        self,
        observation: SponsorObservation,
        *,
        current_cycle: int,
    ) -> int:
        if current_cycle < observation.due_cycle:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "current_cycle", "observation not due")
        key = (observation.sponsor_id, observation.candidate_id, observation.due_cycle)
        if key in self.sponsor_observations_settled:
            raise ModelRed(RedCode.DUPLICATE_ID, "observation", "already settled")
        delta = observation.strength if observation.competent else -observation.strength
        self.sponsor_credit[observation.sponsor_id] = self.sponsor_credit.get(observation.sponsor_id, 0) + delta
        self.sponsor_observations_settled.add(key)
        return delta

    def manager_hit_rate(self, observations: Sequence[NominationObservation], *, omitted_qualified: int = 0) -> float:
        omitted = _integer("omitted_qualified", omitted_qualified, minimum=0)
        matured = [item for item in observations if item.matured]
        self.manager_observations.extend(observations)
        denominator = sum(item.difficulty for item in matured) + omitted
        if denominator == 0:
            return 0.0
        success = sum(item.difficulty for item in matured if item.passed and item.competent)
        return success / denominator


class PanelistKind(str, Enum):
    EXPERT = "expert"
    EXTERNAL = "external"


@dataclass(frozen=True)
class Panelist:
    panelist_id: str
    unit_id: str
    kind: PanelistKind
    conflicts: frozenset[str] = frozenset()
    candidate_team_familiar: bool = False

    def __post_init__(self) -> None:
        _nonempty("panelist_id", self.panelist_id)
        _nonempty("unit_id", self.unit_id)
        PanelistKind(self.kind)
        for conflict in self.conflicts:
            _nonempty("conflict", conflict)


class DecisionRule(str, Enum):
    VETO = "veto"
    MAJORITY = "majority"
    TRIMMED_MEAN = "trimmed-mean"


@dataclass(frozen=True)
class RejectionFeedback:
    owner_id: str
    gap: str
    next_evidence: str
    no_slot: bool = False

    def __post_init__(self) -> None:
        _nonempty("owner_id", self.owner_id)
        _nonempty("gap", self.gap)
        _nonempty("next_evidence", self.next_evidence)


@dataclass
class PromotionPanel(GuardedCase):
    """Domain V: reproducible panel, recusal, blind/live scores and decision."""

    candidate_id: str = "candidate"
    panelists: dict[str, Panelist] = field(default_factory=dict)
    expertise_weights: dict[PanelistKind, int] = field(default_factory=dict)
    recused: set[str] = field(default_factory=set)
    replacement_history: dict[str, str] = field(default_factory=dict)
    decision_rule: DecisionRule | None = None
    votes: dict[str, float] = field(default_factory=dict)
    veto_reasons: dict[str, str] = field(default_factory=dict)
    blind_scores: dict[str, float] = field(default_factory=dict)
    live_scores: dict[str, float] = field(default_factory=dict)
    blind_frozen: bool = False
    final_decision: bool | None = None
    defense_total: int | None = None
    defense_presentation: int = 0
    defense_questions: int = 0
    coaching_opening: int = 0
    coaching_allocations: dict[str, int] = field(default_factory=dict)
    attribution: dict[str, int] = field(default_factory=dict)
    scale_score: int | None = None
    leverage_score: int | None = None
    artifact_score: int | None = None
    narrative_score: int | None = None
    rejection_feedback: list[RejectionFeedback] = field(default_factory=list)
    material_versions: tuple[str, ...] = ()
    frozen_gaps: tuple[str, ...] = ()
    cooldown_until: int | None = None
    retried: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        _nonempty("candidate_id", self.candidate_id)

    def form_panel(
        self,
        pool: Sequence[Panelist],
        *,
        seats: int,
        seed: int,
        expertise_weights: Mapping[PanelistKind, int],
    ) -> tuple[str, ...]:
        seats = _integer("seats", seats, minimum=2)
        seed = _integer("seed", seed)
        if self.panelists:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "panel", "already formed")
        ids = _unique_nonempty("panelist_ids", (item.panelist_id for item in pool))
        if len(ids) < seats:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "pool", "not enough panelists")
        weights = {
            PanelistKind(key): _integer("expertise_weight", value, minimum=0, maximum=100)
            for key, value in expertise_weights.items()
        }
        if set(weights) != {PanelistKind.EXPERT, PanelistKind.EXTERNAL} or sum(weights.values()) != 100:
            raise ModelRed(RedCode.INVARIANT_BREACH, "expertise_weights", "expert/external must sum 100")
        eligible = list(pool)
        rng = random.Random(seed)
        rng.shuffle(eligible)
        selected = eligible[:seats]
        if not {item.kind for item in selected}.issuperset({PanelistKind.EXPERT, PanelistKind.EXTERNAL}):
            # Deterministically repair the smallest possible number of seats.
            missing = ({PanelistKind.EXPERT, PanelistKind.EXTERNAL} - {item.kind for item in selected}).pop()
            replacement = next((item for item in eligible[seats:] if item.kind == missing), None)
            if replacement is None:
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "pool", "mixed expertise unavailable")
            selected[-1] = replacement
        self.panelists = {item.panelist_id: item for item in selected}
        self.expertise_weights = weights
        return tuple(item.panelist_id for item in selected)

    def recuse_conflicts(self, alternates: Sequence[Panelist]) -> None:
        alternate_by_kind: dict[PanelistKind, list[Panelist]] = {
            PanelistKind.EXPERT: [],
            PanelistKind.EXTERNAL: [],
        }
        for alternate in alternates:
            if alternate.panelist_id not in self.panelists and self.candidate_id not in alternate.conflicts:
                alternate_by_kind[alternate.kind].append(alternate)
        for panelist_id, panelist in tuple(self.panelists.items()):
            if self.candidate_id not in panelist.conflicts:
                continue
            candidates = alternate_by_kind[panelist.kind]
            if not candidates:
                raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "alternates", "no clean replacement")
            replacement = candidates.pop(0)
            del self.panelists[panelist_id]
            self.panelists[replacement.panelist_id] = replacement
            self.recused.add(panelist_id)
            self.replacement_history[panelist_id] = replacement.panelist_id

    def freeze_decision_rule(self, rule: DecisionRule) -> None:
        if self.decision_rule is not None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "decision_rule", "already frozen")
        if self.votes:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "decision_rule", "votes already exist")
        self.decision_rule = DecisionRule(rule)

    def blind_review(self, packet: Mapping[str, object], scores: Mapping[str, float]) -> None:
        forbidden = {"name", "candidate_id", "family", "manager", "faction"}
        leaked = forbidden.intersection(packet)
        if leaked:
            raise ModelRed(RedCode.PRIVACY_BREACH, "blind_packet", f"identity fields={sorted(leaked)}")
        if set(scores) != set(self.panelists):
            raise ModelRed(RedCode.INVARIANT_BREACH, "blind_scores", "one score per panelist")
        self.blind_scores = {
            panelist_id: _number("blind_score", score, minimum=0, maximum=100)
            for panelist_id, score in scores.items()
        }
        self.blind_frozen = True

    def live_review(self, scores: Mapping[str, float]) -> None:
        if self.blind_scores and not self.blind_frozen:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "blind_scores", "not frozen")
        if set(scores) != set(self.panelists):
            raise ModelRed(RedCode.INVARIANT_BREACH, "live_scores", "one score per panelist")
        self.live_scores = {
            panelist_id: _number("live_score", score, minimum=0, maximum=100)
            for panelist_id, score in scores.items()
        }

    def record_votes(
        self,
        votes: Mapping[str, float],
        *,
        veto_reasons: Mapping[str, str] | None = None,
    ) -> bool:
        if self.decision_rule is None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "decision_rule", "freeze before votes")
        if self.final_decision is not None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "decision", "already final")
        if set(votes) != set(self.panelists):
            raise ModelRed(RedCode.INVARIANT_BREACH, "votes", "one vote per active panelist")
        normalized_votes = {
            panelist_id: _number("vote", value, minimum=0, maximum=100)
            for panelist_id, value in votes.items()
        }
        reasons = dict(veto_reasons or {})
        if self.decision_rule == DecisionRule.VETO:
            vetoers = {panelist_id for panelist_id, value in normalized_votes.items() if value < 50}
            if vetoers - set(reasons):
                raise ModelRed(RedCode.INVALID_VALUE, "veto_reasons", "every veto needs a reason")
            normalized_reasons = {
                panelist_id: _nonempty("veto_reason", reasons[panelist_id])
                for panelist_id in vetoers
            }
            result = not vetoers
        elif self.decision_rule == DecisionRule.MAJORITY:
            normalized_reasons = {}
            result = sum(value >= 50 for value in normalized_votes.values()) > len(normalized_votes) / 2
        else:
            normalized_reasons = {}
            values = sorted(normalized_votes.values())
            if len(values) < 3:
                raise ModelRed(RedCode.INVALID_VALUE, "votes", "trimmed mean requires >=3")
            result = sum(values[1:-1]) / len(values[1:-1]) >= 60
        self.votes = normalized_votes
        self.veto_reasons = normalized_reasons
        self.final_decision = result
        return result

    def allocate_defense_time(
        self,
        *,
        total: int,
        presentation_requested: int,
        protected_questions: int,
    ) -> tuple[int, int]:
        total = _integer("total", total, minimum=1)
        requested = _integer("presentation_requested", presentation_requested, minimum=0)
        protected = _integer("protected_questions", protected_questions, minimum=0, maximum=total)
        presentation = min(requested, total - protected)
        questions = total - presentation
        self.defense_total = total
        self.defense_presentation = presentation
        self.defense_questions = questions
        return presentation, questions

    def allocate_coaching(self, opening_hours: int, allocations: Mapping[str, int]) -> int:
        opening = _integer("opening_hours", opening_hours, minimum=0)
        normalized = {
            _nonempty("candidate_id", key): _integer("coaching_hours", value, minimum=0)
            for key, value in allocations.items()
        }
        if sum(normalized.values()) > opening:
            raise ModelRed(RedCode.RESOURCE_EXHAUSTED, "coaching_hours", "allocation exceeds pool")
        self.coaching_opening = opening
        self.coaching_allocations = normalized
        return opening - sum(normalized.values())

    def freeze_attribution(self, shares: Mapping[str, int]) -> int:
        self.attribution = _shares_100("attribution", shares)
        if self.candidate_id not in self.attribution:
            raise ModelRed(RedCode.INVALID_VALUE, "candidate_id", "candidate share missing")
        return self.attribution[self.candidate_id]

    def freeze_scale_and_leverage(self, *, scale_score: int, leverage_score: int) -> None:
        self.scale_score = _integer("scale_score", scale_score, minimum=0, maximum=100)
        self.leverage_score = _integer("leverage_score", leverage_score, minimum=0, maximum=100)

    def dual_evidence_gate(
        self,
        *,
        artifact_score: int,
        narrative_score: int,
        artifact_threshold: int,
        narrative_threshold: int,
    ) -> bool:
        self.artifact_score = _integer("artifact_score", artifact_score, minimum=0, maximum=100)
        self.narrative_score = _integer("narrative_score", narrative_score, minimum=0, maximum=100)
        artifact_threshold = _integer("artifact_threshold", artifact_threshold, minimum=0, maximum=100)
        narrative_threshold = _integer("narrative_threshold", narrative_threshold, minimum=0, maximum=100)
        return self.artifact_score >= artifact_threshold and self.narrative_score >= narrative_threshold

    def add_rejection_feedback(self, feedback: RejectionFeedback) -> None:
        if feedback.owner_id not in self.panelists:
            raise ModelRed(RedCode.PERMISSION_DENIED, "owner_id", "must be an actual panelist")
        self.rejection_feedback.append(feedback)

    def freeze_retry(
        self,
        *,
        cooldown_until: int,
        material_versions: Iterable[str],
        gaps: Iterable[str],
    ) -> None:
        if self.cooldown_until is not None:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "retry", "already frozen")
        self.cooldown_until = _integer("cooldown_until", cooldown_until, minimum=1)
        self.material_versions = _unique_nonempty("material_versions", material_versions)
        self.frozen_gaps = _unique_nonempty("gaps", gaps)

    def retry(
        self,
        *,
        current_day: int,
        completed_gaps: Iterable[str] = (),
    ) -> None:
        current_day = _integer("current_day", current_day, minimum=1)
        if self.cooldown_until is None or self.retried:
            raise ModelRed(RedCode.ILLEGAL_TRANSITION, "retry", "not available")
        completed = set(_unique_nonempty("completed_gaps", completed_gaps))
        if current_day < self.cooldown_until and not set(self.frozen_gaps).issubset(completed):
            raise ModelRed(RedCode.PERMISSION_DENIED, "cooldown", "not due and gaps incomplete")
        self.retried = True


def validate_model() -> None:
    """Import-time, side-effect-free checks for the static behavior contract."""

    validate_behavior_registry()
    expected_domains = {
        **{mechanism_id: "D" for mechanism_id in range(19, 26)},
        **{mechanism_id: "M" for mechanism_id in range(92, 98)},
        **{mechanism_id: "N" for mechanism_id in range(98, 106)},
        **{mechanism_id: "O" for mechanism_id in range(106, 114)},
        **{mechanism_id: "P" for mechanism_id in range(114, 121)},
        **{mechanism_id: "Q" for mechanism_id in range(121, 129)},
        **{mechanism_id: "U" for mechanism_id in range(157, 169)},
        **{mechanism_id: "V" for mechanism_id in range(169, 181)},
    }
    for mechanism_id, domain in expected_domains.items():
        if MECHANISM_BEHAVIORS[mechanism_id].domain != domain:
            raise ModelRed(RedCode.INVARIANT_BREACH, "domain", f"{mechanism_id} != {domain}")


validate_model()

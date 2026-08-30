#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic L0 model for the phase-three 361 project/credit slice.

This is deliberately a Python-only executable specification.  It proves
resource conservation, immutable provenance and transaction semantics for
E(026-031), I(054-061), J(062-068), and R(129-134).  It does *not* claim CK3
script wiring, a GUI loop, fixture-live evidence, or production readiness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Mapping


READINESS: Final[str] = "python-l0-only"
SHARE_TOTAL_BPS: Final[int] = 10_000


class RedCode(str, Enum):
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"
    NOT_FOUND = "not_found"
    STATE_CONFLICT = "state_conflict"
    COMMAND_COLLISION = "command_collision"
    PROJECT_SLOT_EXHAUSTED = "project_slot_exhausted"
    CAPACITY_EXCEEDED = "capacity_exceeded"
    SHARE_IMBALANCE = "share_imbalance"
    SIGNATURE_REQUIRED = "signature_required"
    ROUTE_INVALID = "route_invalid"
    ATTENTION_EXHAUSTED = "attention_exhausted"
    MATRIX_WEIGHT_IMBALANCE = "matrix_weight_imbalance"
    DUAL_SIGNATURE_REQUIRED = "dual_signature_required"
    UNIQUE_OWNER_REQUIRED = "unique_owner_required"
    INVARIANT_BROKEN = "invariant_broken"


class DomainRed(ValueError):
    """A typed, expected domain rejection; callers may render ``code``."""

    def __init__(self, code: RedCode, message: str) -> None:
        super().__init__(message)
        self.code = code


class ActionStatus(str, Enum):
    APPLIED = "applied"
    STALE_NOOP = "stale_noop"
    IDEMPOTENT_NOOP = "idempotent_noop"


@dataclass(frozen=True)
class CommandToken:
    model_id: str
    owner_id: str
    cycle_serial: int
    case_serial: int
    expected_revision: int
    command_id: str


@dataclass(frozen=True)
class ActionResult:
    status: ActionStatus
    mechanism_id: int
    previous_revision: int
    current_revision: int

    @property
    def applied(self) -> bool:
        return self.status is ActionStatus.APPLIED


@dataclass(frozen=True)
class MechanismBinding:
    mechanism_id: int
    domain: str
    title_cn: str
    behaviors: tuple[str, ...]


def _binding(
    mechanism_id: int, domain: str, title_cn: str, *behaviors: str
) -> MechanismBinding:
    return MechanismBinding(mechanism_id, domain, title_cn, tuple(behaviors))


MECHANISM_BINDINGS: Final[dict[int, MechanismBinding]] = {
    26: _binding(26, "E", "真实贡献 / 上司可见度双账", "record_effort_026"),
    27: _binding(27, "E", "跨部门贡献账本", "sign_contributions_027"),
    28: _binding(
        28,
        "E",
        "抢功仲裁 / 甩锅复盘",
        "file_credit_claim_028",
        "audit_credit_claim_028",
    ),
    29: _binding(
        29,
        "E",
        "指标包装、造假与京察审计",
        "record_metric_029",
        "audit_metric_029",
    ),
    30: _binding(30, "E", "资源赛马与抢预算", "award_resource_race_030"),
    31: _binding(31, "E", "恩主 / Sponsor 网络", "apply_sponsorship_031"),
    54: _binding(54, "I", "汇报工时挤占真实产出", "build_report_054"),
    55: _binding(55, "I", "上司注意力席位", "read_report_055"),
    56: _binding(56, "I", "逐级汇报中的截功", "forward_report_056"),
    57: _binding(57, "I", "贡献留痕与版本签名", "sign_report_057"),
    58: _binding(58, "I", "越级抄送（CC）与信息政治", "route_report_058"),
    59: _binding(59, "I", "坏消息早报、迟报与隐瞒", "record_risk_059"),
    60: _binding(60, "I", "材料泄露与创意窃取", "arbitrate_idea_060"),
    61: _binding(61, "I", "短文档 / 长叙事汇报制度", "set_report_policy_061"),
    62: _binding(62, "J", "实线与虚线目标冲突", "resolve_matrix_conflict_062"),
    63: _binding(63, "J", "周期初权重契约", "lock_matrix_weights_063"),
    64: _binding(
        64,
        "J",
        "换老板交接双签",
        "open_handoff_064",
        "sign_handoff_064",
        "finalize_handoff_064",
    ),
    65: _binding(65, "J", "空降主管与旧部包", "apply_parachute_065"),
    66: _binding(66, "J", "项目取消：业务失败与个人失败分离", "cancel_project_066"),
    67: _binding(67, "J", "合并后‘一岗两人’", "resolve_duplicate_role_067"),
    68: _binding(68, "J", "可携带履历与本地重新证明", "carry_history_068"),
    129: _binding(
        129,
        "R",
        "晋升排队与职业平台期",
        "enqueue_promotion_129",
        "allocate_promotion_129",
    ),
    130: _binding(130, "R", "把低绩效‘倾倒’给别组", "transfer_talent_130"),
    131: _binding(131, "R", "探索型 OKR 与承诺型 KPI 双赛道", "register_project_131"),
    132: _binding(132, "R", "及时砍项目也算功", "stop_project_132"),
    133: _binding(133, "R", "无责复盘与有责追究分轨", "record_postmortem_133"),
    134: _binding(134, "R", "共享指标的唯一 owner 与仲裁", "assign_shared_metric_134"),
}

EXPECTED_MECHANISM_IDS: Final[frozenset[int]] = frozenset(
    (*range(26, 32), *range(54, 69), *range(129, 135))
)


class ProjectTrack(str, Enum):
    EXPLORATION = "exploration"
    COMMITMENT = "commitment"


class ProjectState(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    STOPPED = "stopped"


class MetricStrategy(str, Enum):
    GENUINE = "genuine"
    GAMING = "gaming"
    FRAUD = "fraud"


class ReportFormat(str, Enum):
    SHORT_FACT = "short_fact"
    LONG_NARRATIVE = "long_narrative"
    EXCEPTION_ONLY = "exception_only"


REPORT_HOURS: Final[dict[ReportFormat, int]] = {
    ReportFormat.SHORT_FACT: 1,
    ReportFormat.LONG_NARRATIVE: 4,
    ReportFormat.EXCEPTION_ONLY: 1,
}


class ReportState(str, Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    ROUTED = "routed"


class RiskTiming(str, Enum):
    EARLY = "early"
    DELAYED = "delayed"
    HIDDEN = "hidden"


class MatrixConflictChoice(str, Enum):
    SOLID_LINE = "solid_line"
    DOTTED_LINE = "dotted_line"
    JOINT_ARBITRATION = "joint_arbitration"
    PROMISE_BOTH = "promise_both"


class DuplicateRoleMethod(str, Enum):
    OPEN_COMPETITION = "open_competition"
    DUAL_TRANSITION = "dual_transition"
    RETAIN_ONE = "retain_one"
    REDEPLOY = "redeploy"


@dataclass
class CreditClaim:
    claim_id: str
    source_id: str
    claimant_id: str
    basis_points: int
    status: str = "open"
    transfer_delta: dict[str, int] = field(default_factory=dict)
    audit_delta: dict[str, int] = field(default_factory=dict)


@dataclass
class MetricRecord:
    metric_id: str
    baseline: int
    strategy: MetricStrategy
    short_kpi_gain: int
    delayed_cost: int
    audited: bool = False
    clawback: int = 0
    realized_delayed_cost: int = 0


@dataclass
class Project:
    project_id: str
    manager_id: str
    owner_id: str
    origin_cycle_serial: int
    origin_case_serial: int
    version: int
    deadline_cycle: int
    participants: tuple[str, ...]
    track: ProjectTrack
    track_locked: bool
    metric_owner_id: str
    original_capacity_hours: int
    reserved_capacity_hours: int
    state: ProjectState = ProjectState.ACTIVE
    delivery_hours: int = 0
    report_hours: int = 0
    relationship_hours: int = 0
    hard_output: int = 0
    visibility_points: int = 0
    signed_contributions: dict[str, int] | None = None
    claimed_contributions: dict[str, int] | None = None
    claims: dict[str, CreditClaim] = field(default_factory=dict)
    metrics: dict[str, MetricRecord] = field(default_factory=dict)
    business_outcome: str | None = None
    individual_outcome: str | None = None
    stop_judgement: str | None = None

    @property
    def booked_hours(self) -> int:
        return self.delivery_hours + self.report_hours + self.relationship_hours

    @property
    def remaining_capacity_hours(self) -> int:
        return self.reserved_capacity_hours - self.booked_hours

    @property
    def delivery_capacity_hours(self) -> int:
        return self.reserved_capacity_hours - self.report_hours - self.relationship_hours

    @property
    def occupies_slot(self) -> bool:
        return self.state is ProjectState.ACTIVE


@dataclass
class ReportPacket:
    packet_id: str
    project_id: str
    owner_id: str
    cycle_serial: int
    case_serial: int
    object_version: int
    deadline_cycle: int
    author_id: str
    format: ReportFormat
    hours: int
    state: ReportState = ReportState.DRAFT
    claimed_attribution: dict[str, int] = field(default_factory=dict)
    signed_attribution: dict[str, int] | None = None
    version_signature: str | None = None
    routes: tuple[str, ...] = ()
    seen_by: set[str] = field(default_factory=set)
    risk_timing: RiskTiming | None = None
    risk_remaining_loss: int | None = None
    integrity_delta: int = 0
    idea_owner_id: str | None = None
    theft_upheld: bool | None = None


@dataclass
class SponsorLine:
    actor_id: str
    balance: int
    expires_cycle: int
    spent: int = 0
    visibility_bonus: int = 0


@dataclass
class MatrixAgreement:
    subject_id: str
    weights: dict[str, int]
    locked_cycle: int
    conflict_records: list[dict[str, object]] = field(default_factory=list)


@dataclass
class Handoff:
    old_manager_id: str
    new_manager_id: str
    signatures: set[str] = field(default_factory=set)
    finalized: bool = False


@dataclass(frozen=True)
class HistoricalCase:
    case_id: str
    owner_id: str
    subject_id: str
    rating: str
    pip_open: bool = False


@dataclass(frozen=True)
class PortableHistory:
    subject_id: str
    new_manager_id: str
    case_ids: tuple[str, ...]
    ratings: tuple[str, ...]
    protection_cycles: int
    pip_carried: bool
    consumes_current_quota: bool = False


@dataclass(frozen=True)
class PromotionQueueEntry:
    subject_id: str
    eligible_until_cycle: int
    sequence: int


@dataclass(frozen=True)
class TalentTransfer:
    subject_id: str
    source_manager_id: str
    destination_manager_id: str
    pip_disclosed: bool
    wrong_role_evidence: bool
    trial_success: bool
    outcome: str
    source_accountability: bool


@dataclass(frozen=True)
class SharedMetric:
    metric_id: str
    owner_id: str
    contributors: tuple[str, ...]
    dependencies: tuple[str, ...]


@dataclass
class Phase3CreditProjectModel:
    """One deterministic portfolio aggregate with guarded atomic commands."""

    model_id: str
    owner_id: str
    cycle_serial: int
    case_serial: int
    project_slot_total: int
    capacity_hours_total: int
    attention_slot_total: int
    promotion_slot_total: int
    active_manager_id: str
    historical_cases: tuple[HistoricalCase, ...] = ()
    revision: int = 0
    projects: dict[str, Project] = field(default_factory=dict)
    reports: dict[str, ReportPacket] = field(default_factory=dict)
    sponsor_lines: dict[str, SponsorLine] = field(default_factory=dict)
    matrix: MatrixAgreement | None = None
    pending_handoff: Handoff | None = None
    report_policy: ReportFormat = ReportFormat.SHORT_FACT
    parachute_records: list[dict[str, object]] = field(default_factory=list)
    duplicate_role_records: dict[str, dict[str, object]] = field(default_factory=dict)
    portable_histories: dict[str, PortableHistory] = field(default_factory=dict)
    promotion_queue: list[PromotionQueueEntry] = field(default_factory=list)
    promotion_awards: set[str] = field(default_factory=set)
    talent_transfers: dict[str, TalentTransfer] = field(default_factory=dict)
    postmortems: dict[str, dict[str, object]] = field(default_factory=dict)
    shared_metrics: dict[str, SharedMetric] = field(default_factory=dict)
    applied_commands: dict[str, int] = field(default_factory=dict)
    applied_mechanism_ids: set[int] = field(default_factory=set)
    _historical_owner_fingerprint: tuple[tuple[str, str], ...] = field(
        init=False, repr=False
    )

    def __post_init__(self) -> None:
        for label in ("model_id", "owner_id", "active_manager_id"):
            self._require_text(getattr(self, label), label)
        for label in (
            "cycle_serial",
            "case_serial",
            "project_slot_total",
            "capacity_hours_total",
            "attention_slot_total",
            "promotion_slot_total",
        ):
            self._require_int(getattr(self, label), label, minimum=1)
        case_ids = [case.case_id for case in self.historical_cases]
        if len(case_ids) != len(set(case_ids)):
            raise DomainRed(RedCode.INVALID_VALUE, "historical case ids must be unique")
        self._historical_owner_fingerprint = tuple(
            (case.case_id, case.owner_id) for case in self.historical_cases
        )

    @staticmethod
    def _require_text(value: object, label: str) -> str:
        if not isinstance(value, str):
            raise DomainRed(RedCode.INVALID_TYPE, f"{label} must be a string")
        if not value.strip():
            raise DomainRed(RedCode.INVALID_VALUE, f"{label} must be non-empty")
        return value

    @staticmethod
    def _require_int(
        value: object, label: str, *, minimum: int | None = None
    ) -> int:
        if isinstance(value, bool) or not isinstance(value, int):
            raise DomainRed(RedCode.INVALID_TYPE, f"{label} must be an integer")
        if minimum is not None and value < minimum:
            raise DomainRed(
                RedCode.INVALID_VALUE, f"{label} must be at least {minimum}"
            )
        return value

    @staticmethod
    def _as_enum(value: object, enum_type: type[Enum], label: str) -> Enum:
        try:
            return enum_type(value)
        except (TypeError, ValueError) as exc:
            raise DomainRed(RedCode.INVALID_VALUE, f"invalid {label}: {value!r}") from exc

    def command(self, command_id: str) -> CommandToken:
        self._require_text(command_id, "command_id")
        return CommandToken(
            self.model_id,
            self.owner_id,
            self.cycle_serial,
            self.case_serial,
            self.revision,
            command_id,
        )

    def _gate(self, command: object, mechanism_id: int) -> ActionResult | None:
        if not isinstance(command, CommandToken):
            raise DomainRed(RedCode.INVALID_TYPE, "command must be a CommandToken")
        self._require_text(command.command_id, "command_id")
        prior = self.applied_commands.get(command.command_id)
        if prior is not None:
            if prior != mechanism_id:
                raise DomainRed(
                    RedCode.COMMAND_COLLISION,
                    f"command {command.command_id} already belongs to {prior}",
                )
            return ActionResult(
                ActionStatus.IDEMPOTENT_NOOP,
                mechanism_id,
                self.revision,
                self.revision,
            )
        identity_matches = (
            command.model_id == self.model_id
            and command.owner_id == self.owner_id
            and command.cycle_serial == self.cycle_serial
            and command.case_serial == self.case_serial
            and command.expected_revision == self.revision
        )
        if not identity_matches:
            return ActionResult(
                ActionStatus.STALE_NOOP,
                mechanism_id,
                self.revision,
                self.revision,
            )
        return None

    def _commit(self, command: CommandToken, mechanism_id: int) -> ActionResult:
        previous = self.revision
        self.applied_commands[command.command_id] = mechanism_id
        self.applied_mechanism_ids.add(mechanism_id)
        self.revision += 1
        self.assert_invariants()
        return ActionResult(ActionStatus.APPLIED, mechanism_id, previous, self.revision)

    def _project(self, project_id: object, *, active: bool = False) -> Project:
        project_id = self._require_text(project_id, "project_id")
        project = self.projects.get(project_id)
        if project is None:
            raise DomainRed(RedCode.NOT_FOUND, f"unknown project {project_id}")
        if active and project.state is not ProjectState.ACTIVE:
            raise DomainRed(RedCode.STATE_CONFLICT, f"project {project_id} is not active")
        return project

    def _report(self, packet_id: object) -> ReportPacket:
        packet_id = self._require_text(packet_id, "packet_id")
        packet = self.reports.get(packet_id)
        if packet is None:
            raise DomainRed(RedCode.NOT_FOUND, f"unknown report {packet_id}")
        return packet

    @staticmethod
    def _touch_project(project: Project) -> None:
        project.version += 1

    @staticmethod
    def _touch_report(packet: ReportPacket) -> None:
        packet.object_version += 1

    @property
    def project_slots_used(self) -> int:
        return sum(project.occupies_slot for project in self.projects.values())

    @property
    def project_slots_free(self) -> int:
        return self.project_slot_total - self.project_slots_used

    @property
    def capacity_hours_reserved_or_spent(self) -> int:
        return sum(project.reserved_capacity_hours for project in self.projects.values())

    @property
    def capacity_hours_free(self) -> int:
        return self.capacity_hours_total - self.capacity_hours_reserved_or_spent

    @property
    def attention_slots_used(self) -> int:
        return sum(len(packet.seen_by) for packet in self.reports.values())

    def _new_project(
        self,
        *,
        project_id: object,
        owner_id: object,
        participants: object,
        track: object,
        metric_owner_id: object,
        capacity_hours: object,
    ) -> Project:
        project_id = self._require_text(project_id, "project_id")
        owner_id = self._require_text(owner_id, "project owner_id")
        metric_owner_id = self._require_text(metric_owner_id, "metric_owner_id")
        capacity_hours = self._require_int(capacity_hours, "capacity_hours", minimum=1)
        track = self._as_enum(track, ProjectTrack, "project track")
        if project_id in self.projects:
            raise DomainRed(RedCode.STATE_CONFLICT, f"project {project_id} already exists")
        if not isinstance(participants, (tuple, list)):
            raise DomainRed(RedCode.INVALID_TYPE, "participants must be a tuple or list")
        participant_rows = tuple(
            self._require_text(actor, "participant") for actor in participants
        )
        if not participant_rows or len(participant_rows) != len(set(participant_rows)):
            raise DomainRed(
                RedCode.INVALID_VALUE, "participants must be non-empty and unique"
            )
        if owner_id not in participant_rows or metric_owner_id not in participant_rows:
            raise DomainRed(
                RedCode.UNIQUE_OWNER_REQUIRED,
                "project and metric owners must be registered participants",
            )
        if self.project_slots_free < 1:
            raise DomainRed(RedCode.PROJECT_SLOT_EXHAUSTED, "no project slot remains")
        if capacity_hours > self.capacity_hours_free:
            raise DomainRed(RedCode.CAPACITY_EXCEEDED, "portfolio capacity exceeded")
        return Project(
            project_id=project_id,
            manager_id=self.owner_id,
            owner_id=owner_id,
            origin_cycle_serial=self.cycle_serial,
            origin_case_serial=self.case_serial,
            version=1,
            deadline_cycle=self.cycle_serial + 2,
            participants=participant_rows,
            track=track,
            track_locked=True,
            metric_owner_id=metric_owner_id,
            original_capacity_hours=capacity_hours,
            reserved_capacity_hours=capacity_hours,
        )

    def register_project_131(
        self,
        command: CommandToken,
        *,
        project_id: str,
        owner_id: str,
        participants: tuple[str, ...],
        track: ProjectTrack,
        metric_owner_id: str,
        capacity_hours: int,
    ) -> ActionResult:
        gate = self._gate(command, 131)
        if gate:
            return gate
        project = self._new_project(
            project_id=project_id,
            owner_id=owner_id,
            participants=participants,
            track=track,
            metric_owner_id=metric_owner_id,
            capacity_hours=capacity_hours,
        )
        self.projects[project.project_id] = project
        return self._commit(command, 131)

    def record_effort_026(
        self,
        command: CommandToken,
        *,
        project_id: str,
        delivery_hours: int,
        report_hours: int,
        relationship_hours: int,
    ) -> ActionResult:
        gate = self._gate(command, 26)
        if gate:
            return gate
        project = self._project(project_id, active=True)
        values = {
            "delivery_hours": self._require_int(
                delivery_hours, "delivery_hours", minimum=0
            ),
            "report_hours": self._require_int(report_hours, "report_hours", minimum=0),
            "relationship_hours": self._require_int(
                relationship_hours, "relationship_hours", minimum=0
            ),
        }
        if sum(values.values()) > project.remaining_capacity_hours:
            raise DomainRed(RedCode.CAPACITY_EXCEEDED, "effort exceeds project capacity")
        project.delivery_hours += values["delivery_hours"]
        project.report_hours += values["report_hours"]
        project.relationship_hours += values["relationship_hours"]
        project.hard_output += values["delivery_hours"]
        project.visibility_points += values["report_hours"] * 2 + values[
            "relationship_hours"
        ] * 3
        self._touch_project(project)
        return self._commit(command, 26)

    def sign_contributions_027(
        self,
        command: CommandToken,
        *,
        project_id: str,
        shares: Mapping[str, int],
    ) -> ActionResult:
        gate = self._gate(command, 27)
        if gate:
            return gate
        project = self._project(project_id)
        if project.signed_contributions is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "contributions already signed")
        if not isinstance(shares, Mapping):
            raise DomainRed(RedCode.INVALID_TYPE, "shares must be a mapping")
        candidate = {
            self._require_text(actor, "contributor"): self._require_int(
                points, "share basis points", minimum=0
            )
            for actor, points in shares.items()
        }
        if set(candidate) != set(project.participants):
            raise DomainRed(
                RedCode.SHARE_IMBALANCE,
                "signed shares must name every and only registered participant",
            )
        if sum(candidate.values()) != SHARE_TOTAL_BPS:
            raise DomainRed(
                RedCode.SHARE_IMBALANCE,
                f"signed shares must total {SHARE_TOTAL_BPS}",
            )
        project.signed_contributions = candidate
        project.claimed_contributions = dict(candidate)
        self._touch_project(project)
        return self._commit(command, 27)

    @staticmethod
    def _transfer_shares(
        shares: Mapping[str, int], source_id: str, claimant_id: str, basis_points: int
    ) -> tuple[dict[str, int], dict[str, int]]:
        if source_id == claimant_id or source_id not in shares or claimant_id not in shares:
            raise DomainRed(RedCode.INVALID_VALUE, "credit transfer actors are invalid")
        if basis_points <= 0 or shares[source_id] < basis_points:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "credit transfer exceeds source share")
        candidate = dict(shares)
        candidate[source_id] -= basis_points
        candidate[claimant_id] += basis_points
        delta = {source_id: -basis_points, claimant_id: basis_points}
        if sum(candidate.values()) != SHARE_TOTAL_BPS or sum(delta.values()) != 0:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "credit transfer is not net zero")
        return candidate, delta

    def file_credit_claim_028(
        self,
        command: CommandToken,
        *,
        project_id: str,
        claim_id: str,
        source_id: str,
        claimant_id: str,
        basis_points: int,
    ) -> ActionResult:
        gate = self._gate(command, 28)
        if gate:
            return gate
        project = self._project(project_id)
        claim_id = self._require_text(claim_id, "claim_id")
        source_id = self._require_text(source_id, "source_id")
        claimant_id = self._require_text(claimant_id, "claimant_id")
        basis_points = self._require_int(basis_points, "basis_points", minimum=1)
        if project.claimed_contributions is None:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "contributions must be signed")
        if claim_id in project.claims:
            raise DomainRed(RedCode.STATE_CONFLICT, "claim id already exists")
        candidate, delta = self._transfer_shares(
            project.claimed_contributions, source_id, claimant_id, basis_points
        )
        claim = CreditClaim(
            claim_id,
            source_id,
            claimant_id,
            basis_points,
            transfer_delta=delta,
        )
        project.claimed_contributions = candidate
        project.claims[claim_id] = claim
        self._touch_project(project)
        return self._commit(command, 28)

    def audit_credit_claim_028(
        self,
        command: CommandToken,
        *,
        project_id: str,
        claim_id: str,
        upheld: bool,
    ) -> ActionResult:
        gate = self._gate(command, 28)
        if gate:
            return gate
        project = self._project(project_id)
        claim_id = self._require_text(claim_id, "claim_id")
        if type(upheld) is not bool:
            raise DomainRed(RedCode.INVALID_TYPE, "upheld must be a bool")
        claim = project.claims.get(claim_id)
        if claim is None:
            raise DomainRed(RedCode.NOT_FOUND, "credit claim not found")
        if claim.status != "open":
            raise DomainRed(RedCode.STATE_CONFLICT, "credit claim already audited")
        candidate = dict(project.claimed_contributions or {})
        audit_delta: dict[str, int] = {}
        if upheld:
            status = "upheld"
        else:
            audit_delta = {
                actor: -delta for actor, delta in claim.transfer_delta.items()
            }
            for actor, delta in audit_delta.items():
                candidate[actor] += delta
            if sum(audit_delta.values()) != 0 or sum(candidate.values()) != SHARE_TOTAL_BPS:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "audit reversal is not net zero")
            status = "reversed"
        project.claimed_contributions = candidate
        claim.audit_delta = audit_delta
        claim.status = status
        self._touch_project(project)
        return self._commit(command, 28)

    def record_metric_029(
        self,
        command: CommandToken,
        *,
        project_id: str,
        metric_id: str,
        baseline: int,
        strategy: MetricStrategy,
        short_kpi_gain: int,
        delayed_cost: int,
    ) -> ActionResult:
        gate = self._gate(command, 29)
        if gate:
            return gate
        project = self._project(project_id)
        metric_id = self._require_text(metric_id, "metric_id")
        baseline = self._require_int(baseline, "baseline", minimum=0)
        strategy = self._as_enum(strategy, MetricStrategy, "metric strategy")
        short_kpi_gain = self._require_int(
            short_kpi_gain, "short_kpi_gain", minimum=0
        )
        delayed_cost = self._require_int(delayed_cost, "delayed_cost", minimum=0)
        if metric_id in project.metrics:
            raise DomainRed(RedCode.STATE_CONFLICT, "metric already recorded")
        if strategy is MetricStrategy.GENUINE and delayed_cost:
            raise DomainRed(
                RedCode.INVALID_VALUE, "genuine improvement cannot carry gaming debt"
            )
        project.metrics[metric_id] = MetricRecord(
            metric_id, baseline, strategy, short_kpi_gain, delayed_cost
        )
        self._touch_project(project)
        return self._commit(command, 29)

    def audit_metric_029(
        self, command: CommandToken, *, project_id: str, metric_id: str
    ) -> ActionResult:
        gate = self._gate(command, 29)
        if gate:
            return gate
        project = self._project(project_id)
        metric = project.metrics.get(self._require_text(metric_id, "metric_id"))
        if metric is None:
            raise DomainRed(RedCode.NOT_FOUND, "metric not found")
        if metric.audited:
            raise DomainRed(RedCode.STATE_CONFLICT, "metric audit already settled")
        clawback = metric.short_kpi_gain if metric.strategy is MetricStrategy.FRAUD else 0
        realized_cost = (
            metric.delayed_cost
            if metric.strategy in (MetricStrategy.GAMING, MetricStrategy.FRAUD)
            else 0
        )
        metric.audited = True
        metric.clawback = clawback
        metric.realized_delayed_cost = realized_cost
        self._touch_project(project)
        return self._commit(command, 29)

    def award_resource_race_030(
        self,
        command: CommandToken,
        *,
        project_id: str,
        candidate_ids: tuple[str, ...],
        winner_id: str,
        participants: tuple[str, ...],
        capacity_hours: int,
    ) -> ActionResult:
        gate = self._gate(command, 30)
        if gate:
            return gate
        if not isinstance(candidate_ids, tuple):
            raise DomainRed(RedCode.INVALID_TYPE, "candidate_ids must be a tuple")
        candidates = tuple(self._require_text(row, "candidate_id") for row in candidate_ids)
        winner_id = self._require_text(winner_id, "winner_id")
        if len(candidates) < 2 or len(candidates) != len(set(candidates)):
            raise DomainRed(RedCode.INVALID_VALUE, "resource race requires unique rivals")
        if winner_id not in candidates:
            raise DomainRed(RedCode.INVALID_VALUE, "winner must be a race candidate")
        project = self._new_project(
            project_id=project_id,
            owner_id=winner_id,
            participants=participants,
            track=ProjectTrack.COMMITMENT,
            metric_owner_id=winner_id,
            capacity_hours=capacity_hours,
        )
        self.projects[project.project_id] = project
        return self._commit(command, 30)

    def apply_sponsorship_031(
        self,
        command: CommandToken,
        *,
        actor_id: str,
        granted_credit: int,
        spent_credit: int,
        expires_cycle: int,
        visibility_bonus: int,
    ) -> ActionResult:
        gate = self._gate(command, 31)
        if gate:
            return gate
        actor_id = self._require_text(actor_id, "actor_id")
        granted_credit = self._require_int(
            granted_credit, "granted_credit", minimum=0
        )
        spent_credit = self._require_int(spent_credit, "spent_credit", minimum=0)
        expires_cycle = self._require_int(expires_cycle, "expires_cycle", minimum=1)
        visibility_bonus = self._require_int(
            visibility_bonus, "visibility_bonus", minimum=0
        )
        old = self.sponsor_lines.get(actor_id)
        balance = (old.balance if old else 0) + granted_credit
        lifetime_spent = old.spent if old else 0
        if expires_cycle < self.cycle_serial:
            raise DomainRed(RedCode.STATE_CONFLICT, "sponsor credit is expired")
        if balance > 100 or spent_credit > balance or visibility_bonus > 20:
            raise DomainRed(
                RedCode.INVALID_VALUE, "sponsor credit or visibility exceeds its cap"
            )
        self.sponsor_lines[actor_id] = SponsorLine(
            actor_id=actor_id,
            balance=balance - spent_credit,
            expires_cycle=expires_cycle,
            spent=lifetime_spent + spent_credit,
            visibility_bonus=(old.visibility_bonus if old else 0) + visibility_bonus,
        )
        return self._commit(command, 31)

    def set_report_policy_061(
        self, command: CommandToken, *, policy: ReportFormat
    ) -> ActionResult:
        gate = self._gate(command, 61)
        if gate:
            return gate
        candidate = self._as_enum(policy, ReportFormat, "report policy")
        self.report_policy = candidate
        return self._commit(command, 61)

    def build_report_054(
        self,
        command: CommandToken,
        *,
        packet_id: str,
        project_id: str,
        author_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 54)
        if gate:
            return gate
        packet_id = self._require_text(packet_id, "packet_id")
        author_id = self._require_text(author_id, "author_id")
        project = self._project(project_id, active=True)
        if packet_id in self.reports:
            raise DomainRed(RedCode.STATE_CONFLICT, "report packet already exists")
        if author_id not in project.participants:
            raise DomainRed(RedCode.INVALID_VALUE, "report author is not a participant")
        hours = REPORT_HOURS[self.report_policy]
        if hours > project.remaining_capacity_hours:
            raise DomainRed(RedCode.CAPACITY_EXCEEDED, "report displaces unavailable capacity")
        claims = project.claimed_contributions or {
            actor: 0 for actor in project.participants
        }
        project.report_hours += hours
        self.reports[packet_id] = ReportPacket(
            packet_id=packet_id,
            project_id=project.project_id,
            owner_id=self.owner_id,
            cycle_serial=self.cycle_serial,
            case_serial=self.case_serial,
            object_version=1,
            deadline_cycle=self.cycle_serial + 1,
            author_id=author_id,
            format=self.report_policy,
            hours=hours,
            claimed_attribution=dict(claims),
        )
        self._touch_project(project)
        return self._commit(command, 54)

    def forward_report_056(
        self,
        command: CommandToken,
        *,
        packet_id: str,
        source_id: str,
        manager_id: str,
        basis_points: int,
    ) -> ActionResult:
        gate = self._gate(command, 56)
        if gate:
            return gate
        packet = self._report(packet_id)
        if packet.state is not ReportState.DRAFT:
            raise DomainRed(RedCode.STATE_CONFLICT, "only a draft can change attribution")
        source_id = self._require_text(source_id, "source_id")
        manager_id = self._require_text(manager_id, "manager_id")
        basis_points = self._require_int(basis_points, "basis_points", minimum=1)
        candidate, _ = self._transfer_shares(
            packet.claimed_attribution, source_id, manager_id, basis_points
        )
        packet.claimed_attribution = candidate
        self._touch_report(packet)
        return self._commit(command, 56)

    def sign_report_057(
        self, command: CommandToken, *, packet_id: str, signer_id: str, version: int
    ) -> ActionResult:
        gate = self._gate(command, 57)
        if gate:
            return gate
        packet = self._report(packet_id)
        signer_id = self._require_text(signer_id, "signer_id")
        version = self._require_int(version, "version", minimum=1)
        if packet.state is not ReportState.DRAFT:
            raise DomainRed(RedCode.STATE_CONFLICT, "report is not an unsigned draft")
        if signer_id != packet.author_id:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "only the author signs this version")
        if sum(packet.claimed_attribution.values()) != SHARE_TOTAL_BPS:
            raise DomainRed(RedCode.SHARE_IMBALANCE, "report attribution does not conserve")
        packet.signed_attribution = dict(packet.claimed_attribution)
        packet.version_signature = f"{packet.packet_id}:v{version}:{signer_id}"
        packet.state = ReportState.SIGNED
        self._touch_report(packet)
        return self._commit(command, 57)

    def route_report_058(
        self,
        command: CommandToken,
        *,
        packet_id: str,
        direct_manager_id: str,
        skip_level_manager_id: str | None = None,
    ) -> ActionResult:
        gate = self._gate(command, 58)
        if gate:
            return gate
        packet = self._report(packet_id)
        direct_manager_id = self._require_text(direct_manager_id, "direct_manager_id")
        if packet.state is not ReportState.SIGNED or not packet.version_signature:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "signed version required before routing")
        if direct_manager_id != self.active_manager_id:
            raise DomainRed(RedCode.ROUTE_INVALID, "route must include the active manager")
        routes = [direct_manager_id]
        if skip_level_manager_id is not None:
            skip_level_manager_id = self._require_text(
                skip_level_manager_id, "skip_level_manager_id"
            )
            if skip_level_manager_id == direct_manager_id:
                raise DomainRed(RedCode.ROUTE_INVALID, "skip-level route must be distinct")
            routes.append(skip_level_manager_id)
        packet.routes = tuple(routes)
        packet.state = ReportState.ROUTED
        self._touch_report(packet)
        return self._commit(command, 58)

    def read_report_055(
        self, command: CommandToken, *, packet_id: str, manager_id: str
    ) -> ActionResult:
        gate = self._gate(command, 55)
        if gate:
            return gate
        packet = self._report(packet_id)
        manager_id = self._require_text(manager_id, "manager_id")
        if packet.state is not ReportState.ROUTED or manager_id not in packet.routes:
            raise DomainRed(RedCode.ROUTE_INVALID, "manager cannot read an unrouted report")
        if manager_id in packet.seen_by:
            raise DomainRed(RedCode.STATE_CONFLICT, "manager already consumed this report")
        if self.attention_slots_used >= self.attention_slot_total:
            raise DomainRed(RedCode.ATTENTION_EXHAUSTED, "no deep-read slot remains")
        packet.seen_by.add(manager_id)
        project = self.projects[packet.project_id]
        project.visibility_points += 5
        self._touch_project(project)
        self._touch_report(packet)
        return self._commit(command, 55)

    def record_risk_059(
        self,
        command: CommandToken,
        *,
        packet_id: str,
        timing: RiskTiming,
        severity: int,
    ) -> ActionResult:
        gate = self._gate(command, 59)
        if gate:
            return gate
        packet = self._report(packet_id)
        timing = self._as_enum(timing, RiskTiming, "risk timing")
        severity = self._require_int(severity, "severity", minimum=1)
        if packet.risk_timing is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "risk timing already frozen")
        if timing is RiskTiming.EARLY:
            loss, integrity = (severity + 1) // 2, 1
        elif timing is RiskTiming.DELAYED:
            loss, integrity = severity, 0
        else:
            loss, integrity = severity * 2, -2
        packet.risk_timing = timing
        packet.risk_remaining_loss = loss
        packet.integrity_delta = integrity
        self._touch_report(packet)
        return self._commit(command, 59)

    def arbitrate_idea_060(
        self,
        command: CommandToken,
        *,
        packet_id: str,
        original_author_id: str,
        claimed_author_id: str,
    ) -> ActionResult:
        gate = self._gate(command, 60)
        if gate:
            return gate
        packet = self._report(packet_id)
        original_author_id = self._require_text(
            original_author_id, "original_author_id"
        )
        claimed_author_id = self._require_text(claimed_author_id, "claimed_author_id")
        if not packet.version_signature:
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "no signed provenance exists")
        if claimed_author_id == original_author_id:
            raise DomainRed(RedCode.INVALID_VALUE, "idea dispute requires two claimants")
        signature_proves_original = packet.author_id == original_author_id
        packet.idea_owner_id = original_author_id if signature_proves_original else claimed_author_id
        packet.theft_upheld = signature_proves_original
        self._touch_report(packet)
        return self._commit(command, 60)

    def lock_matrix_weights_063(
        self,
        command: CommandToken,
        *,
        subject_id: str,
        weights: Mapping[str, int],
    ) -> ActionResult:
        gate = self._gate(command, 63)
        if gate:
            return gate
        subject_id = self._require_text(subject_id, "subject_id")
        if self.matrix is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "matrix weights already locked")
        if not isinstance(weights, Mapping):
            raise DomainRed(RedCode.INVALID_TYPE, "weights must be a mapping")
        candidate = {
            self._require_text(manager, "manager_id"): self._require_int(
                weight, "manager weight", minimum=1
            )
            for manager, weight in weights.items()
        }
        if len(candidate) != 2 or sum(candidate.values()) != 100:
            raise DomainRed(
                RedCode.MATRIX_WEIGHT_IMBALANCE,
                "matrix requires two managers whose weights total 100",
            )
        if self.active_manager_id not in candidate:
            raise DomainRed(
                RedCode.MATRIX_WEIGHT_IMBALANCE, "active manager must hold a weight"
            )
        self.matrix = MatrixAgreement(subject_id, candidate, self.cycle_serial)
        return self._commit(command, 63)

    def resolve_matrix_conflict_062(
        self,
        command: CommandToken,
        *,
        choice: MatrixConflictChoice,
        solid_priority: str,
        dotted_priority: str,
    ) -> ActionResult:
        gate = self._gate(command, 62)
        if gate:
            return gate
        if self.matrix is None:
            raise DomainRed(RedCode.STATE_CONFLICT, "matrix contract is not locked")
        choice = self._as_enum(choice, MatrixConflictChoice, "matrix conflict choice")
        solid_priority = self._require_text(solid_priority, "solid_priority")
        dotted_priority = self._require_text(dotted_priority, "dotted_priority")
        if solid_priority == dotted_priority:
            raise DomainRed(RedCode.INVALID_VALUE, "conflict priorities must differ")
        ranked = sorted(self.matrix.weights, key=self.matrix.weights.get, reverse=True)
        if choice is MatrixConflictChoice.SOLID_LINE:
            chosen, integrity = ranked[0], 0
        elif choice is MatrixConflictChoice.DOTTED_LINE:
            chosen, integrity = ranked[-1], 0
        elif choice is MatrixConflictChoice.JOINT_ARBITRATION:
            chosen, integrity = "joint", 1
        else:
            chosen, integrity = "both_promised", -2
        self.matrix.conflict_records.append(
            {
                "choice": choice.value,
                "chosen": chosen,
                "solid_priority": solid_priority,
                "dotted_priority": dotted_priority,
                "integrity_delta": integrity,
            }
        )
        return self._commit(command, 62)

    def open_handoff_064(
        self, command: CommandToken, *, old_manager_id: str, new_manager_id: str
    ) -> ActionResult:
        gate = self._gate(command, 64)
        if gate:
            return gate
        old_manager_id = self._require_text(old_manager_id, "old_manager_id")
        new_manager_id = self._require_text(new_manager_id, "new_manager_id")
        if self.pending_handoff is not None:
            raise DomainRed(RedCode.STATE_CONFLICT, "a handoff is already open")
        if old_manager_id != self.active_manager_id or old_manager_id == new_manager_id:
            raise DomainRed(RedCode.INVALID_VALUE, "handoff managers are invalid")
        self.pending_handoff = Handoff(old_manager_id, new_manager_id)
        return self._commit(command, 64)

    def sign_handoff_064(
        self, command: CommandToken, *, signer_id: str
    ) -> ActionResult:
        gate = self._gate(command, 64)
        if gate:
            return gate
        signer_id = self._require_text(signer_id, "signer_id")
        handoff = self.pending_handoff
        if handoff is None or handoff.finalized:
            raise DomainRed(RedCode.STATE_CONFLICT, "no open handoff")
        if signer_id not in (handoff.old_manager_id, handoff.new_manager_id):
            raise DomainRed(RedCode.SIGNATURE_REQUIRED, "signer is not a handoff party")
        if signer_id in handoff.signatures:
            raise DomainRed(RedCode.STATE_CONFLICT, "handoff party already signed")
        handoff.signatures.add(signer_id)
        return self._commit(command, 64)

    def finalize_handoff_064(self, command: CommandToken) -> ActionResult:
        gate = self._gate(command, 64)
        if gate:
            return gate
        handoff = self.pending_handoff
        if handoff is None or handoff.finalized:
            raise DomainRed(RedCode.STATE_CONFLICT, "no open handoff")
        required = {handoff.old_manager_id, handoff.new_manager_id}
        if handoff.signatures != required:
            raise DomainRed(RedCode.DUAL_SIGNATURE_REQUIRED, "both managers must sign")
        new_weights = None
        if self.matrix is not None and handoff.old_manager_id in self.matrix.weights:
            if handoff.new_manager_id in self.matrix.weights:
                raise DomainRed(
                    RedCode.MATRIX_WEIGHT_IMBALANCE,
                    "new manager already has a separate matrix weight",
                )
            new_weights = dict(self.matrix.weights)
            weight = new_weights.pop(handoff.old_manager_id)
            new_weights[handoff.new_manager_id] = weight
            if sum(new_weights.values()) != 100:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "handoff changed weight total")
        self.active_manager_id = handoff.new_manager_id
        if new_weights is not None and self.matrix is not None:
            self.matrix.weights = new_weights
        handoff.finalized = True
        return self._commit(command, 64)

    def apply_parachute_065(
        self,
        command: CommandToken,
        *,
        manager_id: str,
        team_size: int,
        imported_staff: int,
    ) -> ActionResult:
        gate = self._gate(command, 65)
        if gate:
            return gate
        manager_id = self._require_text(manager_id, "manager_id")
        team_size = self._require_int(team_size, "team_size", minimum=1)
        imported_staff = self._require_int(imported_staff, "imported_staff", minimum=0)
        if manager_id != self.active_manager_id or imported_staff > team_size:
            raise DomainRed(RedCode.INVALID_VALUE, "parachute staffing is invalid")
        self.parachute_records.append(
            {
                "manager_id": manager_id,
                "team_size": team_size,
                "imported_staff": imported_staff,
                "retained_memory": team_size - imported_staff,
                "favoritism_audit": imported_staff * 4 > team_size,
            }
        )
        return self._commit(command, 65)

    def _terminal_project_candidate(
        self, project: Project, *, state: ProjectState
    ) -> tuple[int, int]:
        if project.state is not ProjectState.ACTIVE:
            raise DomainRed(RedCode.STATE_CONFLICT, "project is already terminal")
        spent = project.booked_hours
        if spent > project.reserved_capacity_hours:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "project overspent capacity")
        return spent, project.reserved_capacity_hours - spent

    def cancel_project_066(
        self,
        command: CommandToken,
        *,
        project_id: str,
        strategic_reason: str,
        verified_milestones: bool,
    ) -> ActionResult:
        gate = self._gate(command, 66)
        if gate:
            return gate
        project = self._project(project_id, active=True)
        strategic_reason = self._require_text(strategic_reason, "strategic_reason")
        if type(verified_milestones) is not bool:
            raise DomainRed(RedCode.INVALID_TYPE, "verified_milestones must be bool")
        spent, _released = self._terminal_project_candidate(
            project, state=ProjectState.CANCELLED
        )
        project.reserved_capacity_hours = spent
        project.state = ProjectState.CANCELLED
        project.business_outcome = f"strategic_cancel:{strategic_reason}"
        project.individual_outcome = (
            "verified_contribution_preserved" if verified_milestones else "no_verified_credit"
        )
        self._touch_project(project)
        return self._commit(command, 66)

    def resolve_duplicate_role_067(
        self,
        command: CommandToken,
        *,
        role_id: str,
        incumbents: tuple[str, str],
        method: DuplicateRoleMethod,
        retained_id: str | None,
    ) -> ActionResult:
        gate = self._gate(command, 67)
        if gate:
            return gate
        role_id = self._require_text(role_id, "role_id")
        if role_id in self.duplicate_role_records:
            raise DomainRed(RedCode.STATE_CONFLICT, "duplicate role already resolved")
        if not isinstance(incumbents, tuple) or len(incumbents) != 2:
            raise DomainRed(RedCode.INVALID_TYPE, "incumbents must be a pair")
        incumbents = tuple(self._require_text(row, "incumbent") for row in incumbents)
        if incumbents[0] == incumbents[1]:
            raise DomainRed(RedCode.INVALID_VALUE, "duplicate role needs two people")
        method = self._as_enum(method, DuplicateRoleMethod, "role resolution")
        if method is DuplicateRoleMethod.DUAL_TRANSITION:
            if retained_id is not None:
                raise DomainRed(RedCode.INVALID_VALUE, "dual transition has no sole incumbent")
            final_holders = incumbents
        else:
            retained_id = self._require_text(retained_id, "retained_id")
            if retained_id not in incumbents:
                raise DomainRed(RedCode.INVALID_VALUE, "retained actor was not an incumbent")
            final_holders = (retained_id,)
        self.duplicate_role_records[role_id] = {
            "method": method.value,
            "incumbents": incumbents,
            "final_holders": final_holders,
            "transition_temporary": method is DuplicateRoleMethod.DUAL_TRANSITION,
        }
        return self._commit(command, 67)

    def carry_history_068(
        self,
        command: CommandToken,
        *,
        subject_id: str,
        new_manager_id: str,
        protection_cycles: int,
        carry_open_pip: bool,
    ) -> ActionResult:
        gate = self._gate(command, 68)
        if gate:
            return gate
        subject_id = self._require_text(subject_id, "subject_id")
        new_manager_id = self._require_text(new_manager_id, "new_manager_id")
        protection_cycles = self._require_int(
            protection_cycles, "protection_cycles", minimum=0
        )
        if type(carry_open_pip) is not bool:
            raise DomainRed(RedCode.INVALID_TYPE, "carry_open_pip must be bool")
        rows = tuple(case for case in self.historical_cases if case.subject_id == subject_id)
        if not rows:
            raise DomainRed(RedCode.NOT_FOUND, "no portable history exists")
        if subject_id in self.portable_histories:
            raise DomainRed(RedCode.STATE_CONFLICT, "history already carried")
        has_open_pip = any(case.pip_open for case in rows)
        self.portable_histories[subject_id] = PortableHistory(
            subject_id,
            new_manager_id,
            tuple(case.case_id for case in rows),
            tuple(case.rating for case in rows),
            protection_cycles,
            pip_carried=carry_open_pip and has_open_pip,
        )
        return self._commit(command, 68)

    def enqueue_promotion_129(
        self, command: CommandToken, *, subject_id: str, eligible_until_cycle: int
    ) -> ActionResult:
        gate = self._gate(command, 129)
        if gate:
            return gate
        subject_id = self._require_text(subject_id, "subject_id")
        eligible_until_cycle = self._require_int(
            eligible_until_cycle, "eligible_until_cycle", minimum=self.cycle_serial
        )
        if subject_id in {row.subject_id for row in self.promotion_queue}:
            raise DomainRed(RedCode.STATE_CONFLICT, "subject already queued")
        if subject_id in self.promotion_awards:
            raise DomainRed(RedCode.STATE_CONFLICT, "subject already promoted")
        self.promotion_queue.append(
            PromotionQueueEntry(subject_id, eligible_until_cycle, len(self.promotion_queue))
        )
        return self._commit(command, 129)

    def allocate_promotion_129(self, command: CommandToken) -> ActionResult:
        gate = self._gate(command, 129)
        if gate:
            return gate
        if len(self.promotion_awards) >= self.promotion_slot_total:
            raise DomainRed(RedCode.PROJECT_SLOT_EXHAUSTED, "no promotion slot remains")
        eligible = [
            row
            for row in self.promotion_queue
            if row.eligible_until_cycle >= self.cycle_serial
        ]
        if not eligible:
            raise DomainRed(RedCode.NOT_FOUND, "promotion queue has no eligible candidate")
        winner = min(eligible, key=lambda row: row.sequence)
        candidate_queue = [row for row in self.promotion_queue if row != winner]
        self.promotion_queue = candidate_queue
        self.promotion_awards.add(winner.subject_id)
        return self._commit(command, 129)

    def transfer_talent_130(
        self,
        command: CommandToken,
        *,
        subject_id: str,
        source_manager_id: str,
        destination_manager_id: str,
        pip_disclosed: bool,
        wrong_role_evidence: bool,
        trial_success: bool,
    ) -> ActionResult:
        gate = self._gate(command, 130)
        if gate:
            return gate
        subject_id = self._require_text(subject_id, "subject_id")
        source_manager_id = self._require_text(source_manager_id, "source_manager_id")
        destination_manager_id = self._require_text(
            destination_manager_id, "destination_manager_id"
        )
        for label, value in (
            ("pip_disclosed", pip_disclosed),
            ("wrong_role_evidence", wrong_role_evidence),
            ("trial_success", trial_success),
        ):
            if type(value) is not bool:
                raise DomainRed(RedCode.INVALID_TYPE, f"{label} must be bool")
        if source_manager_id == destination_manager_id:
            raise DomainRed(RedCode.INVALID_VALUE, "transfer managers must differ")
        if subject_id in self.talent_transfers:
            raise DomainRed(RedCode.STATE_CONFLICT, "subject already transferred")
        if wrong_role_evidence and trial_success:
            outcome = "wrong_role_rescued"
        elif not trial_success:
            outcome = "trial_failed"
        else:
            outcome = "transfer_sustained"
        self.talent_transfers[subject_id] = TalentTransfer(
            subject_id,
            source_manager_id,
            destination_manager_id,
            pip_disclosed,
            wrong_role_evidence,
            trial_success,
            outcome,
            source_accountability=(not pip_disclosed and not trial_success),
        )
        return self._commit(command, 130)

    def stop_project_132(
        self,
        command: CommandToken,
        *,
        project_id: str,
        evidence_strength: int,
        avoidable_delay: bool,
    ) -> ActionResult:
        gate = self._gate(command, 132)
        if gate:
            return gate
        project = self._project(project_id, active=True)
        evidence_strength = self._require_int(
            evidence_strength, "evidence_strength", minimum=0
        )
        if type(avoidable_delay) is not bool:
            raise DomainRed(RedCode.INVALID_TYPE, "avoidable_delay must be bool")
        spent, _released = self._terminal_project_candidate(project, state=ProjectState.STOPPED)
        if evidence_strength >= 60 and not avoidable_delay:
            judgement = "timely_stop_credit"
        elif avoidable_delay:
            judgement = "late_stop_accountability"
        else:
            judgement = "insufficient_evidence_no_credit"
        project.reserved_capacity_hours = spent
        project.state = ProjectState.STOPPED
        project.business_outcome = "stopped"
        project.individual_outcome = "judgement_separate_from_business_result"
        project.stop_judgement = judgement
        self._touch_project(project)
        return self._commit(command, 132)

    def record_postmortem_133(
        self,
        command: CommandToken,
        *,
        project_id: str,
        system_causes: tuple[str, ...],
        violations_by_actor: Mapping[str, tuple[str, ...]],
        learning_actions: tuple[str, ...],
    ) -> ActionResult:
        gate = self._gate(command, 133)
        if gate:
            return gate
        project = self._project(project_id)
        if project.state is ProjectState.ACTIVE:
            raise DomainRed(RedCode.STATE_CONFLICT, "postmortem requires a terminal project")
        if project_id in self.postmortems:
            raise DomainRed(RedCode.STATE_CONFLICT, "postmortem already recorded")
        if not isinstance(system_causes, tuple) or not isinstance(learning_actions, tuple):
            raise DomainRed(RedCode.INVALID_TYPE, "postmortem lists must be tuples")
        causes = tuple(self._require_text(row, "system cause") for row in system_causes)
        learning = tuple(self._require_text(row, "learning action") for row in learning_actions)
        if not causes or not learning:
            raise DomainRed(RedCode.INVALID_VALUE, "postmortem requires facts and learning")
        if not isinstance(violations_by_actor, Mapping):
            raise DomainRed(RedCode.INVALID_TYPE, "violations must be a mapping")
        violations: dict[str, tuple[str, ...]] = {}
        for actor, rows in violations_by_actor.items():
            actor = self._require_text(actor, "violation actor")
            if actor not in project.participants or not isinstance(rows, tuple):
                raise DomainRed(RedCode.INVALID_VALUE, "invalid violation assignment")
            violations[actor] = tuple(
                self._require_text(row, "violation") for row in rows
            )
        self.postmortems[project_id] = {
            "system_causes": causes,
            "learning_actions": learning,
            "individual_liability": violations,
            "blanket_penalty": False,
        }
        self._touch_project(project)
        return self._commit(command, 133)

    def assign_shared_metric_134(
        self,
        command: CommandToken,
        *,
        metric_id: str,
        owner_id: str,
        contributors: tuple[str, ...],
        dependencies: tuple[str, ...],
    ) -> ActionResult:
        gate = self._gate(command, 134)
        if gate:
            return gate
        metric_id = self._require_text(metric_id, "metric_id")
        owner_id = self._require_text(owner_id, "owner_id")
        if metric_id in self.shared_metrics:
            raise DomainRed(RedCode.UNIQUE_OWNER_REQUIRED, "shared metric already has an owner")
        if not isinstance(contributors, tuple) or not isinstance(dependencies, tuple):
            raise DomainRed(RedCode.INVALID_TYPE, "contributors/dependencies must be tuples")
        contributor_rows = tuple(
            self._require_text(row, "contributor") for row in contributors
        )
        dependency_rows = tuple(
            self._require_text(row, "dependency") for row in dependencies
        )
        if owner_id in contributor_rows or len(contributor_rows) != len(set(contributor_rows)):
            raise DomainRed(
                RedCode.UNIQUE_OWNER_REQUIRED,
                "owner is unique and contributors cannot duplicate it or each other",
            )
        self.shared_metrics[metric_id] = SharedMetric(
            metric_id, owner_id, contributor_rows, dependency_rows
        )
        return self._commit(command, 134)

    def assert_invariants(self) -> None:
        if set(MECHANISM_BINDINGS) != EXPECTED_MECHANISM_IDS:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "mechanism coverage drifted")
        if self.project_slots_used > self.project_slot_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "project slots do not conserve")
        if not 0 <= self.capacity_hours_free <= self.capacity_hours_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "portfolio capacity does not conserve")
        for project in self.projects.values():
            if (
                project.manager_id != self.owner_id
                or project.origin_cycle_serial != self.cycle_serial
                or project.origin_case_serial != self.case_serial
                or project.version < 1
                or project.deadline_cycle < project.origin_cycle_serial
            ):
                raise DomainRed(RedCode.INVARIANT_BROKEN, "project identity/version drifted")
            if project.booked_hours > project.reserved_capacity_hours:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "project capacity overspent")
            if project.delivery_hours > project.delivery_capacity_hours:
                raise DomainRed(
                    RedCode.INVARIANT_BROKEN,
                    "reporting/relationship hours failed to displace delivery",
                )
            if project.signed_contributions is not None:
                if sum(project.signed_contributions.values()) != SHARE_TOTAL_BPS:
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "signed shares drifted")
            if project.claimed_contributions is not None:
                if sum(project.claimed_contributions.values()) != SHARE_TOTAL_BPS:
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "claimed shares drifted")
            for claim in project.claims.values():
                if sum(claim.transfer_delta.values()) != 0:
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "claim delta is not net zero")
                if claim.audit_delta and sum(claim.audit_delta.values()) != 0:
                    raise DomainRed(RedCode.INVARIANT_BROKEN, "audit delta is not net zero")
        for packet in self.reports.values():
            project = self.projects.get(packet.project_id)
            if project is None:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "report packet lost its project")
            if (
                packet.owner_id != self.owner_id
                or packet.cycle_serial != self.cycle_serial
                or packet.case_serial != self.case_serial
                or packet.object_version < 1
                or packet.deadline_cycle < packet.cycle_serial
            ):
                raise DomainRed(RedCode.INVARIANT_BROKEN, "report identity/version drifted")
        if self.attention_slots_used > self.attention_slot_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "attention slots overspent")
        if self.matrix is not None:
            if len(self.matrix.weights) != 2 or sum(self.matrix.weights.values()) != 100:
                raise DomainRed(RedCode.INVARIANT_BROKEN, "matrix weights drifted")
        fingerprint = tuple((case.case_id, case.owner_id) for case in self.historical_cases)
        if fingerprint != self._historical_owner_fingerprint:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "historical case owner drifted")
        if len(self.promotion_awards) > self.promotion_slot_total:
            raise DomainRed(RedCode.INVARIANT_BROKEN, "promotion slots overspent")


def validate_model_contract() -> None:
    """Static registry validation; still only Python L0 evidence."""

    if set(MECHANISM_BINDINGS) != EXPECTED_MECHANISM_IDS:
        raise ValueError("phase-three project/credit model must cover exact requested IDs")
    for mechanism_id, binding in MECHANISM_BINDINGS.items():
        if mechanism_id != binding.mechanism_id or not binding.behaviors:
            raise ValueError(f"invalid behavior binding for {mechanism_id}")
        for behavior in binding.behaviors:
            if not callable(getattr(Phase3CreditProjectModel, behavior, None)):
                raise ValueError(f"mechanism {mechanism_id} lacks behavior {behavior}")


validate_model_contract()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Closed typed-operation registry for the ZhongGuo 361 domain runtime.

Runtime JSON is data, never executable Paradox script.  This registry is the
only compiler boundary: a plan may select a whitelisted domain operation and
typed transaction/deadline/feedback records, but it cannot inject arbitrary
script text.  CK3 rendering will consume these immutable compiled records in
domain batches; merely compiling them does not raise gameplay readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

from zg361_domain_data import DOMAIN_SPECS, STALE_GUARD


class OperationKind(str, Enum):
    DOMAIN = "domain"
    PRIMITIVE = "primitive"
    TRANSACTION = "transaction"
    DEADLINE = "deadline"
    FEEDBACK = "feedback"


@dataclass(frozen=True)
class CompiledOperation:
    kind: OperationKind
    mechanism_id: int
    choice: str
    domain: str
    operation_key: str
    payload: tuple[tuple[str, object], ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "mechanism_id": self.mechanism_id,
            "choice": self.choice,
            "domain": self.domain,
            "operation_key": self.operation_key,
            "payload": dict(self.payload),
        }


OPERATION_WHITELIST: Final[frozenset[str]] = frozenset(
    domain.operation_key for domain in DOMAIN_SPECS
)

PRIMITIVE_WHITELIST: Final[frozenset[str]] = frozenset(
    {
        "case.create",
        "case.transition",
        "binding.freeze",
        "record.version",
        "policy.bind",
        "policy.parameter",
        "policy.defer",
        "evidence.attach",
        "evidence.freeze",
        "capacity.allocate",
        "score.compute",
        "rule.evaluate",
        "cohort.lock",
        "vote.record",
        "deadline.schedule",
        "deadline.expire",
        "notice.deliver",
        "access.project",
        "transaction.reserve",
        "transaction.settle",
        "transaction.refund",
        "capacity.reserve",
        "capacity.release",
        "obligation.open",
        "obligation.resolve",
        "candidate.advance",
        "audit.open",
        "audit.resolve",
        "timeline.append",
        "feedback.project",
        "relationship.apply",
        "modifier.apply",
    }
)

_COMMON_RECIPE: Final[tuple[str, ...]] = (
    "case.create",
    "binding.freeze",
    "record.version",
    "rule.evaluate",
    "case.transition",
    "timeline.append",
    "feedback.project",
)

_DOMAIN_RECIPE_EXTRAS: Final[dict[str, tuple[str, ...]]] = {
    "A": ("policy.bind", "evidence.attach", "evidence.freeze", "score.compute", "capacity.reserve", "capacity.release"),
    "B": ("evidence.attach", "evidence.freeze", "score.compute", "cohort.lock", "vote.record"),
    "C": ("notice.deliver", "obligation.open", "obligation.resolve", "transaction.reserve", "transaction.settle", "transaction.refund"),
    "D": ("candidate.advance", "vote.record", "capacity.reserve", "transaction.reserve", "transaction.settle", "capacity.release"),
    "E": ("evidence.attach", "evidence.freeze", "audit.open", "audit.resolve", "vote.record"),
    "F": ("evidence.freeze", "score.compute", "modifier.apply", "access.project"),
    "G": ("cohort.lock", "score.compute", "vote.record", "obligation.open", "obligation.resolve"),
    "H": ("capacity.reserve", "evidence.attach", "evidence.freeze", "audit.open", "audit.resolve", "capacity.release"),
    "I": ("capacity.reserve", "evidence.attach", "record.version", "access.project", "capacity.release"),
    "J": ("binding.freeze", "vote.record", "relationship.apply", "record.version"),
    "K": ("notice.deliver", "deadline.schedule", "deadline.expire", "audit.open", "audit.resolve", "transaction.refund", "access.project"),
    "L": ("transaction.reserve", "transaction.settle", "transaction.refund", "obligation.open", "obligation.resolve"),
    "M": ("candidate.advance", "vote.record", "modifier.apply", "relationship.apply"),
    "N": ("capacity.reserve", "candidate.advance", "deadline.schedule", "deadline.expire", "capacity.release"),
    "O": ("candidate.advance", "evidence.attach", "score.compute", "obligation.open", "obligation.resolve"),
    "P": ("candidate.advance", "deadline.schedule", "deadline.expire", "relationship.apply", "modifier.apply"),
    "Q": ("score.compute", "evidence.attach", "evidence.freeze", "modifier.apply", "relationship.apply"),
    "R": ("policy.parameter", "capacity.reserve", "evidence.freeze", "audit.open", "audit.resolve", "capacity.release"),
    "S": ("score.compute", "cohort.lock", "vote.record", "evidence.freeze", "obligation.open", "obligation.resolve"),
    "T": ("notice.deliver", "obligation.open", "deadline.schedule", "deadline.expire", "obligation.resolve"),
    "U": ("candidate.advance", "capacity.reserve", "evidence.attach", "audit.open", "audit.resolve", "capacity.release"),
    "V": ("candidate.advance", "vote.record", "capacity.reserve", "evidence.freeze", "capacity.release"),
    "W": ("notice.deliver", "capacity.reserve", "obligation.open", "deadline.schedule", "deadline.expire", "obligation.resolve", "capacity.release"),
    "X": ("capacity.reserve", "notice.deliver", "evidence.freeze", "audit.open", "audit.resolve", "modifier.apply", "capacity.release"),
    "Y": ("obligation.open", "capacity.reserve", "evidence.attach", "audit.open", "audit.resolve", "obligation.resolve", "capacity.release"),
    "Z": ("candidate.advance", "capacity.reserve", "transaction.reserve", "transaction.settle", "audit.open", "audit.resolve", "capacity.release"),
    "AA": ("policy.parameter", "record.version", "capacity.reserve", "evidence.freeze", "score.compute", "audit.open", "audit.resolve", "capacity.release"),
    "AB": ("capacity.allocate", "capacity.reserve", "transaction.reserve", "transaction.settle", "transaction.refund", "modifier.apply", "capacity.release"),
    "AC": ("candidate.advance", "capacity.reserve", "transaction.reserve", "transaction.settle", "relationship.apply", "capacity.release"),
    "AD": ("candidate.advance", "vote.record", "capacity.reserve", "transaction.reserve", "transaction.settle", "capacity.release"),
    "AE": ("notice.deliver", "transaction.reserve", "transaction.settle", "transaction.refund", "obligation.open", "obligation.resolve"),
    "AF": ("candidate.advance", "transaction.reserve", "transaction.settle", "transaction.refund", "deadline.schedule", "deadline.expire"),
    "AG": ("binding.freeze", "record.version", "capacity.allocate", "relationship.apply", "evidence.freeze"),
    "AH": ("candidate.advance", "deadline.schedule", "deadline.expire", "relationship.apply", "transaction.reserve", "transaction.settle"),
    "AI": ("capacity.reserve", "evidence.attach", "score.compute", "obligation.open", "obligation.resolve", "capacity.release"),
    "AJ": ("policy.parameter", "capacity.reserve", "obligation.open", "evidence.freeze", "obligation.resolve", "capacity.release"),
    "AK": ("policy.bind", "policy.parameter", "audit.open", "audit.resolve", "deadline.schedule", "deadline.expire", "access.project"),
    "AL": ("evidence.freeze", "score.compute", "cohort.lock", "vote.record", "transaction.refund", "policy.bind", "relationship.apply"),
}

DOMAIN_RECIPE_PRIMITIVES: Final[dict[str, tuple[str, ...]]] = {
    domain.operation_key: tuple(dict.fromkeys((*_COMMON_RECIPE, *_DOMAIN_RECIPE_EXTRAS[domain.code])))
    for domain in DOMAIN_SPECS
}

if set(_DOMAIN_RECIPE_EXTRAS) != {domain.code for domain in DOMAIN_SPECS}:
    raise ValueError("primitive recipes must cover every domain exactly once")
if any(
    primitive not in PRIMITIVE_WHITELIST
    for recipe in DOMAIN_RECIPE_PRIMITIVES.values()
    for primitive in recipe
):
    raise ValueError("a domain recipe contains a non-whitelisted primitive")


def _frozen_payload(**values: object) -> tuple[tuple[str, object], ...]:
    return tuple(sorted(values.items()))


def compile_choice_ops(
    plan: dict[str, object],
    choice_name: str,
) -> tuple[CompiledOperation, ...]:
    mechanism_id = int(plan["id"])
    domain = str(plan["domain"])
    operation_key = str(plan["operation_key"])
    if operation_key not in OPERATION_WHITELIST:
        raise ValueError(
            f"mechanism {mechanism_id:03d} requested non-whitelisted operation {operation_key!r}"
        )
    choices = plan.get("choices")
    if not isinstance(choices, dict) or choice_name not in choices:
        raise ValueError(f"mechanism {mechanism_id:03d} lacks choice {choice_name}")
    route = choices[choice_name]
    if not isinstance(route, dict):
        raise ValueError(f"mechanism {mechanism_id:03d}/{choice_name} is not an object")
    old_states = route.get("allowed_from_states")
    if not isinstance(old_states, list) or len(old_states) != 1:
        raise ValueError(f"mechanism {mechanism_id:03d}/{choice_name} lacks one source state")

    compiled: list[CompiledOperation] = [
        CompiledOperation(
            kind=OperationKind.DOMAIN,
            mechanism_id=mechanism_id,
            choice=choice_name,
            domain=domain,
            operation_key=operation_key,
            payload=_frozen_payload(
                from_state=old_states[0],
                to_state=route["to_state"],
                hook=plan["trigger_hook"],
                variant=plan["semantic_family"],
                mode=route["parameters"]["mode"],
            ),
        )
    ]
    policy_primitive = "policy.defer" if choice_name == "c" else "policy.bind"
    primitives = tuple(
        dict.fromkeys((policy_primitive, *DOMAIN_RECIPE_PRIMITIVES[operation_key]))
    )
    for primitive in primitives:
        compiled.append(
            CompiledOperation(
                kind=OperationKind.PRIMITIVE,
                mechanism_id=mechanism_id,
                choice=choice_name,
                domain=domain,
                operation_key=primitive,
                payload=_frozen_payload(
                    recipe=operation_key,
                    variant=plan["semantic_family"],
                    mode=route["parameters"]["mode"],
                ),
            )
        )
    for transaction in route["transactions"]:
        compiled.append(
            CompiledOperation(
                kind=OperationKind.TRANSACTION,
                mechanism_id=mechanism_id,
                choice=choice_name,
                domain=domain,
                operation_key="transfer_with_receipt",
                payload=tuple(sorted(transaction.items())),
            )
        )
    deadline = route["deadline"]
    if deadline["kind"] == "scheduled_event":
        if tuple(deadline["stale_guard"]) != STALE_GUARD:
            raise ValueError(
                f"mechanism {mechanism_id:03d}/{choice_name} deadline lacks the full stale guard"
            )
        compiled.append(
            CompiledOperation(
                kind=OperationKind.DEADLINE,
                mechanism_id=mechanism_id,
                choice=choice_name,
                domain=domain,
                operation_key="schedule_guarded_deadline",
                payload=tuple(sorted(deadline.items())),
            )
        )
    for index, feedback in enumerate(route["visible_feedback"], start=1):
        compiled.append(
            CompiledOperation(
                kind=OperationKind.FEEDBACK,
                mechanism_id=mechanism_id,
                choice=choice_name,
                domain=domain,
                operation_key="project_visible_feedback",
                payload=_frozen_payload(index=index, feedback=feedback),
            )
        )
    return tuple(compiled)


def render_transition_guard(operation: CompiledOperation) -> dict[str, object]:
    if operation.kind is not OperationKind.DOMAIN:
        raise ValueError("transition guards apply only to domain operations")
    payload = dict(operation.payload)
    return {
        "owner_scope": "frozen_reviewing_manager",
        "subject_scope": "frozen_assessed_official",
        "cycle_scope": "review_cycle_serial",
        "case_scope": f"{operation.domain.lower()}_case_serial",
        "expected_state": payload["from_state"],
        "to_state": payload["to_state"],
        "hook": payload["hook"],
    }


def render_transaction(operation: CompiledOperation) -> dict[str, object]:
    if operation.kind is not OperationKind.TRANSACTION:
        raise ValueError("transaction rendering requires a transaction operation")
    payload = dict(operation.payload)
    return {
        key: payload[key]
        for key in (
            "debit_account",
            "credit_account",
            "currency",
            "amount",
            "timing",
            "receipt_key",
            "refund_policy",
        )
    }


def render_deadline(operation: CompiledOperation) -> dict[str, object]:
    if operation.kind is not OperationKind.DEADLINE:
        raise ValueError("deadline rendering requires a deadline operation")
    payload = dict(operation.payload)
    if tuple(payload["stale_guard"]) != STALE_GUARD:
        raise ValueError("deadline stale guard drifted after compilation")
    return payload


def render_feedback_projection(operation: CompiledOperation) -> dict[str, object]:
    if operation.kind is not OperationKind.FEEDBACK:
        raise ValueError("feedback rendering requires a feedback operation")
    return dict(operation.payload)

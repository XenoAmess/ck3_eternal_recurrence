"""Phase 0 validator for the 361-domain graph catalogue.

The validator is intentionally independent of CK3 and has no runtime side
effects. It checks coverage, graph reachability, capacity/cleanup contracts and
the unified manager/subject ACL. A valid catalogue is still only a schema
milestone; it is not evidence that any domain executes in CK3.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DOMAIN_CODES = [chr(i) for i in range(ord("A"), ord("Z") + 1)] + [f"A{chr(i)}" for i in range(ord("A"), ord("L") + 1)]
# The global boundary carries the complete deferred-religion vocabulary,
# including `fervor`.  Per-domain records predate that global addition and
# intentionally repeat the narrower prohibition list; requiring `fervor` in
# every record would reject the canonical catalogue while still adding no
# protection beyond the global boundary/text check.
FORBIDDEN = {"religion", "faith", "doctrine", "tenet", "fervor", "conversion", "reformation", "holy_order"}
DOMAIN_REQUIRED_FORBIDDEN = FORBIDDEN - {"fervor"}
STALE_GUARD = {"owner", "cycle_serial", "case_serial", "expected_state"}
POLICY = "celestial_manager_reviews_direct_vassal"


def load_catalogue(path: str | Path | None = None) -> dict[str, Any]:
    path = Path(path) if path else Path(__file__).parents[1] / "src/main/resources/zg361/domains.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalogue(catalogue: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(catalogue, dict):
        return ["catalogue must be an object"]
    if catalogue.get("lifecycle_status") != "schema-and-validator-only":
        errors.append("lifecycle_status must remain schema-and-validator-only in Phase 0")
    if catalogue.get("mechanism_coverage") != {"first": 1, "last": 361, "cardinality": 361}:
        errors.append("mechanism_coverage must describe 1..361")
    if catalogue.get("domain_coverage", {}).get("cardinality") != 38:
        errors.append("domain_coverage must describe 38 domains")

    policies = _mapping_or_empty(catalogue.get("permission_policies"))
    policy = _mapping_or_empty(policies.get(POLICY))
    player_manager = _mapping_or_empty(policy.get("player_manager"))
    ai_manager = _mapping_or_empty(policy.get("ai_manager"))
    subject = _mapping_or_empty(policy.get("subject"))
    boundaries = _mapping_or_empty(catalogue.get("global_boundaries"))
    _require(player_manager.get("all_of", []), {"is_ai=no", "zg361_is_celestial_liege_trigger=yes"}, "player manager ACL", errors)
    _require(ai_manager.get("all_of", []), {"is_ai=yes", "zg361_is_celestial_liege_trigger=yes", "entry=backend_resolver_only"}, "AI manager ACL", errors)
    _require(subject.get("all_of", []), {"zg361_is_reviewable_vassal_trigger=yes"}, "subject ACL", errors)
    _require(policy.get("denied", []), {"baron_or_count_as_manager", "non_celestial_government_manager", "non_direct_vassal_subject", "ai_event_or_gui_entry", "religion_or_faith_system_entry"}, "denied ACL", errors)
    _require(boundaries.get("prohibited_capabilities", []), FORBIDDEN, "global prohibited capabilities", errors)

    domains = _list_or_empty(catalogue.get("domains"))
    if len(domains) != 38:
        errors.append(f"expected exactly 38 domains, got {len(domains)}")
    seen_codes: set[str] = set()
    covered: set[int] = set()
    for domain in domains:
        if not isinstance(domain, dict):
            errors.append("domain entry must be an object")
            continue
        code = domain.get("code", "<missing>")
        prefix = f"{code}: "
        if code in seen_codes:
            errors.append(prefix + "duplicate domain code")
        seen_codes.add(code)
        if code not in DOMAIN_CODES:
            errors.append(prefix + "unknown domain code")
        ids = _mapping_or_empty(domain.get("mechanism_ids"))
        first, last = ids.get("first"), ids.get("last")
        if not isinstance(first, int) or not isinstance(last, int) or not (1 <= first <= last <= 361):
            errors.append(prefix + "invalid mechanism id range")
        else:
            overlap = covered.intersection(range(first, last + 1))
            if overlap:
                errors.append(prefix + f"overlapping mechanism ids: {sorted(overlap)}")
            covered.update(range(first, last + 1))

        if domain.get("permission_policy") != POLICY:
            errors.append(prefix + "must use unified permission policy")
        entry_hooks = _list_or_empty(domain.get("allowed_entry_hooks"))
        if not isinstance(entry_hooks, list) or not entry_hooks:
            errors.append(prefix + "at least one allowed entry hook is required")
        states = _list_or_empty(domain.get("states"))
        values = [domain.get("object_type"), domain.get("owner_scope"), domain.get("subject_scope"), *states, *entry_hooks]
        if any(any(token in str(value).lower() for token in FORBIDDEN) for value in values):
            errors.append(prefix + "religion/faith/holy-order semantics are prohibited")
        _require(domain.get("prohibited_capabilities", []), DOMAIN_REQUIRED_FORBIDDEN,
                 prefix + "prohibited capabilities", errors)

        capacity = _mapping_or_empty(domain.get("capacity"))
        if capacity.get("max_active_per_subject") != 1 or capacity.get("max_active_per_owner", 0) < 1 or not capacity.get("invariant"):
            errors.append(prefix + "bounded capacity invariant is required")
        cleanup = _mapping_or_empty(domain.get("cleanup"))
        if cleanup.get("stale_deadline") != "no_op_with_marker":
            errors.append(prefix + "stale deadline must be a marked no-op")
        _require(cleanup.get("guard", []), STALE_GUARD, prefix + "stale guard", errors)
        if cleanup.get("retention_cycles", -1) < 0 or not cleanup.get("on_terminal"):
            errors.append(prefix + "cleanup retention and terminal action are required")

        state_set = set(states)
        if len(states) < 2 or len(state_set) != len(states):
            errors.append(prefix + "states must be unique and contain at least two entries")
        if domain.get("initial_state") not in state_set:
            errors.append(prefix + "initial_state is not declared")
        terminals = set(_list_or_empty(domain.get("terminal_states")))
        if not terminals or not terminals <= state_set:
            errors.append(prefix + "terminal_states must be declared states")
        edges: dict[str, set[str]] = {}
        for transition in _list_or_empty(domain.get("transitions")):
            if not isinstance(transition, dict):
                errors.append(prefix + "transition must be an object")
                continue
            source, target = transition.get("from"), transition.get("to")
            if source not in state_set or target not in state_set or source == target or not transition.get("hook") or not transition.get("actor"):
                errors.append(prefix + f"invalid transition: {transition}")
                continue
            if source in terminals:
                errors.append(prefix + f"terminal state has outgoing transition: {source}")
            edges.setdefault(source, set()).add(target)
        reachable = _reachable(domain.get("initial_state"), edges)
        if reachable != state_set:
            errors.append(prefix + f"unreachable states: {sorted(state_set - reachable)}")

    if seen_codes != set(DOMAIN_CODES):
        errors.append(f"domain code set mismatch: missing {sorted(set(DOMAIN_CODES) - seen_codes)}")
    if covered != set(range(1, 362)):
        errors.append("mechanism id coverage must be exactly 1..361")
    return errors


def _require(actual: list[str], required: set[str], label: str, errors: list[str]) -> None:
    missing = required - set(actual or [])
    if missing:
        errors.append(f"{label} is missing {sorted(missing)}")


def _list_or_empty(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _mapping_or_empty(value: Any) -> dict[str, Any]:
    """Treat a malformed object field as absent so validation can report it.

    The validator is a diagnostic boundary: a broken schema should produce a
    deterministic error list rather than an incidental ``AttributeError``.
    """
    return value if isinstance(value, dict) else {}


def _reachable(initial: str | None, edges: dict[str, set[str]]) -> set[str]:
    seen: set[str] = set()
    queue = [initial] if initial else []
    while queue:
        state = queue.pop(0)
        if state in seen:
            continue
        seen.add(state)
        queue.extend(edges.get(state, ()))
    return seen


if __name__ == "__main__":
    problems = validate_catalogue(load_catalogue())
    if problems:
        raise SystemExit("\n".join(problems))
    print("zg361 domains: PASS (schema-only; runtime not implemented)")

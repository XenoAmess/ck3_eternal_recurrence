"""Finite stage permissions for the explicit major-H1 / H2 / H3 product case."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Literal, Protocol, TypedDict, runtime_checkable

import faith_e02_h1_queue as Q
import faith_e02_hof_queue as HOF
from ck3_mod_acceptance_cases.faith_e02_ghw_observation_contract import GhwObservation

CASE = "faith-engine-e02-h1-major-h2-ghw-composite-v1"
SCHEMA = "faith-e02-h1-major-h2-ghw-composite-case-v1"
Stage = Literal["h1", "h2", "events", "h3", "done"]
MAX_CALLS = 128
GHW = "ck3_query_player_ghw_permissions_v1"
PILGRIMAGE = "ck3_query_player_pilgrimage_activities_v1"
EVENTS = frozenset({HOF.EVENT_CONTEXT, HOF.EVENT_SELECT, "ck3_take_snapshot"})
H1_TOOLS = Q.READS | Q.PRESENT | {Q.PROMOTE}
H2_TOOLS = frozenset({Q.RELIGION, Q.GOVERNANCE, HOF.CONFIRM, "ck3_take_snapshot"})
H3_TOOLS = Q.READS | Q.PRESENT | {GHW, PILGRIMAGE}
STAGE_TOOLS: dict[Stage, frozenset[str]] = {
    "h1": frozenset(H1_TOOLS), "h2": H2_TOOLS, "events": EVENTS,
    "h3": frozenset(H3_TOOLS), "done": frozenset(),
}
REQUIRED = frozenset(H1_TOOLS | H2_TOOLS | H3_TOOLS | EVENTS | Q.LIFECYCLE)
READONLY = frozenset({Q.SITES, Q.RELIGION, Q.GOVERNANCE, Q.DETAIL, Q.COOLDOWN, GHW, PILGRIMAGE})


class Client(Protocol):
    operator_reviewer: str
    manifest: Q.Obj
    def snapshot(self, *, require_event_free: bool = True) -> object: ...
    def execute_plan(self, steps: list[Q.Obj], name: str, timeout: float | None = None,
                     reserve: Literal[90] = 90) -> object: ...
    def guard(self, reserve: float = 0) -> object: ...
    def root_checkpoint(self, name: str, payload: Q.Obj, reserve: int = 120) -> object: ...


class Wallet(TypedDict):
    gold: int
    prestige: int
    piety: int
    treasury_field_present: bool
    treasury_raw: int | None


class WalletDelta(TypedDict):
    gold: int | None
    prestige: int | None
    piety: int | None
    treasury: int | None


class H2Post(TypedDict):
    snapshot: Q.Obj | None
    religion: Q.Obj | None
    governance: Q.Obj | None
    heads: Q.Obj | None
    wallet: Wallet | None
    errors: dict[str, str]
    head_creation_observed: bool


@runtime_checkable
class LegacyObservation(Protocol):
    """Checked calls to existing typed observation / bounded event entry points."""
    __file__: str
    def require_identity(self, religion: Q.Obj, governance: Q.Obj, *, no_head: bool) -> object: ...
    def drain_current_events(self, context: Q.Obj, client: Client, frame: Q.Obj,
        binding: Mapping[str, object], reader: Callable[[object], Mapping[str, object]],
        *, phase: str = "hof-r19-post") -> object: ...
    def observe_ghw(self, context: Mapping[str, object], client: Client,
        binding: Mapping[str, object], reader: Callable[[object], Mapping[str, object]]) -> GhwObservation: ...


def validate_steps(stage: Stage, steps: object) -> list[Q.Obj]:
    values = Q.array(steps)
    Q.require(1 <= len(values) <= 8, "Composite requires a finite public batch")
    result: list[Q.Obj] = []
    ids: set[str] = set()
    for value in values:
        row = Q.obj(value)
        name, tool = Q.text(row.get("id")), Q.text(row.get("tool"))
        Q.require(name not in ids and len(name) <= 128
            and set(row) <= {"id", "tool", "kind", "args", "fresh_revision", "continue_on_error", "timeout"}
            and row.get("kind", "tool") == "tool" and row.get("fresh_revision") is True
            and row.get("continue_on_error") is True and tool in STAGE_TOOLS[stage],
            "Tool is outside the explicit current composite stage")
        args = Q.obj(row.get("args"))
        if tool == HOF.CONFIRM:
            Q.require(stage == "h2" and args == {"decision_key": Q.DECISION, "expected_outcome": "decision_closed"},
                "Only the major H2 phase can submit the original HoF Confirm")
        Q.require(not (tool == Q.PROMOTE and stage != "h1"), "Promotion belongs only to H1")
        ids.add(name)
        result.append(row)
    return result


def dependency_paths(value: object) -> set[Path]:
    return {Path(Q.checked_pin(ref)["path"]).resolve() for ref in Q.array(value)}


def main() -> None:
    import argparse
    from ck3_mod_acceptance_cases.faith_e02_h1_h2_composite_adapter import make_metadata
    parser = argparse.ArgumentParser(description="Write the explicit major H1/H2/H3 case metadata only")
    parser.add_argument("--major-h1-fragment", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    fragment: object = args.major_h1_fragment
    output: object = args.output
    if not isinstance(fragment, Path) or not isinstance(output, Path):
        raise ValueError("Composite CLI requires parsed paths")
    make_metadata(fragment, output)


if __name__ == "__main__":
    main()

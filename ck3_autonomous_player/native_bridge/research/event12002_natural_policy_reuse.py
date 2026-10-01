"""Read a saved paused event with the existing registry and formal turn planner.

This adapter never opens CK3, sends a query, or submits the returned typed call.
It adds no policy. The caller supplies the actual public snapshot, query receipt,
and advertised action steps from its already-owned production session.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src"
sys.path.insert(0, str(SOURCE_ROOT))

from xar_autoplayer.bridge.event_contract import action_step_set
from xar_autoplayer.strategy import choose_one_life_turn
from xar_autoplayer.vanilla_events.builds import CURRENT_CK3_BUILD
from xar_autoplayer.vanilla_events.policy import (
    recommend_registered_vanilla_event_option_v1,
)


def inspect_saved_event(
    snapshot: dict[str, object],
    query_result: dict[str, object],
    *,
    action_steps: list[str],
    commands: list[dict[str, object]],
    bridge_capabilities: list[str] | None = None,
) -> dict[str, object]:
    """Return the production decision and its existing typed-call parameters."""
    context = query_result["current_event_window_context"]
    player = snapshot["played_character"]
    active = snapshot["active_event"]
    registry_decision = recommend_registered_vanilla_event_option_v1(
        context,
        played_character_id=player["character_id"],
        snapshot_option_count=active["option_count"],
        ck3_build=CURRENT_CK3_BUILD,
    )
    plan = choose_one_life_turn(
        commands,
        snapshot=snapshot,
        action_steps=action_steps,
        bridge_capabilities=bridge_capabilities,
    )
    typed_call = None
    if plan.get("phase") == "active_event_registry_choice":
        decision = plan["event_decision"]
        typed_call = {
            "api": "GameplayBridgeService.select_event_option",
            "mcp_tool": "ck3_select_event_option",
            "arguments": {
                "option_number": decision["selected_option_number"],
                "event_instance_id": context["current_event_instance_id"],
                "expected_revision": query_result["queried_revision"],
            },
        }
    return {
        "ck3_build": CURRENT_CK3_BUILD,
        "registry_decision": registry_decision,
        "formal_plan": plan,
        "typed_call": typed_call,
        "read_only": True,
        "new_live_evidence": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--query-result", type=Path, required=True)
    parser.add_argument("--capabilities", type=Path, required=True)
    parser.add_argument("--commands", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8"))
    capabilities = read(args.capabilities)
    result = inspect_saved_event(
        read(args.snapshot), read(args.query_result),
        action_steps=sorted(action_step_set(capabilities)),
        bridge_capabilities=capabilities.get("bridge_capabilities"),
        commands=read(args.commands),
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"phase": result["formal_plan"]["phase"],
                      "typed_call": result["typed_call"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

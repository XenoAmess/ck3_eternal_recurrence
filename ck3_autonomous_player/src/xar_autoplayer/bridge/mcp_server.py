"""Official MCP v2 server facade for replaceable CK3 gameplay drivers."""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
from .driver import (
    DevelopmentReportDriver,
    GameplayBridgeDriver,
    HybridGameplayDriver,
)
from .mod_driver import load_data_mod_driver
from .native_driver import (
    ConfiguredHybridFallbackDriver,
    MinimizedRejectingVisualDriver,
    NativeHeadlessGameplayDriver,
    selected_pipe_name,
)
from .session_driver import DevelopmentSessionDriver
from .service import GameplayBridgeService
from .war_entry_contract import normalize_war_entry_target_ids


def _default_state_dir() -> Path:
    configured = os.environ.get("XAR_AUTOPLAYER_STATE_DIR")
    if configured:
        return Path(configured)
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA or XAR_AUTOPLAYER_STATE_DIR is required")
    return Path(local) / "XarAutoplayer"


def load_driver(
    factory: str | None,
    *,
    userdir: str | os.PathLike[str] | None = None,
    state_dir: str | os.PathLike[str] | None = None,
    pipe_name: str | None = None,
) -> GameplayBridgeDriver:
    """Load a daemon driver without coupling MCP to a concrete game bridge."""
    def selected_state_dir() -> Path:
        return Path(state_dir) if state_dir else _default_state_dir()

    def selected_save_dir() -> Path:
        return selected_state_dir() / "profile" / "save games"

    if not factory or factory == "vision-report":
        return DevelopmentReportDriver(selected_state_dir())
    if factory == "vision-session":
        return DevelopmentSessionDriver(selected_state_dir())
    if factory == "mod":
        return load_data_mod_driver(userdir)
    if factory == "hybrid":
        return HybridGameplayDriver(
            load_data_mod_driver(userdir),
            DevelopmentSessionDriver(selected_state_dir()),
        )
    if factory == "native-headless":
        return NativeHeadlessGameplayDriver(
            selected_pipe_name(pipe_name),
            state_dir=selected_state_dir(),
            save_dir=selected_save_dir(),
        )
    if factory == "hybrid-fallback":
        return ConfiguredHybridFallbackDriver(
            NativeHeadlessGameplayDriver(
                selected_pipe_name(pipe_name),
                state_dir=selected_state_dir(),
                save_dir=selected_save_dir(),
            ),
            load_data_mod_driver(userdir),
            MinimizedRejectingVisualDriver(
                DevelopmentSessionDriver(selected_state_dir())
            ),
        )
    module_name, separator, attribute = factory.partition(":")
    if not separator or not module_name or not attribute:
        raise ValueError(
            "driver factory must be vision-report, vision-session, mod, "
            "hybrid, native-headless, hybrid-fallback, or module:callable"
        )
    candidate = getattr(importlib.import_module(module_name), attribute)
    if not callable(candidate):
        raise TypeError("driver factory is not callable")
    driver = candidate()
    if not isinstance(driver, GameplayBridgeDriver):
        raise TypeError("driver factory did not return a GameplayBridgeDriver")
    return driver


def _ck3_query_combat_simulation_inputs_v3(
    service: GameplayBridgeService,
    target_province_id: int,
    attacker_entry_province_id: int,
    attacker_army_ids: list[int],
    defender_army_ids: list[int],
    expected_revision: int | None = None,
) -> dict[str, object]:
    """Official production-v3 facade shared by MCP and contract tests."""
    return service.query_combat_simulation_inputs_v3(
        target_province_id,
        attacker_entry_province_id,
        attacker_army_ids,
        defender_army_ids,
        expected_revision=expected_revision,
    )


def _ck3_query_war_entry_assessments(
    service: GameplayBridgeService,
    target_character_ids: list[int],
    expected_revision: int | None = None,
) -> dict[str, object]:
    """Official one-target exact-build strategic-power facade."""
    targets = normalize_war_entry_target_ids(target_character_ids)
    return service.query_war_entry_assessments(
        targets,
        expected_revision=expected_revision,
    )


def _ck3_query_actual_contact_scope(
    service: GameplayBridgeService,
    subject_army_id: int,
    target_province_id: int,
    expected_revision: int | None = None,
) -> dict[str, object]:
    """Official pre-contact prediction or post-contact observation facade."""
    return service.query_actual_contact_scope(
        subject_army_id,
        target_province_id,
        expected_revision=expected_revision,
    )


def _ck3_query_battle_control_snapshot_v1(
    service: GameplayBridgeService,
    subject_army_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe retreat gates for one full public CUnitID without mutation."""
    return service.query_battle_control_snapshot_v1(
        subject_army_id,
        expected_revision=expected_revision,
    )


def _ck3_query_battle_transition_v1(
    service: GameplayBridgeService,
    combat_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe one positive full CombatID without an army-state gate."""
    return service.query_battle_transition_v1(
        combat_id,
        expected_revision=expected_revision,
    )


def _ck3_query_battle_terminal_transition_v1(
    service: GameplayBridgeService,
    prior_combat_id: int,
    subject_public_cunit_id: int,
    expected_revision: int,
    after_terminal_sequence: int | None = None,
) -> dict[str, object]:
    """Observe a journal-backed terminal event and exact successor state."""
    return service.query_battle_terminal_transition_v1(
        prior_combat_id,
        subject_public_cunit_id,
        expected_revision=expected_revision,
        after_terminal_sequence=after_terminal_sequence,
    )


def _ck3_query_battle_reinforcement_assignment_v1(
    service: GameplayBridgeService,
    selected_public_cunit_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe one CUnit's native AI help assignment without mutation."""
    return service.query_battle_reinforcement_assignment_v1(
        selected_public_cunit_id,
        expected_revision=expected_revision,
    )


def _ck3_query_campaign_root_context_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Observe the exact local-player root and loaded rule selection."""
    return service.query_campaign_root_context_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_loaded_feature_manifest_v1(
    service: GameplayBridgeService,
    expected_revision: int,
) -> dict[str, object]:
    """Observe effective feature flags and script DLC keys without ownership inference."""
    return service.query_loaded_feature_manifest_v1(
        expected_revision=expected_revision,
    )


def _ck3_query_pending_character_interaction_context_v1(
    service: GameplayBridgeService,
    pending_interaction_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe one pending request, including costs and typed war binding."""
    return service.query_pending_character_interaction_context_v1(
        pending_interaction_id,
        expected_revision=expected_revision,
    )


def _ck3_query_current_event_window_context_v1(
    service: GameplayBridgeService,
    event_instance_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Observe one active event's options and lossy typed effect indicators."""
    return service.query_current_event_window_context_v1(
        event_instance_id,
        expected_revision=expected_revision,
    )


def _ck3_preview_active_combat_retreat_v1(
    service: GameplayBridgeService,
    selected_public_cunit_id: int,
    target_province_id: int,
    expected_revision: int,
) -> dict[str, object]:
    """Issue a token only for a legal same-frame exact native route."""
    return service.preview_active_combat_retreat_v1(
        selected_public_cunit_id,
        target_province_id,
        expected_revision=expected_revision,
    )


def _ck3_order_active_combat_retreat_v1(
    service: GameplayBridgeService,
    selected_public_cunit_id: int,
    expected_revision: int,
    expected_combat_id: int,
    expected_side_index: int,
    expected_scope: str,
    target_province_id: int,
    candidate_token: str,
) -> dict[str, object]:
    """Re-prove and consume one active-retreat token before player movement."""
    return service.order_active_combat_retreat_v1(
        selected_public_cunit_id,
        expected_revision=expected_revision,
        expected_combat_id=expected_combat_id,
        expected_side_index=expected_side_index,
        expected_scope=expected_scope,
        target_province_id=target_province_id,
        candidate_token=candidate_token,
    )


def create_server(driver: GameplayBridgeDriver):
    """Build the MCP server lazily so baseline vision installs need no SDK."""
    try:
        from mcp.server import MCPServer
    except ImportError as error:
        raise RuntimeError(
            "MCP mode requires the optional dependency: pip install 'mcp==2.0.0'"
        ) from error

    service = GameplayBridgeService(driver)
    server = MCPServer(
        name="Xar CK3 Gameplay Bridge",
        version="0.1.0",
        instructions=(
            "Control the current one-life CK3 episode through semantic steps. "
            "Use ck3_plan_turn unless a specific gameplay step is requested."
        ),
    )

    @server.tool()
    def ck3_get_capabilities() -> dict[str, object]:
        """List the current bridge backend and gameplay steps it implements."""
        return service.capabilities()

    @server.tool()
    def ck3_get_bridge_diagnostics() -> dict[str, object]:
        """Return live transport diagnostics without claiming CK3 game state."""
        diagnostics = getattr(driver, "diagnostics", None)
        if callable(diagnostics):
            return diagnostics()
        capabilities = service.capabilities()
        nested = capabilities.get("diagnostics")
        return nested if isinstance(nested, dict) else {
            "backend_id": capabilities.get("backend_id"),
            "connected": capabilities.get("connected"),
        }

    @server.tool()
    def ck3_take_snapshot() -> dict[str, object]:
        """Return the latest backend-neutral CK3 session snapshot."""
        return service.snapshot()

    @server.tool()
    def ck3_get_one_life_settlement() -> dict[str, object]:
        """Inspect the current death settlement and its episode binding."""
        return service.one_life_settlement()

    @server.tool()
    def ck3_settle_one_life(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Finish this life only after its score and new record are durable."""
        return service.settle_one_life(expected_revision=expected_revision)

    @server.tool()
    def ck3_plan_turn() -> dict[str, object]:
        """Choose the next one-life gameplay step from the shared planner."""
        return service.plan_turn()

    @server.tool()
    def ck3_auto_turn() -> dict[str, object]:
        """Plan and execute exactly one supported one-life gameplay turn."""
        return service.auto_turn()

    @server.tool()
    def ck3_execute_step(
        step: str, expected_revision: int | None = None
    ) -> dict[str, object]:
        """Execute one semantic gameplay step through the selected backend."""
        return service.execute_step(step, expected_revision=expected_revision)

    @server.tool()
    def ck3_save_checkpoint(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Create and materialize the fixed isolated CK3 checkpoint save."""
        return service.save_checkpoint(expected_revision=expected_revision)

    @server.tool()
    def ck3_restore_checkpoint(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Restart the pure-native CK3 session and continue its checkpoint."""
        return service.restore_checkpoint(expected_revision=expected_revision)

    @server.tool()
    def ck3_start_next_episode(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Start a new one-life run from the immutable native seed save."""
        return service.start_next_episode(expected_revision=expected_revision)

    @server.tool()
    def ck3_reply_pending_character_interaction(
        accept: bool,
        interaction_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Accept or reject the current native character interaction."""
        return service.reply_pending_character_interaction(
            accept=accept,
            interaction_instance_id=interaction_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_acknowledge_pending_character_interaction(
        interaction_instance_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Acknowledge one exact native auto-accept interaction notification."""
        return service.acknowledge_pending_character_interaction(
            interaction_instance_id=interaction_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_get_war_state() -> dict[str, object]:
        """Return active native wars and the player's currently raised armies."""
        return service.war_state()

    @server.tool()
    def ck3_query_arrange_marriage_choices(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Enumerate native marriage choices for the current player character."""
        return service.query_arrange_marriage_choices(
            expected_revision=expected_revision
        )

    @server.tool()
    def ck3_arrange_marriage(
        choice_id: str,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit one exact choice from ck3_query_arrange_marriage_choices."""
        return service.arrange_marriage(
            choice_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_declarable_wars(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Enumerate CK3's currently valid native war declarations."""
        return service.query_declarable_wars(
            expected_revision=expected_revision
        )

    @server.tool()
    def ck3_declare_war(
        declaration_id: str,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Declare one exact choice returned by ck3_query_declarable_wars."""
        return service.declare_war(
            declaration_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_raise_troops_default(
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Raise troops at CK3's native default rally point."""
        return service.raise_troops_default(
            expected_revision=expected_revision
        )

    @server.tool()
    def ck3_move_army(
        army_id: int,
        target_province_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Move one native player army to an exact CK3 province."""
        return service.move_army(
            army_id,
            target_province_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_start_assault(
        siege_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Start Assault for one exact full-generation native SiegeID."""
        return service.start_assault(
            siege_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_stop_assault(
        siege_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Stop Assault for one exact full-generation native SiegeID."""
        return service.stop_assault(
            siege_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_disband_army(
        army_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Disband one exact native player army."""
        return service.disband_army(
            army_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_enforce_demands(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Enforce demands in an exact native war that reached 100%."""
        return service.enforce_demands(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_army_strengths(
        army_ids: list[int],
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read soldiers and AI base power; never interpret them as win odds."""
        return service.query_army_strengths(
            army_ids,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_actual_contact_scope(
        subject_army_id: int,
        target_province_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Predict contact or read actual CombatID/sides; pass order to v3."""
        return _ck3_query_actual_contact_scope(
            service,
            subject_army_id,
            target_province_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_battle_control_snapshot_v1(
        subject_army_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read one full public CUnitID's battle and retreat gates while paused."""
        return _ck3_query_battle_control_snapshot_v1(
            service,
            subject_army_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_battle_transition_v1(
        combat_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read phase, winner and ordered sides for one full CombatID."""
        return _ck3_query_battle_transition_v1(
            service,
            combat_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_battle_terminal_transition_v1(
        prior_combat_id: int,
        subject_public_cunit_id: int,
        expected_revision: int,
        after_terminal_sequence: int | None = None,
    ) -> dict[str, object]:
        """Read terminal history, removal, subject and successor while paused."""
        return _ck3_query_battle_terminal_transition_v1(
            service,
            prior_combat_id,
            subject_public_cunit_id,
            expected_revision,
            after_terminal_sequence,
        )

    @server.tool()
    def ck3_query_battle_reinforcement_assignment_v1(
        selected_public_cunit_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read native help flags, target, exact route/ETA and contact candidates."""
        return _ck3_query_battle_reinforcement_assignment_v1(
            service,
            selected_public_cunit_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_campaign_root_context_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read player, title, capital, lieges, government and rule tokens."""
        return _ck3_query_campaign_root_context_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_query_loaded_feature_manifest_v1(
        expected_revision: int,
    ) -> dict[str, object]:
        """Read effective build flags and script DLC keys; ownership stays unknown."""
        return _ck3_query_loaded_feature_manifest_v1(
            service,
            expected_revision,
        )

    @server.tool()
    def ck3_query_pending_character_interaction_context_v1(
        pending_interaction_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read routing, paid costs, exact special-war binding, and legality."""
        return _ck3_query_pending_character_interaction_context_v1(
            service,
            pending_interaction_id,
            expected_revision,
        )

    @server.tool()
    def ck3_query_current_event_window_context_v1(
        event_instance_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Read shown options and typed indicators; full preview stays unavailable."""
        return _ck3_query_current_event_window_context_v1(
            service,
            event_instance_id,
            expected_revision,
        )

    @server.tool()
    def ck3_preview_active_combat_retreat_v1(
        selected_public_cunit_id: int,
        target_province_id: int,
        expected_revision: int,
    ) -> dict[str, object]:
        """Preview one legal active-combat withdrawal and return a short token."""
        return _ck3_preview_active_combat_retreat_v1(
            service,
            selected_public_cunit_id,
            target_province_id,
            expected_revision,
        )

    @server.tool()
    def ck3_order_active_combat_retreat_v1(
        selected_public_cunit_id: int,
        expected_revision: int,
        expected_combat_id: int,
        expected_side_index: int,
        expected_scope: str,
        target_province_id: int,
        candidate_token: str,
    ) -> dict[str, object]:
        """Consume a fresh retreat token; ACK remains verification-pending."""
        return _ck3_order_active_combat_retreat_v1(
            service,
            selected_public_cunit_id,
            expected_revision,
            expected_combat_id,
            expected_side_index,
            expected_scope,
            target_province_id,
            candidate_token,
        )

    @server.tool()
    def ck3_query_combat_simulation_inputs(
        target_province_id: int,
        attacker_entry_province_id: int,
        attacker_army_ids: list[int],
        defender_army_ids: list[int],
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read one explicit hypothetical contact; does not claim win odds."""
        return service.query_combat_simulation_inputs(
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_combat_simulation_inputs_v3(
        target_province_id: int,
        attacker_entry_province_id: int,
        attacker_army_ids: list[int],
        defender_army_ids: list[int],
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read exact phase inputs; readiness does not imply simulated odds."""
        return _ck3_query_combat_simulation_inputs_v3(
            service,
            target_province_id,
            attacker_entry_province_id,
            attacker_army_ids,
            defender_army_ids,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_war_entry_assessments(
        target_character_ids: list[int],
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read native strategic power for one declarable-war target."""
        return _ck3_query_war_entry_assessments(
            service,
            target_character_ids,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_war_termination_options(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read native surrender/white-peace/victory legality for one WarID."""
        return service.query_war_termination_options(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_query_war_termination_terms(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Read exact claim-CB claimant, targets, claims and dispositions."""
        return service.query_war_termination_terms(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_surrender_war(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Submit surrender only from a same-revision native query result."""
        return service.surrender_war(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_offer_white_peace(
        war_id: int,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Offer white peace only when native support and query prove legality."""
        return service.offer_white_peace(
            war_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_select_event_option(
        option_number: int,
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Select a 1-based option on the current CK3 event."""
        return service.select_event_option(
            option_number,
            event_instance_id=event_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_resolve_active_event(
        event_instance_id: int | None = None,
        expected_revision: int | None = None,
    ) -> dict[str, object]:
        """Choose and select the best enabled option on the current event."""
        return service.resolve_active_event(
            event_instance_id=event_instance_id,
            expected_revision=expected_revision,
        )

    @server.tool()
    def ck3_wait_for_change(
        after_revision: int, timeout_seconds: float = 10.0
    ) -> dict[str, object]:
        """Wait until CK3 publishes a newer semantic snapshot or timeout."""
        return service.wait_for_change(
            after_revision, timeout_seconds=timeout_seconds
        )

    @server.resource("ck3://capabilities")
    def ck3_capabilities_resource() -> dict[str, object]:
        return service.capabilities()

    @server.resource("ck3://state/current")
    def ck3_current_state_resource() -> dict[str, object]:
        return service.snapshot()

    return server


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="xar-ck3-mcp")
    result.add_argument(
        "--driver",
        default=os.environ.get("XAR_CK3_BRIDGE_DRIVER", "vision-report"),
        help=(
            "vision-report, vision-session, mod, hybrid, native-headless, "
            "hybrid-fallback, or a module:factory returning GameplayBridgeDriver"
        ),
    )
    result.add_argument(
        "--state-dir",
        default=os.environ.get("XAR_AUTOPLAYER_STATE_DIR"),
        help=(
            "XarAutoplayer state root; native checkpoints materialize under "
            "<state-dir>/profile/save games"
        ),
    )
    result.add_argument(
        "--userdir",
        default=os.environ.get("XAR_CK3_USERDIR"),
        help="active CK3 user directory used by --driver mod",
    )
    result.add_argument(
        "--pipe-name",
        default=os.environ.get("XAR_CK3_BRIDGE_PIPE"),
        help=(
            r"native bridge pipe (default: \\.\pipe\xar_ck3_bridge_mcp); "
            "also accepted through XAR_CK3_BRIDGE_PIPE"
        ),
    )
    result.add_argument(
        "--transport", choices=("stdio", "streamable-http"), default="stdio"
    )
    result.add_argument("--host", default="127.0.0.1")
    result.add_argument("--port", type=int, default=8765)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    driver = load_driver(
        args.driver,
        userdir=args.userdir,
        state_dir=args.state_dir,
        pipe_name=args.pipe_name,
    )
    server = create_server(driver)
    try:
        if args.transport == "stdio":
            server.run(transport="stdio")
        else:
            server.run(
                transport="streamable-http",
                host=args.host,
                port=args.port,
                stateless_http=True,
                json_response=True,
            )
    finally:
        close = getattr(driver, "close", None)
        if callable(close):
            close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

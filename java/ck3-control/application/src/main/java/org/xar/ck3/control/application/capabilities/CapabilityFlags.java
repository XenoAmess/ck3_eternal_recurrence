package org.xar.ck3.control.application.capabilities;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.function.Predicate;
import org.xar.ck3.control.application.action.ExecutableStepBindings;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** The public capability fields are one typed contract, separate from descriptive hello metadata. */
public enum CapabilityFlags {
    ONE_LIFE_SETTLEMENT_SUPPORTED("one_life_settlement_supported","game.state.xar-one-life-settlement"),
    ARMY_ROUTES_SUPPORTED("army_routes_supported","game.state.army-routes"),
    MOVE_ROUTE_PREVIEW_SUPPORTED("move_route_preview_supported","game.command.preview-move-army-N-to-N"),
    ROUTE_CONTACT_HORIZON_SUPPORTED("route_contact_horizon_supported","game.command.query-route-contact-horizon-v1-N"),
    ACTUAL_CONTACT_SCOPE_QUERY_SUPPORTED("actual_contact_scope_query_supported","game.command.query-actual-contact-scope-v1-N"),
    PROJECTED_CONTACT_SCOPE_V1_QUERY_SUPPORTED("projected_contact_scope_v1_query_supported","game.command.query-projected-contact-scope-v1-N"),
    BATTLE_CONTROL_SNAPSHOT_V1_QUERY_SUPPORTED("battle_control_snapshot_v1_query_supported","game.command.query-battle-control-snapshot-v1-N"),
    BATTLE_TRANSITION_V1_QUERY_SUPPORTED("battle_transition_v1_query_supported","game.command.query-battle-transition-v1-N"),
    BATTLE_TERMINAL_TRANSITION_V1_QUERY_SUPPORTED("battle_terminal_transition_v1_query_supported","game.command.query-battle-terminal-transition-v1"),
    BATTLE_REINFORCEMENT_ASSIGNMENT_V1_QUERY_SUPPORTED("battle_reinforcement_assignment_v1_query_supported","game.command.query-battle-reinforcement-assignment-v1-N"),
    CAMPAIGN_ROOT_CONTEXT_V1_QUERY_SUPPORTED("campaign_root_context_v1_query_supported","game.command.query-campaign-root-context-v1"),
    COUNCIL_COMPOSITION_CANDIDATES_V1_QUERY_SUPPORTED("council_composition_candidates_v1_query_supported","game.query.council-composition-candidates-v1"),
    STEWARD_DEVELOP_COUNTY_CANDIDATES_V1_QUERY_SUPPORTED("steward_develop_county_candidates_v1_query_supported","game.command.query-steward-develop-county-candidates-v1"),
    PLAYER_FACTION_ALERTS_V1_QUERY_SUPPORTED("player_faction_alerts_v1_query_supported","game.command.query-player-faction-alerts-v1"),
    ZHONGGUO_CASE_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_case_snapshot_v1_query_supported","game.command.query-zhongguo-case-snapshot-v1"),
    ZHONGGUO_B1_CYCLE_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_b1_cycle_snapshot_v1_query_supported","game.command.query-zhongguo-b1-cycle-snapshot-v1"),
    ZHONGGUO_AI_OWNED_CASE_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_ai_owned_case_snapshot_v1_query_supported","game.command.query-zhongguo-ai-owned-case-snapshot-v1"),
    ZHONGGUO_RESULT_CASE_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_result_case_snapshot_v1_query_supported","game.command.query-zhongguo-result-case-snapshot-v1"),
    ZHONGGUO_B2_PIP_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_b2_pip_snapshot_v1_query_supported","game.command.query-zhongguo-b2-pip-snapshot-v1"),
    ZHONGGUO_COMPENSATION_AF5_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_compensation_af5_snapshot_v1_query_supported","game.command.query-zhongguo-compensation-af5-snapshot-v1"),
    ZHONGGUO_WORKFORCE_OWNER_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_workforce_owner_snapshot_v1_query_supported","game.command.query-zhongguo-workforce-owner-snapshot-v1"),
    ZHONGGUO_WORKFORCE_COLLECTIVE_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_workforce_collective_snapshot_v1_query_supported","game.command.query-zhongguo-workforce-collective-snapshot-v1"),
    ZHONGGUO_WORKFORCE_NORMAL_EXIT_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_workforce_normal_exit_snapshot_v1_query_supported","game.command.query-zhongguo-workforce-normal-exit-snapshot-v1"),
    ZHONGGUO_INCIDENT_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_incident_snapshot_v1_query_supported","game.command.query-zhongguo-incident-snapshot-v1"),
    ZHONGGUO_MANAGER_GOVERNANCE_SNAPSHOT_V1_QUERY_SUPPORTED("zhongguo_manager_governance_snapshot_v1_query_supported","game.command.query-zhongguo-manager-governance-snapshot-v1"),
    ZHONGGUO_MANAGER_SUBORDINATE_SELECTOR_V1_QUERY_SUPPORTED("zhongguo_manager_subordinate_selector_v1_query_supported","game.command.query-zhongguo-manager-subordinate-selector-v1"),
    ZHONGGUO_SCOREBOARD_STATE_V1_QUERY_SUPPORTED("zhongguo_scoreboard_state_v1_query_supported","game.command.query-zhongguo-scoreboard-state-v1"),
    ZHONGGUO_PROMOTION_COMPENSATION_V1_QUERY_SUPPORTED("zhongguo_promotion_compensation_v1_query_supported","game.command.query-zhongguo-promotion-compensation-postcondition-v1"),
    ZHONGGUO_PROJECTS_METRICS_V1_QUERY_SUPPORTED("zhongguo_projects_metrics_v1_query_supported","game.command.query-zhongguo-projects-metrics-postcondition-v1"),
    ZHONGGUO_CAREER_HC_WORKFORCE_V1_QUERY_SUPPORTED("zhongguo_career_hc_workforce_v1_query_supported","game.command.query-zhongguo-career-hc-workforce-postcondition-v1"),
    ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_WIRED("zhongguo_scoreboard_action_v1_transport_wired","game.contract.zhongguo-scoreboard-action-v1-fail-closed"),
    ZHONGGUO_SCOREBOARD_ACTION_V1_SUPPORTED("zhongguo_scoreboard_action_v1_supported","game.command.activate-zhongguo-scoreboard-v1"),
    LOADED_FEATURE_MANIFEST_V1_QUERY_SUPPORTED("loaded_feature_manifest_v1_query_supported","game.command.query-loaded-feature-manifest-v1"),
    PENDING_CHARACTER_INTERACTION_CONTEXT_V1_QUERY_SUPPORTED("pending_character_interaction_context_v1_query_supported","game.command.query-pending-character-interaction-context-v1"),
    CURRENT_EVENT_WINDOW_CONTEXT_V1_QUERY_SUPPORTED("current_event_window_context_v1_query_supported","game.command.query-current-event-window-context-v1"),
    ARMY_STRENGTH_QUERY_SUPPORTED("army_strength_query_supported","game.command.query-army-strengths-v1"),
    COMBAT_SIMULATION_INPUTS_QUERY_SUPPORTED("combat_simulation_inputs_query_supported","game.command.query-combat-simulation-inputs-v2-N"),
    COMBAT_SIMULATION_INPUTS_V3_QUERY_SUPPORTED("combat_simulation_inputs_v3_query_supported","game.command.query-combat-simulation-inputs-v3-N"),
    COMBAT_PHASE_EVENT_TRACE_V1_QUERY_SUPPORTED("combat_phase_event_trace_v1_query_supported","game.command.query-combat-phase-event-trace-v1-N"),
    WAR_ENTRY_ASSESSMENTS_QUERY_SUPPORTED("war_entry_assessments_query_supported","game.command.query-war-entry-assessments-v1-N"),
    WAR_TERMINATION_QUERY_SUPPORTED("war_termination_query_supported","game.command.query-war-termination-options-N"),
    WAR_PRISONER_RELEASE_PAIRS_V1_QUERY_SUPPORTED("war_prisoner_release_pairs_v1_query_supported","game.command.query-war-prisoner-release-pairs-v1-N"),
    OUTBOUND_WAR_WHITE_PEACE_STATUS_QUERY_SUPPORTED("outbound_war_white_peace_status_query_supported","game.command.query-outbound-war-white-peace-status-v1-N"),
    WAR_TERMINATION_TERMS_QUERY_SUPPORTED("war_termination_terms_query_supported","game.command.query-war-termination-terms-v1-N"),
    WAR_TERMINATION_EXIT_TERMS_QUERY_SUPPORTED("war_termination_exit_terms_query_supported","game.command.query-war-termination-exit-terms-v2-N"),
    SURRENDER_WAR_SUPPORTED("surrender_war_supported","game.command.surrender-war-N"),
    OFFER_WHITE_PEACE_SUPPORTED("offer_white_peace_supported","game.command.offer-white-peace-N"),
    WAR_OBJECTIVE_OCCUPATION_SUPPORTED("war_objective_occupation_supported","game.state.war-objective-occupation"),
    WAR_OBJECTIVE_FORT_LEVEL_SUPPORTED("war_objective_fort_level_supported","game.state.war-objective-fort-level"),
    WAR_OBJECTIVE_GARRISON_SUPPORTED("war_objective_garrison_supported","game.state.war-objective-garrison"),
    WAR_OBJECTIVE_SIEGE_PROGRESS_SUPPORTED("war_objective_siege_progress_supported","game.state.war-objective-siege-progress"),
    WAR_OBJECTIVE_ASSAULT_SUPPORTED("war_objective_assault_supported","game.state.war-objective-assault");

    private final String field;
    private final String capability;
    CapabilityFlags(String field,String capability) { this.field=field;this.capability=capability; }
    public String field() { return field; }
    public String capability() { return capability; }
    public static OpportunityJson.Obj project(Set<String> actualCapabilities,ExecutableStepBindings installed,boolean snapshot) {
        Objects.requireNonNull(installed);
        return project(actualCapabilities,capability -> installed.frozen() && installed.supportsCapability(capability),snapshot);
    }
    static OpportunityJson.Obj project(Set<String> actualCapabilities,Predicate<String> actualBinding,boolean snapshot) {
        Objects.requireNonNull(actualCapabilities);Objects.requireNonNull(actualBinding);
        Map<String,OpportunityJson.Value> flags=new LinkedHashMap<>();
        for(CapabilityFlags flag:values()) {
            boolean supported=actualCapabilities.contains(flag.capability) && (flag.capability.startsWith("game.state.")
                    ? snapshot : actualBinding.test(flag.capability));
            // This production route remains disabled in the source producer. A protocol declaration cannot enable it.
            if(flag==WAR_TERMINATION_EXIT_TERMS_QUERY_SUPPORTED) supported=false;
            if(flag==ZHONGGUO_SCOREBOARD_ACTION_V1_TRANSPORT_WIRED) supported=actualCapabilities.contains(flag.capability)
                    && actualCapabilities.contains(ZHONGGUO_SCOREBOARD_ACTION_V1_SUPPORTED.capability)
                    && actualBinding.test(ZHONGGUO_SCOREBOARD_ACTION_V1_SUPPORTED.capability);
            flags.put(flag.field,new OpportunityJson.Bool(supported));
        }
        return new OpportunityJson.Obj(flags);
    }
}


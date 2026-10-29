package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The actual ordinary-core battle prelude caller, including cleanup after the last War disappears. */
public final class BattleControlPrelude {
    private BattleControlPrelude() { }
    public static WarCorePlanner.Leaf factory(ExactRef implementationSource) {
        return new WarCorePlanner.Leaf(WarCorePlanner.Boundary.BATTLE_CONTROL_PRELUDE,implementationSource,BattleControlPrelude::evaluate);
    }
    public static MilitaryPlanningDecision evaluate(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        Obj state=BattleControlTurnState.collect(request);String status=optionalText(state.get("status"));
        if(status==null)return new MilitaryPlanningDecision.Unavailable(List.of("battle_control_turn_state.status"),"actual battle collector omitted its terminal status");
        return switch(status) {
            case "not_in_combat","ready" -> new MilitaryPlanningDecision.Keep(obj(f("battle_control_state",state)));
            case "transition_recognized" -> transition(request,state);
            case "wait_for_pause" -> choose(request,"native_war_battle_wait_for_pause","pause-map","pause-map",
                    "pause the map before reading any active subject's exact battle-control frame",f("battle_subject_army_ids",nullable(state.get("subject_army_ids"))));
            case "reader_unavailable_hands_off" -> {
                boolean ready=request.observations().bridgeCapabilities().containsAll(CLOCK_CAPABILITIES)
                        &&List.of("life-advance-one-day","set-speed-1","resume-map","pause-map").stream().allMatch(step->advertised(request,step));
                yield select(request,"native_war_battle_reader_unavailable_one_day_observation",ready?"life-advance-one-day":null,null,
                        "the native battle read is incomplete; observe the ongoing battle for one exact native-stopped day without a prediction or retreat command",
                        f("battle_reader_watch",state),f("battle_subject_army_id",nullable(state.get("subject_army_id"))),f("battle_outcome_inferred",new Bool(false)),
                        f("prediction_ready",new Bool(false)),f("retreat_authorized",new Bool(false)));
            }
            case "identity_pending" -> advertised(request,"life-advance")?
                    select(request,"native_war_battle_identity_materialization","life-advance",null,
                            "the frozen paused public subject is in combat, but CK3 has not materialized its CombatID; advance exactly one day once, then require a non-missing full CombatID on the next revision",
                            f("battle_subject_army_id",nullable(state.get("subject_army_id"))),f("battle_identity_pending",nullable(state.get("identity_pending"))),f("next_revision_requirement",text("full_combat_id"))):
                    select(request,"native_war_battle_identity_materialization_unsupported",null,"life-advance",
                            "the frozen CombatID materialization boundary requires one explicit bounded day, but this backend cannot advance it",f("battle_subject_army_id",nullable(state.get("subject_army_id"))));
            case "identity_pending_after_materialization" -> select(request,"native_war_battle_identity_materialization_failed",null,null,
                    "the single explicit one-day materialization was consumed, but the next frozen revision still lacks a non-missing CombatID; do not advance again",
                    f("required_observation",text("full-current-revision-CombatID")),f("battle_subject_army_id",nullable(state.get("subject_army_id"))),
                    f("battle_identity_pending",nullable(state.get("identity_pending"))),f("battle_identity_materialization",nullable(state.get("prior_materialization"))));
            case "query_required" -> {
                String step=optionalText(state.get("step"));boolean supported=step!=null&&advertised(request,step);
                yield select(request,supported?"native_war_battle_control_query":"native_war_battle_control_query_unsupported",supported?step:null,supported?null:step,
                        supported?"read an available exact battle-control frame bound to the current paused revision before any combat time slice":
                                "the active combat cannot advance without a current-revision available battle-control frame",f("battle_subject_army_id",nullable(state.get("subject_army_id"))));
            }
            case "invalid_subject" -> select(request,"native_war_battle_control_query_unsupported",null,null,
                    "the active controllable combat subject lacks a queryable canonical public CUnitID",f("required_capability",text("game.command.query-battle-control-snapshot-v1-N")),
                    f("battle_subject_army_id",nullable(state.get("subject_army_id"))));
            case "terminal_query_required" -> {
                String step=optionalText(state.get("step"));boolean supported=step!=null&&request.observations().bridgeCapabilities().contains(TERMINAL_CAPABILITY);
                yield supported?select(request,"native_war_battle_terminal_journal_query",step,null,
                        "read the cursor-bound terminal journal after the native terminal stop before accepting the CombatID outcome",f("battle_subject_army_id",nullable(state.get("subject_army_id"))),
                        f("battle_combat_id",nullable(state.get("combat_id"))),f("after_terminal_sequence",nullable(state.get("after_terminal_sequence")))):
                        select(request,"native_war_battle_terminal_journal_query_unsupported",null,step,
                                "the terminal cruise stopped, but its cursor-bound CombatID outcome cannot be queried",f("required_capability",text(TERMINAL_CAPABILITY)));
            }
            case "transition_invalid" -> select(request,"native_war_battle_transition_invalid",null,"fresh-paused-battle-control-frame",
                    "the post-advance exact frame did not prove a legal same-CombatID phase/day or casualty-ledger transition",
                    f("battle_transition",nullable(state.get("transition"))),f("battle_control_frame",nullable(state.get("frame"))));
            case "terminal_observed" -> {
                Obj fallback=obj(f("status",text("terminal_observed")),f("subject_army_id",nullable(state.get("subject_army_id"))),f("outcome",Nil.INSTANCE));
                Obj transition=state.get("transition") instanceof Obj actual?actual:fallback;
                yield advertised(request,"life-advance")?select(request,"native_war_battle_terminal_cleanup","life-advance",null,
                        "the exact frame explicitly reached finalized/done while the semantic subject remains in combat; advance at most one day so CK3 can remove the completed combat, then observe the subject again",
                        f("battle_transition",transition),f("battle_transitions",objects(List.of(transition))),f("battle_control_frame",nullable(state.get("frame")))):
                        select(request,"native_war_battle_terminal_cleanup_unsupported",null,"life-advance",
                                "the exact frame explicitly reached finalized/done while the semantic subject remains in combat, but the backend cannot perform the bounded cleanup slice",
                                f("battle_transition",fallback),f("battle_control_frame",nullable(state.get("frame"))));
            }
            default -> new MilitaryPlanningDecision.Unavailable(List.of("battle_control_turn_state:"+status),"actual battle collector returned an unsupported state; do not advance or infer an outcome");
        };
    }
    private static MilitaryPlanningDecision transition(PlanningRequest request,Obj state) {
        if(!(state.get("remaining_rows") instanceof Arr remaining)||remaining.items().size()>=request.observations().history().size())
            return select(request,"native_war_battle_transition_invalid",null,"fresh-paused-battle-control-frame",
                    "the recognized battle transition could not be separated from its pre-advance evidence epoch",f("battle_transitions",nullable(state.get("transitions"))));
        List<Obj> rows=remaining.items().stream().map(value->{require(value instanceof Obj,"actual remaining history row required");return (Obj)value;}).toList();
        return new MilitaryPlanningDecision.Replan(request.withHistory(rows),obj(f("battle_transitions",nullable(state.get("transitions")))));
    }
    private static MilitaryPlanningDecision choose(PlanningRequest request,String phase,String candidate,String required,String reason,Field... fields) {
        return select(request,phase,advertised(request,candidate)?candidate:null,required,reason,fields);
    }
    private static MilitaryPlanningDecision select(PlanningRequest request,String phase,String step,String required,String reason,Field... fields) {
        Obj detail=merge(obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",step==null?Nil.INSTANCE:text(step)),f("reason",text(reason))),obj(fields));
        if(required!=null)detail=put(detail,"required_step",text(required));
        if(step==null)return new MilitaryPlanningDecision.Hold("one-life-turn-v1",phase,reason,Optional.ofNullable(required).map(OperationKey::new),detail);
        // Terminal journal recipes are bound through capability/ReadCatalog, and need not be separately enumerated actionSteps.
        OrdinaryPolicy.Purpose purpose=step.startsWith("query-")?OrdinaryPolicy.Purpose.READ_ONLY:step.startsWith("life-advance")?OrdinaryPolicy.Purpose.DATE_ADVANCE:OrdinaryPolicy.Purpose.WORLD_ACTION;
        return new MilitaryPlanningDecision.Select("one-life-turn-v1",phase,reason,new OperationKey(step),empty(),purpose,detail);
    }
    private static final String TERMINAL_CAPABILITY="game.command.query-battle-terminal-transition-v1";
    private static final Set<String> CLOCK_CAPABILITIES=Set.of("game.command.research-arm-tactical-daily-sentinel-v1-N","game.command.research-query-tactical-daily-sentinel-v1","game.command.research-cancel-tactical-daily-sentinel-v1-generation-N");
}

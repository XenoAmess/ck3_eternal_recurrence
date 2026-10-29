package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.EarlyWarCoreLeaves.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import java.util.TreeMap;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.war.SplitMergeRecovery;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Actual strategy10832..11210 producers. Native submission remains the sole action path. */
public final class WarBattleControlCore {
    private static final int FALLBACK_DAYS=45,MAX_WATCH=64;
    private static final Set<String> CLOCK=Set.of("game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1","game.command.research-cancel-tactical-daily-sentinel-v1-generation-N");
    private static final String TERMINAL_QUERY="game.command.query-battle-terminal-transition-v1";
    private WarBattleControlCore() { }
    public static List<WarCorePlanner.Leaf> factories(ExactRef source,EarlyWarCoreInputs.Collector collector) {
        Objects.requireNonNull(source);Objects.requireNonNull(collector);
        return List.of(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.COMBAT_AND_RETREAT_PROGRESS,source,
                (request,current)->progress(request,current,collector)),
                new WarCorePlanner.Leaf(WarCorePlanner.Boundary.MERGE_RENDEZVOUS_BOUNDARY,source,
                        (request,current)->rendezvous(request,current,collector)));
    }
    public static MilitaryPlanningDecision progress(PlanningRequest request,OrdinaryPolicy.Draft current,EarlyWarCoreInputs.Collector collector) {
        var captured=collector.capture(request,current);
        if(captured instanceof EarlyWarCoreInputs.Unavailable missing)return new MilitaryPlanningDecision.Unavailable(missing.missing(),"actual battle progress inputs unavailable");
        var actual=((EarlyWarCoreInputs.Available)captured).state();actual.requireSame(request);
        try {
            if(!actual.unsafeArmyIds().isEmpty()||!actual.threatenedStationaryArmyIds().isEmpty())return new MilitaryPlanningDecision.Keep(empty());
            List<Army> combat=actual.controlled().stream().filter(a->"combat".equals(a.tacticalState())).toList();
            if(!combat.isEmpty())return combat(request,actual,combat);
            List<Army> retreat=actual.controlled().stream().filter(a->"retreating".equals(a.tacticalState())).toList();
            if(retreat.isEmpty())return new MilitaryPlanningDecision.Keep(empty());
            Optional<Obj> forced=existingNativeRetreat(request,actual.controlled());
            Obj detail=obj(f("combat_retreat_armies",tactical(forced.isPresent()?actual.controlled():retreat)));
            if(forced.isPresent()) {
                detail=merge(detail,obj(f("native_forced_retreat_observation_v1",forced.orElseThrow()),f("active_attack_allowed",new Bool(false))));
                boolean available=has(request,"life-advance-one-day")&&request.observations().bridgeCapabilities().containsAll(CLOCK);
                return available?select(request,"native_war_global_combat_retreat_progress","life-advance-one-day",
                        "observe the already active Native retreat for at most one native-stopped day and replan from the independent paused frame",detail,actual.warSummaries(),OrdinaryPolicy.Purpose.DATE_ADVANCE)
                        :hold("native_war_global_combat_retreat_progress_unsupported","life-advance-one-day","the existing retreat needs the native daily clock capability set",detail,actual.warSummaries());
            }
            return select(request,"native_war_global_combat_retreat_progress","life-advance",
                    "a controllable army is retreating; every other route and stationary position passed the global audit; observe one bounded day",detail,actual.warSummaries(),OrdinaryPolicy.Purpose.DATE_ADVANCE);
        }catch(IllegalArgumentException|ArithmeticException invalid){return unavailable(invalid);}
    }
    private static MilitaryPlanningDecision combat(PlanningRequest request,EarlyWarCoreInputs.Actual actual,List<Army> combat) {
        Obj state=actual.battleControl();require(new Text("ready").equals(state.get("status")),"actual current battle-control frames must pass the earlier shared prelude");
        List<Integer> watch=actual.controlled().stream().map(Army::id).sorted().toList();boolean watchReady=!watch.isEmpty()&&watch.size()<=MAX_WATCH&&watch.stream().distinct().count()==watch.size();
        BigInteger start=request.before().frame().identity().dateRaw(),fallback=start.add(BigInteger.valueOf(FALLBACK_DAYS*24L)),decisionTarget=fallback;
        Map<Integer,Obj> distinct=new TreeMap<>();
        for(Obj frame:rows(state.get("full_frames"))) {
            Integer combatId=optionalInt(frame.get("combat_id")),subject=optionalInt(frame.get("subject_public_cunit_id"));
            require(combatId!=null&&combatId!=-1&&subject!=null&&subject>=0,"normalized battle identities required");
            Obj previous=distinct.get(combatId);if(previous==null||subject<id(previous.get("subject_public_cunit_id")))distinct.put(combatId,frame);
            if(frame.get("legality") instanceof Obj legal) {
                BigInteger gate=optionalInteger(legal.get("earliest_day_gate_date_raw"));
                if(Objects.equals(frame.get("observed_date_raw"),number(start))&&new Text("available").equals(legal.get("status"))&&no(legal.get("legal_now"))
                        &&strings(List.of("too_early")).equals(legal.get("reason_codes_in_native_order"))&&gate!=null&&gate.compareTo(start)>0&&gate.compareTo(fallback)<=0
                        &&gate.subtract(start).mod(BigInteger.valueOf(24)).signum()==0&&gate.compareTo(decisionTarget)<0)decisionTarget=gate;
            }
        }
        require(!distinct.isEmpty(),"combat progress requires every distinct active CombatID");
        Optional<Obj> comparison=new ActiveCombatObservedComparison().observe(request)
                .filter(value->distinct.size()==1&&distinct.containsKey(int32(value.get("combat_id"))));
        boolean severe=comparison.filter(value->yes(value.get("severe_observed_disadvantage"))||yes(value.get("severe_conditional_damage_basis_disadvantage"))).isPresent();
        Obj readiness=request.observations().battleSpeedReadiness().orElse(empty());List<Obj> assessments=new ArrayList<>();boolean all=true;
        for(Obj frame:distinct.values()) {
            var assessment=BattleTerminalCruisePolicy.assess(frame,new BattleTerminalCruisePolicy.Context(request.observations().paused(),request.observations().mapReady(),
                    request.observations().snapshot().get("active_event")!=Nil.INSTANCE,request.observations().snapshot().get("pending_character_interaction")!=Nil.INSTANCE,
                    watch,watch,Optional.of(fallback),has(request,"battle-terminal-cruise"),watchReady&&has(request,"battle-terminal-cruise"),
                    yes(readiness.get("terminal_sentinel_live_ready")),yes(readiness.get("overwhelming_matrix_live_ready")),4));
            assessments.add(assessment.document());all&=assessment.productionReady();
        }
        List<Obj> cursors=new ArrayList<>();
        if(all)for(var entry:distinct.entrySet()) {
            int subject=id(entry.getValue().get("subject_public_cunit_id"));var cursor=BattleControlTurnState.terminalCursor(request,entry.getKey(),subject);
            if(cursor.currentCursor().isPresent()){cursors.add(cursor.currentCursor().orElseThrow());continue;}
            if(!cursor.currentQueryAttempted()&&request.observations().bridgeCapabilities().contains(TERMINAL_QUERY)) {
                String step=new BattleControlTurnState.TerminalRequest(entry.getKey(),subject,Optional.empty(),List.of()).step();
                return selectDynamic("native_war_battle_terminal_cursor_query",step,"freeze a gap-free native terminal journal cursor for every qualifying CombatID before the cruise",
                        obj(f("battle_combat_id",number(entry.getKey())),f("battle_subject_army_id",number(subject)),f("watch_army_ids",numbers(watch)),f("battle_terminal_cruise_assessments",objects(assessments))),actual.warSummaries(),OrdinaryPolicy.Purpose.READ_ONLY);
            }
            all=false;break;
        }
        Obj detail=obj(f("combat_retreat_armies",tactical(combat)),f("battle_control_frames",nullable(state.get("evidence"))),f("battle_transitions",nullable(state.get("transitions"))));
        if(all&&cursors.size()==distinct.size())return select(request,"native_war_global_battle_terminal_cruise","battle-terminal-cruise",
                "every distinct CombatID passed terminal-cruise production qualification and has its exact pre-arm native cursor",
                merge(detail,obj(f("timeline_policy",text("battle_terminal_cruise_speed_5")),f("timeline_speed",number(5)),f("sentinel_mode",text("terminal_or_sentinel")),
                        f("absolute_target_date_raw",number(fallback)),f("watch_army_ids",numbers(watch)),f("terminal_journal_cursors",objects(cursors)),f("battle_terminal_cruise_assessments",objects(assessments)))),actual.warSummaries(),OrdinaryPolicy.Purpose.DATE_ADVANCE);
        if(yes(readiness.get("decision_sentinel_live_ready"))&&!severe&&actual.activeAssaults().isEmpty()&&watchReady&&has(request,"battle-decision-epoch-advance")) {
            require(decisionTarget.signum()>0&&decisionTarget.bitLength()<=63,"positive native int64 decision target required");
            String step="battle-decision-epoch-advance-to-"+decisionTarget;
            return selectDynamic("native_war_global_battle_decision_epoch",step,"run the qualified speed-three decision sentinel until current tactical operands or its absolute bound change",
                    merge(detail,obj(f("timeline_policy",text("battle_decision_epoch_speed_3")),f("timeline_speed",number(3)),f("sentinel_mode",text("decision_epoch")),f("absolute_target_date_raw",number(decisionTarget)),f("watch_army_ids",numbers(watch)))),actual.warSummaries(),OrdinaryPolicy.Purpose.DATE_ADVANCE);
        }
        detail=merge(detail,obj(f("provisional_combat_comparison",comparison.<Value>map(value->value).orElse(Nil.INSTANCE)),f("provisional_combat_comparison_used_for_decision",new Bool(severe))));
        return select(request,"native_war_global_battle_control_progress","life-advance","observe at most one day after the complete global tactical audit and re-query every continuing combat",detail,actual.warSummaries(),OrdinaryPolicy.Purpose.DATE_ADVANCE);
    }
    private static MilitaryPlanningDecision selectDynamic(String phase,String step,String reason,Obj detail,List<Obj> summaries,OrdinaryPolicy.Purpose purpose) {
        // Dynamic issue still passes the sole concrete CommandFactory; the base capability was checked above.
        Obj full=merge(detail,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",text(step)),f("reason",text(reason)),f("active_wars",objects(summaries))));
        return new MilitaryPlanningDecision.Select("one-life-turn-v1",phase,reason,new org.xar.ck3.control.application.action.OperationKey(step),empty(),purpose,full);
    }
    public static MilitaryPlanningDecision rendezvous(PlanningRequest request,OrdinaryPolicy.Draft current,EarlyWarCoreInputs.Collector collector) {
        var captured=collector.capture(request,current);if(captured instanceof EarlyWarCoreInputs.Unavailable missing)return new MilitaryPlanningDecision.Unavailable(missing.missing(),"actual merge boundary inputs unavailable");
        var actual=((EarlyWarCoreInputs.Available)captured).state();actual.requireSame(request);
        var recovery=SplitMergeRecovery.collect(request);if(recovery.split().isEmpty())return new MilitaryPlanningDecision.Keep(empty());
        var split=recovery.split().orElseThrow();
        if(split.status()==SplitMergeRecovery.SplitStatus.MERGE_REQUIRES_RENDEZVOUS||split.status()==SplitMergeRecovery.SplitStatus.MERGE_WAITING_FOR_IDLE
                &&actual.unsafeArmyIds().isEmpty()&&actual.threatenedStationaryArmyIds().isEmpty())return hold("native_war_merge_rendezvous_blocked","safe-exact-rendezvous",
                "the exact split pair is separated or not merge-idle; no proven safe rendezvous intent is available",obj(f("merge_recovery",split.detail())),actual.warSummaries());
        return new MilitaryPlanningDecision.Keep(empty());
    }
    static Optional<Obj> existingNativeRetreat(PlanningRequest request,List<Army> controlled) {
        Obj snapshot=request.observations().snapshot();if(controlled.isEmpty()||!new Text("native-headless").equals(snapshot.get("backend_id"))
                ||!new Text("injected-dll-named-pipe").equals(snapshot.get("source"))||!request.observations().paused()||!request.observations().mapReady()
                ||!yes(org.xar.ck3.control.planning.opportunity.OpportunityJson.object(snapshot.get("played_character"),"actor").get("alive"))
                ||request.before().frame().identity().nativeRevision().signum()<=0||request.before().frame().revision().signum()<=0
                ||!request.before().frame().snapshotId().equals("native:"+request.before().frame().identity().nativeRevision())
                ||snapshot.get("active_event")!=Nil.INSTANCE||snapshot.get("pending_character_interaction")!=Nil.INSTANCE
                ||snapshot.get("top_exclusive_modal_choice_hint") instanceof Obj hint&&new Text("present").equals(hint.get("status")))return Optional.empty();
        for(Army army:controlled)if(!new Text("native").equals(army.raw().get("source"))||army.owner()==null||!BigInteger.valueOf(army.owner()).equals(request.before().frame().identity().player())
                ||!army.controllable()||!"retreating".equals(army.state())||!Integer.valueOf(6).equals(army.stateCode())||!Boolean.TRUE.equals(army.retreating())||!Boolean.FALSE.equals(army.inCombat())
                ||army.current()==null||army.current()<=0||!yes(army.raw().get("move_target_observable"))||army.target()==null||army.target()<=0
                ||!"complete_nonempty".equals(army.routeReadStatus())||army.route().isEmpty()||army.route().orElseThrow().isEmpty()
                ||!army.route().orElseThrow().getLast().equals(army.target()))return Optional.empty();
        List<Integer> ids=controlled.stream().map(Army::id).sorted().toList();if(ids.stream().distinct().count()!=ids.size())return Optional.empty();
        Set<Integer> published=rows(snapshot.get("player_armies")).stream().filter(row->yes(row.get("controllable"))).map(row->id(row.get("army_id"))).collect(java.util.stream.Collectors.toSet());
        if(!published.equals(Set.copyOf(ids)))return Optional.empty();
        return Optional.of(obj(f("schema",text("xar.ck3.existing-native-forced-retreat/v1")),f("army_ids",numbers(ids)),f("source_snapshot_id",snapshot.get("snapshot_id")),
                f("source_native_revision",snapshot.get("native_revision")),f("source_date_raw",snapshot.get("date_raw")),f("existing_native_retreat_only",new Bool(true)),f("new_retreat_order",new Bool(false)),
                f("contact_free_proven",new Bool(false)),f("attack_authorized",new Bool(false)),f("arrival_or_battle_success_inferred",new Bool(false))));
    }
    private static Arr tactical(List<Army> armies){return objects(armies.stream().map(a->obj(f("army_id",number(a.id())),f("army_state",a.tacticalState()==null?Nil.INSTANCE:text(a.tacticalState())))).toList());}
    private static MilitaryPlanningDecision unavailable(Exception invalid){return new MilitaryPlanningDecision.Unavailable(List.of(Objects.toString(invalid.getMessage(),"actual battle input invalid")),"actual battle progress input unavailable");}
}

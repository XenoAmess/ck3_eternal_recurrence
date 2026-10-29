package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.LateWarCoreInputs.is;
import static org.xar.ck3.control.application.planning.military.LateWarCoreLeaves.*;
import static org.xar.ck3.control.application.planning.military.CapitalRegroupEligibility.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.military.LateWarCoreInputs.Context;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Full four original defensive observation predicates21650..22025. No proof of safety, movement or victory is created. */
public final class LateWarCoreWatches {
    private LateWarCoreWatches() {}
    private static final Set<String> CAPS=Set.of("game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1","game.command.research-cancel-tactical-daily-sentinel-v1-generation-N");
    public static Optional<MilitaryPlanningDecision> afterExhausted(Context c,List<Obj> rejections) {
        Optional<MilitaryPlanningDecision> selected=retainedEmbarked(c,c.published().passiveRouteAudit(),rejections);
        if(selected.isPresent())return selected;
        selected=retainedLand(c,c.published().passiveRouteAudit(),rejections);if(selected.isPresent())return selected;
        selected=excludedSiege(c,rejections);if(selected.isPresent())return selected;
        return stationaryUnavailable(c,rejections);
    }
    private static boolean foregroundAbsent(Context c) {
        Obj snapshot=c.snapshot(),hint=object(snapshot.get("top_exclusive_modal_choice_hint"));
        return none(snapshot.get("active_event"))&&none(snapshot.get("pending_character_interaction"))&&!is(hint,"status","present");
    }
    private static boolean clock(Context c) {
        return c.request().observations().bridgeCapabilities().containsAll(CAPS)
                &&List.of("life-advance-one-day","set-speed-1","resume-map","pause-map").stream().allMatch(step->advertised(c.request(),step));
    }
    private static boolean standard(Context c) {
        Obj snapshot=c.snapshot(),player=object(snapshot.get("played_character"));Army a=c.subject();
        return yes(snapshot.get("paused"))&&yes(snapshot.get("map_ready"))&&foregroundAbsent(c)&&!yes(snapshot.get("one_life_terminal"))
                &&!yes(snapshot.get("episode_identity_pending"))&&yes(player.get("alive"))&&c.controlled().size()==1&&a.controllable()
                &&Objects.equals(a.owner(),optionalInt(player.get("character_id")))&&!wars(c.request()).isEmpty()&&c.published().activeAssaults().isEmpty()&&clock(c);
    }
    private static boolean nativeNegative(List<Obj> rejected) {
        return !rejected.isEmpty()&&rejected.stream().allMatch(r->is(r,"status","blocked")||is(r,"status","unsafe")||is(r,"status","contact_timeline_unsafe"));
    }
    private static Optional<List<Army>> fullHostiles(Context c) {
        List<Army> result=new ArrayList<>();
        for(Obj war:wars(c.request())) {
            if(!(war.get("enemy_armies") instanceof Arr))return Optional.empty();
            for(Obj row:rows(war.get("enemy_armies"))) {
                if(yes(row.get("retreating")))continue;
                result.add(army(row));
            }
        }
        return Optional.of(List.copyOf(result));
    }
    public static Optional<MilitaryPlanningDecision> retainedEmbarked(Context c,Optional<Obj> auditInput,List<Obj> rejections) {
        if(auditInput.isEmpty())return Optional.empty();Obj audit=auditInput.orElseThrow();Army army=c.subject();
        Optional<Obj> pending=WarHistorySteps.pendingUnsafeRouteHalt(c.history(),c.snapshot(),army.id());
        Obj h=object(audit.get("contact_horizon"));List<Integer> route=army.route().orElse(List.of());
        if(!(advertised(c.request(),"life-advance-one-day")&&pending.filter(r->yes(r.get("suffix_cancellation_observed"))).isPresent()
                &&foregroundAbsent(c)&&"embarked".equals(army.state())&&Objects.equals(army.stateCode(),4)&&route.size()==1
                &&is(h,"status","available")&&Objects.equals(optionalInt(h.get("subject_army_id")),army.id())
                &&Objects.equals(h.get("target_province_id"),number(route.getFirst()))&&Objects.equals(h.get("date_raw"),c.snapshot().get("date_raw"))
                &&Objects.equals(h.get("snapshot_revision"),c.snapshot().get("native_revision"))
                &&Objects.equals(object(h.get("subject_route")).get("route_province_ids"),numbers(route))&&no(h.get("one_day_contact_free"))
                &&is(audit,"contact_policy","blocked_without_qualified_combat_permission")&&nativeNegative(rejections)))return Optional.empty();
        Obj watch=obj(f("army_id",number(army.id())),f("current_province_id",nullable(army.raw().get("current_province_id"))),
                f("target_province_id",number(route.getFirst())),f("route_province_ids",numbers(route)),f("source_date_raw",c.snapshot().get("date_raw")),
                f("source_native_revision",c.snapshot().get("native_revision")),f("halt_submission",pending.orElseThrow()),f("contact_free_proven",new Bool(false)),
                f("contact_status",text("unsafe")),f("movement_resubmitted",new Bool(false)),f("offensive_combat_permission",new Bool(false)),f("war_or_material_credit",new Bool(false)));
        return Optional.of(action(c,"native_war_retained_unsafe_edge_one_day_watch","life-advance-one-day",
                "CK3 retained the existing first edge after Halt and every eligible safe replan was rejected; observe one native-stopped day, then read army and battle state again; contact may occur",
                f("retained_edge_watch",watch),f("route_rejections",objects(rejections))));
    }
    public static Optional<MilitaryPlanningDecision> retainedLand(Context c,Optional<Obj> auditInput,List<Obj> rejections) {
        if(auditInput.isEmpty())return Optional.empty();Obj audit=auditInput.orElseThrow();Army a=c.subject();List<Integer> route=a.route().orElse(List.of());
        if(!(standard(c)&&"moving".equals(a.state())&&Objects.equals(a.stateCode(),7)&&Boolean.FALSE.equals(a.inCombat())&&Boolean.FALSE.equals(a.retreating())
                &&"complete_nonempty".equals(a.routeReadStatus())&&route.size()==1&&Objects.equals(a.target(),route.getFirst())
                &&nativeNegative(rejections)&&is(audit,"contact_policy","blocked_without_qualified_combat_permission")))return Optional.empty();
        Optional<List<Army>> enemies=fullHostiles(c);if(enemies.isEmpty())return Optional.empty();
        List<Integer> hostileIds=enemies.orElseThrow().stream().map(Army::id).distinct().sorted().toList();
        if(hostileIds.isEmpty()||hostileIds.size()>64)return Optional.empty();
        Optional<Obj> pending=WarHistorySteps.pendingUnsafeRouteHalt(c.history(),c.snapshot(),a.id());
        if(pending.isEmpty()||!yes(pending.orElseThrow().get("suffix_cancellation_observed"))||!yes(pending.orElseThrow().get("current_edge_retained")))return Optional.empty();
        var query=new MilitaryTimeline.Query(a.id(),c.current(),route.getFirst(),hostileIds,route);var lookup=MilitaryTimeline.fresh(c.request(),query);
        if(!(lookup instanceof MilitaryTimeline.Found found))return Optional.empty();var h=found.horizon();
        if(!Objects.equals(h.original(),audit.get("contact_horizon"))||h.oneDayFree()||h.nativeConflicts().isEmpty())return Optional.empty();
        Obj watch=merge(watchedFrame(c),obj(f("army_id",number(a.id())),f("current_province_id",number(c.current())),f("target_province_id",number(route.getFirst())),
                f("route_province_ids",numbers(route)),f("hostile_army_ids",numbers(hostileIds)),f("halt_submission",pending.orElseThrow()),f("contact_horizon",h.original()),
                f("contact_free_proven",new Bool(false)),f("contact_status",text("unsafe")),f("in_day_contact_or_defeat_possible",new Bool(true)),f("movement_resubmitted",new Bool(false)),
                f("offensive_combat_permission",new Bool(false)),f("war_or_material_credit",new Bool(false)),f("maximum_observation_days",number(1)),
                f("native_clock_scope",text("exact_one_day_date_only_a0")),f("native_watch_army_ids",numbers(List.of())),f("in_day_army_event_actor_watch",new Bool(false)),
                f("next_paused_frame_army_event_actor_read_required",new Bool(true))));
        return Optional.of(action(c,"native_war_land_retained_unsafe_edge_one_day_watch","life-advance-one-day",
                "the original native Halt canceled the future tail, but a fresh readback retains the first land edge and every safe replan was rejected; observe one native-stopped day of possible contact, then re-read army, battle and event state",
                f("retained_edge_watch",watch),f("route_rejections",objects(rejections))));
    }
    public static Optional<MilitaryPlanningDecision> excludedSiege(Context c,List<Obj> rejections) {
        var p=c.published();Army a=c.subject();if(p.exactSiegeRejection().isEmpty())return Optional.empty();
        Obj rejected=p.exactSiegeRejection().orElseThrow(),contribution=object(rejected.get("subject_contribution"));
        Integer besieging=optionalInt(rejected.get("besieging_army_id")),nativeArmy=optionalInt(contribution.get("native_carmy_id"));
        Obj onlyRejection=obj(f("target_province_id",number(c.current())),f("status",text("current_exact_siege_rejected")),f("siege_status",text("not_player_besieging")));
        if(!(standard(c)&&p.unsafeArmyIds().isEmpty()&&"regular".equals(a.state())&&Objects.equals(a.stateCode(),1)&&idle(a,true)
                &&"complete_empty".equals(a.routeReadStatus())&&is(rejected,"status","not_player_besieging")
                &&Objects.equals(optionalInt(rejected.get("province_id")),c.current())&&no(rejected.get("player_army_besieging"))
                &&besieging!=null&&besieging>=0&&besieging!=a.id()&&is(contribution,"status","excluded")
                &&Objects.equals(optionalInt(contribution.get("public_unit_id")),a.id())&&nativeArmy!=null&&nativeArmy>0
                &&no(contribution.get("matches_current_selection"))&&is(contribution,"reason","measured_native_province_qualification")
                &&rejections.equals(List.of(onlyRejection))))return Optional.empty();
        Optional<List<Army>> enemies=fullHostiles(c);if(enemies.isEmpty()||enemies.orElseThrow().isEmpty())return Optional.empty();
        for(Army enemy:enemies.orElseThrow()) {
            if(enemy.current()==null||enemy.current()<=0||!enemy.moveTargetPresent()||!Set.of("complete_empty","complete_nonempty").contains(enemy.routeReadStatus()==null?"":enemy.routeReadStatus())
                    ||enemy.route().isEmpty()||enemy.tacticalState()==null)return Optional.empty();
            if(enemy.route().orElseThrow().isEmpty()&&(enemy.target()!=null||!"complete_empty".equals(enemy.routeReadStatus())))return Optional.empty();
        }
        if(routeEvidenceIssue(a,true)||enemies.orElseThrow().stream().anyMatch(e->!"retreating".equals(e.tacticalState())&&routeEvidenceIssue(e,false))
                ||!stationaryThreats(c.current(),enemies.orElseThrow()).isEmpty())return Optional.empty();
        List<Integer> hostileIds=enemies.orElseThrow().stream().map(Army::id).distinct().sorted().toList();
        Obj watch=merge(watchedFrame(c),obj(f("army_id",number(a.id())),f("current_province_id",number(c.current())),f("hostile_army_ids",numbers(hostileIds)),
                f("siege_rejection",rejected),f("siege_contribution_credit",new Bool(false)),f("native_clock_scope",text("exact_one_day_date_only_a0")),
                f("native_watch_army_ids",numbers(List.of())),f("in_day_army_event_actor_watch",new Bool(false)),f("maximum_observation_days",number(1)),
                f("next_paused_frame_complete_planner_required",new Bool(true)),f("contact_free_proven",new Bool(false)),f("in_day_contact_or_defeat_possible",new Bool(true)),
                f("movement_or_assault_submitted",new Bool(false)),f("offensive_combat_permission",new Bool(false)),f("war_or_material_credit",new Bool(false))));
        return Optional.of(action(c,"native_war_stationary_excluded_siege_one_day_observation","life-advance-one-day",
                "the only exact objective is the current idle province, but native regiment qualification excludes this army from another army's siege; make no move or assault, observe one date-stopped day, then re-evaluate the complete war and financing plan",
                f("excluded_siege_watch",watch),f("route_rejections",objects(rejections))));
    }
    public static Optional<MilitaryPlanningDecision> stationaryUnavailable(Context c,List<Obj> rejections) {
        var p=c.published();Army a=c.subject();
        List<Obj> actualArmies=rows(c.snapshot().get("player_armies"));
        if(!(standard(c)&&actualArmies.size()==1&&Objects.equals(actualArmies.getFirst(),a.raw())&&"regular".equals(a.state())&&Objects.equals(a.stateCode(),1)
                &&idle(a,true)&&p.unsafeArmyIds().isEmpty()&&!p.stationaryThreats().isEmpty()&&!rejections.isEmpty()
                &&!c.hostileIds().isEmpty()&&c.hostileIds().size()<=64))return Optional.empty();
        Optional<List<Army>> enemies=fullHostiles(c);if(enemies.isEmpty())return Optional.empty();
        List<Integer> observedIds=enemies.orElseThrow().stream().map(Army::id).distinct().sorted().toList();
        if(!observedIds.equals(c.hostileIds())||p.stationaryThreats().stream().noneMatch(r->Objects.equals(optionalInt(r.get("province_id")),c.current())
                &&observedIds.contains(optionalInt(r.get("enemy_army_id")))))return Optional.empty();
        Optional<Obj> attempt=failure(c,c.current(),List.of());
        if(attempt.isEmpty()||!is(attempt.orElseThrow(),"scope_status","current_frame")||!is(attempt.orElseThrow(),"status","unavailable")||!no(attempt.orElseThrow().get("ok")))return Optional.empty();
        Obj result=null;List<Obj> history=afterRestore(c.history());String query=query(c,c.current());
        for(int i=history.size()-1;i>=0;i--)if(query.equals(command(history.get(i)))) {result=result(history.get(i));break;}
        Obj evidence=result==null?empty():object(result.get("readonly_unavailable_evidence")),raw=object(evidence.get("native_command_result"));
        if(!no(raw.get("ok"))||!is(raw,"error","CK3 route arrival timeline is unavailable")||rejections.stream().noneMatch(r->Objects.equals(optionalInt(r.get("target_province_id")),c.current())
                &&is(r,"status","contact_timeline_unavailable")&&Objects.equals(r.get("contact_query_attempt"),attempt.orElseThrow())))return Optional.empty();
        Obj watch=obj(f("army_id",number(a.id())),f("current_province_id",number(c.current())),f("hostile_army_ids",numbers(observedIds)),f("stationary_threats",objects(p.stationaryThreats())),
                f("query_step",text(query)),f("native_request_id",nullable(evidence.get("native_request_id"))),f("native_error",raw.get("error")),f("source_date_raw",c.snapshot().get("date_raw")),
                f("source_native_revision",c.snapshot().get("native_revision")),f("contact_free_proven",new Bool(false)),f("contact_status",text("unknown")),f("in_day_contact_or_defeat_possible",new Bool(true)),
                f("movement_resubmitted",new Bool(false)),f("offensive_combat_permission",new Bool(false)),f("war_or_material_credit",new Bool(false)),f("maximum_observation_days",number(1)),f("native_terminal_daily_sentinel_required",new Bool(true)));
        return Optional.of(action(c,"native_war_stationary_timeline_unavailable_defensive_one_day_observation","life-advance-one-day",
                "all exact exits were rejected and the complete hostile arrival timeline is unavailable; defend the current province for one native-stopped day, accepting possible in-day contact or defeat, then re-read the war",
                f("defensive_risk_watch",watch),f("contact_query_attempt",attempt.orElseThrow()),f("route_rejections",objects(rejections))));
    }
    private static Obj watchedFrame(Context c) {return obj(f("source_snapshot_id",c.snapshot().get("snapshot_id")),f("source_public_revision",c.snapshot().get("revision")),
            f("source_native_revision",c.snapshot().get("native_revision")),f("source_date_raw",c.snapshot().get("date_raw")));}
    private static boolean routeEvidenceIssue(Army a,boolean player) {
        List<Integer> route=a.route().orElse(List.of());boolean active="moving".equals(a.tacticalState())||Objects.equals(a.stateCode(),7)||!route.isEmpty()||player&&a.target()!=null;
        if(!active)return false;
        if(a.target()==null||a.target()<=0||a.route().isEmpty())return true;
        List<Integer> remaining=MilitaryRouteGeometry.remaining(route,a.current()==null?-1:a.current());return remaining.isEmpty()||!remaining.getLast().equals(a.target());
    }
    public static List<Obj> stationaryThreats(int province,List<Army> enemies) {
        List<Obj> result=new ArrayList<>();
        for(Army e:enemies) {
            if("retreating".equals(e.tacticalState()))continue;
            String kind=Objects.equals(e.current(),province)?"enemy_at_stationary_province":Objects.equals(e.target(),province)?"enemy_targeting_stationary_province":
                    e.route().filter(route->route.contains(province)).isPresent()?"enemy_route_to_stationary_province":null;
            if(kind!=null)result.add(obj(f("kind",text(kind)),f("enemy_army_id",number(e.id())),f("province_id",number(province))));
        }
        return List.copyOf(result);
    }
}

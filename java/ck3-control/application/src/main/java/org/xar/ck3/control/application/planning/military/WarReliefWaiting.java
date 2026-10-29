package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.DefaultRaiseObservation;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevanceCodec;
import org.xar.ck3.control.wave2.military.reliefrelevance.ReliefRelevancePolicy;

/** strategy19225..19590: actual reserve legality first, then independent stationary one-day observation. */
public final class WarReliefWaiting {
    private WarReliefWaiting() { }
    public static Optional<MilitaryPlanningDecision> plan(PlanningRequest request,WarContactObservation.Context contact,
            Obj relief,Obj battle,List<Obj> summaries) {
        Optional<MilitaryPlanningDecision> reserve=reserve(request,contact,relief,summaries);
        return reserve.isPresent()?reserve:watch(request,contact,relief,battle,summaries);
    }
    private static Optional<List<Integer>> incompleteWars(Obj relief) {
        if(!new Text("complete-same-frame-siege-position-and-war-strength").equals(relief.get("required_observation"))||!(relief.get("war_ids") instanceof Arr))return Optional.empty();
        List<Integer> wars=ids(relief.get("war_ids"));return wars.isEmpty()||wars.stream().anyMatch(i->i<=0)?Optional.empty():Optional.of(wars);
    }
    private static boolean common(PlanningRequest request,WarContactObservation.Context contact) {
        Obj s=request.observations().snapshot();
        return request.observations().paused()&&request.observations().mapReady()&&s.get("active_event")==Nil.INSTANCE&&s.get("pending_character_interaction")==Nil.INSTANCE
                &&contact.controlledArmies().size()==1&&Set.of("partial","available").contains(Objects.toString(optionalText(s.get("army_strengths_status")),""));
    }
    public static Optional<MilitaryPlanningDecision> reserve(PlanningRequest request,WarContactObservation.Context contact,Obj relief,List<Obj> summaries) {
        Obj s=request.observations().snapshot();var wars=incompleteWars(relief);
        if(wars.isEmpty()||!common(request,contact)||!EarlyWarCoreLeaves.has(request,DefaultRaiseObservation.STEP)
                ||!EarlyWarCoreLeaves.has(request,"raise-troops-default")
                ||!Objects.equals(s.get("army_strengths_queried_snapshot_id"),s.get("snapshot_id"))
                ||!Objects.equals(s.get("army_strengths_queried_revision"),s.get("revision")))return Optional.empty();
        Army army=contact.controlledArmies().getFirst();
        if(!"regular".equals(army.tacticalState())||!Boolean.FALSE.equals(army.inCombat())||!Boolean.FALSE.equals(army.retreating())
                ||army.target()!=null||army.route().isEmpty()||!army.route().orElseThrow().isEmpty()||!(s.get("army_strengths") instanceof Arr))return Optional.empty();
        Map<Integer,Obj> strengths=new LinkedHashMap<>();for(Obj row:rows(s.get("army_strengths")))strengths.put(id(row.get("army_id")),row);
        Obj own=strengths.get(army.id());BigInteger ownSoldiers=own==null?null:optionalInteger(own.get("current_soldiers"));
        if(own==null||!new Text("available").equals(own.get("status"))||!new Text("player").equals(own.get("scope_role"))||ownSoldiers==null||ownSoldiers.signum()<=0)return Optional.empty();
        Set<Integer> siegeEnemies=new LinkedHashSet<>();List<Obj> active=wars(request);
        for(int wi=0;wi<active.size();wi++) {
            Obj war=active.get(wi);if(!wars.orElseThrow().contains(id(war.get("war_id"))))continue;
            List<Obj> enemies=rows(war.get("enemy_armies"));
            for(int ei=0;ei<enemies.size();ei++){Army enemy=army(enemies.get(ei));if("sieging".equals(enemy.tacticalState())&&!Boolean.TRUE.equals(enemy.retreating())&&relevant(s,wi,ei))siegeEnemies.add(enemy.id());}
        }
        if(siegeEnemies.isEmpty())return Optional.empty();BigInteger enemySoldiers=BigInteger.ZERO;
        for(int enemy:siegeEnemies) {
            Obj row=strengths.get(enemy);BigInteger soldiers=row==null?null:optionalInteger(row.get("current_soldiers"));
            if(row==null||!new Text("available").equals(row.get("status"))||!new Text("active_war_enemy").equals(row.get("scope_role"))||soldiers==null||soldiers.signum()<0)return Optional.empty();
            enemySoldiers=enemySoldiers.add(soldiers);
        }
        if(enemySoldiers.multiply(BigInteger.TWO).compareTo(ownSoldiers.multiply(BigInteger.valueOf(3)))<0)return Optional.empty();
        if(!(s.get("diagnostics") instanceof Obj diagnostics)||!(s.get("played_character") instanceof Obj player)
                ||!(s.get("episode_run_id") instanceof Text episode)||episode.value().isEmpty()
                ||!(diagnostics.get("connection_generation") instanceof IntegerValue)||!(diagnostics.get("bridge_pid") instanceof IntegerValue)
                ||!(player.get("character_id") instanceof IntegerValue))return Optional.empty();
        List<Obj> branch=afterRestore(request.observations().history());BigInteger date=request.before().frame().identity().dateRaw();
        for(int i=branch.size()-1;i>=0;i--) {
            Obj row=branch.get(i);if(!DefaultRaiseObservation.STEP.equals(command(row)))continue;
            Obj result=result(row);if(result==null||!(result.get("player_default_raise") instanceof Obj observation))continue;
            if(!Objects.equals(result.get("queried_episode_run_id"),s.get("episode_run_id"))
                    ||!Objects.equals(result.get("queried_connection_generation"),diagnostics.get("connection_generation"))
                    ||!Objects.equals(result.get("queried_bridge_pid"),diagnostics.get("bridge_pid"))
                    ||!Objects.equals(observation.get("actor_character_id"),player.get("character_id")))continue;
            BigInteger observed=optionalInteger(observation.get("date_raw"));if(observed==null||observed.compareTo(date)>0)continue;
            if(observed.equals(date)) {
                if(!yes(row.get("ok"))||!yes(result.get("accepted"))||!new Text("completed").equals(result.get("status"))||!yes(result.get("read_only"))
                        ||!Objects.equals(result.get("queried_snapshot_id"),s.get("snapshot_id"))||!Objects.equals(result.get("queried_revision"),s.get("revision"))
                        ||!Objects.equals(result.get("queried_native_revision"),s.get("native_revision")))return Optional.empty();
                DefaultRaiseObservation.Observed normalized;
                try{normalized=DefaultRaiseObservation.parse(StrictJson.parse(OpportunityJson.encode(observation)),new DefaultRaiseObservation.Expected(request.source().exactBuild(),
                        request.before().frame().identity().player(),request.before().frame().identity().nativeRevision(),date));}catch(IllegalArgumentException malformed){return Optional.empty();}
                if(!normalized.raising().legal().orElse(false)||!normalized.reserve().ready()||normalized.reserve().unraisedSoldiers().orElse(0)<=0)return Optional.empty();
                return Optional.of(EarlyWarCoreLeaves.select(request,"native_war_defender_siege_raise_verified_reserve","raise-troops-default",
                        "same-frame native default raise is legal with unraised troops; add defenders without authorizing siege contact",
                        obj(f("default_raise",observation),f("siege_relief",relief)),summaries,OrdinaryPolicy.Purpose.WORLD_ACTION));
            }
            BigInteger elapsed=date.subtract(observed);
            if(elapsed.signum()>0&&elapsed.compareTo(BigInteger.valueOf(72))<0&&yes(row.get("ok"))&&yes(result.get("accepted"))
                    &&new Text("completed").equals(result.get("status"))&&yes(result.get("read_only"))&&new Text("available").equals(observation.get("status"))
                    &&new Text("available").equals(observation.get("unraised_troops_status"))
                    &&(no(observation.get("native_default_raise_legal"))||number(0).equals(observation.get("unraised_soldiers"))))return Optional.empty();
            break;
        }
        return Optional.of(EarlyWarCoreLeaves.select(request,"native_war_defender_siege_reserve_query",DefaultRaiseObservation.STEP,
                "read native default raise legality and unraised troops; deployed soldiers are not reserves",
                obj(f("observed_player_soldiers",number(ownSoldiers)),f("observed_enemy_siege_soldiers",number(enemySoldiers)),f("siege_relief",relief)),summaries,OrdinaryPolicy.Purpose.READ_ONLY));
    }
    public static Optional<MilitaryPlanningDecision> watch(PlanningRequest request,WarContactObservation.Context contact,Obj relief,Obj battle,List<Obj> summaries) {
        Obj s=request.observations().snapshot();var affected=incompleteWars(relief);
        if(affected.isEmpty()||!common(request,contact)||!yes(s.get("route_contact_horizon_supported"))||!yes(s.get("army_routes_supported"))
                ||!new Text("not_in_combat").equals(battle.get("status"))||!contact.evidenceIssues().isEmpty()
                ||contact.hostileArmyIds().isEmpty()||contact.hostileArmyIds().size()>64||!EarlyWarCoreLeaves.has(request,"life-advance-one-day"))return Optional.empty();
        Army army=contact.controlledArmies().getFirst();Integer origin=army.current();
        if(origin==null||origin<=0||!"regular".equals(army.tacticalState())||!Boolean.FALSE.equals(army.inCombat())||!Boolean.FALSE.equals(army.retreating())
                ||!army.moveTargetPresent()||army.target()!=null||army.route().isEmpty()||!army.route().orElseThrow().isEmpty())return Optional.empty();
        List<Army> enemies=contact.completeRouteThreatEnemies();
        if(!Set.copyOf(contact.hostileArmyIds()).equals(enemies.stream().map(Army::id).collect(java.util.stream.Collectors.toSet()))
                ||enemies.stream().anyMatch(a->a.current()==null||a.current()<=0))return Optional.empty();
        Set<Integer> observedWars=new LinkedHashSet<>();List<Obj> active=wars(request);
        for(int wi=0;wi<active.size();wi++) {
            Obj war=active.get(wi);int warId=id(war.get("war_id"));if(!affected.orElseThrow().contains(warId))continue;
            List<Obj> rawEnemies=rows(war.get("enemy_armies"));
            for(int ei=0;ei<rawEnemies.size();ei++) {
                Army enemy=army(rawEnemies.get(ei));if(!"sieging".equals(enemy.tacticalState())||Boolean.TRUE.equals(enemy.retreating())||!relevant(s,wi,ei))continue;
                observedWars.add(warId);
                if(enemy.current()==null||!Boolean.FALSE.equals(enemy.inCombat())||!Boolean.FALSE.equals(enemy.retreating())||!enemy.moveTargetPresent()
                        ||enemy.target()!=null||enemy.route().isEmpty()||!enemy.route().orElseThrow().isEmpty())return Optional.empty();
            }
        }
        if(!observedWars.equals(Set.copyOf(affected.orElseThrow()))||WarSiegeDaily.reviews(request,enemies).stream().anyMatch(r->!new Text("inactive").equals(r.get("status"))))return Optional.empty();
        List<Integer> targets=new ArrayList<>();
        for(Army enemy:enemies)if("sieging".equals(enemy.tacticalState())&&enemy.current()!=null&&enemy.current()>0&&!origin.equals(enemy.current())&&!targets.contains(enemy.current())) {
            var query=new MilitaryTimeline.Query(army.id(),origin,enemy.current(),contact.hostileArmyIds(),List.of());
            if(EarlyWarCoreLeaves.has(request,query.step()))targets.add(enemy.current());if(targets.size()==2)break;
        }
        List<Obj> history=afterRestore(request.observations().history());
        for(int target:targets) {
            var query=new MilitaryTimeline.Query(army.id(),origin,target,contact.hostileArmyIds(),List.of());MilitaryTimeline.Horizon proof=null;
            for(int i=history.size()-1;i>=0;i--) {
                Obj row=history.get(i);if(!query.step().equals(command(row))||!yes(row.get("ok")))continue;
                Obj result=result(row);if(result==null||!(result.get("route_contact_horizon") instanceof Obj horizon)
                        ||!(horizon.get("subject_route") instanceof Obj subject)||!(subject.get("route_province_ids") instanceof Arr))continue;
                var actualQuery=new MilitaryTimeline.Query(army.id(),origin,target,contact.hostileArmyIds(),route(subject.get("route_province_ids")).orElseThrow());
                var found=MilitaryTimeline.fresh(request,actualQuery);if(found instanceof MilitaryTimeline.Found available)proof=available.horizon();break;
            }
            if(proof==null) {
                if(MilitaryTimeline.failure(request,query).isPresent())continue;
                return Optional.of(EarlyWarCoreLeaves.select(request,"native_war_defender_siege_observation_contact_query",query.step(),
                        "read a full-hostile timeline for stationary one-day observation; the reference target is read-only and relief/battle remain unqualified",
                        obj(f("siege_relief",relief)),summaries,OrdinaryPolicy.Purpose.READ_ONLY));
            }
            if(proof.targetProvinceId()!=target||!WarContactWindows.stationaryFree(proof,origin))return Optional.empty();
            return Optional.of(EarlyWarCoreLeaves.select(request,"native_war_defender_siege_observation_one_day_watch","life-advance-one-day",
                    "the complete same-frame hostile timeline proves one stationary day at the actual Province without contact; the reference route is never submitted",
                    obj(f("reference_route_query_step",text(query.step())),f("contact_horizon",proof.original()),f("siege_relief",relief)),summaries,OrdinaryPolicy.Purpose.DATE_ADVANCE));
        }
        return Optional.empty();
    }
    private static boolean relevant(Obj snapshot,int war,int enemy) {
        Obj frame=obj(f("schema",text(RealmSiegePolicy.INPUT_SCHEMA)),f("snapshot",snapshot),f("detached_wars",new Arr(List.of())),f("detached_enemies",new Arr(List.of())),
                f("candidate_war_ref",obj(f("collection",text("active_wars")),f("index",number(war)))),
                f("candidate_enemy_ref",obj(f("collection",text("candidate_war_enemy_armies")),f("index",number(enemy)))));
        return ReliefRelevancePolicy.assess(ReliefRelevanceCodec.decodeNode(StrictJson.parse(OpportunityJson.encode(
                obj(f("schema",text(ReliefRelevancePolicy.INPUT_SCHEMA)),f("frame",frame)))))).candidateSiegeReliefRelevant();
    }
}

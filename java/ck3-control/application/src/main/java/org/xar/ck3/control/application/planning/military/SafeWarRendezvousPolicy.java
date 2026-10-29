package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy.PreviewStatus;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** Real war_safe_rendezvous_v1 consumer. A route candidate grants no arrival, merge or battle credit. */
public final class SafeWarRendezvousPolicy implements OrdinaryPolicy {
    public interface MovementState {
        WarStrengthRelief.EvidenceLookup activeIntent(PlanningRequest request,int army,int target);
        WarStrengthRelief.EvidenceLookup deferredBackoff(PlanningRequest request,int army,int target);
    }
    private final ExactRef source;
    private final MovementState movement;
    private final MilitaryPlanningDecision.ApplicationAdapter adapter;
    public SafeWarRendezvousPolicy(ExactRef source,MovementState movement,MilitaryPlanningDecision.ApplicationAdapter adapter) {
        this.source=Objects.requireNonNull(source);this.movement=Objects.requireNonNull(movement);this.adapter=Objects.requireNonNull(adapter);
    }
    @Override public PlanningStage stage(){return PlanningStage.WAR_RENDEZVOUS;}
    @Override public ExactRef implementationSource(){return source;}
    @Override public Decision evaluate(PlanningRequest request,Draft previous) {
        return adapter.adapt(request,previous,review(request,previous));
    }
    public MilitaryPlanningDecision review(PlanningRequest request,Draft previous) {
        Obj baseline=previous.detail(),snapshot=request.observations().snapshot();String original=optionalText(baseline.get("selected_step"));
        if(!"native_war_stationary_objective_hold_sentinel".equals(previous.phase())||original==null
                ||!original.startsWith("war-objective-hold-sentinel-advance-")||yes(baseline.get("active_attack_allowed"))
                ||!request.observations().bridgeCapabilities().contains("game.command.merge-armies-N-with-N"))return keep();
        if(!quiet(snapshot)||!(snapshot.get("played_character") instanceof Obj actor)||!yes(actor.get("alive"))
                ||optionalInt(actor.get("character_id"))==null
                ||!Objects.equals(snapshot.get("army_strengths_queried_snapshot_id"),snapshot.get("snapshot_id"))
                ||!Objects.equals(snapshot.get("army_strengths_queried_revision"),snapshot.get("revision")))return keep();
        List<Obj> wars=wars(request);if(wars.size()!=1)return keep();Obj war=wars.get(0);
        Integer score=optionalInt(war.get("player_relative_war_score"));
        if(!new Text("defender").equals(war.get("player_side"))||!yes(war.get("player_is_primary_war_leader"))||score==null||score>=0)return keep();
        List<Army> armies=rows(snapshot.get("player_armies")).stream().map(MilitaryPlanInputs::army).toList();
        if(armies.size()<=1||armies.stream().anyMatch(army->!army.explicitIdle()||army.current()==null||army.current()<=0
                ||!army.controllable()||!Objects.equals(army.raw().get("owner_character_id"),actor.get("character_id"))))return keep();
        Set<Integer> ownIds=new HashSet<>();Set<Integer> places=new HashSet<>();for(Army army:armies){ownIds.add(army.id());places.add(army.current());}
        if(ownIds.size()!=armies.size()||places.size()==1||balance(request,id(war.get("war_id"))).isEmpty())return keep();
        List<Obj> strengthRows=rows(snapshot.get("army_strengths"));Map<Integer,BigInteger> strengths=strengths(strengthRows,"player",id(war.get("war_id")));
        if(!strengths.keySet().equals(ownIds)||strengths.values().stream().anyMatch(n->n.signum()<=0))return keep();
        List<Integer> hostiles=hostiles(request);if(hostiles.isEmpty()||hostiles.size()>64)return keep();
        Map<Integer,BigInteger> enemyStrengths=strengths(strengthRows,"active_war_enemy",null);
        if(!enemyStrengths.keySet().equals(new HashSet<>(hostiles)))return keep();
        List<Army> enemies=enemies(request);Map<Integer,Set<Integer>> groups=new java.util.TreeMap<>();
        for(Army enemy:enemies)if(hostiles.contains(enemy.id())&&Boolean.FALSE.equals(enemy.inCombat())&&Boolean.FALSE.equals(enemy.retreating())
                &&enemy.route().isPresent()&&enemy.route().orElseThrow().isEmpty()&&enemy.current()!=null)
            groups.computeIfAbsent(enemy.current(),ignored->new HashSet<>()).add(enemy.id());
        BigInteger total=sum(strengths),strongest=strengths.values().stream().max(Comparator.naturalOrder()).orElseThrow();
        List<Obj> opportunities=new ArrayList<>();
        for(var entry:groups.entrySet()) {
            BigInteger local=entry.getValue().stream().map(enemyStrengths::get).reduce(BigInteger.ZERO,BigInteger::add);
            if(local.compareTo(strongest)>0&&local.compareTo(total)<0)opportunities.add(obj(f("province_id",number(entry.getKey())),
                    f("enemy_army_ids",numbers(entry.getValue().stream().sorted().toList())),f("observed_current_soldiers",number(local))));
        }
        if(opportunities.isEmpty()||!(war.get("objective_province_states") instanceof Arr)||!(war.get("war_objective_province_ids") instanceof Arr))return keep();
        Map<Integer,Obj> states=new HashMap<>();for(Obj row:rows(war.get("objective_province_states")))states.put(int32(row.get("province_id")),row);
        List<Integer> objectives=ids(war.get("war_objective_province_ids"));
        List<Army> anchors=armies.stream().sorted(Comparator.<Army,BigInteger>comparing(a->strengths.get(a.id())).reversed().thenComparingInt(Army::id))
                .filter(a->objectives.contains(a.current())&&states.get(a.current())!=null&&yes(states.get(a.current()).get("occupation_observable"))
                        &&no(states.get(a.current()).get("is_occupied"))).toList();
        List<Army> movers=armies.stream().sorted(Comparator.<Army,BigInteger>comparing(a->strengths.get(a.id())).thenComparingInt(Army::id)).toList();
        List<Obj> rejections=new ArrayList<>();
        for(Army anchor:anchors)for(Army mover:movers) {
            int target=anchor.current(),origin=mover.current();if(origin==target)continue;
            String previewStep="preview-move-army-"+mover.id()+"-to-"+target;
            var preview=freshPreview(request,mover,target);
            if(preview.isEmpty()) {
                if(advertised(request,previewStep))return select(request,plan(previewStep,"native_war_route_preview",
                        "read a route to the existing defensive army before considering concentration; no attack is authorized"),
                        anchor,mover,"observe",war,ownIds,hostiles,opportunities,total,sum(enemyStrengths),rejections,empty(),Purpose.READ_ONLY);
                continue;
            }
            var observed=preview.orElseThrow();var audit=MilitaryRouteGeometry.geometry(observed.routeProvinceIds(),origin,target,enemies.stream().map(Army::geometry).toList());
            if(observed.status()!=PreviewStatus.AVAILABLE||audit.status()!=MilitaryRouteGeometry.Status.SAFE) {
                rejections.add(rejection(mover,target,"whole_route_geometry_unavailable_or_unsafe"));continue;
            }
            Map<Integer,MilitaryTimeline.Horizon> horizons=new LinkedHashMap<>();
            List<Army> ordered=new ArrayList<>();ordered.add(mover);for(Army own:armies)if(own.id()!=mover.id())ordered.add(own);
            for(Army own:ordered) {
                var query=new MilitaryTimeline.Query(own.id(),own.current(),own.id()==mover.id()?target:own.current(),hostiles,
                        own.id()==mover.id()?observed.routeProvinceIds():List.of());
                var horizon=MilitaryTimeline.fresh(request,query);
                if(!(horizon instanceof MilitaryTimeline.Found found)) {
                    if(horizon instanceof MilitaryTimeline.Missing&&MilitaryTimeline.failure(request,query).isEmpty()&&advertised(request,query.step()))
                        return select(request,plan(query.step(),"native_war_candidate_contact_horizon",
                                "check this army and every waiting friendly against all observed hostile timelines before a rendezvous move"),
                                anchor,mover,"observe",war,ownIds,hostiles,opportunities,total,sum(enemyStrengths),rejections,empty(),Purpose.READ_ONLY);
                    break;
                }
                horizons.put(own.id(),found.horizon());
            }
            if(horizons.size()!=armies.size()||horizons.values().stream().anyMatch(h->!h.oneDayFree())) {
                rejections.add(rejection(mover,target,"complete_friendly_full_hostile_h1_not_free"));continue;
            }
            var contact=horizons.get(mover.id());
            if(horizons.values().stream().anyMatch(h->!h.original().get("hostile_routes").equals(contact.original().get("hostile_routes")))) {
                rejections.add(rejection(mover,target,"friendly_horizons_disagree_on_hostile_timelines"));continue;
            }
            Obj locked=MilitaryTimeline.lockedRoute(contact);
            if(!new Text("available").equals(locked.get("status"))||yes(locked.get("veto"))) {
                rejections.add(put(rejection(mover,target,"known_contact_during_committed_route"),"locked_route_exposure",locked));continue;
            }
            var exposure=MilitaryTimeline.origin(contact,origin);List<Integer> arrivals=contact.subject().arrivalDates();
            if(!exposure.available()||exposure.veto()||arrivals.isEmpty()) {rejections.add(rejection(mover,target,"origin_exposed_during_locked_leg"));continue;}
            int end=arrivals.getLast();Set<Integer> waiting=new HashSet<>();for(Army own:armies)if(own.id()!=mover.id())waiting.add(own.current());
            List<Integer> exposed=new ArrayList<>();
            for(var hostile:contact.hostiles()) {
                boolean conflict=waiting.contains(hostile.currentProvinceId());
                for(int i=0;i<hostile.provinceIds().size();i++)conflict|=waiting.contains(hostile.provinceIds().get(i))&&hostile.arrivalDates().get(i)<=end;
                if(conflict)exposed.add(hostile.armyId());
            }
            if(!exposed.isEmpty()) {rejections.add(put(rejection(mover,target,"waiting_friendly_exposed_before_rendezvous"),"hostile_army_ids",numbers(exposed)));continue;}
            String move="move-army-"+mover.id()+"-to-"+target;if(!advertised(request,move))continue;
            var intent=movement.activeIntent(request,mover.id(),target);
            if(!(intent instanceof WarStrengthRelief.EvidenceAbsent))continue;
            var backoff=movement.deferredBackoff(request,mover.id(),target);
            if(backoff instanceof WarStrengthRelief.EvidenceUnavailable)continue;
            if(backoff instanceof WarStrengthRelief.EvidenceFound found) {
                require(found.before().equals(request.before()),"rendezvous backoff crossed frame");if(!yes(found.evidence().get("retry_due")))continue;
            }
            String reason="两军分驻，先向现有己军所在防御目标"+target+"集中；己军合计"+total+"，局部已观测敌军"+
                    org.xar.ck3.control.planning.opportunity.OpportunityJson.integer(opportunities.getFirst().get("observed_current_soldiers"),"local soldiers")+"，全部已观测敌军"+sum(enemyStrengths)+"含在途。仅选择经独立核验的会合路线；抵达、原生合并及新战斗评估后再决策，未授接战";
            Obj candidate=merge(plan(move,"native_war_pursuit",reason),obj(f("pursuit",obj(f("army_id",number(mover.id())),f("target_province_id",number(target)),
                    f("target_source",text("existing_defensive_friendly_rendezvous")))),f("route_preview",previewDocument(observed)),
                    f("route_audit",put(auditDocument(audit),"contact_horizon",contact.original()))));
            Obj extra=obj(f("origin_exposure",exposure.detail()),f("locked_route_exposure",locked),f("predicted_rendezvous_date_raw",number(end)),
                    f("observation_required",text("native committed-route daily stops and independent arrival; original CanMerge and fresh forecast afterwards")));
            return select(request,candidate,anchor,mover,"move_candidate",war,ownIds,hostiles,opportunities,total,sum(enemyStrengths),rejections,extra,Purpose.WORLD_ACTION);
        }
        if(!anchors.isEmpty())return new MilitaryPlanningDecision.Keep(decorate(baseline,anchors.getFirst(),armies.getFirst(),"not_selected",war,
                ownIds,hostiles,opportunities,total,sum(enemyStrengths),rejections,empty()));
        return keep();
    }
    private static boolean quiet(Obj s) {
        return yes(s.get("paused"))&&yes(s.get("map_ready"))&&s.get("active_event")==Nil.INSTANCE&&s.get("pending_character_interaction")==Nil.INSTANCE
                &&s.members().containsKey("top_exclusive_modal_choice_hint")
                &&!(s.get("top_exclusive_modal_choice_hint") instanceof Obj hint&&new Text("present").equals(hint.get("status")));
    }
    private static Map<Integer,BigInteger> strengths(List<Obj> rows,String role,Integer war) {
        Map<Integer,BigInteger> result=new HashMap<>();
        for(Obj row:rows)if(new Text("available").equals(row.get("status"))&&new Text(role).equals(row.get("scope_role"))
                &&optionalInteger(row.get("army_id"))!=null&&optionalInteger(row.get("current_soldiers"))!=null
                &&(war==null||row.get("war_ids") instanceof Arr&&ids(row.get("war_ids")).contains(war)))
            result.put(id(row.get("army_id")),optionalInteger(row.get("current_soldiers")));
        return Map.copyOf(result);
    }
    private static BigInteger sum(Map<Integer,BigInteger> values){return values.values().stream().reduce(BigInteger.ZERO,BigInteger::add);}
    private static Obj plan(String step,String phase,String reason){return obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",text(step)),f("reason",text(reason)));}
    private static Obj rejection(Army army,int target,String reason){return obj(f("army_id",number(army.id())),f("target",number(target)),f("reason",text(reason)));}
    private static MilitaryPlanningDecision.Keep keep(){return new MilitaryPlanningDecision.Keep(empty());}
    private static Obj decorate(Obj plan,Army anchor,Army mover,String stage,Obj war,Set<Integer> own,List<Integer> hostile,List<Obj> opportunities,
            BigInteger total,BigInteger enemyTotal,List<Obj> rejected,Obj extra) {
        Obj detail=merge(obj(f("schema",text("xar.ck3.safe-war-rendezvous/v1")),f("stage",text(stage)),f("war_id",war.get("war_id")),
                f("anchor_army_id",number(anchor.id())),f("moving_army_id",number(mover.id())),f("rendezvous_province_id",number(anchor.current())),
                f("all_controlled_army_ids",numbers(own.stream().sorted().toList())),f("all_hostile_army_ids",numbers(hostile)),f("local_opportunities",objects(opportunities)),
                f("observed_own_total",number(total)),f("observed_all_hostile_total",number(enemyTotal)),f("other_hostiles_and_future_arrivals_not_ignored",new Bool(true)),
                f("battle_win_probability",Nil.INSTANCE),f("attack_authorized",new Bool(false)),f("arrival_guaranteed",new Bool(false)),f("merge_accepted",new Bool(false)),
                f("candidate_rejections",objects(rejected))),extra);
        return merge(plan,obj(f("active_wars",objects(List.of(war))),f("active_attack_allowed",new Bool(false)),f("war_safe_rendezvous_v1",detail)));
    }
    private static MilitaryPlanningDecision select(PlanningRequest request,Obj plan,Army anchor,Army mover,String stage,Obj war,Set<Integer> own,
            List<Integer> hostile,List<Obj> opportunities,BigInteger total,BigInteger enemyTotal,List<Obj> rejected,Obj extra,Purpose purpose) {
        Obj detail=decorate(plan,anchor,mover,stage,war,own,hostile,opportunities,total,enemyTotal,rejected,extra);
        return new MilitaryPlanningDecision.Select("one-life-turn-v1",optionalText(detail.get("phase")),optionalText(detail.get("reason")),
                new OperationKey(optionalText(detail.get("selected_step"))),empty(),purpose,detail);
    }
}

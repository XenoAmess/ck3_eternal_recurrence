package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningStage;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactCodec;
import org.xar.ck3.control.military.projectedcontact.ProjectedContactPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.military.forecast.CombatJson;
import org.xar.ck3.control.wave2.military.forecast.FixedContactForecast;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/** strategy._general_battle_forecast_ingress: route/roster/cache are actual consumers, not caller flags. */
public final class GeneralBattleForecastPolicy implements OrdinaryPolicy {
    private static final String PROJECTED_CAPABILITY="game.command.query-projected-contact-scope-v1-N";
    private static final Set<String> CLOCK_CAPABILITIES=Set.of("game.command.research-arm-tactical-daily-sentinel-v1-N",
            "game.command.research-query-tactical-daily-sentinel-v1","game.command.research-cancel-tactical-daily-sentinel-v1-generation-N");
    @FunctionalInterface public interface PrimaryDefenderSiegeIngress {Obj review(PlanningRequest request,Obj baseline);}
    @FunctionalInterface public interface ActiveCombatComparison {Optional<Obj> observe(PlanningRequest request);}
    private final ExactRef source;
    private final CombatObservationCache cache;
    private final PrimaryDefenderSiegeIngress siege;
    private final ActiveCombatComparison activeComparison;
    private final MilitaryPlanningDecision.ApplicationAdapter adapter;
    public GeneralBattleForecastPolicy(ExactRef source,CombatObservationCache cache,PrimaryDefenderSiegeIngress siege,
            ActiveCombatComparison activeComparison,MilitaryPlanningDecision.ApplicationAdapter adapter) {
        this.source=Objects.requireNonNull(source);this.cache=Objects.requireNonNull(cache);this.siege=Objects.requireNonNull(siege);
        this.activeComparison=Objects.requireNonNull(activeComparison);this.adapter=Objects.requireNonNull(adapter);
    }
    @Override public PlanningStage stage(){return PlanningStage.SIEGE_AND_BATTLE_FORECAST;}
    @Override public ExactRef implementationSource(){return source;}
    @Override public Decision evaluate(PlanningRequest request,Draft previous) {
        Obj reviewed=reviewGeneral(request,Objects.requireNonNull(siege.review(request,previous.detail())));
        if(reviewed.equals(previous.detail()))return new NotApplicable("forecast ingress retained the original ordinary action");
        String step=optionalText(reviewed.get("selected_step")),policy=OpportunityJson.text(reviewed.get("policy"),"policy"),phase=OpportunityJson.text(reviewed.get("phase"),"phase"),reason=OpportunityJson.text(reviewed.get("reason"),"reason");
        MilitaryPlanningDecision result;
        if(step==null)result=new MilitaryPlanningDecision.Hold(policy,phase,reason,Optional.empty(),reviewed);
        else if(step.equals(optionalText(previous.detail().get("selected_step"))))return new Annotate(new Draft(policy,phase,reason,previous.kind(),previous.command(),previous.purpose(),previous.domain(),reviewed),"current forecast evidence retained with the original exact operation");
        else result=new MilitaryPlanningDecision.Select(policy,phase,reason,new OperationKey(step),empty(),readOnly(step)?Purpose.READ_ONLY:Purpose.WORLD_ACTION,reviewed);
        return adapter.adapt(request,previous,result);
    }
    /** Also used by the unique origin-exposure alternate route provider; it performs no execution. */
    public Obj reviewGeneral(PlanningRequest request,Obj baseline) {
        Obj snapshot=request.observations().snapshot();
        if(!yes(snapshot.get("paused")))return baseline;
        Optional<WarHistorySteps.Move> parsed=WarHistorySteps.parseMove(optionalText(baseline.get("selected_step")));
        if(parsed.isEmpty()||!(snapshot.get("player_armies") instanceof Arr)||!(snapshot.get("active_wars") instanceof Arr))return baseline;
        int subject=parsed.orElseThrow().armyId(),target=parsed.orElseThrow().targetProvinceId();
        Optional<Obj> selected=rows(snapshot.get("player_armies")).stream().filter(a->number(subject).equals(a.get("army_id"))).findFirst();
        if(selected.isEmpty())return baseline;Army army=army(selected.orElseThrow());Integer origin=army.current();
        List<Army> enemies=enemies(request);
        List<Integer> defenders=enemies.stream().filter(a->Integer.valueOf(target).equals(a.current())&&!"retreating".equals(a.tacticalState())).map(Army::id).distinct().sorted().toList();
        List<Integer> activeDefenders=enemies.stream().filter(a->Integer.valueOf(target).equals(a.current())&&"combat".equals(a.tacticalState())).map(Army::id).distinct().sorted().toList();
        boolean activeSubject="combat".equals(army.tacticalState());
        if(!activeDefenders.isEmpty()&&!activeSubject&&enemyBattleObserver(request,baseline,army,target))
            return merge(obj(f("policy",text("general-battle-forecast-v1")),f("phase",text("native_war_enemy_ongoing_combat_one_day_observation")),f("selected_step",text("life-advance-one-day")),
                    f("reason",text("the proposed pursuit target is already in a different combat; leave the stationary player army in place and observe one exact native-stopped day before replanning"))),
                    obj(f("baseline_phase",nullable(baseline.get("phase"))),f("baseline_selected_step",nullable(baseline.get("selected_step"))),f("active_combat_subject_army_id",Nil.INSTANCE),f("active_combat_defender_army_ids",numbers(activeDefenders)),
                    f("subject_army_id",number(subject)),f("subject_current_province_id",number(origin)),f("target_province_id",number(target)),f("source_snapshot_id",snapshot.get("snapshot_id")),f("source_native_revision",snapshot.get("native_revision")),f("source_date_raw",snapshot.get("date_raw")),
                    f("contact_free_proven",new Bool(false)),f("offensive_combat_permission",new Bool(false)),f("battle_outcome_inferred",new Bool(false)),f("war_or_material_credit",new Bool(false))));
        if(activeSubject||!activeDefenders.isEmpty()) {
            Optional<Obj> comparison=activeSubject?Objects.requireNonNull(activeComparison.observe(request)):Optional.empty();
            return obj(f("policy",text("general-battle-forecast-v1")),f("phase",text("native_war_active_combat_resume_unavailable")),f("selected_step",Nil.INSTANCE),f("reason",text("an observed participant is already in combat; fixed-contact inputs cannot estimate its ongoing battle")),
                    f("baseline_phase",nullable(baseline.get("phase"))),f("baseline_selected_step",nullable(baseline.get("selected_step"))),f("active_combat_forecast_status",text(comparison.isPresent()?"provisional_observed_comparison":"unavailable")),f("provisional_combat_comparison",comparison.<Value>map(v->v).orElse(Nil.INSTANCE)),
                    f("active_combat_subject_army_id",activeSubject?number(subject):Nil.INSTANCE),f("active_combat_defender_army_ids",numbers(activeDefenders)),f("required_observation",text("same-frame-active-combat-resume-inputs")));
        }
        if(baseline.members().containsKey("provisional_forecast")||baseline.members().containsKey("qualified_forecast")||origin==null||origin==target||defenders.isEmpty())return baseline;
        List<Integer> attackers=List.of(subject);Obj projection=null;Integer constructor=null,entry=null;
        Obj encounter=encounter(target,attackers,defenders,null,null,false);
        Optional<RouteReroutePolicy.Preview> found=freshPreview(request,army,target);
        if(found.isEmpty())return bounded(baseline,"native_war_general_battle_route_query",advertisedStep(request,"preview-move-army-"+subject+"-to-"+target),"read the current native route before forecasting an observed enemy contact",encounter,empty());
        RouteReroutePolicy.Preview preview=found.orElseThrow();Obj previewJson=previewDocument(preview);
        List<Integer> route=MilitaryRouteGeometry.remaining(preview.routeProvinceIds(),origin);
        if(preview.status()!=RouteReroutePolicy.PreviewStatus.AVAILABLE||route.isEmpty()||route.getLast()!=target)return bounded(baseline,"native_war_general_battle_route_blocked",null,"the current native route is not an exact route to the contact",encounter,obj(f("route_preview",previewJson)));
        entry=route.size()>1?route.get(route.size()-2):origin;
        List<Integer> hostileIds=hostiles(request);
        if(hostileIds.isEmpty()||hostileIds.size()>64)return bounded(baseline,"native_war_general_battle_roster_blocked",null,"the observed hostile roster exceeds the route query contract",encounter,empty());
        MilitaryTimeline.Query query=new MilitaryTimeline.Query(subject,origin,target,hostileIds,preview.routeProvinceIds());
        var lookup=MilitaryTimeline.fresh(request,query);
        if(!(lookup instanceof MilitaryTimeline.Found full))return bounded(baseline,"native_war_general_battle_contact_query",advertisedStep(request,query.step()),"read all possible hostile contacts on the proposed route",encounter,obj(f("route_preview",previewJson)));
        MilitaryTimeline.Horizon contact=full.horizon();Obj contactJson=contact.original();
        List<Integer> finalDefenders=defenders;
        if(contact.nativeConflicts().stream().anyMatch(c->!(c instanceof MilitaryTimeline.SameProvince same)||same.provinceId()!=target||!finalDefenders.contains(same.hostileId())))
            return bounded(baseline,"native_war_general_battle_contact_blocked",null,"another encounter can occur before the simulated target battle",encounter,obj(f("route_preview",previewJson),f("route_contact_horizon",contactJson)));
        if(route.size()!=1)return shortHop(request,baseline,army,target,route,hostileIds,contact,previewJson,encounter);
        if(request.observations().bridgeCapabilities().contains(PROJECTED_CAPABILITY)) {
            var input=projectionInput(request,army,target,entry);var choice=ProjectedContactPolicy.select(input.snapshot(),input.queryRows(),input.request());
            if(choice instanceof ProjectedContactPolicy.QueryRequired missing)return bounded(baseline,"native_war_general_battle_projected_contact_query",missing.key().step(),"read native current target contact roles before selecting endpoint battle participants",encounter,obj(f("route_preview",previewJson),f("route_contact_horizon",contactJson)));
            var available=(ProjectedContactPolicy.Available)choice;var actual=available.projection();projection=OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(ProjectedContactCodec.encodeScope(actual))),"native projection");
            attackers=actual.attackerArmyIds();defenders=actual.defenderArmyIds();
            encounter=encounter(target,attackers,defenders,null,null,false);
            if(actual.transition()==ProjectedContactPolicy.Transition.NONE)return bounded(baseline,"native_war_general_battle_projected_no_contact",advertisedStep(request,"move-army-"+subject+"-to-"+target),"native current target projection selects no encounter; retain the ordinary one-hop move",encounter,obj(f("projected_contact_scope",projection),f("route_preview",previewJson),f("route_contact_horizon",contactJson),f("general_battle_forecast_used_for_decision",new Bool(false)),f("future_contact_authorized",new Bool(false))));
            if(actual.transition()==ProjectedContactPolicy.Transition.JOIN_EXISTING)return bounded(baseline,"native_war_active_combat_resume_unavailable",null,"native target selects an existing Combat; a new fixed-contact forecast cannot resume it",encounter,obj(f("projected_contact_scope",projection),f("required_observation",text("same-frame-active-combat-resume-inputs"))));
            if(!available.incomingAttackerGeometryReady()){entry=null;constructor=0;}
        }
        encounter=encounter(target,attackers,defenders,entry,constructor,false);
        CombatRequest modelRequest=new CombatRequest(target,entry,attackers,defenders,constructor);
        boolean v3=request.observations().bridgeCapabilities().contains(CombatPhaseInputsCodec.CAPABILITY);
        String capability=v3?CombatPhaseInputsCodec.CAPABILITY:CombatRequest.CAPABILITY,step=v3?CombatPhaseInputsCodec.toStep(modelRequest):modelRequest.toStep();
        Optional<? extends CombatObservationCache.Observation> cached=v3?cache.projectV3(OpportunityJson.toNode(snapshot),request.before().frame().episodeRunId()):cache.projectV2(OpportunityJson.toNode(snapshot),request.before().frame().episodeRunId());
        Obj extras=obj(f("route_preview",previewJson),f("route_contact_horizon",contactJson));if(projection!=null)extras=put(extras,"projected_contact_scope",projection);
        if(!request.observations().bridgeCapabilities().contains(capability)||cached.isEmpty()||!cached.orElseThrow().request().equals(modelRequest)||!queryWitness(request,modelRequest,v3,cached.orElseThrow().status().wire()))
            return bounded(baseline,"native_war_general_battle_inputs_query",request.observations().bridgeCapabilities().contains(capability)?step:null,"obtain same-frame per-regiment inputs for this encounter",encounter,extras);
        FixedContactForecast.Forecast forecast=cached.orElseThrow().forecast(FixedContactForecast.DEFAULT_SAMPLE_COUNT,FixedContactForecast.DEFAULT_HORIZON_DAYS);
        var admission=FixedContactForecast.contactAdmission(forecast);Obj forecastJson=OpportunityJson.object(OpportunityJson.parse(CombatJson.canonical(forecast.toJson())),"forecast"),admissionJson=OpportunityJson.object(OpportunityJson.parse(CombatJson.canonical(admission.toJson())),"admission");
        Obj model=obj(f("battle_forecast",forecastJson),f("contact_admission",admissionJson));if(projection!=null)model=put(model,"projected_contact_scope",projection);
        if(!admission.admitted())return bounded(baseline,"native_war_general_battle_model_rejected",null,"the bounded whole-battle model exceeds the configured contact risk budget",encounter,model);
        List<Integer> allParticipants=new ArrayList<>(attackers);allParticipants.addAll(defenders);
        List<Integer> inbound=enemies.stream().filter(a->!Integer.valueOf(target).equals(a.current())&&!"retreating".equals(a.tacticalState())&&a.route().isPresent()&&a.route().orElseThrow().contains(target)&&!allParticipants.contains(a.id())).map(Army::id).distinct().sorted().toList();
        if(!inbound.isEmpty())return bounded(baseline,"native_war_general_battle_observed_inbound_reinforcement",null,"an unmodeled hostile army has a same-frame native route through the contact province",encounter,merge(model,obj(f("observed_unmodeled_inbound_enemy_army_ids",numbers(inbound)),f("inbound_arrival_before_battle_resolution_proven",new Bool(false)))));
        List<Integer> arrivals=contact.subject().arrivalDates();Integer arrival=arrivals.isEmpty()?null:arrivals.getLast();int date=contact.dateRaw();
        if(arrival==null||arrival<=date)return bounded(baseline,"native_war_general_battle_arrival_blocked",null,"the single-step contact has no valid future arrival date",encounter,model);
        if((long)arrival>(long)date+24) {
            List<Obj> wars=wars(request);Obj war=wars.size()==1?wars.getFirst():null;
            boolean oneWar=war!=null&&optionalInt(war.get("war_id"))!=null&&id(war.get("war_id"))>0&&war.get("allied_armies") instanceof Arr
                    &&rows(war.get("allied_armies")).stream().filter(a->yes(a.get("controllable"))&&number(subject).equals(a.get("army_id"))&&number(origin).equals(a.get("current_province_id"))).count()==1
                    &&war.get("enemy_armies") instanceof Arr&&rows(war.get("enemy_armies")).stream().map(MilitaryPlanInputs::army).filter(a->!"retreating".equals(a.tacticalState())).map(Army::id).distinct().sorted().toList().equals(hostileIds);
            boolean routeExact=contact.subject().armyId()==subject&&contact.subject().currentProvinceId()==origin&&contact.subject().provinceIds().equals(List.of(target))&&arrivals.equals(List.of(arrival));
            String move=advertisedStep(request,"move-army-"+subject+"-to-"+target);
            if(!oneWar||!routeExact||!contact.oneDayFree()||!contact.nativeConflicts().isEmpty()||move==null)return bounded(baseline,"native_war_general_battle_arrival_blocked",null,"the distant single-step contact lacks an exact, contact-free first-day route order",encounter,put(model,"future_arrival_date_raw",number(arrival)));
            return bounded(baseline,"native_war_general_battle_distant_route_start",move,"start the exact one-hop route; recheck every day and forecast the future contact again",encounter,merge(model,obj(f("future_arrival_date_raw",number(arrival)),f("source_war_id",war.get("war_id")),f("contact_recheck_required_before_each_day",new Bool(true)),f("future_contact_authorized",new Bool(false)),f("general_battle_forecast_used_for_decision",new Bool(true)))));
        }
        Obj result=merge(baseline,obj(f("encounter",encounter(target,attackers,defenders,entry,constructor,true)),f("general_battle_forecast",forecastJson),f("general_battle_contact_admission",admissionJson),f("general_battle_forecast_used_for_decision",new Bool(true))));
        return projection==null?result:put(result,"projected_contact_scope",projection);
    }
    private static Obj shortHop(PlanningRequest request,Obj baseline,Army army,int target,List<Integer> route,List<Integer> hostiles,MilitaryTimeline.Horizon contact,Obj preview,Obj encounter) {
        Obj extras=obj(f("route_preview",preview),f("route_contact_horizon",contact.original()));
        if(!contact.oneDayFree())return bounded(baseline,"native_war_general_battle_short_route_blocked",null,"the first travel day has another possible contact",encounter,extras);
        int hop=route.getFirst(),origin=army.current();var first=freshPreview(request,army,hop);
        if(first.isEmpty())return bounded(baseline,"native_war_general_battle_short_preview",advertisedStep(request,"preview-move-army-"+army.id()+"-to-"+hop),"prove an exact first waypoint before a distant predicted contact",encounter,extras);
        var observed=first.orElseThrow();Obj firstJson=previewDocument(observed);
        if(observed.status()!=RouteReroutePolicy.PreviewStatus.AVAILABLE||!MilitaryRouteGeometry.remaining(observed.routeProvinceIds(),origin).equals(List.of(hop)))return bounded(baseline,"native_war_general_battle_short_preview_blocked",null,"the first waypoint does not have an exact one-hop route",encounter,obj(f("route_preview",firstJson),f("route_contact_horizon",contact.original())));
        var query=new MilitaryTimeline.Query(army.id(),origin,hop,hostiles,List.of(hop));var lookup=MilitaryTimeline.fresh(request,query);
        if(!(lookup instanceof MilitaryTimeline.Found found))return bounded(baseline,"native_war_general_battle_short_contact_query",advertisedStep(request,query.step()),"prove the first waypoint has no near-term hostile contact",encounter,obj(f("route_preview",firstJson),f("route_contact_horizon",contact.original())));
        var horizon=found.horizon();String move=advertisedStep(request,"move-army-"+army.id()+"-to-"+hop);
        if(!horizon.oneDayFree()||!horizon.nativeConflicts().isEmpty()||move==null)return bounded(baseline,"native_war_general_battle_short_contact_blocked",null,"the first waypoint is not proved contact-free",encounter,obj(f("route_preview",firstJson),f("route_contact_horizon",horizon.original())));
        return bounded(baseline,"native_war_general_battle_short_move",move,"move one proved contact-free waypoint and refresh the battle estimate next turn",encounter,obj(f("route_preview",firstJson),f("route_contact_horizon",horizon.original()),f("general_battle_forecast_used_for_decision",new Bool(false)),f("future_contact_authorized",new Bool(false))));
    }
    private static ProjectedContactCodec.Input projectionInput(PlanningRequest request,Army army,int target,int entry) {
        int latest=latestAdvanceIndex(request);List<Obj> rows=new ArrayList<>();
        for(Obj row:afterRestore(request.observations().history()))if(index(row)>latest)rows.add(obj(f("step",nullable(command(row)==null?null:text(command(row)))),f("ok",nullable(row.get("ok"))),f("result",nullable(result(row)))));
        Obj body=obj(f("snapshot",request.observations().snapshot()),f("query_rows",objects(rows)),f("request",obj(f("subject_army_id",number(army.id())),f("target_province_id",number(target)),f("incoming_entry_province_id",number(entry)),f("subject_current_province_id",number(army.current())),f("subject_owner_character_id",army.owner()==null?Nil.INSTANCE:number(army.owner())))));
        return ProjectedContactCodec.decode(OpportunityJson.encode(body));
    }
    private static boolean queryWitness(PlanningRequest request,CombatRequest expected,boolean v3,String status) {
        int latest=latestAdvanceIndex(request);Obj snapshot=request.observations().snapshot();
        for(Obj row:afterRestore(request.observations().history())) {
            if(!yes(row.get("ok"))||index(row)<=latest)continue;
            Optional<CombatRequest> parsed=v3?CombatPhaseInputsCodec.parseStep(command(row)):CombatRequest.parseStep(command(row));Obj result=result(row);
            if(parsed.equals(Optional.of(expected))&&result!=null&&Objects.equals(result.get("queried_snapshot_id"),snapshot.get("snapshot_id"))&&Objects.equals(result.get("queried_revision"),snapshot.get("revision"))
                    &&Objects.equals(result.get("queried_native_revision"),snapshot.get("native_revision"))&&new Text(status).equals(result.get("status")))return true;
        }
        return false;
    }
    private static int latestAdvanceIndex(PlanningRequest request){int latest=0;for(Obj row:request.observations().history())if(WarHistorySteps.isLifeAdvance(command(row)))latest=Math.max(latest,index(row));return latest;}
    private static int index(Obj row){Integer value=optionalInt(row.get("index"));return value==null?0:value;}
    private static boolean enemyBattleObserver(PlanningRequest request,Obj baseline,Army army,int target) {
        Obj snapshot=request.observations().snapshot();Obj actor=snapshot.get("played_character") instanceof Obj a?a:empty();
        boolean modal=snapshot.get("top_exclusive_modal_choice_hint") instanceof Obj hint&&new Text("present").equals(hint.get("status"));
        return new Text("native_war_pursuit").equals(baseline.get("phase"))&&yes(snapshot.get("map_ready"))&&nil(snapshot.get("active_event"))&&nil(snapshot.get("pending_character_interaction"))&&!modal&&yes(actor.get("alive"))
                &&actor.get("character_id") instanceof IntegerValue&&Objects.equals(army.raw().get("owner_character_id"),actor.get("character_id"))&&army.controllable()
                &&army.current()!=null&&army.current()>0&&army.current()!=target&&army.explicitIdle()&&request.observations().bridgeCapabilities().containsAll(CLOCK_CAPABILITIES)
                &&List.of("life-advance-one-day","set-speed-1","resume-map","pause-map").stream().allMatch(step->advertised(request,step));
    }
    private static boolean nil(Value value){return value==null||value==Nil.INSTANCE;}
    private static boolean readOnly(String step){return step.startsWith("query-")||step.startsWith("preview-move-army-");}
    private static String advertisedStep(PlanningRequest request,String step){return advertised(request,step)?step:null;}
    private static Obj encounter(int target,List<Integer> attackers,List<Integer> defenders,Integer entry,Integer constructor,boolean full) {
        Obj value=obj(f("target_province_id",number(target)),f("attacker_army_ids",numbers(attackers)),f("defender_army_ids",numbers(defenders)));
        if(full||constructor!=null)value=put(value,"attacker_entry_province_id",entry==null?Nil.INSTANCE:number(entry));
        if(constructor!=null)value=merge(value,obj(f("contact_geometry_mode",text("native_defender_constructor_zero")),f("constructor_adjacency_kind_raw",number(constructor))));return value;
    }
    private static Obj bounded(Obj baseline,String phase,String step,String reason,Obj encounter,Obj extras) {
        return merge(obj(f("policy",text("general-battle-forecast-v1")),f("phase",text(phase)),f("selected_step",step==null?Nil.INSTANCE:text(step)),f("reason",text(reason)),
                f("baseline_phase",nullable(baseline.get("phase"))),f("baseline_selected_step",nullable(baseline.get("selected_step"))),f("encounter",encounter)),extras);
    }
}

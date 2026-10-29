package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;
import org.xar.ck3.control.wave2.military.combatwire.CombatRequest;
import org.xar.ck3.control.wave2.military.combatwire.CombatPhaseInputsCodec;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegeCodec;
import org.xar.ck3.control.wave2.military.realmsiege.RealmSiegePolicy;
import org.xar.ck3.control.wave3.military.routereroute.RouteReroutePolicy;

/** Complete strategy18130..18942 siege ingress. It selects plans only through the ordinary GeneralBattleForecastPolicy caller. */
public final class PrimaryDefenderSiegePolicy implements GeneralBattleForecastPolicy.PrimaryDefenderSiegeIngress {
    private static final Set<String> PHASES=Set.of("native_war_no_safe_exact_route","native_war_stationary_objective_hold_sentinel","native_war_reconnaissance",
            "native_war_route_preview","native_war_route_preview_unsupported","native_war_pursuit","native_war_pursuit_progress");
    private final CombatObservationCache cache;
    private final WarStrengthRelief.MovementEvidence movement;
    private final WarStrengthRelief.BattleControlPort battle;
    public PrimaryDefenderSiegePolicy(CombatObservationCache sameCache,WarStrengthRelief.MovementEvidence movement,WarStrengthRelief.BattleControlPort battle) {
        cache=Objects.requireNonNull(sameCache);this.movement=Objects.requireNonNull(movement);this.battle=Objects.requireNonNull(battle);
    }
    private record Context(PlanningRequest request,Obj snapshot,Obj baseline,Obj candidate,Army army,int warId,int target,int origin,
            List<Integer> route,Obj preview,MilitaryTimeline.Horizon contact,List<Integer> hostiles,Obj evidence) {
        Context {route=List.copyOf(route);hostiles=List.copyOf(hostiles);}
    }
    @Override public Obj review(PlanningRequest request,Obj baseline) {
        Objects.requireNonNull(request);Objects.requireNonNull(baseline);Obj s=request.observations().snapshot();String phase=optionalText(baseline.get("phase"));
        if(!yes(s.get("paused"))||!PHASES.contains(Objects.toString(phase,""))||!(s.get("active_wars") instanceof Arr)||!(s.get("player_armies") instanceof Arr))return baseline;
        List<Army> controlled=rows(s.get("player_armies")).stream().map(MilitaryPlanInputs::army).filter(Army::controllable).toList();
        if(controlled.size()!=1)return baseline;Army army=controlled.getFirst();
        Obj candidate=WarStrengthRelief.assess(request,new WarStrengthRelief.ContactFacts(request.before(),controlled,Optional.of(army),Optional.empty()),movement,battle);
        if(!new Text("forecast_required").equals(candidate.get("status")))return baseline;
        Integer armyId=optionalInt(candidate.get("army_id")),warId=optionalInt(candidate.get("war_id")),target=optionalInt(candidate.get("target_province_id")),origin=army.current();
        if(armyId==null||warId==null||target==null||origin==null||armyId!=army.id())return baseline;
        List<Obj> wars=wars(request);Obj war=wars.stream().filter(row->number(warId).equals(row.get("war_id"))).findFirst().orElse(null);
        if(("native_war_route_preview".equals(phase)||"native_war_route_preview_unsupported".equals(phase))) {
            Integer previewTarget=baseline.get("route_preview") instanceof Obj p?optionalInt(p.get("target_province_id")):null;
            if(!Objects.equals(previewTarget,target)&&!(nonleadingRealmSiege(request,warId)
                    &&("native_war_route_preview".equals(phase)&&previewTarget!=null&&previewTarget>0
                    &&new Text(previewStep(army.id(),previewTarget)).equals(baseline.get("selected_step"))
                    ||"native_war_route_preview_unsupported".equals(phase)&&baseline.get("selected_step")==Nil.INSTANCE)))return baseline;
        }
        if("native_war_pursuit".equals(phase)||"native_war_pursuit_progress".equals(phase)) {
            boolean matches=baseline.get("pursuit") instanceof Obj p&&number(warId).equals(p.get("war_id"))&&number(target).equals(p.get("target_province_id"));
            if(!matches&&!("native_war_pursuit_progress".equals(phase)&&new Text("life-advance").equals(baseline.get("selected_step"))))return baseline;
        }
        Obj evidence=obj(f("siege_relief",candidate),f("baseline_phase",text(phase)),f("baseline_selected_step",nullable(baseline.get("selected_step"))),
                f("forecast_status",text("research_only")),f("active_attack_allowed",new Bool(false)));
        if(origin.equals(target))return blocked(evidence,"the subject is already at the hostile siege; a route-entry encounter cannot be inferred","fresh-route-entry-and-contact-scope",empty());
        var found=freshPreview(request,army,target);String step=previewStep(army.id(),target);
        if(found.isEmpty())return advertised(request,step)?plan("native_war_siege_forecast_route_preview",step,"read the route to the observed enemy siege before deriving its battle entry Province",evidence):blocked(evidence,"the exact route preview is unavailable",step,empty());
        var nativePreview=found.orElseThrow();Obj preview=previewDocument(nativePreview);List<Integer> route=nativePreview.routeProvinceIds();
        if(nativePreview.status()!=RouteReroutePolicy.PreviewStatus.AVAILABLE||route.isEmpty()||route.getLast().intValue()!=target.intValue())
            return blocked(evidence,"the native preview does not prove a complete route into the siege Province","fresh-complete-siege-route-preview",obj(f("route_preview",preview)));
        int entry=route.size()>1?route.get(route.size()-2):origin;
        if(entry==target)return blocked(evidence,"the route does not identify a distinct final entry Province","exact-adjacent-attacker-entry",obj(f("route_preview",preview)));
        List<Integer> hostiles=hostiles(request);
        if(hostiles.isEmpty()||hostiles.size()>64)return blocked(evidence,"the full hostile contact roster is unavailable","complete-hostile-contact-roster",empty());
        var query=new MilitaryTimeline.Query(army.id(),origin,target,hostiles,route);var contactLookup=MilitaryTimeline.fresh(request,query);
        if(!(contactLookup instanceof MilitaryTimeline.Found full))return advertised(request,query.step())?plan("native_war_siege_forecast_contact_query",query.step(),
                "read the full hostile contact timeline before forming a hypothetical siege battle input",merge(evidence,obj(f("route_preview",preview)))):
                blocked(evidence,"the exact route contact query is unavailable",query.step(),empty());
        var contact=full.horizon();boolean targetOnly=targetOnly(war,target,contact);
        if(!contact.oneDayFree()&&!targetOnly)return blocked(evidence,"contact can occur outside the proposed siege encounter; this target forecast would not cover it","contact-safe-entry-to-siege-target",obj(f("route_preview",preview),f("route_contact_horizon",contact.original())));
        Obj balance=candidate.get("army_strength_balance") instanceof Obj row?row:null;
        var partition=SiegeForecastParticipantPartition.partition(war,balance,contact,army.id(),target);
        Context context=new Context(request,s,baseline,candidate,army,warId,target,origin,route,preview,contact,hostiles,evidence);
        if(partition instanceof SiegeForecastParticipantPartition.Unavailable unavailable) {
            if(unavailable.reason()==SiegeForecastParticipantPartition.Reason.OFFSITE_HOSTILE_MAY_JOIN_BY_TARGET_ENTRY
                    ||unavailable.reason()==SiegeForecastParticipantPartition.Reason.STRENGTH_OR_CONTACT_ROSTER_MISMATCH)return uncertainWaypoint(context,partition.toJson());
            return blocked(evidence,"the observed siege does not prove a complete one-encounter participant partition","exact-attacker-defender-participant-scope",
                    obj(f("route_preview",preview),f("route_contact_horizon",contact.original()),f("participant_partition",partition.toJson())));
        }
        var scope=(SiegeForecastParticipantPartition.Available)partition;
        evidence=put(evidence,"participant_partition",scope.toJson());context=new Context(request,s,baseline,candidate,army,warId,target,origin,route,preview,contact,hostiles,evidence);
        var encounter=new CombatRequest(target,entry,List.of(army.id()),scope.defenderArmyIds(),null);boolean v3=request.observations().bridgeCapabilities().contains(CombatPhaseInputsCodec.CAPABILITY);
        String capability=v3?CombatPhaseInputsCodec.CAPABILITY:CombatRequest.CAPABILITY,inputStep=v3?CombatPhaseInputsCodec.toStep(encounter):encounter.toStep();
        boolean attempted=false;List<Obj> history=afterRestore(request.observations().history());int lastAdvance=latestAdvance(request);
        for(int i=history.size()-1;i>=0;i--) {
            Obj row=history.get(i);Optional<CombatRequest> parsed=v3?CombatPhaseInputsCodec.parseStep(command(row)):CombatRequest.parseStep(command(row));
            if(!parsed.equals(Optional.of(encounter)))continue;
            Integer index=optionalInt(row.get("index"));attempted=index!=null&&index>lastAdvance;Obj result=result(row);
            if(result==null||!sameInputFrame(s,result))break;
            Optional<? extends CombatObservationCache.Observation> cached=v3?cache.projectV3(OpportunityJson.toNode(s),request.before().frame().episodeRunId()):cache.projectV2(OpportunityJson.toNode(s),request.before().frame().episodeRunId());
            if(cached.isEmpty()||!cached.orElseThrow().request().equals(encounter)||!new Text(cached.orElseThrow().status().wire()).equals(result.get("status")))
                return blocked(evidence,"the selected input query returned but its generation-bound cached readback is absent or mismatched","fresh-v"+(v3?3:2)+"-cache-readback",obj(f("route_preview",preview),f("route_contact_horizon",contact.original())));
            var actual=cached.orElseThrow();Obj qualified=SiegeForecastAssessments.qualified(s,warId,army.id(),target,entry,scope.defenderArmyIds(),contact.oneDayFree()||targetOnly);
            Integer arrival=contact.subject().arrivalDates().isEmpty()?null:contact.subject().arrivalDates().getLast();int date=contact.dateRaw();
            if(new Text("ready").equals(qualified.get("status"))) {
                Obj trial=obj(f("qualified_forecast",qualified));
                if(route.size()>1)return shortWaypoint(context,trial,true);
                if(!scope.offsiteHostileArmyIds().isEmpty()||arrival==null||arrival<=date||(long)arrival>(long)date+24)
                    return blocked(evidence,"the qualified encounter is not a proved one-day direct contact","one-day-target-entry-horizon-and-complete-participants",trial);
                String move=moveStep(army.id(),target);
                if(!advertised(request,move))return blocked(evidence,"the qualified forecast has no advertised typed move action",move,trial);
                return plan("native_war_siege_forecast_move",move,"the same-frame qualified combat forecast favors immediate siege relief over avoid and wait/reinforce within its risk limits",
                        merge(evidence,obj(f("route_preview",preview),f("route_contact_horizon",contact.original()),f("qualified_forecast",qualified),f("forecast_status",text("qualified")),f("active_attack_allowed",new Bool(true)))));
            }
            BigInteger friendly=OpportunityJson.integer(Objects.requireNonNull(balance).get("friendly_current_soldiers"),"friendly_current_soldiers");
            Obj provisional=SiegeForecastAssessments.provisional(s,encounter,friendly,actual);
            if(scope.defenderArmyIds().size()==1&&new Text("provisional_admissible").equals(provisional.get("status"))) {
                Context currentContext=context;
                List<Obj> terminal=s.get("war_termination_options") instanceof Arr rows?rows(rows).stream().filter(option->sameTermination(currentContext,option)).toList():List.of();
                if(terminal.size()!=1) {
                    String terminalStep="query-war-termination-options-"+warId;
                    return advertised(request,terminalStep)?plan("native_war_provisional_defense_terminal_query",terminalStep,"compare same-frame war exits before a provisional relief march",merge(evidence,obj(f("provisional_forecast",provisional)))):
                            blocked(evidence,"same-frame war exit options are unavailable",terminalStep,obj(f("provisional_forecast",provisional)));
                }
                if(!(terminal.getFirst().get("options") instanceof Obj options))return blocked(evidence,"same-frame war exit options are incomplete","complete-same-frame-war-termination-options",obj(f("provisional_forecast",provisional)));
                if(safeExit(options))return blocked(evidence,"a legal, observable and accepted noncombat war exit is available","compare-or-select-safe-war-termination",obj(f("provisional_forecast",provisional)));
                Obj surrender=options.get("surrender") instanceof Obj option?option:empty();
                Obj trial=obj(f("provisional_forecast",provisional),f("terminal_comparison",obj(f("war_id",number(warId)),f("safe_noncombat_exit_available",new Bool(false)),f("surrender_terms_observable",nullable(surrender.get("terms_observable"))))),
                        f("model_error_policy",text("reobserve_route_roster_and_simulation_before_contact")),f("qualified_forecast",qualified));
                if(route.size()==1&&targetOnly&&scope.offsiteHostileArmyIds().isEmpty()&&arrival!=null&&date<arrival&&(long)arrival<=(long)date+24) {
                    String move=moveStep(army.id(),target);if(!advertised(request,move))return blocked(evidence,"typed contact move is unavailable",move,trial);
                    return plan("native_war_provisional_defense_contact_move",move,"fresh same-frame research trial admits one immediate siege contact within its provisional loss budget",
                            merge(merge(evidence,trial),obj(f("route_preview",preview),f("route_contact_horizon",contact.original()),f("forecast_status",text("provisional_trial")),f("active_attack_allowed",new Bool(true)))));
                }
                return shortWaypoint(context,trial,false);
            }
            boolean research=new Text("same_frame_encounter_scope_mismatch").equals(provisional.get("status"))
                    ||new Text("multi_defender_research_only").equals(provisional.get("status"))&&no(provisional.get("planner_usable"));
            if(new Text("producer_unavailable").equals(qualified.get("status"))&&research&&yes(result.get("accepted"))&&new Text("available").equals(result.get("status"))
                    &&scope.defenderArmyIds().size()>1&&route.size()>1&&route.getFirst().intValue()!=origin.intValue()&&route.getFirst().intValue()!=target.intValue()&&oneDayFree(contact,date)&&wars.size()==1&&controlled.size()==1&&rows(s.get("player_armies")).size()==1) {
                Obj possible=researchFirstHop(context,qualified,provisional);if(possible!=null)return possible;
            }
            Obj normalized=DriverJson.object(actual.normalizedJson().toString().getBytes(java.nio.charset.StandardCharsets.UTF_8),DriverJson.MAX_NATIVE_BYTES);
            Obj completeness=normalized.get("completeness") instanceof Obj complete?complete:empty();
            return blocked(evidence,"the selected combat input readback has no admitted battle forecast authorizing contact","qualified-same-frame-combat-forecast-and-expected-utility",
                    obj(f("phase",text("native_war_siege_forecast_inputs_observed")),f("route_preview",preview),f("route_contact_horizon",contact.original()),f("qualified_forecast",qualified),f("provisional_forecast",provisional),
                    f("combat_inputs_v"+(v3?3:2)+"_query",obj(f("step",text(inputStep)),f("accepted",nullable(result.get("accepted"))),f("status",nullable(result.get("status"))),f("queried_snapshot_id",nullable(result.get("queried_snapshot_id"))),
                            f("queried_revision",nullable(result.get("queried_revision"))),f("queried_native_revision",nullable(result.get("queried_native_revision"))),f("monte_carlo_ready",nullable(completeness.get("monte_carlo_ready"))),f("planner_usable",nullable(completeness.get("planner_usable")))))));
        }
        if(attempted)return blocked(evidence,"the same siege input query was already attempted in this date epoch without a reusable current-frame result","fresh-v"+(v3?3:2)+"-query-after-state-change",obj(f("route_preview",preview),f("route_contact_horizon",contact.original())));
        if(!request.observations().bridgeCapabilities().contains(capability))return blocked(evidence,"the selected combat input read-only query is unavailable",inputStep,empty());
        return plan("native_war_siege_forecast_inputs_query",inputStep,"read exact same-frame combat inputs for the observed siege encounter; no attack is authorized",merge(evidence,obj(f("route_preview",preview),f("route_contact_horizon",contact.original()))));
    }
    private static Obj uncertainWaypoint(Context c,Obj partition) {
        Obj uncertain=obj(f("route_preview",c.preview()),f("route_contact_horizon",c.contact().original()),f("participant_partition",partition),f("forecast_status",text("participant_scope_unresolved")),f("active_attack_allowed",new Bool(false)));
        if(c.route().size()<=1||!c.contact().oneDayFree()||!c.contact().nativeConflicts().isEmpty())return blocked(c.evidence(),"future target participants are unknown and no contact-free first segment is proved","fresh-contact-free-first-segment",uncertain);
        int hop=c.route().getFirst();String previewStep=previewStep(c.army().id(),hop);var preview=freshPreview(c.request(),c.army(),hop);
        if(preview.isEmpty())return advertised(c.request(),previewStep)?plan("native_war_siege_uncertain_first_hop_preview",previewStep,"read a first-hop route without committing the unresolved siege contact",merge(c.evidence(),uncertain)):
                blocked(c.evidence(),"first-hop route preview is unavailable",previewStep,uncertain);
        Obj shortPreview=previewDocument(preview.orElseThrow());
        if(preview.orElseThrow().status()!=RouteReroutePolicy.PreviewStatus.AVAILABLE||!preview.orElseThrow().routeProvinceIds().equals(List.of(hop)))return blocked(c.evidence(),"first-hop preview has another route","exact-one-hop-preview",put(uncertain,"short_route_preview",shortPreview));
        var query=new MilitaryTimeline.Query(c.army().id(),c.origin(),hop,c.hostiles(),List.of(hop));var found=MilitaryTimeline.fresh(c.request(),query);
        if(!(found instanceof MilitaryTimeline.Found shortFull))return advertised(c.request(),query.step())?plan("native_war_siege_uncertain_first_hop_contact_query",query.step(),"read next-day full-hostile contact safety for the first segment",merge(merge(c.evidence(),uncertain),obj(f("short_route_preview",shortPreview)))):
                blocked(c.evidence(),"first-hop contact query is unavailable",query.step(),put(uncertain,"short_route_preview",shortPreview));
        var shortContact=shortFull.horizon();Obj detail=merge(uncertain,obj(f("short_route_preview",shortPreview),f("short_route_contact_horizon",shortContact.original())));
        if(!shortContact.oneDayFree()||!shortContact.nativeConflicts().isEmpty())return blocked(c.evidence(),"the first segment has a possible next-day contact","contact-free-first-segment",detail);
        if(shortContact.hostiles().size()!=c.hostiles().size()||!shortContact.hostileIds().equals(c.hostiles())||c.hostiles().stream().anyMatch(id->{
            var a=c.contact().hostiles().stream().filter(route->route.armyId()==id).findFirst();var b=shortContact.hostiles().stream().filter(route->route.armyId()==id).findFirst();
            return a.isEmpty()||b.isEmpty()||b.orElseThrow().currentProvinceId()<=0||a.orElseThrow().currentProvinceId()!=b.orElseThrow().currentProvinceId();}))
            return blocked(c.evidence(),"the first-hop contact query does not preserve the full hostile positions","same-frame-first-hop-hostile-roster",detail);
        String move=moveStep(c.army().id(),hop);if(!advertised(c.request(),move))return blocked(c.evidence(),"typed first-hop move is unavailable",move,detail);
        return plan("native_war_siege_uncertain_first_hop_move",move,"move one contact-free waypoint, then re-read the full hostile roster before any further advance",merge(merge(c.evidence(),detail),obj(f("daily_recheck_required",new Bool(true)))));
    }
    private static Obj shortWaypoint(Context c,Obj trial,boolean qualified) {
        if(c.route().size()<=1||!c.contact().oneDayFree()||!c.contact().nativeConflicts().isEmpty())return blocked(c.evidence(),"the route has no proved contact-free first segment","fresh-contact-free-first-segment",trial);
        int hop=c.route().getFirst();String previewStep=previewStep(c.army().id(),hop);var preview=freshPreview(c.request(),c.army(),hop);String prefix=qualified?"native_war_siege_forecast_short_":"native_war_provisional_defense_short_";
        if(preview.isEmpty())return advertised(c.request(),previewStep)?plan(prefix+"preview",previewStep,"read a first-hop route that cannot commit the distant siege contact",merge(trial,c.evidence())):
                blocked(c.evidence(),"first-hop route preview is unavailable",previewStep,trial);
        Obj shortPreview=previewDocument(preview.orElseThrow());
        if(preview.orElseThrow().status()!=RouteReroutePolicy.PreviewStatus.AVAILABLE||!preview.orElseThrow().routeProvinceIds().equals(List.of(hop)))return blocked(c.evidence(),"first-hop preview has another route","exact-one-hop-preview",trial);
        var query=new MilitaryTimeline.Query(c.army().id(),c.origin(),hop,c.hostiles(),List.of(hop));var found=MilitaryTimeline.fresh(c.request(),query);
        if(!(found instanceof MilitaryTimeline.Found shortFull))return advertised(c.request(),query.step())?plan(prefix+"contact_query",query.step(),"read next-day contact safety for the short relief segment",merge(merge(trial,c.evidence()),obj(f("short_route_preview",shortPreview)))):
                blocked(c.evidence(),"first-hop contact query is unavailable",query.step(),trial);
        var contact=shortFull.horizon();if(!contact.oneDayFree()||!contact.nativeConflicts().isEmpty())return blocked(c.evidence(),"the first segment has a possible next-day contact","contact-free-first-segment",put(trial,"short_route_contact_horizon",contact.original()));
        String move=moveStep(c.army().id(),hop);if(!advertised(c.request(),move))return blocked(c.evidence(),"typed first-hop move is unavailable",move,trial);
        return plan(prefix+"move",move,"move one proved contact-free waypoint and refresh the siege forecast next turn",merge(merge(trial,c.evidence()),
                obj(f("route_preview",c.preview()),f("route_contact_horizon",c.contact().original()),f("short_route_preview",shortPreview),f("short_route_contact_horizon",contact.original()),f("forecast_status",text(qualified?"qualified":"provisional_trial")),f("active_attack_allowed",new Bool(false)))));
    }
    private static Obj researchFirstHop(Context c,Obj qualified,Obj provisional) {
        int hop=c.route().getFirst();if(!advertised(c.request(),moveStep(c.army().id(),hop)))return null;
        Obj detail=merge(c.evidence(),obj(f("route_preview",c.preview()),f("route_contact_horizon",c.contact().original()),f("qualified_forecast",qualified),f("provisional_forecast",provisional)));
        String previewStep=previewStep(c.army().id(),hop);var preview=freshPreview(c.request(),c.army(),hop);
        if(preview.isEmpty()&&advertised(c.request(),previewStep)&&!attemptedThisDate(c.request(),previewStep))return plan("native_war_siege_first_hop_preview_query",previewStep,"collect the exact first-waypoint route as read-only research",detail);
        if(preview.isEmpty()||preview.orElseThrow().status()!=RouteReroutePolicy.PreviewStatus.AVAILABLE||!preview.orElseThrow().routeProvinceIds().equals(List.of(hop)))return blocked(c.evidence(),"the first-waypoint route preview is missing or mismatched","fresh-exact-first-hop-preview",obj(f("short_route_preview",preview.<Value>map(MilitaryPlanInputs::previewDocument).orElse(Nil.INSTANCE))));
        var query=new MilitaryTimeline.Query(c.army().id(),c.origin(),hop,c.hostiles(),List.of(hop));var contact=MilitaryTimeline.fresh(c.request(),query);
        if(!(contact instanceof MilitaryTimeline.Found)&&advertised(c.request(),query.step())&&!attemptedThisDate(c.request(),query.step()))return plan("native_war_siege_first_hop_contact_query",query.step(),"collect the same-frame full-hostile one-day first-waypoint timeline as read-only research",put(detail,"short_route_preview",previewDocument(preview.orElseThrow())));
        return null;
    }
    private static boolean targetOnly(Obj war,int target,MilitaryTimeline.Horizon contact) {
        if(war==null||!(war.get("enemy_armies") instanceof Arr))return false;
        Set<Integer> targetIds=rows(war.get("enemy_armies")).stream().map(MilitaryPlanInputs::army).filter(enemy->Integer.valueOf(target).equals(enemy.current())).map(Army::id).collect(java.util.stream.Collectors.toSet());
        return !contact.nativeConflicts().isEmpty()&&contact.nativeConflicts().stream().allMatch(conflict->conflict instanceof MilitaryTimeline.SameProvince same&&same.provinceId()==target&&targetIds.contains(same.hostileId()));
    }
    private static boolean nonleadingRealmSiege(PlanningRequest request,int war) {
        List<Obj> wars=wars(request);int index=-1;for(int i=0;i<wars.size();i++)if(number(war).equals(wars.get(i).get("war_id"))){index=i;break;}
        if(index<0)return false;
        Obj input=obj(f("schema",text(RealmSiegePolicy.INPUT_SCHEMA)),f("snapshot",request.observations().snapshot()),f("detached_wars",new Arr(List.of())),f("detached_enemies",new Arr(List.of())),
                f("candidate_war_ref",obj(f("collection",text("active_wars")),f("index",number(index)))),f("candidate_enemy_ref",Nil.INSTANCE));
        var actual=RealmSiegeCodec.decodeNode(OpportunityJson.toNode(input));return RealmSiegePolicy.warQualifies(actual.snapshot(),actual.candidateWar());
    }
    private static boolean sameInputFrame(Obj snapshot,Obj result) {return Objects.equals(snapshot.get("snapshot_id"),result.get("queried_snapshot_id"))&&Objects.equals(snapshot.get("revision"),result.get("queried_revision"))&&Objects.equals(snapshot.get("native_revision"),result.get("queried_native_revision"));}
    private static boolean sameTermination(Context c,Obj row) {
        Obj d=c.snapshot().get("diagnostics") instanceof Obj diagnostics?diagnostics:empty();
        return number(c.warId()).equals(row.get("war_id"))&&sameInputFrame(c.snapshot(),row)&&Objects.equals(d.get("connection_generation"),row.get("queried_connection_generation"))&&Objects.equals(c.snapshot().get("episode_run_id"),row.get("episode_run_id"));
    }
    private static boolean safeExit(Obj options) {return List.of("victory","white_peace").stream().anyMatch(name->options.get(name) instanceof Obj row&&yes(row.get("available"))&&yes(row.get("terms_observable"))&&(name.equals("victory")||row.get("recipient_response") instanceof Obj response&&yes(response.get("would_accept_now"))));}
    private static int latestAdvance(PlanningRequest request) {int latest=0;for(Obj row:request.observations().history())if(WarHistorySteps.isLifeAdvance(command(row))){Integer index=optionalInt(row.get("index"));if(index!=null)latest=Math.max(latest,index);}return latest;}
    public static boolean attemptedThisDate(PlanningRequest request,String step) {int latest=latestAdvance(request);return afterRestore(request.observations().history()).stream().anyMatch(row->{Integer index=optionalInt(row.get("index"));Obj result=result(row);return step.equals(command(row))&&index!=null&&index>latest&&(!yes(row.get("ok"))||result!=null&&sameLease(request,result));});}
    public static boolean oneDayFree(MilitaryTimeline.Horizon contact,int date) {return contact.horizonStart()==date&&(long)contact.horizonEnd()==(long)date+24&&contact.oneDayFree()&&contact.nativeConflicts().isEmpty();}
    private static String previewStep(int army,int target) {return "preview-move-army-"+army+"-to-"+target;}
    private static String moveStep(int army,int target) {return "move-army-"+army+"-to-"+target;}
    private static Obj plan(String phase,String step,String reason,Obj evidence) {return merge(obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("selected_step",text(step)),f("reason",text(reason))),evidence);}
    private static Obj blocked(Obj evidence,String reason,String required,Obj detail) {return merge(merge(obj(f("policy",text("one-life-turn-v1")),f("phase",text("native_war_siege_forecast_observation_blocked")),f("selected_step",Nil.INSTANCE),f("required_observation",text(required)),f("reason",text(reason))),evidence),detail);}
}

package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import static org.xar.ck3.control.application.planning.military.LateWarCoreInputs.is;
import static org.xar.ck3.control.application.planning.military.LateWarCoreLeaves.*;
import static org.xar.ck3.control.application.planning.military.CapitalRegroupEligibility.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.military.LateWarCoreInputs.Context;
import org.xar.ck3.control.application.planning.warexit.LegacyWarExitPolicy;
import org.xar.ck3.control.application.planning.warexit.WarExitLateBridge;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The original all-alternatives-exhausted, capital, defensive and pursuit sequence: strategy12934..14762. */
public final class LateWarCoreFallback {
    private LateWarCoreFallback() {}
    public static MilitaryPlanningDecision plan(Context c,OrdinaryPolicy.Draft previous,LateRouteSelection ranked) {
        var p=c.published();List<Obj> rejected=new ArrayList<>(ranked.rejections());
        Optional<Integer> target=ranked.target();String source=ranked.source();Optional<Obj> selectedAudit=ranked.audit();
        if(ranked.sweepEntered()&&target.isEmpty()) {
            if("player_held_county_capital".equals(source)) {
                Set<Integer> unsafe=new HashSet<>();for(Obj r:rejected)if(is(r,"status","unsafe"))unsafe.add(optionalInt(r.get("target_province_id")));
                Obj root=ranked.campaignRoot().orElse(empty());Integer capital=optionalInt(root.get("capital_province_id"));
                if(ranked.defensiveHold().isPresent()&&ranked.nativeRallyBinding().isPresent()&&c.balance().filter(Balance::hostileOvermatch).isPresent()
                        &&capital!=null&&capital!=c.current()&&rejected.size()==ranked.candidates().size()&&unsafe.equals(new HashSet<>(ranked.candidates()))) {
                    Obj defensive=bindRoot(ranked.defensiveHold().orElseThrow(),root,capital);
                    return defensiveContact(c,"native_war_defender_native_rally_",defensive,rejected,ranked.nativeRallyBinding(),true);
                }
                return hold(c,"native_war_no_safe_player_held_county_route",null,
                        "every observed directly-held county-capital fallback route is blocked or unsafe; keep the map paused until broader native objective candidates are observable",
                        f("required_observation",text("broader-safe-war-objective-candidates")),f("candidate_province_ids",numbers(ranked.candidates())),
                        f("native_rally_hold_binding",ranked.nativeRallyBinding().<Value>map(v->v).orElse(Nil.INSTANCE)),f("route_rejections",objects(rejected)));
            }
            if(ranked.stationaryTransition().isPresent()) {
                Obj transition=ranked.stationaryTransition().orElseThrow();String step=optionalText(transition.get("advance_step"));
                if(step!=null&&advertised(c.request(),step))return action(c,"native_war_unavoidable_contact_transition",step,
                        "every alternate exact objective route was rejected; hold the occupied objective for one proof-bound day and require an observed contact transition",
                        f("route_audit",obj(f("status",text("stationary_current_province_contact")),f("target_province_id",transition.get("target_province_id")),
                            f("contact_horizon",transition.get("contact_horizon")))),f("route_rejections",objects(rejected)));
                return hold(c,"native_war_unavoidable_contact_transition_unsupported",step,
                        "every alternate exact objective route was rejected and the stationary contact proof is fresh, but no proof-bound one-day transition is available",f("route_rejections",objects(rejected)));
            }
            Optional<MilitaryPlanningDecision> exit=response(c,previous,rejected);
            if(exit.isPresent())return exit.orElseThrow();
            exit=exit(c,previous,rejected,LegacyWarExitPolicy.Position.OBJECTIVES_EXHAUSTED_BEFORE_CAPITAL_REGROUP);
            if(exit.isPresent())return exit.orElseThrow();
            boolean siegeRegroup=CapitalRegroupEligibility.insufficientSiege(c);
            boolean capitalHold=CapitalRegroupEligibility.defeatedAttackerAtCapital(c,rejected);
            boolean nonleader=CapitalRegroupEligibility.nonleaderAttacker(c,ranked.candidates(),rejected);
            boolean coalition=CapitalRegroupEligibility.coalitionAttacker(c,rejected);
            boolean defender=CapitalRegroupEligibility.outnumberedPrimaryDefender(c,ranked.candidates(),rejected);
            Optional<Obj> nonleaderCapitalRisk=Optional.empty();
            if(siegeRegroup||capitalHold||nonleader||coalition||defender) {
                Optional<Obj> root=WarCapitalContext.sameFrameRoot(c.request());
                if(root.isEmpty())return required(c,"native_war_capital_regroup_context","query-campaign-root-context-v1",
                        "the exhausted exact siege may retreat only to a fresh same-frame campaign-root capital",f("route_rejections",objects(rejected)));
                Obj campaignRoot=root.orElseThrow();Integer capital=optionalInt(campaignRoot.get("capital_province_id"));
                if((defender||nonleader)&&!WarCapitalContext.directlyHeldCountyCapitals(campaignRoot).orElse(List.of()).contains(capital))
                    return hold(c,"native_war_defender_capital_regroup_ownership_blocked",null,
                            "the primary defender's same-frame capital is not confirmed as a directly held county capital",
                            f("required_observation",text("directly-held-capital-county")),f("capital_province_id",capital==null?Nil.INSTANCE:number(capital)),f("route_rejections",objects(rejected)));
                if(Objects.equals(capital,c.current())&&nonleader) {
                    Optional<MilitaryTimeline.Horizon> h=horizon(c,c.current(),List.of());String query=query(c,c.current());
                    if(h.isEmpty()) {
                        Optional<Obj> failed=failure(c,c.current(),List.of());
                        Field[] detail={f("contact_query_attempt",failed.<Value>map(v->v).orElse(Nil.INSTANCE)),f("route_rejections",objects(rejected))};
                        return failed.isPresent()?hold(c,"native_war_nonleader_capital_stationary_contact",query,
                                "require a fresh exact stationary full-hostile contact horizon at the directly held capital",detail):
                                required(c,"native_war_nonleader_capital_stationary_contact",query,
                                    "require a fresh exact stationary full-hostile contact horizon at the directly held capital",detail);
                    }
                    var observed=h.orElseThrow();String advance=advance(c,c.current());
                    if(!(observed.oneDayFree()||unavoidable(observed)))return required(c,"native_war_nonleader_capital_contact_risk_defensive_hold","life-advance-one-day",
                            "all exact exits remain native-negative; stay at the directly held capital for one exact day and observe any defensive contact",
                            f("contact_horizon",observed.original()),f("contact_risk",text("all_exact_exits_native_negative_passive_defense")),f("route_rejections",objects(rejected)));
                    return required(c,"native_war_nonleader_capital_stationary_watch",advance,
                            "hold the directly held capital for one native proof-bound day when contact-free or unavoidable current-province contact is verified",
                            f("contact_horizon",observed.original()),f("route_rejections",objects(rejected)));
                }
                if(Objects.equals(capital,c.current())&&(siegeRegroup||capitalHold||coalition))return available(c,
                        "native_war_capital_regroup_hold_progress","native_war_capital_regroup_hold_unsupported","life-advance",
                        "every exact offensive route is unsafe, but the attacker is already at its fresh same-frame capital; hold there for one bounded slice and re-query the war termination and route state",
                        "the exhausted attacker is already holding its fresh same-frame capital, but the backend cannot execute a bounded observation slice",
                        f("capital_province_id",number(capital)),f("route_rejections",objects(rejected)));
                if((siegeRegroup||coalition||defender||nonleader)&&capital!=null&&capital!=c.current()) {
                    Optional<Obj> preview=preview(c,capital);String previewStep=previewStep(c,capital);
                    if(preview.isEmpty()) {
                        if(!advertised(c.request(),previewStep)) {
                            Optional<MilitaryPlanningDecision> watch=LateWarCoreWatches.retainedEmbarked(c,p.passiveRouteAudit(),rejected);
                            if(watch.isPresent())return watch.orElseThrow();
                        }
                        return required(c,"native_war_capital_regroup_preview",previewStep,
                                "preview the same-frame capital regroup route before leaving the unsafe offensive route",f("route_rejections",objects(rejected)));
                    }
                    Obj routePreview=preview.orElseThrow();
                    if(is(routePreview,"status","deferred"))return hold(c,"native_war_capital_regroup_blocked","fresh-safe-capital-regroup-route",
                            "the exact capital regroup preview is deferred; do not advance or submit an unconfirmed retreat",f("route_preview",routePreview),f("route_rejections",objects(rejected)));
                    List<Integer> route=route(routePreview.get("route_province_ids")).orElseThrow();Obj regroupAudit=audit(c,capital,route);
                    if((defender||nonleader)&&!c.contactSupported())return hold(c,"native_war_capital_regroup_contact_horizon_unsupported","complete-scope-route-contact-horizon",
                            "the primary defender cannot leave an unsafe route without a complete hostile-scope contact horizon for the capital route",f("route_preview",routePreview),f("route_audit",regroupAudit),f("route_rejections",objects(rejected)));
                    if((is(regroupAudit,"status","unsafe")||defender||nonleader)&&c.contactSupported()) {
                        Optional<MilitaryTimeline.Horizon> h=horizon(c,capital,route);
                        if(h.isEmpty()) {
                            Optional<Obj> failed=failure(c,capital,route);
                            if(failed.isPresent())regroupAudit=merge(regroupAudit,obj(f("status",text("contact_timeline_unavailable")),f("contact_query_attempt",failed.orElseThrow())));
                            else return required(c,"native_war_capital_regroup_contact_horizon",query(c,capital),
                                    "the capital regroup route intersects hostile routing and requires a fresh exact contact horizon",
                                    f("route_preview",routePreview),f("route_audit",regroupAudit),f("route_rejections",objects(rejected)));
                        }
                        if(h.isPresent()) {
                            var observed=h.orElseThrow();
                            if(observed.oneDayFree())regroupAudit=merge(regroupAudit,obj(f("status",text("safe_one_day_contact_horizon")),f("contact_horizon",observed.original())));
                            else if(defender||nonleader) {
                                if(nonleader)nonleaderCapitalRisk=Optional.of(observed.original());
                                regroupAudit=merge(regroupAudit,obj(f("status",text("contact_timeline_unsafe")),f("contact_horizon",observed.original())));
                            }
                        }
                    }
                    Optional<Obj> rollback=rollback(c,capital,route(regroupAudit.get("route_province_ids")).orElseThrow());
                    if(safe(regroupAudit)&&rollback.isEmpty()) {
                        target=Optional.of(capital);source="player_capital_regroup";
                        selectedAudit=Optional.of(put(regroupAudit,"selection",obj(f("policy",text(defender?"outnumbered_primary_defender_capital_regroup":nonleader?
                                "nonleader_attacker_owned_capital_regroup":coalition?"outnumbered_coalition_capital_regroup":"insufficient_siege_capital_regroup")),f("evaluated_enemy_count",number(c.hostileIds().size())))));
                    } else {if(rollback.isPresent())regroupAudit=put(regroupAudit,"failure",rollback.orElseThrow());rejected.add(regroupAudit);}
                }
            }
            if(target.isEmpty()) {
                if(nonleader&&nonleaderCapitalRisk.isPresent()&&idle(c.subject(),false)&&!c.routeUnsafe())return required(c,
                        "native_war_nonleader_all_exits_contact_risk_defensive_hold","life-advance-one-day",
                        "all observed objective exits and the directly held capital route have native one-day contact risk; make no offensive move and observe one exact defensive day",
                        f("contact_risk",text("all_exact_objectives_and_owned_capital_native_negative")),f("capital_contact_horizon",nonleaderCapitalRisk.orElseThrow()),f("route_rejections",objects(rejected)));
                boolean uncontested=c.enemies().stream().noneMatch(a->Objects.equals(a.current(),c.current()));
                if(c.balance().filter(Balance::hostileOvermatch).isPresent()&&idle(c.subject(),false)&&uncontested&&p.stationaryThreats().isEmpty()
                        &&p.unsafeArmyIds().isEmpty()&&advertised(c.request(),"life-advance"))return action(c,"native_war_no_safe_route_defensive_hold_progress","life-advance",
                        "all exact offensive and capital routes are unsafe under hostile operational overmatch; hold the current uncontested Province for one bounded day and re-query every route and army strength",f("route_rejections",objects(rejected)));
                exit=exit(c,previous,rejected,LegacyWarExitPolicy.Position.DEFENSIVE_HOLD_EXHAUSTED);if(exit.isPresent())return exit.orElseThrow();
                Optional<MilitaryPlanningDecision> watch=LateWarCoreWatches.afterExhausted(c,rejected);if(watch.isPresent())return watch.orElseThrow();
                return hold(c,"native_war_no_safe_exact_route","safe-exact-war-route",
                        "every remaining exact objective route and any eligible capital regroup route is blocked or unsafe",f("route_rejections",objects(rejected)));
            }
        }
        if(c.routeUnsafe()&&target.isEmpty()) {
            List<Obj> activeRejected=List.of(p.passiveRouteAudit().orElseThrow());Optional<MilitaryPlanningDecision> exit=response(c,previous,activeRejected);
            if(exit.isPresent())return exit.orElseThrow();
            exit=exit(c,previous,activeRejected,LegacyWarExitPolicy.Position.ACTIVE_ROUTE_UNSAFE_WITHOUT_PREVIEW_TARGET);if(exit.isPresent())return exit.orElseThrow();
            Optional<MilitaryPlanningDecision> watch=LateWarCoreWatches.retainedEmbarked(c,p.passiveRouteAudit(),activeRejected);if(watch.isPresent())return watch.orElseThrow();
            return hold(c,"native_war_no_safe_exact_route","safe-exact-war-route","the active route became unsafe and no remaining exact objective has a safe preview",f("route_rejections",objects(activeRejected)));
        }
        String kind;
        if(target.isPresent())kind="player_capital_regroup".equals(source)||refugeSource(source)?"regroup":"enemy_siege_relief".equals(source)?"relief":"siege";
        else {
            Set<Integer> enemyThreat=new HashSet<>();for(Army enemy:c.enemies()) {if(enemy.current()!=null)enemyThreat.add(enemy.current());if(enemy.target()!=null)enemyThreat.add(enemy.target());}
            boolean blockedEnemy=p.tacticalState().get("blocked_enemy_ids") instanceof Arr ids&&!ids.items().isEmpty();
            for(int candidate:p.rankedExactObjectives())if(!p.blockedProvinces().contains(candidate)&&!enemyThreat.contains(candidate)
                    &&!(candidate==c.current()&&!p.stationaryThreats().isEmpty())
                    &&!(blockedEnemy&&tacticalEnemies(c).stream().anyMatch(a->Objects.equals(a.current(),candidate)))) {target=Optional.of(candidate);break;}
            source="war_objective_province";kind="siege";
        }
        if(target.isEmpty())return noTarget(c,ranked);
        return pursuit(c,target.orElseThrow(),source,kind,selectedAudit);
    }
    private static Optional<MilitaryPlanningDecision> response(Context c,OrdinaryPolicy.Draft previous,List<Obj> rejected) {
        return adapted(WarExitLateBridge.lateResponse(c.request(),previous,c.published().tacticalWarId(),rejected));
    }
    private static Optional<MilitaryPlanningDecision> exit(Context c,OrdinaryPolicy.Draft previous,List<Obj> rejected,LegacyWarExitPolicy.Position position) {
        return adapted(LegacyWarExitPolicy.atBoundary(c.request(),new LegacyWarExitPolicy.TacticalBoundary(position,c.published().tacticalWarId(),rejected),previous));
    }
    private static Optional<MilitaryPlanningDecision> adapted(OrdinaryPolicy.Decision decision) {
        return decision instanceof OrdinaryPolicy.Keep||decision instanceof OrdinaryPolicy.NotApplicable?Optional.empty():Optional.of(new MilitaryPlanningDecision.ApplicationDecision(decision));
    }
    static Obj bindRoot(Obj admission,Obj root,int capital) {
        return merge(admission,obj(f("capital_province_id",number(capital)),f("campaign_root_snapshot_revision",nullable(root.get("snapshot_revision"))),f("campaign_root_date_raw",nullable(root.get("date_raw")))));
    }
    private static MilitaryPlanningDecision noTarget(Context c,LateRouteSelection ranked) {
        var p=c.published();
        if(p.exactOccupationFullyObservable()&&p.allSiegeObjectivesCompleted()&&p.stationaryThreats().isEmpty()&&p.unsafeArmyIds().isEmpty())
            return available(c,"native_war_objective_settlement_progress","native_war_objective_settlement_progress_unsupported","life-advance",
                    "every authoritative exact occupation objective is complete and the global route matrix is safe; advance one bounded settlement slice without selecting an enemy target",
                    "all authoritative exact objectives are complete, but the backend cannot advance the bounded war-settlement slice");
        if(p.exactSiegeRejection().isPresent())return hold(c,"native_war_siege_stalled","progress-capable-exact-war-objective",
                "the current exact siege is not progressing and no alternate exact objective is available",f("siege_state",p.exactSiegeRejection().orElseThrow()));
        if(!p.stationaryThreats().isEmpty()) {
            Optional<Obj> admission=WarCapitalContext.primaryDefenderHold(c,true,true);
            if(admission.isPresent()) {
                Optional<Obj> root=WarCapitalContext.sameFrameRoot(c.request());
                if(root.isEmpty())return required(c,"native_war_defender_capital_contact_context","query-campaign-root-context-v1",
                        "a threatened primary-defender hold may query contact timing only at a fresh same-frame exact campaign capital",f("defensive_hold",admission.orElseThrow()),f("route_rejections",objects(p.stationaryThreats())));
                Integer capital=optionalInt(root.orElseThrow().get("capital_province_id"));
                if(Objects.equals(capital,c.current()))return defensiveContact(c,"native_war_defender_capital_",bindRoot(admission.orElseThrow(),root.orElseThrow(),capital),p.stationaryThreats(),Optional.empty(),false);
            }
            boolean exact=p.rankedExactObjectives().contains(c.current());
            return hold(c,exact?"native_war_no_safe_exact_route":"native_war_no_safe_target",exact?"safe-exact-war-route":"query-safe-war-objectives",
                    "the stationary province is under observable enemy convergence and no alternate target is available",f("route_rejections",objects(p.stationaryThreats())));
        }
        Optional<Obj> admission=WarCapitalContext.primaryDefenderHold(c,false,false);
        if(admission.isPresent()) {
            Optional<Obj> root=WarCapitalContext.sameFrameRoot(c.request());
            if(root.isEmpty())return required(c,"native_war_defender_capital_hold_context","query-campaign-root-context-v1",
                    "the primary defender may hold only at a fresh same-frame exact campaign capital",f("defensive_hold",admission.orElseThrow()));
            Integer capital=optionalInt(root.orElseThrow().get("capital_province_id"));
            if(Objects.equals(capital,c.current()))return available(c,"native_war_defender_capital_hold_progress","native_war_defender_capital_hold_progress_unsupported","life-advance",
                    "the primary defender has no exact territorial objective and its sole regular army is holding the fresh same-frame campaign capital; use the existing bounded tactical horizon and re-observe immediately on war, army, or stationary-threat change",
                    "the exact primary-defender capital hold is ready but this backend cannot execute its bounded observation slice",f("defensive_hold",bindRoot(admission.orElseThrow(),root.orElseThrow(),capital)));
        }
        admission=WarCapitalContext.primaryDefenderHold(c,true,false);
        Optional<Obj> rally=admission.isPresent()?WarHistorySteps.nativeRallyHoldBinding(c.history(),c.snapshot(),p.tacticalWarId(),c.subject().id(),c.current()):Optional.empty();
        if(rally.isPresent()) {
            Optional<Obj> root=WarCapitalContext.sameFrameRoot(c.request());
            if(root.isEmpty())return required(c,"native_war_defender_native_rally_hold_context","query-campaign-root-context-v1",
                    "the primary-defender native-rally hold requires a fresh same-frame campaign root so an arbitrary noncapital province cannot inherit this authorization",f("defensive_hold",admission.orElseThrow()),f("native_rally_hold_binding",rally.orElseThrow()));
            Integer capital=optionalInt(root.orElseThrow().get("capital_province_id"));
            if(capital!=null&&capital!=c.current())return available(c,"native_war_defender_native_rally_hold_progress","native_war_defender_native_rally_hold_progress_unsupported","life-advance",
                    "the sole primary-defender army is still stationary at the exact province produced by its durable native raise receipt; advance only through the existing active-war tactical horizon and re-observe immediately",
                    "the exact native-raised defender rally hold is ready, but this backend cannot execute its bounded observation slice",f("defensive_hold",bindRoot(admission.orElseThrow(),root.orElseThrow(),capital)),f("native_rally_hold_binding",rally.orElseThrow()));
        }
        if(allyHold(c)&&terminationUnavailable(c)) {
            Optional<Obj> root=WarCapitalContext.sameFrameRoot(c.request());
            if(root.isEmpty())return required(c,"native_war_attacker_ally_capital_hold_context","query-campaign-root-context-v1",
                    "bind the non-leading attacker's stationary hold to its same-frame directly held capital");
            if(Objects.equals(optionalInt(root.orElseThrow().get("capital_province_id")),c.current())
                    &&WarCapitalContext.directlyHeldCountyCapitals(root.orElseThrow()).orElse(List.of()).contains(c.current())) {
                if(!c.contactSupported())return hold(c,"native_war_attacker_ally_capital_contact_unsupported",queryUnchecked(c,c.current()),
                        "the non-leading attacker requires a complete-scope one-day stationary contact proof");
                Optional<MilitaryTimeline.Horizon> h=horizon(c,c.current(),List.of());String query=query(c,c.current());
                if(h.isEmpty()) {
                    Optional<Obj> failed=failure(c,c.current(),List.of());String phase=failed.isPresent()?"native_war_attacker_ally_capital_contact_unavailable":"native_war_attacker_ally_capital_contact_query";
                    return failed.isPresent()?hold(c,phase,query,"query the exact stationary one-day contact horizon before any allied-war time advance",f("contact_query_attempt",failed.orElseThrow())):
                            required(c,phase,query,"query the exact stationary one-day contact horizon before any allied-war time advance",f("contact_query_attempt",Nil.INSTANCE));
                }
                if(h.orElseThrow().oneDayFree())return required(c,"native_war_attacker_ally_capital_contact_progress",advance(c,c.current()),
                        "the non-leading attacker's directly held capital is contact-free for exactly one day; re-observe the allied war immediately",f("contact_horizon",h.orElseThrow().original()));
                return hold(c,"native_war_attacker_ally_capital_contact_blocked",null,"the same-frame stationary capital horizon does not prove one contact-free day",
                        f("required_observation",text("contact-free-stationary-horizon")),f("contact_horizon",h.orElseThrow().original()));
            }
        }
        return hold(c,"native_war_counterpolicy_hold","safe-exact-war-objective-or-exact-combat-prediction",
                "no safe exact objective is available and the adapter publishes no exact combat prediction; do not infer native power from soldiers or chase a visible enemy province",f("tactical_state",p.tacticalState()));
    }
    private static boolean allyHold(Context c) {
        var p=c.published();
        if(!(wars(c.request()).size()==1&&is(c.war(),"player_side","attacker")&&no(c.war().get("player_is_primary_war_leader"))
                &&p.rankedExactObjectives().isEmpty()&&c.controlled().size()==1&&idle(c.subject(),true)&&p.stationaryThreats().isEmpty()
                &&p.unsafeArmyIds().isEmpty()&&p.activeAssaults().isEmpty()&&!c.enemies().isEmpty()
                &&c.enemies().size()==enemies(c.request()).size()&&c.hostileIds().size()==c.enemies().size()
                &&c.balance().isPresent()&&c.balance().orElseThrow().original().get("friendly_army_ids") instanceof Arr friendly&&friendly.items().size()>=2))return false;
        return c.enemies().stream().allMatch(a->a.current()!=null&&a.current()!=c.current()&&a.moveTargetPresent()&&a.route().isPresent()
                &&(a.route().orElseThrow().isEmpty()&&a.target()==null||!a.route().orElseThrow().isEmpty()&&Objects.equals(a.route().orElseThrow().getLast(),a.target())));
    }
    private static boolean terminationUnavailable(Context c) {
        Obj summary=c.published().warSummaries().getFirst(),reuse=object(summary.get("war_termination_negative_reuse"));
        if(is(reuse,"status","negative_assessment_reused"))return true;
        Obj termination=c.termination(),options=object(termination.get("options"));
        return no(termination.get("player_is_primary_war_leader"))&&List.of("surrender","white_peace","victory").stream().allMatch(k->options.get(k) instanceof Obj o&&no(o.get("available")));
    }
    static String queryUnchecked(Context c,int target) {
        // The original unsupported diagnostic still describes its exact empty/full scope without constructing a native query.
        StringBuilder out=new StringBuilder("query-route-contact-horizon-v1-").append(c.subject().id()).append("-to-").append(target).append("-h-").append(c.hostileIds().size());
        c.hostileIds().forEach(id->out.append('-').append(id));return out.toString();
    }
    static MilitaryPlanningDecision defensiveContact(Context c,String prefix,Obj defensive,List<Obj> rejected,Optional<Obj> rally,boolean nativeRally) {
        List<Field> details=new ArrayList<>();details.add(f("defensive_hold",defensive));rally.ifPresent(r->details.add(f("native_rally_hold_binding",r)));details.add(f("route_rejections",objects(rejected)));
        String query=queryUnchecked(c,c.current());String noun=nativeRally?"native-rally":"capital";
        if(!c.contactSupported())return hold(c,prefix+"contact_horizon_unsupported",query,
                nativeRally?"the threatened native-rally hold requires the existing complete-scope stationary contact-horizon capability":"the threatened capital hold requires the existing complete-scope stationary contact-horizon capability",details.toArray(Field[]::new));
        Optional<MilitaryTimeline.Horizon> h=horizon(c,c.current(),List.of());
        if(h.isEmpty()) {
            Optional<Obj> failed=failure(c,c.current(),List.of());
            if(failed.isPresent()) {
                details.add(f("contact_query_attempt",failed.orElseThrow()));details.add(f("required_observation",text("fresh-available-stationary-contact-horizon")));
                return hold(c,prefix+"contact_horizon_unavailable",null,
                        nativeRally?"the current-frame stationary native-rally contact query failed or returned no usable exact timeline; keep the map paused":"the current-frame stationary capital contact query failed or returned no usable exact timeline; keep the map paused",details.toArray(Field[]::new));
            }
            return required(c,prefix+"contact_horizon",query,
                    nativeRally?"prove the exact native-rally Province contact-free or unavoidable for one day before holding under hostile overmatch":"replace geometric convergence on the exact defender capital with the existing stationary one-day contact timeline",details.toArray(Field[]::new));
        }
        var observed=h.orElseThrow();details.add(f("contact_horizon",observed.original()));
        if(observed.oneDayFree())return required(c,prefix+"contact_horizon_progress",advance(c,c.current()),
                nativeRally?"the fresh stationary timeline proves the exact native-rally Province contact-free for one day":"the fresh stationary timeline proves the exact defender capital contact-free for one day",details.toArray(Field[]::new));
        if(unavoidable(observed))return required(c,prefix+"contact_transition",advance(c,c.current()),
                nativeRally?"the exact native-rally hold has an unavoidable current-province contact within the proof-bound day":"the exact defender-capital hold has an unavoidable current-province contact within the proof-bound day",details.toArray(Field[]::new));
        details.add(f("required_observation",text("contact-free-or-unavoidable-current-province-stationary-horizon")));
        return hold(c,prefix+"contact_horizon_blocked",null,nativeRally?
                "the fresh stationary native-rally horizon is neither contact-free nor an exact unavoidable current-province transition":"the fresh stationary capital horizon is neither contact-free nor an exact unavoidable current-province transition",details.toArray(Field[]::new));
    }
    private static List<Army> tacticalEnemies(Context c) {
        if(!(c.war().get("enemy_armies") instanceof Arr rows))return List.of();
        return MilitaryPlanInputs.rows(rows).stream().map(MilitaryPlanInputs::army).filter(a->!"retreating".equals(a.tacticalState())&&a.current()!=null).toList();
    }
    private static MilitaryPlanningDecision pursuit(Context c,int target,String source,String kind,Optional<Obj> selectedAudit) {
        var p=c.published();Army army=c.subject();String step="move-army-"+army.id()+"-to-"+target;Army enemy=null;
        if("enemy_siege_relief".equals(source))enemy=tacticalEnemies(c).stream().filter(a->Objects.equals(optionalInt(p.siegeRelief().get("enemy_army_id")),a.id())).findFirst().orElse(null);
        Obj pursuit=obj(f("war_id",number(p.tacticalWarId())),f("army_id",number(army.id())),f("target_army_id",enemy==null?Nil.INSTANCE:number(enemy.id())),
                f("target_province_id",number(target)),f("target_soldiers",enemy==null?Nil.INSTANCE:nullable(enemy.raw().get("soldiers"))),f("target_source",text(source)),f("objective_kind",text(kind)));
        if("enemy_siege_relief".equals(source))pursuit=put(pursuit,"siege_relief",p.siegeRelief());if(selectedAudit.isPresent())pursuit=put(pursuit,"route_audit",selectedAudit.orElseThrow());
        Optional<Obj> intent=WarHistorySteps.activeNativeMoveIntent(c.history(),c.snapshot(),army.id(),target);
        Optional<Obj> backoff=WarHistorySteps.deferredMoveBackoff(c.history(),c.snapshot(),step);
        boolean waiting=backoff.isPresent()&&!yes(backoff.orElseThrow().get("retry_due"));boolean same=target==c.current()||Objects.equals(army.target(),target);
        Field[] movement={f("pursuit",pursuit),f("move_intent",intent.<Value>map(v->v).orElse(Nil.INSTANCE)),f("move_backoff",backoff.<Value>map(v->v).orElse(Nil.INSTANCE))};
        if(!p.stationaryThreats().isEmpty()&&(intent.isPresent()||waiting||same))return hold(c,"native_war_stationary_threat_blocked","replace-threatened-stationary-position",
                "enemy convergence threatens the stationary army; deferred, pending, or same-province alternatives cannot justify advancing time",
                append(movement,f("route_rejections",objects(p.stationaryThreats()))));
        if(c.routeUnsafe()) {
            if(intent.isEmpty()&&!waiting&&!same&&advertised(c.request(),step))return action(c,"native_war_unsafe_route_reroute",step,
                    "replace the observably unsafe active route before any game-time advance",f("pursuit",pursuit),f("route_audit",p.passiveRouteAudit().orElseThrow()));
            return hold(c,"native_war_unsafe_route_blocked","replace-unsafe-native-route",
                    "an unsafe route is still active; deferred, pending, or same-province alternatives cannot justify advancing it",append(movement,f("route_audit",p.passiveRouteAudit().orElseThrow())));
        }
        if(p.exactSiegeRejection().isPresent()&&(intent.isPresent()||waiting||same))return hold(c,"native_war_siege_exit_blocked","replace-rejected-siege-position",
                "the exact siege was rejected; deferred, pending, or same-province movement cannot justify advancing time",append(movement,f("siege_state",p.exactSiegeRejection().orElseThrow())));
        if(intent.isPresent())return available(c,"native_war_pursuit_progress","native_war_pursuit_progress_unsupported","life-advance",
                "the accepted native move intent is still active; advance the war without submitting the same move again","the native move intent is still active but this backend cannot advance the march",f("pursuit",pursuit),f("move_intent",intent.orElseThrow()));
        if(waiting)return available(c,"native_war_pursuit_progress","native_war_pursuit_progress_unsupported","life-advance",
                "the army was not move-ready; use the 7/14/30-day retry backoff","the deferred native move needs time to advance but this backend cannot do so",f("pursuit",pursuit),f("move_backoff",backoff.orElseThrow()));
        if(same) {
            String reason="siege".equals(kind)?"the native army is already at or moving toward the stable siege objective; advance the occupation":"the native army is already at or moving toward the strongest visible enemy; advance the battle";
            if(advertised(c.request(),"life-advance")) {
                Optional<MilitaryPlanningDecision> sentinel=StationaryObjectiveHold.plan(c,pursuit);
                if(sentinel.isPresent())return sentinel.orElseThrow();
                return action(c,"native_war_pursuit_progress","life-advance",reason,f("pursuit",pursuit));
            }
            return hold(c,"native_war_pursuit_progress_unsupported","life-advance","the army is already pursuing the enemy but this backend cannot advance time",f("pursuit",pursuit));
        }
        String reason="enemy_army".equals(source)?"move the strongest controllable army to the strongest visible enemy army":"enemy_siege_relief".equals(source)?
                "move the overmatching primary-defender army along the previewed contact-safe route to relieve an observed enemy siege":"war_objective_province".equals(source)?
                "move the army along a previewed safe route to the next exact war objective":"move toward the primary opponent's default rally province fallback";
        return available(c,"native_war_pursuit","native_war_pursuit_unsupported",step,reason,"the backend cannot issue the required native army move",f("pursuit",pursuit));
    }
    private static Field[] append(Field[] old,Field value) {Field[] next=java.util.Arrays.copyOf(old,old.length+1);next[old.length]=value;return next;}
}

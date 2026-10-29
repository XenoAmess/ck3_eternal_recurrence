package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Concrete same-request route, strength, history and siege producer for every early and late consumer. */
public final class EarlyWarCoreInputs implements LateWarCoreInputs.Provider {
    @FunctionalInterface public interface Collector { Capture capture(PlanningRequest request,OrdinaryPolicy.Draft current); }
    public sealed interface Capture permits Available,Unavailable { }
    public record Available(Actual state) implements Capture { public Available {Objects.requireNonNull(state);} }
    public record Unavailable(List<String> missing) implements Capture {
        public Unavailable {missing=List.copyOf(missing);require(!missing.isEmpty(),"actual early input gap required");}
    }
    public record Actual(ObservationIdentity before,WarContactObservation.KnownContact contact,
            Army subject,Obj war,int tacticalWarId,Optional<Balance> balance,Obj siegeRelief,
            WarObjectiveSources.State objectives,List<Obj> assaultReviews,Optional<Obj> exactSiege,
            Optional<Obj> exactAssault,Obj tactical,List<Obj> warSummaries,Obj battleControl) {
        public Actual {
            Objects.requireNonNull(before);Objects.requireNonNull(contact);Objects.requireNonNull(subject);Objects.requireNonNull(war);
            Objects.requireNonNull(balance);Objects.requireNonNull(siegeRelief);Objects.requireNonNull(objectives);
            assaultReviews=List.copyOf(assaultReviews);Objects.requireNonNull(exactSiege);Objects.requireNonNull(exactAssault);
            Objects.requireNonNull(tactical);warSummaries=List.copyOf(warSummaries);Objects.requireNonNull(battleControl);
            require(tacticalWarId>0&&subject.id()>=0&&before.equals(contact.before()),"same actual early identities required");
        }
        public void requireSame(PlanningRequest request) {
            contact.requireSame(request);require(before.equals(request.before()),"early context crossed frame");
            objectives.requireSame(request,tacticalWarId,subject.id());
        }
        public List<Army> controlled(){return contact.context().controlledArmies();}
        public Set<Integer> unsafeArmyIds(){return contact.context().unsafeArmyIds();}
        public Set<Integer> threatenedStationaryArmyIds(){return contact.context().threatenedStationaryArmyIds();}
        public Set<Integer> startBlockingRouteArmyIds(){return contact.context().startBlockingRouteArmyIds();}
        public List<Integer> siegeObjectives(){return objectives.siegeObjectives();}
        public boolean exactOccupationFullyObservable(){return objectives.exactOccupationFullyObservable();}
        public List<Obj> stationaryThreats(){return WarContactObservation.stationaryThreats(subject.current(),contact.context().completeRouteThreatEnemies());}
        public List<Obj> activeAssaults(){return assaultReviews.stream().filter(r->new Text("active").equals(r.get("status"))).toList();}
    }
    private final WarContactHistory history;
    private final WarStrengthRelief strength;
    private final WarContactPolicy contact;
    public EarlyWarCoreInputs() {
        history=new WarContactHistory(WarHistorySteps::isLifeAdvance);
        strength=new WarStrengthRelief(WarContactPolicy::strengthContact,WarContactPolicy.movementEvidence(history),
                request->Optional.of(BattleControlTurnState.collect(request)));
        contact=new WarContactPolicy(history,strength);
    }
    public WarContactPolicy contactPolicy(){return contact;}
    public WarStrengthRelief strengthPolicy(){return strength;}
    public WarContactHistory history(){return history;}
    public Capture capture(PlanningRequest request,OrdinaryPolicy.Draft current) {
        try {
            var observation=WarContactObservation.collect(request);
            if(observation instanceof WarContactObservation.Incomplete missing)return new Unavailable(missing.missing());
            var known=(WarContactObservation.KnownContact)observation;known.requireSame(request);var c=known.context();
            require(request.observations().paused()&&request.observations().mapReady(),"actual early capture requires the paused map");
            require(c.evidenceIssues().isEmpty()&&c.globalRouteAudits().stream().noneMatch(a->a.status()==WarContactObservation.AuditStatus.UNAVAILABLE),"actual route ingress must be complete before downstream capture");
            if(c.pursuitArmy().isEmpty())return new Unavailable(List.of("actual-canonical-pursuit-Unit"));
            Army subject=c.pursuitArmy().orElseThrow();
            var relief=strength.collect(request).orElseThrow(()->new IllegalArgumentException("actual strength/relief collector unavailable"));
            require(relief.before().equals(request.before()),"actual relief crossed frame");
            int warId=relief.selectedWar().orElseThrow(()->new IllegalArgumentException("actual tactical War unavailable"));
            Obj war=wars(request).stream().filter(r->Integer.valueOf(warId).equals(optionalInt(r.get("war_id")))).findFirst().orElseThrow();
            Obj tactical=WarRecentTactics.collect(request,subject.id(),warId);
            var objectives=WarObjectiveSources.collect(request,war,subject,relief.assessment(),tactical);
            List<Obj> assaults=WarSiegeDaily.reviews(request,c.completeRouteThreatEnemies());
            Optional<Obj> siege=WarSiegeDaily.siege(request,warId,subject.current(),objectives.exactStates(),Optional.of(subject));
            Optional<Obj> assault=WarSiegeDaily.assault(request,warId,subject.current(),objectives.exactStates(),
                    WarContactObservation.stationaryThreats(subject.current(),c.completeRouteThreatEnemies()),siege);
            List<Obj> summaries=summary(request,current);
            Optional<Balance> balance=MilitaryPlanInputs.balance(request,warId);
            if(balance.isPresent())summaries=summaries.stream().map(r->Integer.valueOf(warId).equals(optionalInt(r.get("war_id")))
                    ?put(r,"army_strength_balance",balance.orElseThrow().original()):r).toList();
            return new Available(new Actual(request.before(),known,subject,war,warId,balance,relief.assessment(),objectives,
                    assaults,siege,assault,tactical,summaries,BattleControlTurnState.collect(request)));
        }catch(IllegalArgumentException|java.util.NoSuchElementException invalid) {
            return new Unavailable(List.of("actual-early-warcore:"+Objects.toString(invalid.getMessage(),"typed input unavailable")));
        }
    }
    @Override public LateWarCoreInputs.Capture collect(PlanningRequest request,OrdinaryPolicy.Draft current) {
        try{return collectCurrent(request,current);}
        catch(IllegalArgumentException|java.util.NoSuchElementException invalid) {
            return new LateWarCoreInputs.Unavailable(List.of("actual-late-publication:"+Objects.toString(invalid.getMessage(),"typed input unavailable")));
        }
    }
    private LateWarCoreInputs.Capture collectCurrent(PlanningRequest request,OrdinaryPolicy.Draft current) {
        Capture raw=capture(request,current);
        if(!(raw instanceof Available available)) {
            // Only actual absence of every canonical controllable Unit permits the original residual branch.
            var contactResult=WarContactObservation.collect(request);
            if(contactResult instanceof WarContactObservation.KnownContact known) {
                known.requireSame(request);
                if(request.observations().paused()&&request.observations().mapReady()&&known.context().evidenceIssues().isEmpty()
                        &&known.context().globalRouteAudits().stream().noneMatch(a->a.status()==WarContactObservation.AuditStatus.UNAVAILABLE)
                        &&known.context().controlledArmies().stream().noneMatch(a->a.current()!=null&&a.current()>0))
                    return new LateWarCoreInputs.NoPursuit(request.before(),List.of(),Optional.empty(),summary(request,current));
            }
            return new LateWarCoreInputs.Unavailable(((Unavailable)raw).missing());
        }
        Actual actual=available.state();actual.requireSame(request);
        if(actual.subject().current()==null||actual.subject().current()<=0) {
            if(actual.controlled().stream().noneMatch(a->a.current()!=null&&a.current()>0))
                return new LateWarCoreInputs.NoPursuit(request.before(),actual.stationaryThreats(),Optional.empty(),actual.warSummaries());
            return new LateWarCoreInputs.Unavailable(List.of("selected-pursuit-current-Province-unavailable"));
        }
        var continuation=contact.continuation(request,current);
        if(continuation instanceof WarContactPolicy.ContinuationUnavailable missing)return new LateWarCoreInputs.Unavailable(missing.missing());
        var followed=(WarContactPolicy.Continuation)continuation;followed.requireSame(request);
        if(!followed.contact().equals(actual.contact())||!followed.selectedWar().equals(Optional.of(actual.tacticalWarId())))
            return new LateWarCoreInputs.Unavailable(List.of("actual-active-route-continuation-identity-drift"));
        Set<Integer> blocked=new LinkedHashSet<>(actual.objectives().blockedProvinces());blocked.addAll(followed.blockedProvinceIds());
        Optional<Obj> rejection=WarSiegeDaily.rejection(actual.exactSiege(),actual.subject(),Set.copyOf(actual.siegeObjectives()));
        if(rejection.isPresent()&&actual.subject().current()!=null)blocked.add(actual.subject().current());
        var publication=new LateWarCoreInputs.Published(request.before(),actual.tacticalWarId(),actual.subject().id(),
                actual.objectives().rankedExactObjectives(),actual.siegeObjectives(),blocked,actual.stationaryThreats(),actual.unsafeArmyIds(),
                actual.activeAssaults(),followed.passiveRouteAudit(),actual.siegeRelief(),rejection,
                terminationRows(request),actual.warSummaries(),actual.tactical(),
                yes(request.observations().snapshot().get("move_route_preview_supported")),
                yes(request.observations().snapshot().get("route_contact_horizon_supported")),
                actual.exactOccupationFullyObservable(),actual.objectives().allSiegeObjectivesCompleted(),sentinel(request));
        try{return new LateWarCoreInputs.Available(LateWarCoreInputs.collect(request,publication));}
        catch(IllegalArgumentException invalid){return new LateWarCoreInputs.Unavailable(List.of("actual-late-context:"+invalid.getMessage()));}
    }
    public static List<Obj> summary(PlanningRequest request,OrdinaryPolicy.Draft current) {
        return current.detail().get("active_wars") instanceof Arr a?rows(a):NativeWarEndConditions.summaries(request);
    }
    private static List<Obj> terminationRows(PlanningRequest request) {
        Obj snapshot=request.observations().snapshot();
        return rows(snapshot.get("war_termination_options")).stream().filter(row-> {
            Integer war=optionalInt(row.get("war_id"));return war!=null&&war>0&&NativeWarEndConditions.sameFrame(snapshot,row,war);
        }).toList();
    }
    private static LateWarCoreInputs.Sentinel sentinel(PlanningRequest request) {
        Obj readiness=request.observations().battleSpeedReadiness().orElse(empty());
        boolean enabled=yes(readiness.get("stationary_objective_hold_sentinel_live_ready"))||yes(readiness.get("stationary_objective_hold_sentinel_canary_ready"));
        Integer configured=optionalInt(readiness.get("noncombat_sentinel_timeline_speed"));int speed=3;
        boolean high=yes(readiness.get("noncombat_sentinel_high_speed_ab"));
        if(configured!=null&&configured>=1&&configured<=5&&(configured<=3||high
                ||yes(readiness.get("stationary_objective_hold_sentinel_speed_"+configured+"_live_ready"))))speed=configured;
        return new LateWarCoreInputs.Sentinel(enabled,speed,high);
    }
}

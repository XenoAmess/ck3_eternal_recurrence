package org.xar.ck3.control.application.planning.military;

import static org.xar.ck3.control.application.planning.military.MilitaryPlanInputs.*;
import java.util.EnumMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.ActionCommand;
import org.xar.ck3.control.application.action.OperationKey;
import org.xar.ck3.control.application.action.PlanningReadPort;
import org.xar.ck3.control.application.action.PlanningReadResult;
import org.xar.ck3.control.application.planning.OrdinaryPolicy;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.planning.PlanningResult;
import org.xar.ck3.control.application.planning.war.SplitMergeRecovery;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave3.planning.military.MilitaryRouteGeometry;

/**
 * Ordinary military call-order owner. Each leaf is a concrete source-bound Java
 * producer supplied by its domain owner; a missing producer is explicit.
 * No M5 analysis, injected preclassified status or native ACK stands in for a leaf.
 */
public final class WarCorePlanner {
    public enum Boundary {
        TERMINATION_SCORE_PRELUDE, PENDING_WAR_INTERACTION_PRELUDE, BATTLE_CONTROL_PRELUDE,
        WAR_SUMMARY_AND_ASSAULT_LIFECYCLE, PENDING_WAR_INTERACTION_CONSUMPTION,
        WAR_TERMINATION_CONTINUATION, DEFAULT_RAISE_AND_PRIMARY_IDENTITY, ROUTE_INGRESS,
        STRENGTH_AND_RELIEF, ASSAULT_STABILITY, COMBAT_AND_RETREAT_PROGRESS,
        MERGE_RENDEZVOUS_BOUNDARY, ASSAULT_AND_ARMY_STATE,
        ACTIVE_ROUTE_CONTACT, OBJECTIVE_SOURCE_SELECTION, ORDINARY_RANKED_ROUTE,
        DEFENSIVE_ROUTE_FALLBACK_AND_PURSUIT
    }
    @FunctionalInterface public interface CoreStep {
        MilitaryPlanningDecision evaluate(PlanningRequest request, OrdinaryPolicy.Draft current);
    }
    public record Leaf(Boundary boundary, ExactRef implementationSource, CoreStep producer) {
        public Leaf {
            Objects.requireNonNull(boundary);Objects.requireNonNull(implementationSource);Objects.requireNonNull(producer);
            require(implementationSource.bytes()>0,"actual military producer source required");
        }
    }
    public record RouteTactics(Set<Integer> unsafeArmyIds,Set<Integer> threatenedStationaryArmyIds) {
        public RouteTactics {
            unsafeArmyIds=Set.copyOf(unsafeArmyIds);threatenedStationaryArmyIds=Set.copyOf(threatenedStationaryArmyIds);
            unsafeArmyIds.forEach(value->require(value>=0,"unsafe Army ID"));threatenedStationaryArmyIds.forEach(value->require(value>=0,"threatened Army ID"));
        }
    }
    public sealed interface TacticsResult permits KnownTactics,UnknownTactics {}
    public record KnownTactics(org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity before,
                               RouteTactics tactics) implements TacticsResult {
        public KnownTactics { Objects.requireNonNull(before);Objects.requireNonNull(tactics); }
    }
    public record UnknownTactics(List<String> missing) implements TacticsResult {
        public UnknownTactics { missing=List.copyOf(missing);require(!missing.isEmpty(),"exact tactical gaps required"); }
    }
    @FunctionalInterface public interface RouteTacticsCollector {
        TacticsResult collect(PlanningRequest request);
    }
    /** Root-installed exact typed read whitelist; no prefix or query-name substring grants permission. */
    @FunctionalInterface public interface ReadCatalog {
        PlanningReadResult<OpportunityJson.Obj> read(PlanningRequest current, MilitaryPlanningDecision.Select selection);
    }
    @FunctionalInterface public interface CoreContinuation {
        OrdinaryPolicy.Decision plan(PlanningRequest trimmedRequest,OrdinaryPolicy.Draft current);
    }
    private final Map<Boundary,Leaf> leaves;
    private final RouteTacticsCollector tactics;
    private final MilitaryPlanningDecision.CommandFactory commands;
    private final ReadCatalog readCatalog;
    private final CoreContinuation continuation;
    public WarCorePlanner(List<Leaf> actualLeaves,RouteTacticsCollector actualTactics,
            MilitaryPlanningDecision.CommandFactory commands,PlanningReadPort reads,ReadCatalog readCatalog,
            CoreContinuation continuation) {
        EnumMap<Boundary,Leaf> indexed=new EnumMap<>(Boundary.class);
        for(Leaf leaf:List.copyOf(actualLeaves))require(indexed.put(leaf.boundary(),leaf)==null,"duplicate military producer boundary");
        this.leaves=Map.copyOf(indexed);this.tactics=Objects.requireNonNull(actualTactics);
        this.commands=Objects.requireNonNull(commands);Objects.requireNonNull(reads, "actual shared planning read port required");
        this.readCatalog=Objects.requireNonNull(readCatalog);
        this.continuation=Objects.requireNonNull(continuation);
    }
    /** Real uninstalled leaves remain visible to Root readiness; a named boundary is not an implementation. */
    public List<Boundary> missingBoundaries() {
        return java.util.Arrays.stream(Boundary.values()).filter(boundary -> !leaves.containsKey(boundary)).toList();
    }
    public sealed interface PreludeResult permits PreludeContinue,PreludeChosen {}
    public record PreludeContinue(OrdinaryPolicy.Draft draft) implements PreludeResult {
        public PreludeContinue { Objects.requireNonNull(draft); }
    }
    public record PreludeChosen(OrdinaryPolicy.Decision decision) implements PreludeResult {
        public PreludeChosen { Objects.requireNonNull(decision); }
    }
    /** Prelude is also required after the last active War disappears: original BattleID cleanup still precedes peace. */
    public PreludeResult prelude(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        OrdinaryPolicy.Draft current=previous;
        for(Boundary point:List.of(Boundary.TERMINATION_SCORE_PRELUDE,Boundary.PENDING_WAR_INTERACTION_PRELUDE,Boundary.BATTLE_CONTROL_PRELUDE)) {
            MilitaryPlanningDecision result=leaf(point,request,current);
            if(result instanceof MilitaryPlanningDecision.Keep keep)current=annotate(current,keep.annotations());
            else return new PreludeChosen(decision(request,current,result));
        }
        return new PreludeContinue(current);
    }
    /** Actual active-war body, after the three common prelude boundaries. */
    public OrdinaryPolicy.Decision activeWar(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        if(!request.observations().warInProgress())return new OrdinaryPolicy.NotApplicable("actual active War list is empty");
        OrdinaryPolicy.Draft current=previous;
        SplitMergeRecovery.State recovery=null;
        // strategy9840..9859: a staged pending reply must not bypass the exact
        // latched-assault guard or the battle-control prelude that just ran.
        for(Boundary point:List.of(Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE,
                Boundary.PENDING_WAR_INTERACTION_CONSUMPTION,Boundary.WAR_TERMINATION_CONTINUATION,
                Boundary.DEFAULT_RAISE_AND_PRIMARY_IDENTITY,Boundary.ROUTE_INGRESS,
                Boundary.STRENGTH_AND_RELIEF,Boundary.ASSAULT_STABILITY,Boundary.COMBAT_AND_RETREAT_PROGRESS,
                Boundary.MERGE_RENDEZVOUS_BOUNDARY,Boundary.ASSAULT_AND_ARMY_STATE,
                Boundary.ACTIVE_ROUTE_CONTACT,Boundary.OBJECTIVE_SOURCE_SELECTION,
                Boundary.ORDINARY_RANKED_ROUTE,Boundary.DEFENSIVE_ROUTE_FALLBACK_AND_PURSUIT)) {
            // Source strategy10450..10520: collect the real split/merge state
            // after global route audits and before strength/relief queries.
            if(point==Boundary.STRENGTH_AND_RELIEF) {
                recovery=SplitMergeRecovery.collect(request);
                MilitaryPlanningDecision resolution=adaptRecovery(request,current,SplitMergeRecovery.beforeStrength(recovery));
                if(resolution instanceof MilitaryPlanningDecision.Keep keep)current=annotate(current,keep.annotations());
                else return decision(request,current,resolution);
            }
            // Source11211..11368: after combat/retreat and the separated-pair
            // fence. UNKNOWN tactics is not converted into two empty sets.
            if(point==Boundary.ASSAULT_AND_ARMY_STATE) {
                require(recovery!=null,"split state must come from the actual earlier collector");
                TacticsResult observed=tactics.collect(request);
                if(!(observed instanceof KnownTactics known))return decision(request,current,
                        new MilitaryPlanningDecision.Unavailable(((UnknownTactics)observed).missing(),
                                "merge recovery requires actual same-frame route tactics"));
                require(known.before().equals(request.before()),"merge route tactics crossed frame");
                List<MilitaryRouteGeometry.Enemy> enemies=MilitaryPlanInputs.enemies(request).stream()
                        .map(MilitaryPlanInputs.Army::geometry).toList();
                SplitMergeRecovery.Resolution recoveryDecision=SplitMergeRecovery.afterRetreat(request,recovery,
                        known.tactics().unsafeArmyIds(),known.tactics().threatenedStationaryArmyIds(),
                        (route,origin,target)->MilitaryRouteGeometry.geometry(route,origin,target,enemies));
                MilitaryPlanningDecision resolution=adaptRecovery(request,current,recoveryDecision);
                if(resolution instanceof MilitaryPlanningDecision.Keep keep)current=annotate(current,keep.annotations());
                else return decision(request,current,resolution);
            }
            MilitaryPlanningDecision result=leaf(point,request,current);
            if(result instanceof MilitaryPlanningDecision.Keep keep)current=annotate(current,keep.annotations());
            else return decision(request,current,result);
        }
        return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,
                "active-war producers reached the end without an actual original core return");
    }
    public OrdinaryPolicy.Decision evaluate(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        PreludeResult first=prelude(request,previous);
        if(first instanceof PreludeChosen chosen)return chosen.decision();
        var continued=(PreludeContinue)first;
        return activeWar(request,continued.draft());
    }
    private MilitaryPlanningDecision leaf(Boundary boundary,PlanningRequest request,OrdinaryPolicy.Draft current) {
        Leaf leaf=leaves.get(boundary);
        return leaf==null?new MilitaryPlanningDecision.Unavailable(List.of("actual_java_producer:"+boundary),
                "ordinary core source boundary has no installed production Java collector"):
                Objects.requireNonNull(leaf.producer().evaluate(request,current),"military producer returned null");
    }
    public OrdinaryPolicy.Decision decision(PlanningRequest request,OrdinaryPolicy.Draft current,MilitaryPlanningDecision result) {
        if(result instanceof MilitaryPlanningDecision.ApplicationDecision shared) {
            if(shared.decision() instanceof OrdinaryPolicy.Replace replacement&&replacement.draft().command().isPresent()) {
                ActionCommand command=replacement.draft().command().orElseThrow();
                require(command.before().equals(request.before())&&command.source().equals(request.source())
                        &&command.sessionId().equals(request.sessionId())&&command.deadline().equals(request.deadline()),
                        "shared military policy command crossed current planning source/frame/session");
            }
            return shared.decision();
        }
        if(result instanceof MilitaryPlanningDecision.Replan replan) {
            PlanningRequest next=replan.requestWithTrimmedHistory();
            require(next.before().equals(request.before())&&next.source().equals(request.source())
                    &&next.sessionId().equals(request.sessionId())&&next.deadline().equals(request.deadline()),
                    "recognized transition continuation crossed source/frame/session");
            var old=request.observations();var now=next.observations();
            require(request.withHistory(now.history()).equals(next),
                    "transition continuation changed a nonhistory planning input");
            require(now.history().size()<old.history().size(),"recognized transition must shorten its history view");
            int index=0;
            for(var row:now.history()) {
                while(index<old.history().size()&&!old.history().get(index).equals(row))index++;
                require(index<old.history().size(),"trimmed history contains an invented or reordered source row");index++;
            }
            return Objects.requireNonNull(continuation.plan(next,annotate(current,replan.annotations())));
        }
        if(result instanceof MilitaryPlanningDecision.Keep keep)
            return new OrdinaryPolicy.Replace(annotate(current,keep.annotations()),"original military branch kept its action");
        if(result instanceof MilitaryPlanningDecision.Unavailable unavailable)
            return new OrdinaryPolicy.Stop(PlanningResult.StopReason.INCOMPLETE_PRODUCTION_CHAIN,
                    unavailable.reason()+": "+String.join(",",unavailable.missing()));
        if(result instanceof MilitaryPlanningDecision.Hold hold)
            return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(hold.policy(),hold.phase(),hold.reason(),
                    OrdinaryPolicy.Kind.ORDINARY,Optional.empty(),OrdinaryPolicy.Purpose.READ_ONLY,
                    Optional.of(org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain.war),hold.detail()),
                    "original military guard selected no world action");
        var selected=(MilitaryPlanningDecision.Select)result;
        if(selected.purpose()==OrdinaryPolicy.Purpose.READ_ONLY) {
            PlanningReadResult<OpportunityJson.Obj> read=Objects.requireNonNull(readCatalog.read(request, selected),
                    "actual source-bound typed military dispatcher returned null");
            if(read instanceof PlanningReadResult.Known<OpportunityJson.Obj>)
                return new OrdinaryPolicy.Refresh("original military readonly query completed; recapture full semantic request before choosing an action");
            return new OrdinaryPolicy.Wait(((PlanningReadResult.Unavailable<OpportunityJson.Obj>)read).reason());
        }
        return new OrdinaryPolicy.Replace(MilitaryPlanningDecision.draft(request,selected,commands),
                "original military action selected through the single shared command factory");
    }
    private static OrdinaryPolicy.Draft annotate(OrdinaryPolicy.Draft old,OpportunityJson.Obj annotations) {
        return new OrdinaryPolicy.Draft(old.policy(),old.phase(),old.reason(),old.kind(),old.command(),old.purpose(),old.domain(),
                merge(old.detail(),annotations));
    }
    public static OpportunityJson.Arr warSummary(PlanningRequest request) {
        return objects(NativeWarEndConditions.summaries(request));
    }
    private static MilitaryPlanningDecision adaptRecovery(PlanningRequest request,OrdinaryPolicy.Draft previous,
                                                          SplitMergeRecovery.Resolution resolution) {
        if(resolution instanceof SplitMergeRecovery.Keep)return new MilitaryPlanningDecision.Keep(empty());
        String phase,reason;Optional<OperationKey> required;OpportunityJson.Obj detail;
        if(resolution instanceof SplitMergeRecovery.Hold hold) {
            phase=hold.phase();reason=hold.reason();required=hold.requiredStep();detail=hold.detail();
            var full=merge(previous.detail(),detail);
            full=merge(full,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("reason",text(reason)),
                    f("selected_step",OpportunityJson.Nil.INSTANCE),f("active_wars",recoveryWarSummary(request,previous))));
            if(required.isPresent())full=put(full,"required_step",text(required.orElseThrow().value()));
            return new MilitaryPlanningDecision.Hold("one-life-turn-v1",phase,reason,required,full);
        }
        var selected=(SplitMergeRecovery.Select)resolution;phase=selected.phase();reason=selected.reason();
        detail=merge(previous.detail(),selected.detail());
        detail=merge(detail,obj(f("policy",text("one-life-turn-v1")),f("phase",text(phase)),f("reason",text(reason)),
                f("selected_step",text(selected.selectedStep().value())),f("active_wars",recoveryWarSummary(request,previous))));
        return new MilitaryPlanningDecision.Select("one-life-turn-v1",phase,reason,selected.selectedStep(),
                empty(),selected.purpose(),detail);
    }
    /** The earlier source-bound summary includes native end conditions and must survive recovery guards. */
    private static OpportunityJson.Arr recoveryWarSummary(PlanningRequest request,OrdinaryPolicy.Draft previous) {
        OpportunityJson.Value actual=previous.detail().get("active_wars");
        if(actual==null)return warSummary(request);
        require(actual instanceof OpportunityJson.Arr,"actual active-war summary must remain an array");
        return (OpportunityJson.Arr)actual;
    }
}

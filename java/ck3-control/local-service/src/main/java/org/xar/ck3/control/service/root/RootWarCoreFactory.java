package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.EnumSet;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.application.planning.warexit.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.interactions.KnownPendingInteractionPolicy;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;

/**
 * Concrete physical-runtime installation of all seventeen original WarCore boundaries.
 * Native reads retain the military installer's original typed catalogue; every world
 * proposal returns to the same Root command dispatcher before it can leave planning.
 */
public final class RootWarCoreFactory implements OrdinaryCorePolicy.WarCoreFactory {
    public record Sources(ExactRef factory,EarlyWarCoreLeaves.Sources early,ExactRef battleCore,
            ExactRef battlePrelude,ExactRef assaultLifecycle,ExactRef rankedRoute,ExactRef fallback,
            ExactRef scoreExit,ExactRef ordinaryExit,ExactRef exitReads) {
        public Sources {
            Objects.requireNonNull(early);
            for(ExactRef ref:List.of(factory,early.early(),early.contact(),early.siegeDaily(),battleCore,
                    battlePrelude,assaultLifecycle,rankedRoute,fallback,scoreExit,ordinaryExit,exitReads))
                StrictJson.require(ref.bytes()>0,"actual selected WarCore implementation source required");
        }
    }
    private final RootRuntimeContext context;
    private final Sources sources;
    private final OrdinaryMilitaryInstaller military;
    private final KnownInteractionsRuntimeInstaller interactions;
    private final RootRuntimeCommands commands;
    private final WarExitReads exitReads;
    private final ThreadLocal<Current> current=new ThreadLocal<>();
    private WarCorePlanner created;
    private OrdinaryCorePolicy boundCore;
    public RootWarCoreFactory(RootRuntimeContext actual,Sources sources,OrdinaryMilitaryInstaller sameMilitary,
            KnownInteractionsRuntimeInstaller sameInteractions,RootRuntimeCommands sameCommands) {
        context=Objects.requireNonNull(actual);this.sources=Objects.requireNonNull(sources);
        military=Objects.requireNonNull(sameMilitary);interactions=Objects.requireNonNull(sameInteractions);
        commands=Objects.requireNonNull(sameCommands);
        exitReads=new WarExitReads(this::readExit);
    }
    public Sources sources() { return sources; }
    /** Same current-runtime reader for ordinary termination and M0's separately owned full stage. */
    public WarExitReads actualExitReads() { return exitReads; }
    /** Resolve and read the actual single-winner Java bodies before constructing any physical runtime. */
    public static Sources prepare(RootRuntimeDefinitions.Inputs actual)throws IOException {
        Objects.requireNonNull(actual);
        return new Sources(selected(actual,"local-service","service/root/RootWarCoreFactory"),
                new EarlyWarCoreLeaves.Sources(selected(actual,"application","application/planning/military/EarlyWarCoreLeaves"),
                        selected(actual,"application","application/planning/military/WarContactPolicy"),
                        selected(actual,"application","application/planning/military/WarSiegeDaily")),
                selected(actual,"application","application/planning/military/WarBattleControlCore"),
                selected(actual,"application","application/planning/military/BattleControlPrelude"),
                selected(actual,"application","application/planning/military/AssaultLifecycle"),
                selected(actual,"application","application/planning/military/LateWarCoreLeaves"),
                selected(actual,"application","application/planning/military/LateWarCoreFallback"),
                selected(actual,"application","application/planning/warexit/LegacyWarExitPolicy"),
                selected(actual,"application","application/planning/warexit/WarExitPolicies"),
                selected(actual,"application","application/planning/warexit/WarExitReads"));
    }
    private static ExactRef selected(RootRuntimeDefinitions.Inputs actual,String module,String qualifiedPath)throws IOException {
        String target=module+"/src/main/java/org/xar/ck3/control/"+qualifiedPath+".java";
        var matches=actual.sourceIndex().stream().filter(row->row.targetRelative().equals(target)).toList();
        if(matches.size()!=1)throw new IOException("actual unique WarCore producer is missing from the single-winner graph: "+target);
        ExactRef source=matches.getFirst().sourceRef();
        RootRuntimeDefinitions.read(RootApplicationConfiguration.file(source),64<<20);
        return source;
    }
    /** No caller-supplied leaf list or callback registry can replace a production boundary. */
    @Override public synchronized WarCorePlanner create(WarCorePlanner.CoreContinuation exactSameCoreLink) {
        StrictJson.require(created==null,"one actual WarCore may be created for this physical runtime");
        Objects.requireNonNull(exactSameCoreLink);
        EarlyWarCoreInputs sameInputs=new EarlyWarCoreInputs();
        List<WarCorePlanner.Leaf> actual=productionLeaves(sources,interactions.policy(),exitReads,sameInputs);
        List<WarCorePlanner.Leaf> guarded=actual.stream().map(leaf->new WarCorePlanner.Leaf(leaf.boundary(),
                leaf.implementationSource(),(request,previous)->evaluate(leaf,request,previous))).toList();
        created=new WarCorePlanner(guarded,this::routeTactics,commands,context.reads(),
                military.readDispatcher(),exactSameCoreLink);
        StrictJson.require(created.missingBoundaries().isEmpty(),"concrete WarCore installation omitted an original boundary");
        return created;
    }
    /** Called after OrdinaryCorePolicy.assemble; closes only the already-created same-core interaction link. */
    public synchronized void bind(OrdinaryCorePolicy.Assembly actual) {
        Objects.requireNonNull(actual);
        StrictJson.require(created!=null&&actual.war()==created&&boundCore==null,
                "WarCore factory must bind its own one actual ordinary core exactly once");
        interactions.bindCore(actual.core());boundCore=actual.core();
    }
    public synchronized WarCorePlanner actualWar() {
        StrictJson.require(created!=null,"actual WarCore has not been assembled");return created;
    }
    /**
     * The concrete producer composition is shared by the physical factory and its
     * offline regression. It accepts actual domain objects, never a list of steps.
     */
    static List<WarCorePlanner.Leaf> productionLeaves(Sources s,KnownPendingInteractionPolicy actualPending,
            WarExitReads actualReads,EarlyWarCoreInputs sameInputs) {
        Objects.requireNonNull(s);Objects.requireNonNull(actualPending);Objects.requireNonNull(actualReads);Objects.requireNonNull(sameInputs);
        WarExitPolicies ordinary=WarExitPolicies.ordinaryBeforeTactics(s.ordinaryExit(),actualReads);
        List<WarCorePlanner.Leaf> result=new ArrayList<>();
        result.add(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE,s.scoreExit(),
                (request,previous)->application(LegacyWarExitPolicy.evaluateScoreThresholds(request,previous))));
        result.addAll(actualPending.leaves(actualPending.implementationSource()));
        result.add(BattleControlPrelude.factory(s.battlePrelude()));
        result.add(AssaultLifecycle.factory(s.assaultLifecycle()));
        result.add(new WarCorePlanner.Leaf(WarCorePlanner.Boundary.WAR_TERMINATION_CONTINUATION,s.ordinaryExit(),
                (request,previous)->application(ordinary.evaluateBeforeTactics(request,previous))));
        result.addAll(EarlyWarCoreLeaves.completeFactories(s.early(),s.battleCore(),sameInputs));
        result.addAll(LateWarCoreLeaves.factories(s.rankedRoute(),s.fallback(),sameInputs));
        StrictJson.require(result.size()==17&&result.stream().map(WarCorePlanner.Leaf::boundary)
                .collect(java.util.stream.Collectors.toSet()).equals(EnumSet.allOf(WarCorePlanner.Boundary.class)),
                "all seventeen actual WarCore factories must be installed once");
        return List.copyOf(result);
    }
    private static MilitaryPlanningDecision application(OrdinaryPolicy.Decision selected) {
        if(selected instanceof OrdinaryPolicy.Keep||selected instanceof OrdinaryPolicy.NotApplicable)
            return new MilitaryPlanningDecision.Keep(empty());
        return new MilitaryPlanningDecision.ApplicationDecision(selected);
    }
    private MilitaryPlanningDecision evaluate(WarCorePlanner.Leaf actual,PlanningRequest request,OrdinaryPolicy.Draft previous) {
        try {
            return context.withSession(same->{
                requireRuntime(request);
                if(actual.boundary()==WarCorePlanner.Boundary.TERMINATION_SCORE_PRELUDE)
                    capture(same,request);
                else if(actual.boundary()==WarCorePlanner.Boundary.WAR_SUMMARY_AND_ASSAULT_LIFECYCLE&&!valid(same,request))
                    capture(same,request);
                StrictJson.require(valid(same,request),"WarCore boundary lacks its original current complete planning lease");
                // Native reads and their Driver publication occur after the pure
                // currentPlanning callback has left the frozen observation scope.
                MilitaryPlanningDecision decision=Objects.requireNonNull(actual.producer().evaluate(request,previous));
                if(decision instanceof MilitaryPlanningDecision.ApplicationDecision shared)
                    return new MilitaryPlanningDecision.ApplicationDecision(strongDecision(request,shared.decision()));
                return decision;
            });
        } catch(IOException|UncheckedIOException|IllegalArgumentException|IllegalStateException unavailable) {
            current.remove();
            return new MilitaryPlanningDecision.Unavailable(List.of("actual-root-warcore:"+actual.boundary()+":"
                    +Objects.toString(unavailable.getMessage(),unavailable.getClass().getSimpleName())),
                    "actual same-writer WarCore input or native command producer is unavailable");
        }
    }
    private OrdinaryPolicy.Decision strongDecision(PlanningRequest request,OrdinaryPolicy.Decision actual) {
        // Existing durable UNKNOWN reconciliation retains its original action/body/frame.
        if(actual instanceof OrdinaryPolicy.ReconcileExisting)return actual;
        if(actual instanceof OrdinaryPolicy.Replace replacement&&replacement.draft().command().isPresent()) {
            var draft=replacement.draft();var proposed=draft.command().orElseThrow();
            OriginalCommandClocks.requireCurrentProposal(request,proposed);
            ActionCommand strong=OriginalCommandClocks.requireRebound(request,proposed,commands.requireActualStrong(request,proposed));
            return new OrdinaryPolicy.Replace(new OrdinaryPolicy.Draft(draft.policy(),draft.phase(),draft.reason(),draft.kind(),
                    Optional.of(strong),draft.purpose(),draft.domain(),draft.detail()),replacement.reason());
        }
        return actual;
    }
    private void requireRuntime(PlanningRequest request)throws IOException {
        synchronized(this){StrictJson.require(boundCore!=null,"actual ordinary core has not closed the WarCore/known-policy link");}
        context.requireCurrent(request.deadline());
        StrictJson.require(request.source().equals(context.source())
                &&request.before().machineId().equals(context.game().machineId())
                &&request.before().game().equals(context.game().generation())
                &&request.sessionId().equals(context.game().sessionId()),
                "WarCore request belongs to a predecessor physical runtime");
    }
    private void capture(ContinuityStorePort.Session same,PlanningRequest request)throws IOException {
        context.writer().requireSession(same);
        Current checked=context.collector().currentPlanning(same,request,request.deadline(),(original,lease)->{
            StrictJson.require(original==request&&lease.frame().identity().equals(request.before())
                    &&lease.frame().source().equals(request.source())&&lease.frame().sessionId().equals(request.sessionId()),
                    "WarCore current planning collector changed its original frame");
            return new Current(same,same.head().digest(),request.withHistory(List.of()),lease.validUntil());
        });
        current.set(checked);
    }
    private boolean valid(ContinuityStorePort.Session same,PlanningRequest request)throws IOException {
        context.writer().requireSession(same);Current held=current.get();
        return held!=null&&held.same()==same&&held.headDigest().equals(same.head().digest())
                &&held.nonHistory().equals(request.withHistory(List.of()))
                &&context.clock().instant().isBefore(held.validUntil())
                &&context.clock().instant().isBefore(request.deadline());
    }
    private WarCorePlanner.TacticsResult routeTactics(PlanningRequest request) {
        try {
            return context.withSession(same->{
                requireRuntime(request);
                StrictJson.require(valid(same,request),"route tactics lost its actual same-frame WarCore lease");
                return actualRouteTactics(request);
            });
        } catch(IOException|IllegalArgumentException|IllegalStateException unavailable) {
            return new WarCorePlanner.UnknownTactics(List.of("actual-root-route-tactics:"+Objects.toString(unavailable.getMessage(),"current frame unavailable")));
        }
    }
    static WarCorePlanner.TacticsResult actualRouteTactics(PlanningRequest request) {
        var collected=WarContactObservation.collect(request);
        if(collected instanceof WarContactObservation.Incomplete missing)return new WarCorePlanner.UnknownTactics(missing.missing());
        var known=(WarContactObservation.KnownContact)collected;known.requireSame(request);var actual=known.context();
        List<String> gaps=new ArrayList<>();
        if(!actual.evidenceIssues().isEmpty())gaps.add("actual-global-route-evidence");
        if(actual.globalRouteAudits().stream().anyMatch(a->a.status()==WarContactObservation.AuditStatus.UNAVAILABLE
                ||a.status()==WarContactObservation.AuditStatus.ROUTE_DOES_NOT_REACH_TARGET))gaps.add("actual-global-route-audit");
        if(!gaps.isEmpty())return new WarCorePlanner.UnknownTactics(gaps);
        return new WarCorePlanner.KnownTactics(known.before(),new WarCorePlanner.RouteTactics(
                actual.unsafeArmyIds(),actual.threatenedStationaryArmyIds()));
    }
    private PlanningReadResult<WarExitReads.Query> readExit(PlanningRequest request,WarExitReads.Key key,Obj arguments) {
        // Full power consumes the same existing ArmyForecastReads family. The
        // formal two-query/capture state machine stays with M0's actual policy.
        if(key.kind()==WarExitReads.Kind.PREWAR_COALITION)
            return new PlanningReadResult.Unavailable<>("actual selected native declaration lease is not installed by the ordinary WarCore",Optional.empty());
        try { requireRuntime(request); }
        catch(IOException|IllegalArgumentException|IllegalStateException unavailable) {
            return new PlanningReadResult.Unavailable<>("actual current war input runtime is unavailable: "+unavailable.getMessage(),Optional.empty());
        }
        return dispatchExit(request,key,arguments,military.readDispatcher());
    }
    /** Sole collector-plan producer; the strict military contract retains all original explanatory fields. */
    static MilitaryPlanningDecision.Select exitReadSelection(WarExitReads.Key key,Obj arguments) {
        Objects.requireNonNull(key);Objects.requireNonNull(arguments);
        StrictJson.require(arguments.members().isEmpty(),"ordinary war input reads have no caller-selected native arguments");
        String reason=switch(key.kind()) {
            case OPTIONS -> "collect the original current native war termination options";
            case TERMS -> "collect the original current native war termination terms";
            case POWER -> "collect the original current native war-entry power assessment";
            case PREWAR_COALITION -> throw new IllegalArgumentException("prewar coalition requires its actual selected declaration lease");
        };
        String policy="one-life-turn-v1",phase="native_war_actual_exit_read",operation=WarExitReads.step(key);
        var detail=new Obj(java.util.Map.of("policy",new OpportunityJson.Text(policy),
                "phase",new OpportunityJson.Text(phase),"reason",new OpportunityJson.Text(reason),
                "selected_step",new OpportunityJson.Text(operation)));
        return new MilitaryPlanningDecision.Select(policy,phase,reason,new OperationKey(operation),arguments,
                OrdinaryPolicy.Purpose.READ_ONLY,detail);
    }
    /** The physical entry calls this exact adapter after its current-runtime guard; no second read catalogue exists. */
    static PlanningReadResult<WarExitReads.Query> dispatchExit(PlanningRequest request,WarExitReads.Key key,
            Obj arguments,WarCorePlanner.ReadCatalog sameMilitaryReads) {
        Objects.requireNonNull(request);Objects.requireNonNull(sameMilitaryReads);
        var selected=exitReadSelection(key,arguments);String operation=selected.operation().value();
        var result=sameMilitaryReads.read(request,selected);
        if(result instanceof PlanningReadResult.Unavailable<Obj> missing)
            return new PlanningReadResult.Unavailable<>(missing.reason(),missing.original(),missing.decodeFailure(),missing.observedFailure());
        var known=(PlanningReadResult.Known<Obj>)result;
        StrictJson.require(known.receipt().request().operation().equals(new OperationKey(operation)),
                "actual military termination reader changed its exact operation");
        var encoded=OpportunityJson.toNode(known.value());
        StrictJson.require(encoded instanceof com.fasterxml.jackson.databind.node.ObjectNode,
                "actual typed termination publication must encode its complete object envelope");
        var envelope=(com.fasterxml.jackson.databind.node.ObjectNode)encoded;
        if(key.kind()==WarExitReads.Kind.POWER)
            RootWarPowerReads.requireCurrentEnvelope(request,key,envelope);
        var query=new WarExitReads.Query(key,envelope,known.receipt());
        return new PlanningReadResult.Known<>(query,known.receipt(),known.originalReceipt());
    }
    private record Current(ContinuityStorePort.Session same,String headDigest,PlanningRequest nonHistory,Instant validUntil) {
        private Current {Objects.requireNonNull(same);Objects.requireNonNull(headDigest);Objects.requireNonNull(nonHistory);Objects.requireNonNull(validUntil);}
    }
    private static Obj empty(){return new Obj(java.util.Map.of());}
}


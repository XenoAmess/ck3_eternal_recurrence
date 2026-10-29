package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.atomic.AtomicReference;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.planning.*;
import org.xar.ck3.control.application.planning.military.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.capabilities.army.*;
import org.xar.ck3.control.wave2.military.forecast.CombatObservationCache;
import org.xar.ck3.control.wave2.planning.jointshortlist.JointShortlist.Domain;

/** Per-current-runtime actual ordinary bindings. The central installer alone freezes the shared inventory and 34-stage pipeline. */
public final class OrdinaryMilitaryInstaller {
    public record Sources(ExactRef retreatPolicy,ExactRef commanderPolicy,ExactRef rendezvousPolicy,ExactRef forecastPolicy,
            CommanderBindings.Sources commander,ExactRef forecastReads,ExactRef forecastDecoder,ExactRef planningReads,ExactRef planningDecoder,
            ExactRef warReads,ExactRef warDecoder) {
        public Sources {Objects.requireNonNull(commander);for(ExactRef ref:List.of(retreatPolicy,commanderPolicy,rendezvousPolicy,forecastPolicy,forecastReads,forecastDecoder,planningReads,planningDecoder,warReads,warDecoder))StrictJson.require(ref.bytes()>0,"actual military source required");}
    }
    /** These are the native Army installer's actual objects, including its sole ACTIVE_RETREAT registration and services. */
    public record Army(ArmyRetreatFrames frames,ArmyRetreatDomain domain,ArmyRetreatService retreat,ArmyBattleReads battles) {
        public Army {Objects.requireNonNull(frames);Objects.requireNonNull(domain);Objects.requireNonNull(retreat);Objects.requireNonNull(battles);}
    }
    public record PolicySources(ExactRef originExposurePolicy,ExactRef peacetimePolicy,ExactRef wartimePolicy) {
        public PolicySources {for(ExactRef actual:List.of(originExposurePolicy,peacetimePolicy,wartimePolicy))StrictJson.require(actual.bytes()>0,"actual complete ordinary policy source required");}
    }
    private final RootRuntimeContext context;private final Sources sources;private final Army army;private final CombatObservationCache cache;
    private final CommanderBindings commander;private final ArmyForecastReads forecasts;private final ArmyPlanningReads planning;
    private final MilitaryNativeReadDispatcher dispatcher;private final OrdinaryRetreatRuntime retreat;private final MilitaryCanonicalReads ordinaryReads;
    private final ArmyWarReads warReads;
    public OrdinaryMilitaryInstaller(RootRuntimeContext current,Sources actualSources,Army actualArmy,CombatObservationCache soleCombatCache,
            java.util.function.Supplier<org.xar.ck3.control.application.driver.DriverReadHistoryPublisher> actualReadPublisher) {
        context=Objects.requireNonNull(current);sources=Objects.requireNonNull(actualSources);army=Objects.requireNonNull(actualArmy);cache=Objects.requireNonNull(soleCombatCache);
        ordinaryReads=new MilitaryCanonicalReads(context,actualReadPublisher);var holder=new AtomicReference<CommanderBindings>();
        var observer=new CommanderAssignmentPostcondition(original->{
            try {
                var borrowed=context.borrowedSession();
                if(context.reconciliation().hasActiveFor(borrowed,original))
                    return context.reconciliation().currentForCommand(borrowed,original,lease->{
                        lease.assertCurrent(borrowed);
                        return new CommanderAssignmentPostcondition.ReconciliationCurrent(new CommanderReconciliationCollector.Input(lease.identity(),lease.complete().semantic()),lease.validUntil());
                    });
                context.requireCurrent(original.deadline());
                return context.collector().current(borrowed,original.before(),original.deadline(),lease->{
                    var frame=lease.frame();return new CommanderAssignmentPostcondition.Current(new CommanderObservationCollector.ObservedInput(frame.identity(),frame.source(),frame.sessionId(),original.deadline(),frame.semantic(),lease.bridgeCapabilities()));
                });
            }catch(IOException|IllegalArgumentException|IllegalStateException unavailable){return new CommanderAssignmentPostcondition.FrameUnavailable("actual current commander frame unavailable: "+unavailable.getMessage());}
        },(input,unit)-> {
            try{return holder.get().read(input,unit,context.readCatalog(),context.borrowedSession());}
            catch(IOException unavailable){return new PlanningReadResult.Unavailable<>("actual same-writer commander read unavailable: "+unavailable.getMessage(),java.util.Optional.empty());}
        },context.archive(),(input,unit,deadline)->{
            try{return holder.get().readReconciliation(input,unit,deadline,context.readCatalog(),context.borrowedSession());}
            catch(IOException unavailable){return new PlanningReadResult.Unavailable<>("same-writer reconciliation commander read unavailable: "+unavailable.getMessage(),java.util.Optional.empty());}
        });
        commander=new CommanderBindings(sources.commander(),context.reads(),observer,context.frameLoader(),(guard,archive)->
                context.reconciliation().verifyArchived(guard,archive,context.borrowedSession(),context.originals()));holder.set(commander);
        forecasts=new ArmyForecastReads(sources.forecastReads(),sources.forecastDecoder(),context.reads(),cache,context.frameLoader(),context.archive(),this::borrowed);
        planning=new ArmyPlanningReads(sources.planningReads(),sources.planningDecoder(),ordinaryReads,context.archive(),context.frameLoader(),this::borrowed);
        warReads=new ArmyWarReads(sources.warReads(),sources.warDecoder(),context.reads(),()->
                new ArmyWarReads.IndependentDependencies(forecasts,Objects.requireNonNull(actualReadPublisher.get(),"actual same-runtime independent read publisher is unavailable")));
        dispatcher=new MilitaryNativeReadDispatcher(context,planning,forecasts,army.battles(),ordinaryReads,warReads);retreat=new OrdinaryRetreatRuntime(context,army.domain(),army.retreat(),army.frames());
    }
    private org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session borrowed(){try{return context.borrowedSession();}catch(IOException missing){throw new UncheckedIOException(missing);}}
    public CommanderBindings commander(){return commander;}
    public ArmyForecastReads forecasts(){return forecasts;}
    public ArmyPlanningReads planning(){return planning;}
    public WarCorePlanner.ReadCatalog readDispatcher(){return dispatcher;}
    public CombatObservationCache combatCache(){return cache;}
    public ArmyWarReads warReads(){return warReads;}
    /** Root calls this pure factory from its canonical pending QueryPolicy, inside the one physical capture. */
    public List<RootReconciliationAuthority.AllowedRead> reconciliationReads(ActionReceipt original,ReconciliationIdentity identity,
            org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete actual,java.time.Instant actualDeadline) {
        if(!original.command().operation().value().startsWith("assign-army-commander-v1-army-"))return List.of();
        StrictJson.require(identity.pending().actionId().equals(original.command().actionId())
                &&identity.pending().bodySha256().equals(original.bodySha256())&&identity.pending().originalBefore().equals(original.command().before()),
                "commander allowed query belongs to another canonical primitive");
        var args=CommanderAssignmentPostcondition.arguments(original.command().arguments());
        CommanderAssignmentPostcondition.prepare(original.command());
        var issued=commander.reconciliation(new CommanderReconciliationCollector.Input(identity,actual.semantic()),args.army().intValueExact(),actualDeadline,context.readCatalog());
        return List.of(new RootReconciliationAuthority.AllowedRead(issued.contract(),issued.request().arguments(),RootReconciliationAuthority.QueryKind.COMMANDER_CANDIDATES));
    }
    /** The central factory freezes these identical native families before constructing WarCore or the full ordinary pipeline. */
    public RootDomainInstallation readInstallation() {
        List<RootReadContractCatalog.Family<?,?>> reads=new ArrayList<>(forecasts.families());reads.addAll(planning.families());reads.addAll(commander.readFamilies());reads.addAll(warReads.families());
        return new RootDomainInstallation("ordinary-military-reads",List.of(),List.of(),reads,List.of(),List.of(),List.of(),List.of(commander.actionFamily()),List.of(),List.of(),List.of(),Set.of(),
                List.of(),List.of(),List.of(),List.of(new RootDomainInstallation.FamilyDomain(commander.actionFamily(),Domain.war)),List.of());
    }
    /** Construction does not read Game or start Native. The central assembler consumes this exact actual list once. */
    public List<OrdinaryPolicy> actualPolicies(WarCorePlanner actualWarCore,MilitaryPlanningDecision.CommandFactory originalCommands,
            PolicySources actualSources,MilitaryPeacetimeRuntime actualPeacetime) {
        Objects.requireNonNull(actualWarCore);Objects.requireNonNull(originalCommands);Objects.requireNonNull(actualSources);Objects.requireNonNull(actualPeacetime);
        actualPeacetime.requireContext(context);
        var movement=new MilitaryObservationAdapters();
        var general=new GeneralBattleForecastPolicy(sources.forecastPolicy(),cache,new PrimaryDefenderSiegePolicy(cache,movement,MilitaryObservationAdapters::battle),new ActiveCombatObservedComparison(),actualWarCore::decision);
        var origin=new RouteOriginExposurePolicy(actualSources.originExposurePolicy(),new MilitaryHeldCapitals(context),new RouteOriginExposurePolicy.GeneralForecastPort(){
            @Override public org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj review(PlanningRequest request,org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj candidate){return general.reviewGeneral(request,candidate);}
            @Override public org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj contactAdmission(org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj forecast){
                var result=org.xar.ck3.control.wave2.military.forecast.FixedContactForecast.contactAdmission(org.xar.ck3.control.planning.opportunity.OpportunityJson.toNode(forecast));
                return org.xar.ck3.control.application.driver.DriverJson.object(org.xar.ck3.control.wave2.military.forecast.CombatJson.canonical(result.toJson()),org.xar.ck3.control.application.driver.DriverJson.MAX_NATIVE_BYTES);
            }
        },movement,actualWarCore::decision);
        return List.of(
                new OrdinaryActiveRetreatPolicy(sources.retreatPolicy(),retreat,MilitaryObservationAdapters::controls,new CurrentBattleRetreatModel(),retreat,actualWarCore::decision),
                new CommanderQualityPolicy(sources.commanderPolicy(),request->commander.collector(request,context.readCatalog()),ordinaryReads,
                        (request,selected)->commander.command(request,selected,context.bindings(),originalCommands)),
                new SafeWarRendezvousPolicy(sources.rendezvousPolicy(),movement,actualWarCore::decision),
                general,origin,actualPeacetime.policy(actualSources.peacetimePolicy(),actualWarCore::decision),new M5WartimeObservationPolicy(actualSources.wartimePolicy(),true));
    }
    /** Policy-only installation; callers install readInstallation() exactly once before this phase. */
    public RootDomainInstallation install(WarCorePlanner actualWarCore,MilitaryPlanningDecision.CommandFactory originalCommands,
            PolicySources actualSources,MilitaryPeacetimeRuntime actualPeacetime) {
        return new RootDomainInstallation("ordinary-military-policies",List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),
                actualPolicies(actualWarCore,originalCommands,actualSources,actualPeacetime),List.of(),List.of(),List.of(),List.of());
    }
}

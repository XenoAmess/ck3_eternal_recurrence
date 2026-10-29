package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.battleadvance.*;
import org.xar.ck3.control.application.capabilities.DynamicCapabilities;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverObservationEvidenceReader;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.history.DriverHistoryAccess;
import org.xar.ck3.control.application.history.RouteContactHistoryAdapter;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.application.routecontact.*;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Text;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** The original two Route Contact composites over the installed Life infrastructure and the
 * battle owner's window-only engine. Construction creates no Game, writer, clock, Recon lease,
 * native permission or Ready. Every call still consumes the actual Root source and full history. */
public final class RootRouteContactAdvanceRuntime {
    private RootRouteContactAdvanceRuntime() { }

    public record Sources(ExactRef compositeImplementation,ExactRef resultDecoder,
            ExactRef archivedVerifier,List<ExactRef> supporting) {
        public Sources {
            Objects.requireNonNull(compositeImplementation);Objects.requireNonNull(resultDecoder);
            Objects.requireNonNull(archivedVerifier);supporting=List.copyOf(supporting);
            var all=new LinkedHashSet<ExactRef>(List.of(compositeImplementation,resultDecoder,archivedVerifier));
            all.addAll(supporting);
            require(!supporting.isEmpty()&&all.size()<=48&&all.stream().allMatch(ref->ref.bytes()>0),
                    "complete bounded selected Route proof, clock, archive and replay source closure required");
        }
        public List<ExactRef> all() {
            var all=new LinkedHashSet<ExactRef>(List.of(compositeImplementation,resultDecoder,archivedVerifier));
            all.addAll(supporting);return List.copyOf(all);
        }
    }

    /** Exact existing capability configuration and campaign deadline. Neither typed configuration
     * nor an enabled speed advertises the two operations without their current native/history proof. */
    public static final class Configuration {
        private final ExactRef original;
        private final RawJson bytes;
        private final DynamicCapabilities.Configuration dynamic;
        private final RootCampaignPoliciesFactory.BoundDeadline deadline;
        private final boolean ordinary;
        public Configuration(ExactRef capabilityOriginal,RawJson actualCapabilityBytes,
                RootCampaignPoliciesFactory.BoundDeadline actualDeadline) {
            original=Objects.requireNonNull(capabilityOriginal);bytes=Objects.requireNonNull(actualCapabilityBytes);
            deadline=Objects.requireNonNull(actualDeadline);ordinary=false;
            require(bytes.bytes().length<=65536&&original.bytes()==bytes.bytes().length
                    &&original.sha256().equals(DriverJson.sha256(bytes.bytes())),
                    "actual Route capability configuration bytes/SHA differ");
            dynamic=DynamicCapabilities.decodeConfiguration(DriverJson.object(bytes.bytes(),65536));
            int effective=dynamic.routeContactTimelineSpeed()<=3||dynamic.allowRouteContactHighSpeedAb()
                    ?dynamic.routeContactTimelineSpeed():3;
            require(dynamic.routeContactEffectiveTimelineSpeed()==effective,
                    "Route exact-day speed must retain the original explicit A/B rule");
        }
        private Configuration(ExactRef wholeConfigMetadata,DynamicCapabilities.Configuration actualCapabilities,
                RootCampaignPoliciesFactory.BoundDeadline sameDeadline) {
            original=Objects.requireNonNull(wholeConfigMetadata);dynamic=Objects.requireNonNull(actualCapabilities);
            deadline=Objects.requireNonNull(sameDeadline);ordinary=true;
            bytes=new RawJson(DriverJson.encode(DynamicCapabilities.encodeConfiguration(dynamic)));
            int effective=dynamic.routeContactTimelineSpeed()<=3||dynamic.allowRouteContactHighSpeedAb()
                    ?dynamic.routeContactTimelineSpeed():3;
            require(dynamic.routeContactEffectiveTimelineSpeed()==effective,
                    "Route exact-day speed must retain the original explicit A/B rule");
        }
        public static Configuration ordinary(ExactRef wholeConfigMetadata,DynamicCapabilities.Configuration actualCapabilities,
                RootCampaignPoliciesFactory.BoundDeadline sameDeadline) {
            return new Configuration(wholeConfigMetadata,actualCapabilities,sameDeadline);
        }
        public ExactRef original(){return original;}
        public RootCampaignPoliciesFactory.BoundDeadline deadline(){return deadline;}
        public int effectiveSpeed(){return dynamic.routeContactEffectiveTimelineSpeed();}
        public BattleAdvancePlan.Configuration windowConfiguration() {
            // This object is supplied only to the window-only engine. No committed/objective-hold
            // handler, canary or tactical reconciliation capability is installed by this product.
            return new BattleAdvancePlan.Configuration(dynamic.routeContactTimelineSpeed(),
                    dynamic.allowRouteContactHighSpeedAb(),false,false,false,false,
                    Optional.of(deadline.configuration()));
        }
        public void requireOriginal(ActionPorts.OutcomeArchive archive) {
            if(!ordinary) {
                RawJson current=archive.loadMaterial(original);
                require(java.util.Arrays.equals(current.bytes(),bytes.bytes()),"retained Route capability original changed");
            }
            require(java.util.Arrays.equals(archive.loadMaterial(deadline.original()).bytes(),deadline.bytes()),
                    "retained Route campaign deadline original changed");
        }
    }

    /** The only dynamic family argument is the original parsed literal. Proofs and clock plans
     * are derived from current canonical history; callers never supply them as JSON arguments. */
    public record Operation(OperationKey key) {
        public Operation {Objects.requireNonNull(key);RouteContactSteps.parse(key.value());}
        public RawJson json(){return new RawJson(DriverJson.encode(arguments()));}
        public Obj arguments(){return new Obj(Map.of("operation",new Text(key.value())));}
    }

    /** DATA decoded from the actual canonical receipt and owning archived replay. This record's
     * constructor does not grant history publication or source custody; the actual installed
     * material producer must call readRecorded under the original writer and retain its sources. */
    public record Recorded(ExactRef domainEvidence,NativeEffectEvidence.FrameBasis starting,
            NativeEffectEvidence.FrameBasis ending,List<PlanningReadReceipt> reads,RawJson report) {
        public Recorded {Objects.requireNonNull(domainEvidence);Objects.requireNonNull(starting);
            Objects.requireNonNull(ending);reads=List.copyOf(reads);Objects.requireNonNull(report);}
    }

    public static final class Prepared {
        private final Sources sources;
        private final Configuration configuration;
        private final Map<RootRuntimeContext,Installed> installed=new IdentityHashMap<>();
        private final Set<RootRuntimeContext> entered=Collections.newSetFromMap(new IdentityHashMap<>());
        public Prepared(Sources actualSources,Configuration actualConfiguration) {
            sources=Objects.requireNonNull(actualSources);configuration=Objects.requireNonNull(actualConfiguration);
        }
        public Sources sources(){return sources;}
        public Configuration configuration(){return configuration;}
        public List<ExactRef> requiredSources() {
            var all=new LinkedHashSet<ExactRef>(sources.all());
            all.add(configuration.original());all.add(configuration.deadline().original());return List.copyOf(all);
        }
        public synchronized Installed install(RootRuntimeContext actual,RootLifeRuntimeFactory.Installed sameLife)throws IOException {
            Objects.requireNonNull(actual);Objects.requireNonNull(sameLife);sameLife.requireContext(actual);
            Installed prior=installed.get(actual);
            if(prior!=null){require(prior.life==sameLife,"same Route context cannot replace its installed Life owner");return prior;}
            require(installed.size()<64&&entered.add(actual),"Route installation bound exceeded or partial construction remains unresolved");
            var candidate=new Installed(actual,sameLife,sources,configuration);installed.put(actual,candidate);return candidate;
        }
    }

    public static final class Installed {
        private final RootRuntimeContext context;
        private final RootLifeRuntimeFactory.Installed life;
        private final Sources sources;
        private final Configuration configuration;
        private final RouteContactComposite composite;
        private final RouteContactArchivedVerifier replay;
        private final RootExecutableBindings.CompositeBinding binding;
        private final RootExecutableBindings.CompositeFamily<Operation> family;
        private final RootDomainInstallation installation;
        private Installed(RootRuntimeContext actual,RootLifeRuntimeFactory.Installed sameLife,
                Sources sources,Configuration configuration)throws IOException {
            context=actual;life=sameLife;this.sources=sources;this.configuration=configuration;
            context.game().launchPlan().sources().requireLoadedClass(RootBattleAdvancePublicResult.class);
            context.game().launchPlan().sources().requireLoadedClass(RootLifeAdvancePublicResult.class);
            for(Class<?> type:List.of(RouteContactComposite.class,RouteContactSteps.class,RouteContactProofs.class,
                    RouteContactCodec.class,RouteContactEvidenceCodec.class,RouteContactEvidenceArchive.class,
                    RouteContactArchivedVerifier.class,RouteContactArchivedFrames.class,RouteContactArchivedHistory.class,
                    SharedRouteContactClocks.class,SharedRouteContactArchivedClocks.class,RouteContactHistoryAdapter.class,
                    BattleAdvanceComposite.class,BattleAdvanceArchive.class,BattleAdvancePlan.class))
                context.game().launchPlan().sources().requireLoadedClass(type);
            var infra=life.infrastructure();var timings=infra.timings();var observations=infra.observations();
            var windows=BattleAdvanceComposite.windowExecutor(observations,
                    new AdvanceWait(observations,context.clock(),timings.maximumFrames()),infra.statuses(),
                    configuration.windowConfiguration(),life.readiness(),context.core().actions(),
                    new BattleAdvanceArchive(context.archive()),timings.commandTimeout(),timings.advanceTimeout(),context.clock());
            var histories=new DriverHistoryAccess(()->context.adopted().authority(),context.archive());
            composite=new RouteContactComposite(observations,new RouteContactHistoryAdapter(histories,observations),
                    new SharedRouteContactClocks(windows,infra.timeline(),observations,()->{
                        try {
                            var same=context.borrowedSession();context.writer().requireSession(same);
                            return context.archive().withSession(same);
                        }catch(IOException unavailable){throw new UncheckedIOException(unavailable);}
                    },context.frameLoader()),
                    new RouteContactComposite.Settings(configuration.effectiveSpeed(),true,timings.commandTimeout(),timings.maximumFrames()),
                    context.clock(),new RouteContactEvidenceArchive(context.archive()));
            replay=new RouteContactArchivedVerifier(new RouteContactArchivedFrames(context.frameLoader()),
                    new RouteContactArchivedHistory(),
                    new SharedRouteContactArchivedClocks(context.frameLoader(),configuration.windowConfiguration()),true);
            binding=new RootExecutableBindings.CompositeBinding(composite,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,
                    Optional.empty(),sources.compositeImplementation(),sources.resultDecoder());
            family=new RootExecutableBindings.CompositeFamily<>("original-route-contact-advance",Operation.class,binding,
                    sources.archivedVerifier(),Operation::json,Operation::key,
                    operation->replay.binding(operation.key(),sources.archivedVerifier()),
                    operation->RouteContactSteps.supports(operation.value())?Optional.of(new Operation(operation)):Optional.empty());
            installation=new RootDomainInstallation("actual-route-contact-advance",List.of(),List.of(),List.of(),List.of(),
                    List.of(binding),List.of(),List.of(),List.of(family),List.of(),List.of(),Set.of(),
                    List.of(),List.of(),List.of(),List.of(),List.of());
        }
        public void requireContext(RootRuntimeContext actual)throws IOException {
            if(actual!=context)throw new IOException("Route product crossed its identical physical Root context");
            life.requireContext(actual);life.infrastructure().requireOwner(actual,actual.bindings());
            require(installation.composites().size()==1&&installation.composites().getFirst()==binding
                    &&binding.handler()==composite&&installation.compositeFamilies().getFirst()==family
                    &&context.bindings().compositeFamilies().stream().anyMatch(value->value==family),
                    "Route product lost its identical installed composite/family");
        }
        public RootDomainInstallation installation(){return installation;}
        public RouteContactComposite composite(){return composite;}
        public RouteContactArchivedVerifier replay(){return replay;}
        public Sources sources(){return sources;}
        public List<ExactRef> requiredSources(){
            var all=new LinkedHashSet<ExactRef>(sources.all());all.add(configuration.original());
            all.add(configuration.deadline().original());all.add(life.infrastructure().timings().original());
            return List.copyOf(all);
        }

        /** Existing root-held planning lease only. This method cannot execute any native child.
         * It derives the proof twice through the owning shared guard before returning its final command. */
        public ActionCommand prepare(PlanningRequest request,Complete frame,Known known,Session same,
                OperationKey callerStep,String actualActionId)throws IOException {
            Objects.requireNonNull(request);Objects.requireNonNull(frame);Objects.requireNonNull(known);
            context.writer().requireSession(same);requireContext(context);configuration.requireOriginal(context.archive().withSession(same));
            require(frame.identity().equals(request.before())&&frame.source().equals(request.source())
                    &&frame.sessionId().equals(request.sessionId())&&frame.source().equals(context.source())
                    &&known.stamp().game().equals(request.before().game())
                    &&known.stamp().episodeRunId().equals(request.before().frame().episodeRunId()),
                    "Route public preparation crossed the actual complete native/Driver planning lease");
            var operation=new Operation(callerStep);
            require(context.bindings().issueComposite(family,operation)==binding,"Route typed family issued another composite");
            var provisional=new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,request.before(),request.source(),
                    RouteContactComposite.OBSERVER,List.of(new ExpectedBoolean(new FieldKey("paused"),true)));
            var seed=new ActionCommand(actualActionId,request.before(),request.source(),request.sessionId(),callerStep,
                    operation.arguments(),provisional,new Claims(Set.of(),Set.of(),Set.of(),Set.of()),request.deadline());
            RouteContactModel.Proof proof;
            try {proof=composite.project(seed);}
            catch(RouteContactComposite.ProofUnavailable absent) {
                var failure=new PublicServiceFailure(PublicServiceFailure.Kind.BRIDGE_UNAVAILABLE,
                        RouteContactSteps.parse(callerStep.value()).days()==1
                                ?"route-contact one-day advance proof is stale or incomplete"
                                :"route window complete same-frame inputs changed",Optional.empty());
                failure.initCause(absent);throw failure;
            }
            var owned=RouteContactCodec.frame(LifeAdvanceRootReplay.push(frame)).controlledIds().stream()
                    .map(BigInteger::valueOf).collect(java.util.stream.Collectors.toUnmodifiableSet());
            var expected=new ExpectedPostcondition(ProposalLifecycle.POSTCONDITION_VERSION,request.before(),request.source(),
                    RouteContactComposite.OBSERVER,RouteContactComposite.expected(proof));
            var command=new ActionCommand(actualActionId,request.before(),request.source(),request.sessionId(),callerStep,
                    operation.arguments(),expected,new Claims(owned,Set.of(),Set.of(),Set.of()),request.deadline());
            composite.validate(command);context.writer().requireSession(same);return command;
        }
        /** Actual archived owner replay, then the source-owned complete report. No query or retry.
         * The public facade additionally requires canonical ACTION history publication. */
        public RawJson original(ActionReceipt actual,ActionPorts.OutcomeArchive archive,Session same)throws IOException {
            return readRecorded(actual,archive,same).report();
        }
        /** The only partial-return path is the owning verifier's privately minted replay product.
         * A missing report cannot be inferred from an ACK, status string or an UNKNOWN receipt. */
        public Optional<RouteContactArchivedVerifier.FailureReport> failure(ActionReceipt actual,
                ActionPorts.OutcomeArchive archive,Session same)throws IOException {
            context.writer().requireSession(same);requireContext(context);
            ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
            if(!(actual.state() instanceof ActionState.CompositeUnknown))return Optional.empty();
            return replay.verifyFailure(same.head(),actual,archive);
        }
        public Recorded readRecorded(ActionReceipt actual,ActionPorts.OutcomeArchive archive,Session same)throws IOException {
            context.writer().requireSession(same);requireContext(context);
            ContinuityActionJournal.requireHistoricalReceipt(same.head().state(),actual,archive);
            replay.verify(same.head(),actual,archive);
            var effect=ActionEffects.observation(actual).orElseThrow(()->new IOException("Route has no original completed domain observation"));
            ExactRef evidence=RouteContactEvidenceArchive.basis(effect);
            var document=RouteContactEvidenceCodec.decode(archive.loadFullMaterial(evidence),archive);
            require(document instanceof RouteContactEvidenceCodec.Completed,"a failed Route archive cannot impersonate a complete result");
            var completed=((RouteContactEvidenceCodec.Completed)document).completion();
            var reads=completed.clockResult().nativeStopRead().map(ClockStatusRead.Observation::receipt).stream().toList();
            return new Recorded(evidence,basis(document.starting()),basis(document.ending()),reads,
                    RawJson.fullMaterial(DriverJson.encode(RouteContactEvidenceArchive.compatibleResult(actual,archive))));
        }
        private static NativeEffectEvidence.FrameBasis basis(AdvanceObservationPort.Frame frame) {
            return new NativeEffectEvidence.FrameBasis(frame.originalEvidence(),
                    DriverObservationEvidenceReader.reference(frame.semantic().get("java_driver_facts_evidence")));
        }
    }
}


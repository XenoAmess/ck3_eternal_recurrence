package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.PublicPlanningObservation;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Original changed-player preflight: one actual terminal ROOT read, estate comparison,
 * cache publication outside observation, then the caller's fresh public observation. */
public final class RootChangedSuccessionPreflight {
    private static final String ROOT="query-campaign-root-context-v1";
    private static final List<String> FRAME=List.of("snapshot_id","revision","native_revision","date_raw");
    private final RootRuntimeContext context;
    private final RootLifecycleAuthority physical;
    private final RootNaturalSuccessionOriginals natural;
    private final ReadContract<?> root;
    private final List<ExactRef> sources;
    private final ThreadLocal<ReadWindow> reading=new ThreadLocal<>();
    private final DriverCapabilityRuntime.PublicPlanningTerminalRootReadSource retrySource;

    RootChangedSuccessionPreflight(RootRuntimeContext context,RootLifecycleAuthority physical,
            RootNaturalSuccessionOriginals natural,ExactRef implementation)throws IOException {
        this.context=Objects.requireNonNull(context);this.physical=Objects.requireNonNull(physical);this.natural=Objects.requireNonNull(natural);
        var contracts=natural.terminalContracts().stream().filter(value->value.operation().value().equals(ROOT)
                &&value.guardMode()==ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION).toList();
        require(contracts.size()==1,"changed preflight requires the sole installed terminal ROOT contract");root=contracts.getFirst();
        var refs=new LinkedHashSet<ExactRef>(natural.registration().producerSources());refs.add(Objects.requireNonNull(implementation));sources=List.copyOf(refs);
        retrySource=new DriverCapabilityRuntime.PublicPlanningTerminalRootReadSource(){
            @Override public List<ExactRef> sources(){return sources;}
            @Override public void requireOwner(ContinuityStorePort.Session same,DriverStateAssembler authority,
                    ActionPorts.OutcomeArchive archive,ExecutableStepBindings bindings)throws IOException {
                context.writer().requireSession(same);require(authority==context.adopted().authority()&&archive==context.archive()
                        &&bindings==context.bindings(),"terminal ROOT retry source crossed its actual Root/Driver/archive/bindings");
            }
            @Override public Optional<DriverCapabilityRuntime.PublicPlanningTerminalRootReadScope> current(ContinuityStorePort.Session same)throws IOException {
                context.writer().requireSession(same);var actual=reading.get();
                if(actual==null)return Optional.empty();require(actual.same==same,"terminal ROOT retry scope crossed its actual writer");return Optional.of(actual);
            }
        };
    }
    private final class ReadWindow implements DriverCapabilityRuntime.PublicPlanningTerminalRootReadScope {
        final ContinuityStorePort.Session same;final RootLifecycleAuthority.Lease lease;final String head;final Instant deadline;
        ReadWindow(ContinuityStorePort.Session same,RootLifecycleAuthority.Lease lease,Instant deadline)throws IOException {this.same=same;this.lease=lease;this.head=same.head().digest();this.deadline=deadline;}
        @Override public void requireCurrent(ContinuityStorePort.Session borrowed,ReadContract<?> contract,PlanningReadRequest request,
                PlanningReadResult.Unavailable<?> unavailable,PlanningReadCoordinator.FailedReadAttempt original,ActionPorts.OutcomeArchive archive)throws IOException {
            require(reading.get()==this&&borrowed==same&&same.head().digest().equals(head)&&contract==root,
                    "failed preflight READ lacks its identical live private ROOT/writer/source scope");
            lease.assertCurrent(same);require(request.origin() instanceof CommandOrigin.LifecycleTerminal terminal
                    &&terminal.identity().sameGuardFrame(lease.identity())&&request.source().equals(lease.snapshot().source())
                    &&request.sessionId().equals(lease.identity().sessionId())&&request.operation().equals(root.operation())
                    &&!request.deadline().isAfter(deadline),"failed preflight READ changed its actual terminal request");
            original.requireOriginal(same,contract,request,unavailable,archive);lease.sourceQualification().assertCurrent(same);
        }
    }
    /** Pure DATA predicate; no missing actor or Ready is manufactured. */
    static boolean needsRead(OpportunityJson.Obj semantic,boolean rootAvailable) {
        if(!rootAvailable||!new OpportunityJson.Bool(true).equals(semantic.get("paused"))
                ||!new OpportunityJson.Bool(true).equals(semantic.get("map_ready"))
                ||!new OpportunityJson.Text("played_character_changed").equals(semantic.get("one_life_terminal_reason"))
                ||!(semantic.get("succession_expectation") instanceof OpportunityJson.Obj)
                ||!(semantic.get("revision") instanceof OpportunityJson.IntegerValue))return false;
        return !currentBinding(semantic,semantic.get("succession_reconciliation"));
    }
    private boolean available(PublicPlanningObservation actual) {
        var capabilities=actual.frame().receivedCapabilities();if(capabilities.isEmpty())return false;
        if(!(capabilities.orElseThrow().get("diagnostics") instanceof OpportunityJson.Obj diagnostics)
                ||!(diagnostics.get("hello") instanceof OpportunityJson.Obj hello)
                ||!(hello.get("capabilities") instanceof OpportunityJson.Arr values))return false;
        return root.requiredCapability().map(required->values.items().contains(new OpportunityJson.Text(required))).orElse(true);
    }
    Optional<Prepared> capture(ContinuityStorePort.Session same,PublicPlanningObservation actual,Instant deadline)throws IOException {
        Objects.requireNonNull(actual);Objects.requireNonNull(deadline);context.writer().requireSession(same);actual.assertCurrent(same);
        if(!needsRead(actual.frame().snapshot().semantic(),available(actual)))return Optional.empty();
        require(deadline.isAfter(context.clock().instant()),"changed preflight caller window expired");
        context.game().launchPlan().sources().requireLoadedClass(RootChangedSuccessionPreflight.class);
        context.bindPublicPlanningTerminalRootReadSource(retrySource);
        var result=new Prepared(actual,same.head().digest(),deadline.isBefore(actual.frame().validUntil())?deadline:actual.frame().validUntil());
        actual.assertCurrent(same);return Optional.of(result);
    }
    public final class Prepared {
        private final NativeObservationPort.ObservedFrame received;
        private final DriverSnapshotFacts.Known before;
        private final SourceQualification source;
        private final OpportunityJson.Value expectation;
        private final String head;
        private final Instant until;
        private boolean consumed,performed,refreshed;
        private OpportunityJson.Value comparison;
        private ExactRef comparisonSource;
        private Prepared(PublicPlanningObservation actual,String head,Instant until){received=actual.frame().snapshot().actual();before=actual.frame().driver();source=actual.frame().sourceQualification();expectation=actual.frame().snapshot().semantic().get("succession_expectation");this.head=head;this.until=until;}
        /** Must run after the old public raw callback ends. This method never starts an action. */
        public void perform(Instant deadline)throws IOException {
            Objects.requireNonNull(deadline);require(!consumed,"changed preflight is one-use");consumed=true;
            Instant limit=deadline.isBefore(until)?deadline:until;
            context.withSession(same->{
                physical.requireOutsideObservationScope(same);requireHeadAndPacket(same,head,source,received,until,before);
                var captured=physical.withReceivedSnapshot(same,limit,received,snapshot->physical.withObserved(same,limit,lease->{
                    require(lease.identity().terminalReason()==LifecycleIdentity.TerminalReason.CHANGED
                            &&needsRead(lease.snapshot().semantic(),root.requiredCapability().map(lease.bridgeCapabilities()::contains).orElse(true)),
                            "original changed preflight is no longer required or its actual ROOT capability is unavailable");
                    require(expectation.equals(lease.snapshot().semantic().get("succession_expectation")),"retained expectation changed before actual preflight READ");
                    require(reading.get()==null,"nested changed preflight ROOT scope forbidden");var scope=new ReadWindow(same,lease,limit);reading.set(scope);
                    try{return DriverSuccessionReconciliation.prepare(same,context.adopted().authority(),context.archive(),natural,lease,limit);}
                    finally{reading.remove();}
                }));
                physical.requireOutsideObservationScope(same);
                requireHeadAndPacket(same,captured.writerHeadDigest(),captured.source(),received,captured.validUntil(),captured.before());
                var publication=captured.publication();comparison=publication.auxiliary().get("succession_reconciliation");
                comparisonSource=publication.source();
                require(comparison instanceof OpportunityJson.Obj,"actual estate producer returned no typed reconciliation");
                context.adopted().authority().publishCapabilityInputs(same,publication.expectedStamp(),publication.expectedAuxiliarySha256(),publication);
                performed=true;return null;
            });
        }
        /** The caller takes exactly one fresh actual public observation after perform; no loop or old-frame substitution. */
        public void requireRefreshed(PublicPlanningObservation actual,ContinuityStorePort.Session same)throws IOException {
            require(performed&&!refreshed,"changed preflight requires its one actual fresh public observation");actual.assertCurrent(same);
            var now=actual.frame().snapshot();require(now.actual().session().equals(received.session())
                    &&now.facts().source().equals(context.source())&&expectation.equals(now.semantic().get("succession_expectation"))
                    &&comparison.equals(now.semantic().get("succession_reconciliation")),"fresh changed preflight lost its original Game/source/expectation/comparison");
            if(source.proof().isPresent()&&actual.frame().originalSourceProof().isPresent())
                RootSourceProofContinuity.requireRetainedSourceContinuation(natural.readExact(source.proof().orElseThrow()),
                        natural.readExact(actual.frame().originalSourceProof().orElseThrow()));
            require(DriverObservationEvidenceReader.reference(comparisonSource).equals(actual.frame().driver().auxiliary().get("capability_succession_source")),
                    "fresh preflight lost the actual published comparison source");
            DriverCapabilityStateProducer.replaySuccessionSource(actual.frame().driver().auxiliary(),context.archive().withSession(same));
            natural.readExact(comparisonSource);actual.assertCurrent(same);refreshed=true;
        }
    }
    static boolean currentBinding(OpportunityJson.Obj semantic,OpportunityJson.Value comparison) {
        if(!(comparison instanceof OpportunityJson.Obj value)||!(value.get("successor_binding") instanceof OpportunityJson.Obj binding))return false;
        return FRAME.stream().allMatch(key->semantic.get(key)!=null&&semantic.get(key)!=OpportunityJson.Nil.INSTANCE&&semantic.get(key).equals(binding.get(key)));
    }
    private void requireHeadAndPacket(ContinuityStorePort.Session same,String head,SourceQualification source,
            NativeObservationPort.ObservedFrame received,Instant until,DriverSnapshotFacts.Known expected)throws IOException {
        context.writer().requireSession(same);require(same.head().digest().equals(head)&&context.clock().instant().isBefore(until),"changed preflight lost its exact writer head or physical deadline");
        source.assertCurrent(same);
        var metadata=context.sources().optionalMetadata(same,source);if(metadata.isPresent())metadata.orElseThrow().requireCurrent(same);
        context.game().verify();context.transport().verifyHeld(until);
        var current=context.transport().currentSnapshot(until);
        require(current.session().equals(received.session())&&Arrays.equals(current.originalPacket(),received.originalPacket()),"changed preflight substituted its actual received packet");
        context.adopted().authority().withFrozenFacts(same,frozen->{require(frozen.state() instanceof DriverSnapshotFacts.Known,"changed preflight full Known missing");
            require(Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(expected).bytes(),DriverSnapshotFacts.encodeKnownOriginal((DriverSnapshotFacts.Known)frozen.state()).bytes()),"changed preflight changed one of the seven actual Known fields");return null;});
    }
}

package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.ArrayList;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverCheckpointStore;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.checkpoint.RestoredEpisodeOriginData;
import org.xar.ck3.control.application.capabilities.CampaignRootContextJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverPreclockExpectationSource;
import org.xar.ck3.control.application.driver.DriverPendingEpisodeSource;
import org.xar.ck3.control.application.driver.DriverPendingEpisodeProjection;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.Complete;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.application.planning.events.PendingUiEvent;
import org.xar.ck3.control.application.driver.DriverSuccessionReconciliation;
import org.xar.ck3.control.application.lifecycle.LifecycleObservationPort;
import org.xar.ck3.control.application.lifecycle.NaturalSuccessionPreparation;
import org.xar.ck3.control.application.lifecycle.NaturalSuccessionPreparation.*;
import org.xar.ck3.control.application.lifecycle.LifecycleCommit;
import org.xar.ck3.control.application.lifecycle.LifecycleComposites;
import org.xar.ck3.control.application.lifecycle.LifecyclePublication;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider.Session;
import org.xar.ck3.control.nativebridge.capabilities.family.PrisonerTerminalQueries;
import org.xar.ck3.control.platform.ManagedGameSession;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Originals;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Packet;
import org.xar.ck3.control.runtime.lifecycle.NaturalEngineClockProof;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleCodec;
import org.xar.ck3.control.wave3.governance.lifecycle.SuccessionLifecycleBinding;
import org.xar.ck3.control.wave2.governance.succession.NativePlayerHeirObservation12004.Frame;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;
import org.xar.ck3.control.wave2.prisoners.releasepreview.PrisonerMaterial12004;
import static org.xar.ck3.control.service.root.NaturalClockOriginals.*;

/** Real pre-clock producer and retained-original adapter. M3 remains the sole natural-succession verifier. */
public final class RootNaturalSuccessionOriginals implements ActionPorts.IntentPreparationPort,
        org.xar.ck3.control.application.lifecycle.NaturalSuccessionContinuationSource, RootOriginalNaturalSuccessionVerifier.RootOriginals, DomainBodies.Verifier {
    private static final DomainBodies.Slot SLOT=DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS;
    private static final int LIMIT=WriterContracts.MAX_PIN_BYTES;
    private static final OpportunityJson.Obj EMPTY=new OpportunityJson.Obj(java.util.Map.of());
    private final RootNaturalTimeline timeline;
    private volatile Bound bound;
    private final ThreadLocal<Publication> publishing=new ThreadLocal<>();
    private record Bound(RootApplicationAssembly.Core core,RootRuntimeContext runtime,ManagedGameSession game,
            RootLifecycleAuthority terminal,RootNativeSourceAuthority sources,ReadContract<?> campaignRoot,
            Set<String> clockHandlers,ReadContract<RawJson> prisoner,ReadContract<RawJson> terminalRoot) { }
    private record Publication(ContinuityStorePort.Session session,Document document,String predecessor,
            java.util.Optional<org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceGuard> physical) { }
    private record Qualified(Originals originals,ExactRef document,String head) { }
    private final ThreadLocal<Qualified> held=new ThreadLocal<>();
    private final ThreadLocal<CommittedPreclock> committedPreclock=new ThreadLocal<>();
    private record DomainCommitted(DomainBodies.PreparedImport prepared,WriterContracts.Receipt receipt,WriterContracts.Head head,ExactRef payload) { }
    private record PreclockMaterial(Publication publication,Known driver,Complete complete,PlanningReadReceipt root) { }
    private final ThreadLocal<Boolean> liveRead=new ThreadLocal<>();
    private static final class PendingReadFailureScope {
        private final ContinuityStorePort.Session same;
        private final PendingUiEvent.Source source;
        private final PendingUiEvent.Current current;
        private final ReadContract<?> contract;
        private final PlanningReadRequest request;
        private final PlanningReadPort.FailureEvidenceObserver observer;
        private final String head;
        private boolean readStarted,callbackEntered;
        private PendingReadFailureScope(ContinuityStorePort.Session same,PendingUiEvent.Source source,PendingUiEvent.Current current,
                ReadContract<?> contract,PlanningReadRequest request,PlanningReadPort.FailureEvidenceObserver observer,String head){
            this.same=same;this.source=source;this.current=current;this.contract=contract;this.request=request;this.observer=observer;this.head=head;
        }
    }
    private final ThreadLocal<PendingReadFailureScope> pendingReadFailure=new ThreadLocal<>();
    private final ThreadLocal<Capture> retainedReplay=new ThreadLocal<>();
    private Prepared preparedOwner;
    private volatile Replacement replacement;
    private sealed interface ReplacementOrigin permits RestoredReplacement,EpisodeReplacement { }
    private record RestoredReplacement(RestoreCheckpointService.RestoreBinding binding,
            RestoreCheckpointService.ReboundOrigin origin) implements ReplacementOrigin {
        private RestoredReplacement {Objects.requireNonNull(binding);Objects.requireNonNull(origin);}
    }
    private record EpisodeReplacement(LifecyclePublication lifecycle) implements ReplacementOrigin {
        private EpisodeReplacement {Objects.requireNonNull(lifecycle);}
    }
    private record Replacement(GameGeneration game,String episode,BigInteger actor,ExactRef proof,ReplacementOrigin origin) { }
    private final DriverPreclockExpectationSource preclockSource=new PreclockSource();
    private volatile RootPendingUiRuntime pendingUi;
    private InitialPending activeInitialPending;
    private record PendingDomainAuthority(RootPendingNaturalSuccessionQualification.PendingCause cause,
            LifecycleObservationPort.Snapshot terminal,DriverPendingEpisodeProjection.Prepared projection) { }
    private final ThreadLocal<PendingDomainAuthority> pendingDomainAuthority=new ThreadLocal<>();
    private final ThreadLocal<SuccessionNativeEstate12004.ComparedEstate> qualifiedPendingEstate=new ThreadLocal<>();
    private record PendingEstateMaterial(SuccessionNativeEstate12004.ComparedEstate compared,
            RootPendingNaturalSuccessionQualification.EstateOriginals originals) { }
    private final ThreadLocal<PendingEstateMaterial> pendingEstateOriginals=new ThreadLocal<>();
    private final DriverPendingEpisodeSource pendingEpisodeSource=new DriverPendingEpisodeSource.Recovering(){
        @Override public List<ExactRef> sources(){return registration().producerSources();}
        @Override public DriverPendingEpisodeSource.Capture current(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException {
            var actual=activeInitialPending;requireCurrent(same,expected,actual);return actual;
        }
        @Override public void requireCurrent(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Capture identical)throws IOException {requireInitialPending(same,expected,identical,false,null);}
        @Override public void requirePublished(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Capture identical,Known actualPublished)throws IOException {requireInitialPending(same,expected,identical,true,actualPublished);}
        @Override public DriverPendingEpisodeSource.Mutation currentMutation(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException{return pendingUi().currentMutation(same,expected);}
        @Override public void requireMutation(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Mutation actual)throws IOException{pendingUi().requireMutation(same,expected,actual);}
        @Override public void requirePublishedMutation(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Mutation actual,Known published)throws IOException{pendingUi().requirePublishedMutation(same,expected,actual,published);}
        @Override public void requireChild(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverStateAssembler.PendingEpisodePublication publication,ActionCommand parent,ActionCommand child)throws IOException{pendingUi().requireChild(same,expected,publication,parent,child);}
        @Override public DriverPendingEpisodeSource.Recovery currentRecovery(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException{return pendingUi().currentRecovery(same,expected);}
        @Override public void requireRecovery(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Recovery identical)throws IOException{pendingUi().requireRecovery(same,expected,identical);}
        @Override public void requireRecovered(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Recovery identical,DriverStateAssembler.PendingEpisodePublication genuine,Known current)throws IOException{pendingUi().requireRecovered(same,expected,identical,genuine,current);}

    };
    public DriverPendingEpisodeSource pendingEpisodeSource(){required();return pendingEpisodeSource;}
    synchronized void bindPendingUi(RootPendingUiRuntime actual)throws IOException {
        Objects.requireNonNull(actual);actual.requireContext(required().runtime());require(actual.natural()==this,"pending UI must retain the identical natural producer");
        require(pendingUi==null||pendingUi==actual,"one actual per-Game pending UI owner only");pendingUi=actual;
    }
    private RootPendingUiRuntime pendingUi()throws IOException {
        var actual=pendingUi;if(actual==null)throw new IOException("actual PendingUI runtime is not installed");actual.requireContext(required().runtime());return actual;
    }
    void releaseCompletedPending(InitialCause previous,ActionCommand next)throws IOException {
        require(previous!=null&&(previous==activeInitialPending||pendingUi().ownsInitialCause(previous)),"next transition lost actual previous private pending issuer");
        var same=borrowed();var receipt=find(same,previous.originalParent().actionId());require(receipt.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied applied&&applied.proof().kind()==org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,"previous pending parent has no true final lifecycle receipt");
        var document=readDocument(same).orElseThrow();require(document.ready().isEmpty()&&document.pendingProjection().isEmpty()&&document.capture().episodeRunId().equals(next.lifecycleBefore().subject().episodeRunId())&&!document.capture().episodeRunId().equals(previous.cause().oldEpisodeRunId()),"next pending source needs its actual fresh preclock originals in the committed successor episode");activeInitialPending=null;pendingDateClocks.clear();
    }
    /** Private capture custody survives its genuine app CAS; public fields alone cannot instantiate it. */
    interface InitialCause {
        ActionCommand originalParent();
        RootPendingNaturalSuccessionQualification.PendingCause cause();
        SuccessionNativeEstate12004.ComparedEstate matchedEstate();
        LifecycleObservationPort.Snapshot terminalSnapshot();
        LifecycleObservationPort.Snapshot originalParentFrame();
        Known actualKnown();
        SuccessorUiObligationReducer.PendingEpisode pendingEpisode();
    }
    public static final class InitialPending implements DriverPendingEpisodeSource.Capture,InitialCause {
        private final RootNaturalSuccessionOriginals issuer;private final ContinuityStorePort.Session session;
        private final ActionCommand parent;private final LifecycleObservationPort.Snapshot terminal,originalParentFrame;
        private final RootPendingNaturalSuccessionQualification.PendingCause cause;
        private final SuccessionNativeEstate12004.ComparedEstate matchedEstate;
        private final SuccessorUiObligationReducer.PendingEpisode projection;
        private final DriverPendingEpisodeProjection.Prepared child;private final DomainCommitted committed;private final ExactRef parentKnown;
        private Known published;
        private InitialPending(RootNaturalSuccessionOriginals issuer,ContinuityStorePort.Session session,ActionCommand parent,
                LifecycleObservationPort.Snapshot terminal,LifecycleObservationPort.Snapshot originalParentFrame,
                RootPendingNaturalSuccessionQualification.PendingCause cause,SuccessionNativeEstate12004.ComparedEstate matchedEstate,
                SuccessorUiObligationReducer.PendingEpisode projection,DriverPendingEpisodeProjection.Prepared child,DomainCommitted committed,ExactRef parentKnown) {
            this.issuer=issuer;this.session=session;this.parent=parent;this.terminal=terminal;this.originalParentFrame=originalParentFrame;this.cause=cause;this.matchedEstate=matchedEstate;this.projection=projection;this.child=child;this.committed=committed;this.parentKnown=parentKnown;
        }
        public ActionCommand originalParent(){return parent;}
        public RootPendingNaturalSuccessionQualification.PendingCause cause(){return cause;}
        public SuccessionNativeEstate12004.ComparedEstate matchedEstate(){return matchedEstate;}
        @Override public LifecycleObservationPort.Snapshot originalParentFrame(){return originalParentFrame;}
        @Override public Known actualKnown(){return terminal.facts();}
        @Override public LifecycleObservationPort.Snapshot terminalSnapshot(){return terminal;}
        @Override public SuccessorUiObligationReducer.PendingEpisode pendingEpisode(){return projection;}
        @Override public DomainBodies.PreparedImport originalPrepared(){return committed.prepared();}
        @Override public WriterContracts.Receipt actualReceipt(){return committed.receipt();}
        @Override public ExactRef canonicalDomainRef(){return committed.payload();}
        @Override public DriverPendingEpisodeProjection canonicalProjection(){return child.projection();}
        @Override public ExactRef projectionOriginal(){return child.originalRef();}
        @Override public ExactRef originalParentKnown(){return parentKnown;}
        @Override public ExactRef originalBeforeNative(){return terminal.originalEvidence();}
    }
    /** The actual installed source is bound once to this adopted Driver. A template or detached source cannot supply it. */
    public DriverPreclockExpectationSource preclockExpectationSource() {
        require(preparedOwner!=null&&bound!=null,"preclock Driver source requires its actual installed Root producer");return preclockSource;
    }
    private final class PreclockSource implements DriverPreclockExpectationSource {
        @Override public List<ExactRef> sources() {return registration().producerSources();}
        @Override public DriverPreclockExpectationSource.Capture current(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException {
            var actual=committedPreclock.get();requireCurrent(same,expected,actual);return actual;
        }
        @Override public void requireCurrent(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPreclockExpectationSource.Capture identical)throws IOException {
            requireCommittedPreclock(same,expected,identical);
        }
    }
    /** Private constructor and active same-writer source custody are mandatory. Its getters expose original DATA only. */
    public static final class CommittedPreclock implements DriverPreclockExpectationSource.Capture {
        private final RootNaturalSuccessionOriginals issuer;private final ContinuityStorePort.Session session;
        private final ActionCommand clock;private final PreclockMaterial material;private final DomainCommitted committed;
        private CommittedPreclock(RootNaturalSuccessionOriginals issuer,ContinuityStorePort.Session session,ActionCommand clock,PreclockMaterial material,DomainCommitted committed) {
            this.issuer=issuer;this.session=session;this.clock=clock;this.material=material;this.committed=committed;
        }
        public void requireCurrent(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException {issuer.requireCommittedPreclock(same,expected,this);}
        @Override public Known actualKnown() {return material.driver();}
        @Override public Complete actualComplete() {return material.complete();}
        @Override public PlanningReadReceipt originalRootReceipt() {return material.root();}
        @Override public RawJson originalRootResult() {return material.root().original().originalResultToken().orElseThrow();}
        @Override public ExactRef canonicalDomainRef() {return committed.payload();}
        @Override public ExactRef parentCommandRef() {return material.publication().document().capture().parentCommand();}
        @Override public ExactRef clockCommandRef() {return material.publication().document().capture().clockCommand();}
        @Override public ActionCommand originalClock() {return clock;}
        @Override public DomainBodies.PreparedImport originalPrepared() {return committed.prepared();}
        @Override public WriterContracts.Receipt actualReceipt() {return committed.receipt();}
    }
    /** Exact actual lifecycle DATA gate; unknown/missing profiles never silently become ordinary or rogue. */
    static boolean ordinaryPreclockExpectation(OpportunityJson.Obj semantic) {
        var value=semantic.get("succession_lifecycle");require(value instanceof OpportunityJson.Obj,"actual typed succession lifecycle binding required");
        var profile=SuccessionLifecycleCodec.decode(DriverJson.encode(value)).profile();
        require(profile.ordinary()||profile==SuccessionLifecycleBinding.Profile.ROGUE_ONE_LIFE,"unknown lifecycle cannot publish an ordinary preclock expectation");
        return profile.ordinary();
    }
    private void requireCommittedPreclock(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPreclockExpectationSource.Capture identical)throws IOException {
        require(identical instanceof CommittedPreclock,"only this actual committed preclock source may publish Driver expectation");
        var actual=(CommittedPreclock)identical;core().writer().requireSession(same);
        require(actual.issuer==this&&committedPreclock.get()==actual&&actual.session==same
                &&required().runtime().adopted().authority()==expected,"preclock token escaped its private source/current thread/original writer/Driver");
        require(ordinaryPreclockExpectation(actual.material.complete().semantic()),"only actual ordinary campaign preclock can publish the ordinary expectation");
        var capture=actual.material.publication().document().capture();var committed=actual.committed;var head=same.head();
        require(head.digest().equals(committed.head().digest())&&committed.receipt().disposition()==WriterContracts.Disposition.COMMITTED
                &&committed.receipt().writes()>0&&ContinuityJson.digest(committed.receipt().head().toJson()).equals(head.digest())
                &&head.state().sequence()==capture.ledgerSequenceBeforeCapture()+1
                &&committed.prepared().predecessor().digest().equals(capture.headBeforeCapture()),"preclock source needs its actual fresh committed domain head and immediate original predecessor");
        same.requireHistoricalState(capture.ledgerSequenceBeforeCapture(),capture.headBeforeCapture());
        var domain=same.readDomain(SLOT);require(domain instanceof DomainBodies.Available,"actual committed preclock domain unavailable");
        var available=(DomainBodies.Available)domain;byte[] body=encode(actual.material.publication().document());
        require(available.reference().contractSchema().equals(SCHEMA)&&available.reference().payload().equals(committed.payload())
                &&Arrays.equals(available.canonicalBody(),body)&&Arrays.equals(readExact(committed.payload()),body)
                &&Arrays.equals(committed.prepared().request().producerInput(),body),"preclock token differs from its actual canonical domain payload/original body");
        validateCapture(same,capture);checkPhysical(same,capture,actual.clock.deadline());
        require(actual.clock.origin() instanceof CommandOrigin.Gameplay&&actual.material.complete().identity().equals(actual.clock.before())
                &&actual.material.complete().source().equals(actual.clock.source())&&actual.material.complete().sessionId().equals(actual.clock.sessionId())
                &&actual.material.complete().originalEvidence().equals(capture.nativePacket())
                &&Arrays.equals(DriverJson.encode(actual.material.complete().semantic()),readExact(capture.semantic()))
                &&actual.material.root().request().before().equals(actual.clock.before())
                &&Arrays.equals(actual.material.driver().driver().encode(),readExact(capture.driver()))
                &&Arrays.equals(stamp(actual.material.driver().stamp()),readExact(capture.driverStamp()))
                &&Arrays.equals(actual.material.root().original().originalResultToken().orElseThrow().bytes(),readExact(capture.rootResult()))
                &&archive(same).loadRead(capture.rootRead()).equals(actual.material.root()),"preclock token replaced its actual complete Driver/frame/root originals");
        var parent=clockParent(same,actual.clock).orElseThrow(()->new IOException("original running preclock parent unavailable"));
        require(parent.command().actionId().equals(capture.parentActionId())&&parent.bodySha256().equals(capture.parentBodySha256())
                &&Arrays.equals(ActionCodec.encodeCommand(actual.clock),readExact(capture.clockCommand())),"preclock source changed its actual reserved parent/clock body");
        core().actions().withFrozen(same,lease->{require(lease.find(actual.clock.actionId()).isEmpty(),"preclock publication cannot re-enter an existing INTENT/Attempt/UNKNOWN");lease.assertCurrent();return null;});
        var physical=required().sources().verifyLifecycle(same,new NativeObservationPort.TransportSession(capture.machineId(),actual.clock.before().game(),new BigInteger(capture.connectionGeneration()),capture.sessionId()),
                actual.clock.source(),capture.nativePacket(),required().game().nativeTransport().diagnostics(),actual.clock.deadline());
        physical.assertCurrent(same);
    }
    /** Core-lifetime domain registration. Per-Game installers never replace its writer or registration. */
    public static final class Prepared implements DomainBodies.Verifier {
        private final List<ExactRef> sources;private final ExactRef timelineDefinition,closeDefinition;
        private final DomainBodies.Registration registration;
        private RootApplicationAssembly.Core core;
        private final ThreadLocal<RootNaturalSuccessionOriginals> live=new ThreadLocal<>();
        public Prepared(List<ExactRef> sources,ExactRef timelineDefinition,ExactRef closeDefinition) {
            this.sources=List.copyOf(sources);this.timelineDefinition=Objects.requireNonNull(timelineDefinition);this.closeDefinition=Objects.requireNonNull(closeDefinition);
            require(!this.sources.isEmpty()&&this.sources.size()<=64&&this.sources.stream().distinct().count()==this.sources.size(),"finite unique actual Core-lifetime original producer sources");
            registration=new DomainBodies.Registration(SLOT,SCHEMA,MAX_BYTES,this.sources,this);
        }
        /** The catalog and each per-Game producer retain the identical original Core registration object. */
        public DomainBodies.Registration registration() {return registration;}
        public synchronized void linkCore(RootApplicationAssembly.Core actual) {require(core==null&&actual.archive().writer()==actual.writer(),"one original Core/writer link only");core=actual;}
        public RootNaturalSuccessionOriginals install(RootRuntimeContext context,RootLifecycleAuthority terminal,RootNativeSourceAuthority nativeSources,
                ReadContract<?> existingCampaignRoot,ExactRef terminalPrisonerDefinition,Set<String> actualClockHandlers,
                org.xar.ck3.control.nativebridge.NativePrivateActionPermission.QualificationVerifier closeQualifier)throws IOException {
            return install(context,terminal,nativeSources,existingCampaignRoot,terminalPrisonerDefinition,actualClockHandlers,closeQualifier,Optional.empty());
        }
        RootNaturalSuccessionOriginals install(RootRuntimeContext context,RootLifecycleAuthority terminal,RootNativeSourceAuthority nativeSources,
                ReadContract<?> existingCampaignRoot,ExactRef terminalPrisonerDefinition,Set<String> actualClockHandlers,
                org.xar.ck3.control.nativebridge.NativePrivateActionPermission.QualificationVerifier closeQualifier,
                Optional<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> originalPermission)throws IOException {
            synchronized(this){require(core!=null&&context.core()==core&&context.writer()==core.writer(),"per-Game natural installation crossed its original Core/writer");}
            context.game().verify();var installed=new RootNaturalSuccessionOriginals(sources,timelineDefinition,closeDefinition,closeQualifier,originalPermission);installed.preparedOwner=this;
            installed.bind(context,terminal,nativeSources,existingCampaignRoot,terminalPrisonerDefinition,actualClockHandlers);return installed;
        }
        private RootNaturalSuccessionOriginals actual() {var value=live.get();require(value!=null&&value.preparedOwner==this&&value.core()==core,"a detached JSON import has no actual per-Game producer publication");return value;}
        @Override public String verify(ContinuityState head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException {return actual().verify(head,previous,request,original);}
        @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException {return actual().verify(head,previous,request,original);}
    }

    /** Create before Core.open so this one domain registration is installed in the original writer. */
    public RootNaturalSuccessionOriginals(List<ExactRef> actualProducerClosure,ExactRef timelineDefinition,
            ExactRef closeDefinition,org.xar.ck3.control.nativebridge.NativePrivateActionPermission.QualificationVerifier closeQualifier) {
        this(actualProducerClosure,timelineDefinition,closeDefinition,closeQualifier,Optional.empty());
    }
    RootNaturalSuccessionOriginals(List<ExactRef> actualProducerClosure,ExactRef timelineDefinition,
            ExactRef closeDefinition,org.xar.ck3.control.nativebridge.NativePrivateActionPermission.QualificationVerifier closeQualifier,
            Optional<org.xar.ck3.control.nativebridge.NativePrivateActionPermission> originalPermission) {
        var producerSources=List.copyOf(actualProducerClosure);
        require(!producerSources.isEmpty()&&producerSources.size()<=64&&producerSources.stream().distinct().count()==producerSources.size(),"finite exact natural-original producer closure");
        timeline=new RootNaturalTimeline(this,timelineDefinition,closeDefinition,closeQualifier,originalPermission);
    }
    public DomainBodies.Registration registration() {require(preparedOwner!=null,"production registration belongs to the Core-lifetime Prepared owner");return preparedOwner.registration();}
    public RootNaturalTimeline timeline() { return timeline; }
    /** Core and application constructors are private Root producers; this retains their exact same instances. */
    public synchronized void bind(RootRuntimeContext runtime,
            RootLifecycleAuthority terminal,RootNativeSourceAuthority sources,ReadContract<?> existingCampaignRoot,
            ExactRef terminalPrisonerDefinition,Set<String> actualInstalledClockHandlerIds) {
        var core=runtime.core();var game=runtime.game();
        require(bound==null&&runtime.writer()==core.writer()&&runtime.archive()==core.archive()
                &&runtime.source().machineId().equals(game.machineId()),"one actual Root/Game/writer binding only");
        require(existingCampaignRoot.operation().value().equals("query-campaign-root-context-v1")
                &&existingCampaignRoot.guardMode()==ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,"use the installed original campaign-root read, never another route");
        Set<String> handlers=Set.copyOf(actualInstalledClockHandlerIds);require(!handlers.isEmpty()&&handlers.size()<=32,"explicit installed clock composite handlers required");
        var prisoner=PrisonerTerminalQueries.contract(terminalPrisonerDefinition,(request,actual,args)->admitTerminal(request));
        var terminalRoot=new ReadContract<RawJson>("lifecycle/campaign-root12004/v1",existingCampaignRoot.operation(),existingCampaignRoot.requiredCapability(),existingCampaignRoot.permissionKey(),existingCampaignRoot.permissionMode(),existingCampaignRoot.wireProfile(),ReadContract.GuardMode.LIFECYCLE_TERMINAL_SESSION,existingCampaignRoot.sourceRef(),request->{
            require(request.arguments().members().isEmpty(),"terminal original campaign root has no additional arguments");admitTerminal(request);return new NativeRequest(request.operation().value(),existingCampaignRoot.requiredCapability(),new RawJson(new byte[]{'{','}'}));
        },this::decodeTerminalRoot);
        bound=new Bound(core,runtime,game,Objects.requireNonNull(terminal),Objects.requireNonNull(sources),existingCampaignRoot,handlers,prisoner,terminalRoot);
    }
    public List<ReadContract<?>> terminalContracts() { return List.of(required().prisoner(),timeline.contract(),required().terminalRoot()); }
    public ReadContract<RawJson> prisonerContract() {return required().prisoner();}
    /** Original convenience entry; the ordinary restore chain uses the same-writer overload below. */
    public void admitRestoredSource(Instant deadline)throws IOException,InterruptedException {
        var actual=required().runtime().requireRestoration(deadline);
        core().writer().locked(same->{admitRestoredSource(same,actual,deadline);return null;});
    }
    /**
     * Consume the actual private restore binding before ordinary planning, in its original writer scope.
     * FIRST may already have initialized domains; only the exact original domain-import suffix is legal.
     * This retains provenance and grants no fresh Native, SAVE, restore or lifecycle permission.
     */
    public void admitRestoredSource(ContinuityStorePort.Session same,
            RestoreCheckpointService.RestoreBinding actual,Instant deadline)throws IOException {
        var runtime=required().runtime();core().writer().requireSession(same);runtime.requireCurrent(deadline);
        runtime.requireRestorationOriginal(same,Objects.requireNonNull(actual));
        var origin=runtime.requireRestoredOrigin(same);
        require(origin==actual.requireReboundOrigin(same),"natural restoration must retain the identical private restore issuer");
        var pair=actual.pair();var saved=actual.savedMaterial().savedDriver();var restored=actual.driver();
        var savedFrame=pair.frame().frame();
        require(actual.session().game().equals(required().game().generation())
                &&actual.session().sessionId().equals(required().game().sessionId())
                &&actual.session().machineId().equals(required().game().machineId())&&actual.source().equals(runtime.source())
                &&actual.savedMaterial().pair().equals(pair)
                &&saved.session().actorId().equals(savedFrame.identity().player())
                &&saved.session().episodeRunId().equals(savedFrame.episodeRunId())
                &&restored.session().bridgePid()==actual.session().game().pid()
                &&restored.session().actorId().equals(saved.session().actorId())
                &&restored.session().episodeRunId().equals(saved.session().episodeRunId()),
                "natural restored source crossed its actual paired SAVE/Game/session/actor/run");
        require(saved.campaignGoal().getClass().equals(restored.campaignGoal().getClass()),
                "natural restored source changed saved goal presence/null semantics");
        if(saved.campaignGoal() instanceof DriverStateSnapshot.Value oldGoal
                &&restored.campaignGoal() instanceof DriverStateSnapshot.Value newGoal)
            require(StrictJson.parse(oldGoal.json(),DriverCheckpointStore.MAX_DRIVER_BYTES)
                    .equals(StrictJson.parse(newGoal.json(),DriverCheckpointStore.MAX_DRIVER_BYTES)),
                    "natural restored source changed the complete saved goal/calendar");
        require(Arrays.equals(restored.encode(),readExact(actual.semantic().originalDriver())),
                "natural restored source lost the original complete restored Driver");
        String attachmentDigest=ContinuityJson.digest(actual.attachment().head().toJson());
        same.requireDomainImportContinuation(actual.attachment().head().sequence(),attachmentDigest);
        byte[] originBytes=origin.evidence().encode();
        require(Arrays.equals(originBytes,RestoredEpisodeOriginData.decode(originBytes).encode()),
                "natural restored source origin must round trip with its original field types");
        String before=same.head().digest();
        synchronized(this) {
            if(replacement!=null) {
                require(replacement.origin() instanceof RestoredReplacement retained
                        &&retained.binding()==actual&&retained.origin()==origin
                        &&replacement.game().equals(actual.session().game())
                        &&replacement.episode().equals(actual.episodeRunId())
                        &&replacement.actor().equals(restored.session().actorId()),
                        "another actual replacement source is already admitted");
                readExact(replacement.proof());runtime.requireCurrent(deadline);return;
            }
            var row=StrictJson.object().put("schema","xar.java.natural-new-game-original-admission/v2")
                    .put("kind","restored").put("event_identity",actual.attachment().eventIdentity());
            row.set("actual_game",actual.session().game().toJson());
            row.set("canonical_attachment_head",put(same,StrictJson.canonical(actual.attachment().head().toJson(),StrictJson.EXPLICIT_MAX_BYTES)).toJson());
            row.set("restored_origin",put(same,originBytes).toJson());
            row.set("history_basis",actual.originalHistoryBasis().toJson());
            row.set("semantic",actual.semantic().semantic().toJson());
            row.set("native_packet",actual.semantic().originalNativePacket().toJson());
            row.set("original_driver",actual.semantic().originalDriver().toJson());
            ExactRef proof=put(same,StrictJson.canonical(row,MAX_BYTES));readExact(proof);
            origin.requireOriginal(same);runtime.requireRestorationOriginal(same,actual);runtime.requireCurrent(deadline);
            same.requireDomainImportContinuation(actual.attachment().head().sequence(),attachmentDigest);
            require(before.equals(same.head().digest()),"natural restored source admission mutated its canonical writer head");
            replacement=new Replacement(actual.session().game(),actual.episodeRunId(),restored.session().actorId(),
                    proof,new RestoredReplacement(actual,origin));
        }
    }
    /** Consume only the original shared cycle journal's private episode token, never a resumed PID projection. */
    public void admitEpisodeSource(ContinuityStorePort.Session same,ContinuityBatchJournal journal,ContinuityBatchJournal.ReboundEpisode actual)throws IOException {
        core().writer().requireSession(same);journal.requireCurrent(same,actual);var binding=actual.binding();
        require(actual.session().game().equals(required().game().generation())&&actual.session().sessionId().equals(required().game().sessionId()),"actual episode admission belongs to another Root Game/session");
        var row=StrictJson.object().put("schema","xar.java.natural-new-game-original-admission/v1").put("kind","episode").put("event_identity",actual.committed().eventIdentity()).put("lifecycle_commit_digest",binding.commitDigest());row.set("actual_game",actual.session().game().toJson());row.set("canonical_episode_head",put(same,StrictJson.canonical(actual.committed().head().toJson(),StrictJson.EXPLICIT_MAX_BYTES)).toJson());row.set("lifecycle_parent",archive(same).preserveReceipt(binding.parent()).toJson());row.set("semantic",binding.semantic().semantic().toJson());row.set("native_packet",binding.semantic().originalNativePacket().toJson());row.set("original_driver",binding.semantic().originalDriver().toJson());
        synchronized(this){require(replacement==null,"actual replacement source is once admitted");replacement=new Replacement(actual.session().game(),binding.driver().session().episodeRunId(),binding.driver().session().actorId(),put(same,StrictJson.canonical(row,MAX_BYTES)),new EpisodeReplacement(binding.publication()));}
    }
    /** Same native root producer, distinct actual terminal guard profile; no fake ordinary actor identity. */
    public PlanningReadResult.Known<RawJson> readCurrentCampaignRoot(RootLifecycleAuthority.Lease lease,Instant deadline)throws IOException {
        var same=borrowed();lease.assertCurrent(same);var result=read(same,required().terminalRoot(),new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(lease.identity()),lease.snapshot().source(),lease.identity().sessionId(),required().terminalRoot().operation(),EMPTY,deadline));lease.assertCurrent(same);return result;
    }
    public Capture capturedPredecessor(RootLifecycleAuthority.Lease lease)throws IOException {lease.assertCurrent(borrowed());var capture=readDocument(borrowed()).orElseThrow(()->new IOException("actual preclock capture missing")).capture();requireCaptureSubject(capture,lease.identity(),lease.snapshot().source());return capture;}
    public ExactRef capturedPredecessorSource(RootLifecycleAuthority.Lease lease)throws IOException {capturedPredecessor(lease);return currentCaptureDocument();}
    private RawJson decodeTerminalRoot(PlanningReadReceipt receipt) {
        try {
            var same=borrowed();var archive=archive(same);var actual=receipt.request().origin().requireLifecycleTerminal();
            require(receipt.contractId().equals("lifecycle/campaign-root12004/v1")&&receipt.request().operation().equals(required().campaignRoot().operation()),"not the actual terminal original campaign root");
            for(var guard:List.of(receipt.before(),receipt.after())) {var replay=RootLifecycleGuardEvidence.replay(guard.binding(),archive,same,core().originals());require(actual.sameGuardFrame(replay.identity())&&receipt.request().source().equals(replay.original().facts().source()),"terminal root crossed original semantic/source frame");}
            require(receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())&&receipt.before().binding().authorityId().equals(receipt.after().binding().authorityId()),"terminal root crossed held source authority");
            var token=receipt.original().originalResultToken().orElseThrow(()->new IOException("terminal root original token absent"));var envelope=StrictJson.object(StrictJson.parse(receipt.original().originalFrame().bytes(),1<<20),Set.of("type","protocol_version","request_id","ok","result"));StrictJson.integer(envelope.get("protocol_version"),1,1);
            require("command_result".equals(StrictJson.text(envelope.get("type")))&&receipt.requestId().equals(StrictJson.text(envelope.get("request_id")))&&envelope.get("ok").isBoolean()&&envelope.get("ok").booleanValue()&&envelope.get("result").equals(StrictJson.parse(token.bytes(),1<<20)),"terminal root native original frame/token drift");
            var parsed=DriverJson.object(token.bytes(),1<<20);var normalized=CampaignRootContextJson.normalizeNativeResult(parsed,actual.frame().dateRaw(),actual.frame().nativeRevision());
            var context=OpportunityJson.object(normalized.get("campaign_root_context"),"actual root context");require(actual.currentPlayer() instanceof LifecycleIdentity.Character player&&player.alive()&&OpportunityJson.integer(context.get("player_character_id"),"player_character_id").equals(player.characterId())&&OpportunityJson.bool(context.get("player_character_alive"),"player_character_alive"),"terminal root current actor differs from actual living successor");return token;
        } catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    Bound required() { Bound value=bound;if(value==null)throw new IllegalStateException("original Root natural producer is not bound");return value; }
    ContinuityStorePort.Session borrowed() throws IOException { return required().core().writer().borrowedSession(); }
    RootApplicationAssembly.Core core() { return required().core(); }
    RootLifecycleAuthority terminal() { return required().terminal(); }
    ActionPorts.OutcomeArchive archive(ContinuityStorePort.Session same) { return core().archive().withSession(same); }
    void admitTerminal(PlanningReadRequest request) {
        try {
            var same=borrowed();terminal().current(same,request.origin().requireLifecycleTerminal(),request.deadline(),lease->{
                require(lease.identity().sameGuardFrame(request.origin().requireLifecycleTerminal())
                        &&lease.snapshot().source().equals(request.source())&&request.sessionId().equals(required().game().sessionId()),"terminal query crossed its exact live Root lease");
                lease.assertCurrent(same);return null;
            });
        } catch(IOException failure) { throw new UncheckedIOException(failure); }
    }
    /** Only the genuine resume child of an already durable registered clock composite enters this hook. */
    @Override public void prepare(ContinuityStorePort.Session same,ActionCommand clock) {
        if(!clock.operation().value().equals("resume-map"))return;
        try {
            if(pendingDateClocks.containsKey(clock.actionId())){requirePendingDateClock(same,clock);return;}
            core().writer().requireSession(same);required().runtime().requireCurrent(clock.deadline());var selectedParent=clockParent(same,clock);if(selectedParent.isEmpty())return;var parent=selectedParent.orElseThrow();
            var previous=readDocument(same);
            if(previous.isPresent()) {
                Capture old=previous.orElseThrow().capture();
                require(!old.clockActionId().equals(clock.actionId()),"a retained preclock capture never authorizes re-entry or replay");
                boolean sameGame=old.gamePid()==clock.before().game().pid()&&old.gameBirthFiletime().equals(clock.before().game().creationFiletime().value().toString())&&old.sessionId().equals(clock.sessionId());
                if(!sameGame)requireReplacement(same,clock);
                else {ActionReceipt prior=find(same,old.clockActionId());boolean sameActor=old.predecessorFrame().actorCharacterId()==clock.before().frame().identity().player().intValueExact()&&old.episodeRunId().equals(clock.before().frame().episodeRunId());
                    if(sameActor)require(previous.orElseThrow().ready().isEmpty()&&prior.settled(),"an unresolved original clock cannot be replaced in the same episode");
                    else requireCommittedNaturalSuccessor(same,previous.orElseThrow(),clock);require(old.source().equals(clock.source()),"a changed source cannot replace predecessor originals");}
            }
            String predecessor=same.head().digest();long sequence=same.head().state().sequence();
            var captured=required().runtime().collector().current(same,clock.before(),clock.deadline(),lease->{
                require(lease.frame().identity().equals(clock.before())&&lease.frame().source().equals(clock.source()),"actual pre-clock frame drift");
                var result=core().planningReads().read(same,required().campaignRoot(),new PlanningReadRequest(lease.frame().identity(),clock.source(),clock.sessionId(),required().campaignRoot().operation(),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),clock.deadline()));
                PlanningReadResult.Known<?> known=known(result);PlanningReadReceipt receipt=known.receipt();
                var original=receipt.original().originalResultToken().orElseThrow(()->new IOException("original GetPlayerHeir result token absent"));
                Frame frame=frame(lease.frame().semantic(),clock.before().frame().identity().player().intValueExact());
                NativePlayerHeirObservation12004.parseNativeResult(original.bytes(),frame);
                var exe=executable();var file=SharedSourceFiles.nativeFile(Path.of(exe.path()));
                Capture capture=new Capture(parent.command().actionId(),parent.bodySha256(),put(same,ActionCodec.encodeCommand(parent.command())),
                        clock.actionId(),ActionCodec.bodySha256(clock),put(same,ActionCodec.encodeCommand(clock)),clock.before().machineId(),clock.sessionId(),clock.before().game().pid(),clock.before().game().creationFiletime().value().toString(),
                        lease.frame().connectionGeneration().toString(),clock.before().frame().episodeRunId(),clock.source(),frame,exe,file.fileIdDecimal(),mtime(file),
                        known.originalReceipt(),put(same,original.bytes()),lease.frame().originalEvidence(),put(same,DriverJson.encode(lease.frame().semantic())),
                        put(same,stamp(lease.driver().stamp())),put(same,lease.driver().driver().encode()),lease.originalHello(),lease.originalSourceQualification(),predecessor,sequence,Optional.ofNullable(replacement).map(Replacement::proof));
                var physical=required().sources().verifyLifecycle(same,new NativeObservationPort.TransportSession(capture.machineId(),clock.before().game(),new BigInteger(capture.connectionGeneration()),capture.sessionId()),clock.source(),capture.nativePacket(),required().game().nativeTransport().diagnostics(),clock.deadline());
                return new PreclockMaterial(new Publication(same,new Document(capture,Optional.empty(),Optional.empty(),lease.frame().observedAt()),predecessor,physical.guard()),lease.driver(),lease.frame(),receipt);
            });
            // Both canonical original import and the sole Driver publication start after the physical read freeze has closed.
            DomainCommitted committed=publish(same,captured.publication());
            if(!ordinaryPreclockExpectation(captured.complete().semantic()))return;
            require(committedPreclock.get()==null,"a preclock Driver source cannot be nested or replaced");
            var token=new CommittedPreclock(this,same,clock,captured,committed);
            committedPreclock.set(token);
            try {required().runtime().adopted().authority().publishPreclockExpectation(same);}
            finally {committedPreclock.remove();}
        } catch(IOException failure) { throw new UncheckedIOException("original preclock capture unavailable; clock must not dispatch",failure); }
    }
    private record PendingDateClock(ActionCommand parent,ActionCommand clock,String requestId,NativeRequest request,
            Document original,ExactRef originalRef,ExactRef pendingDomain,ContinuityStorePort.Session writer,
            java.util.Optional<org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceGuard> physical) { }
    private final Map<String,PendingDateClock> pendingDateClocks=new LinkedHashMap<>();
    /** Same original ROOT/GetPlayerHeir producer, retained in this actual request before IntentDurable. */
    NativeRequest preparePendingDateClock(ContinuityStorePort.Session same,ActionCommand parent,ActionCommand clock,
            String requestId,NativeRequest base,RootLifecycleAuthority.SnapshotLease lease,ExactRef pendingDomain)throws IOException {
        core().writer().requireSession(same);lease.assertCurrent(same);require(clock.operation().value().equals("resume-map")&&base.step().equals("resume-map")&&parent.operation().value().equals("life-advance"),"only the genuine finite date Life/resume may retain this preclock original");
        require(!pendingDateClocks.containsKey(clock.actionId()),"retained date preclock cannot be prepared or submitted twice");
        var complete=lease.ordinary().orElseThrow();require(complete.identity().equals(clock.before())&&complete.source().equals(clock.source()),"private date clock changed its real pre-write physical frame");
        var result=core().planningReads().read(same,required().campaignRoot(),new PlanningReadRequest(complete.identity(),clock.source(),clock.sessionId(),required().campaignRoot().operation(),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),clock.deadline()));
        var actual=known(result);var token=actual.receipt().original().originalResultToken().orElseThrow(()->new IOException("date preclock lacks actual ROOT result"));
        var predecessor=frame(complete.semantic(),complete.identity().frame().identity().player().intValueExact());NativePlayerHeirObservation12004.parseNativeResult(token.bytes(),predecessor);
        var exe=executable();var file=SharedSourceFiles.nativeFile(Path.of(exe.path()));
        var capture=new Capture(parent.actionId(),ActionCodec.bodySha256(parent),put(same,ActionCodec.encodeCommand(parent)),clock.actionId(),ActionCodec.bodySha256(clock),put(same,ActionCodec.encodeCommand(clock)),clock.before().machineId(),clock.sessionId(),clock.before().game().pid(),clock.before().game().creationFiletime().value().toString(),complete.connectionGeneration().toString(),clock.before().frame().episodeRunId(),clock.source(),predecessor,exe,file.fileIdDecimal(),mtime(file),actual.originalReceipt(),put(same,token.bytes()),complete.originalEvidence(),put(same,DriverJson.encode(complete.semantic())),put(same,stamp(lease.factsKnown().stamp())),put(same,lease.factsKnown().driver().encode()),lease.originalHello(),lease.sourceQualification().proof(),same.head().digest(),same.head().state().sequence(),Optional.empty());
        var document=new Document(capture,Optional.empty(),Optional.empty(),complete.observedAt());var original=put(same,encode(document));var refs=new ArrayList<>(base.preparationEvidence());refs.add(put(same,readExact(pendingDomain)));refs.add(original);refs.addAll(document.artifacts());
        var request=new NativeRequest(base.step(),base.requiredCapability(),base.additionalFields(),refs.stream().distinct().toList());
        require(request.preparationEvidence().size()<=32&&request.additionalFields().equals(base.additionalFields()),"date preclock changed original wire or exceeded finite original custody");
        var privateCapture=new PendingDateClock(parent,clock,requestId,request,document,original,pendingDomain,same,lease.sourceQualification().guard());pendingDateClocks.put(clock.actionId(),privateCapture);requirePendingDateClock(same,clock);return request;
    }
    private void requirePendingDateClock(ContinuityStorePort.Session same,ActionCommand clock)throws IOException {
        var actual=pendingDateClocks.get(clock.actionId());require(actual!=null&&actual.writer()==same&&actual.clock().equals(clock),"date preclock has no same-writer private original capture");
        var capture=actual.original().capture();require(same.head().digest().equals(capture.headBeforeCapture())&&same.head().state().sequence()==capture.ledgerSequenceBeforeCapture()&&currentCaptureDocument().equals(actual.pendingDomain()),"date preclock changed canonical pending/physical predecessor before original INTENT");
        requireGuard(actual.physical(),same);validateCapture(same,capture);require(Arrays.equals(readExact(actual.originalRef()),encode(actual.original()))&&actual.request().preparationEvidence().contains(actual.originalRef()),"date request lost its exact actual preclock original");
        var parent=find(same,actual.parent().actionId());var execution=ActionTransitions.composite(parent.state()).orElseThrow(()->new IOException("actual date Life parent absent"));require(parent.command().equals(actual.parent())&&execution.children().contains(new CompositeExecution.Child(clock.actionId(),ActionCodec.bodySha256(clock))),"date resume is not the actual reserved child of its original Life parent");
    }
    /** Retain a real M3-qualified pending projection under the sole canonical natural domain, before the app CAS. */
    public InitialPending preparePendingEpisode(ActionCommand parent,LifecycleObservationPort.Snapshot original,String newEpisodeRunId)throws IOException {
        var runtime=pendingUi();var same=borrowed();core().writer().requireSession(same);runtime.requireInitialParent(same,parent,original);
        require(activeInitialPending==null,"one actual initial pending publication per installed successor transition");
        var actual=preparePendingOriginals(parent,original);var before=readDocument(same).orElseThrow();var head=same.head();
        require(qualifiedPendingEstate.get()==null&&pendingEstateOriginals.get()==null,"nested pending cause qualification is forbidden");
        RootPendingNaturalSuccessionQualification.PendingCause cause;SuccessionNativeEstate12004.ComparedEstate matchedEstate;
        try{cause=runtime.qualification().qualify(parent,actual,head);matchedEstate=Objects.requireNonNull(qualifiedPendingEstate.get(),"actual M3 compared-estate custody absent");}finally{qualifiedPendingEstate.remove();pendingEstateOriginals.remove();}
        Optional<String> sourceEpoch=terminal().current(same,parent.lifecycleBefore(),parent.deadline(),lease->{requireSameOriginal(actual,lease.snapshot());return required().sources().optionalMetadata(same,lease.sourceQualification()).map(metadata->metadata.ownerSourceEpoch());});
        var binding=new SuccessorUiObligation.Binding(cause.predecessorDeathOrigin(),BigInteger.valueOf(cause.successorCharacterId()),newEpisodeRunId,sourceEpoch,
                cause.causeDigest(),parent.actionId(),ActionCodec.bodySha256(parent),put(same,ActionCodec.encodeCommand(parent)),currentCaptureDocument(),put(same,cause.originalProof()),actual.actual().observedAt());
        var projection=SuccessorUiObligationReducer.pendingEpisode(actual,binding);
        var child=DriverPendingEpisodeProjection.prepare(actual.facts(),projection,archive(same));
        var physical=terminal().current(same,parent.lifecycleBefore(),parent.deadline(),lease->{requireSameOriginal(actual,lease.snapshot());return lease.sourceQualification().guard();});
        var document=new Document(before.capture(),before.ready(),Optional.of(new PendingProjection(child.projection(),child.originalRef())),actual.actual().observedAt());
        require(pendingDomainAuthority.get()==null,"nested pending domain publication is forbidden");pendingDomainAuthority.set(new PendingDomainAuthority(cause,actual,child));
        DomainCommitted committed;
        try{committed=publish(same,new Publication(same,document,head.digest(),physical));}finally{pendingDomainAuthority.remove();}
        var parentKnown=put(same,org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(original.facts()).bytes());
        var token=new InitialPending(this,same,parent,actual,original,cause,matchedEstate,projection,child,committed,parentKnown);activeInitialPending=token;return token;
    }
    private void requireInitialPending(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Capture identical,
            boolean afterCas,Known actualPublished)throws IOException {
        core().writer().requireSession(same);pendingUi().requireContext(required().runtime());
        require(identical instanceof InitialPending,"pending DATA cannot supply the private Root issuer");var actual=(InitialPending)identical;
        require(actual.issuer==this&&(afterCas||actual.session==same)&&activeInitialPending==actual&&required().runtime().adopted().authority()==expected,
                "pending capture crossed its identical installed issuer/writer/Driver");
        require(Arrays.equals(readExact(actual.parentKnown),org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(actual.originalParentFrame.facts()).bytes()),
                "initial pending source lost its complete original parent Known");
        var committed=actual.committed;var head=same.head();
        require((afterCas||head.digest().equals(committed.head().digest()))&&committed.receipt().disposition()==WriterContracts.Disposition.COMMITTED
                &&committed.receipt().writes()>0&&ContinuityJson.digest(committed.receipt().head().toJson()).equals(committed.head().digest())
                &&committed.prepared().predecessor().digest().equals(actual.cause.precommitHead().digest()),"pending capture lost its actual committed canonical head and M3 predecessor");
        same.requireHistoricalState(actual.cause.precommitHead().state().sequence(),actual.cause.precommitHead().digest());
        var current=same.readDomain(SLOT);require(current instanceof DomainBodies.Available,"actual canonical pending domain unavailable");
        var available=(DomainBodies.Available)current;var document=decode(available.canonicalBody());
        require(available.reference().payload().equals(committed.payload())&&Arrays.equals(available.canonicalBody(),readExact(committed.payload()))
                &&document.pendingProjection().isPresent()&&document.pendingProjection().orElseThrow().value().equals(actual.child.projection())
                &&document.pendingProjection().orElseThrow().original().equals(actual.child.originalRef())
                &&Arrays.equals(readExact(actual.child.originalRef()),actual.child.projection().encode())
                &&Arrays.equals(readExact(actual.child.projection().qualifiedCause()),actual.cause.originalProof())
                &&actual.cause.parentBodySha256().equals(ActionCodec.bodySha256(actual.parent)),"canonical pending document/projection/private cause changed");
        expected.withFrozenFacts(same,frozen->{
            require(frozen.state() instanceof Known,"actual pending Driver facts unavailable");var known=(Known)frozen.state();
            if(!afterCas)require(actual.published==null&&known.stamp().equals(actual.actualKnown().stamp())
                    &&Arrays.equals(known.driver().encode(),actual.actualKnown().driver().encode())
                    &&Arrays.equals(DriverJson.encode(known.auxiliary()),DriverJson.encode(actual.actualKnown().auxiliary())),"pending CAS predecessor no longer is the actual original full Driver");
            else {
                require(actualPublished!=null&&known==actualPublished&&known.stamp().driverVersion()==actual.child.projection().afterVersion()
                        &&known.stamp().episodeEpoch()==actual.child.projection().afterEpoch()&&known.stamp().driverSha256().equals(actual.child.projection().afterDriver().sha256())
                        &&Arrays.equals(known.driver().encode(),actual.projection.driver().encode()),"pending published Driver is not the actual source-bound CAS result");
                require(actual.published==null||actual.published.stamp().equals(actualPublished.stamp())&&Arrays.equals(actual.published.driver().encode(),actualPublished.driver().encode())&&actual.published.auxiliary().equals(actualPublished.auxiliary()),"actual pending CAS publication cannot be replaced");
                actual.published=actualPublished;
            }
            return null;
        });
        required().game().verify();
    }
    ReadContract<?> campaignRootContract(){return required().campaignRoot();}
    record MutationCommitted(DomainBodies.PreparedImport prepared,WriterContracts.Receipt receipt,WriterContracts.Head head,ExactRef payload) { }
    MutationCommitted publishPendingMutation(ContinuityStorePort.Session same,Document actual,
            java.util.Optional<org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceGuard> guard)throws IOException {
        core().writer().requireSession(same);pendingUi().requireContext(required().runtime());
        var committed=publish(same,new Publication(same,actual,same.head().digest(),guard));
        return new MutationCommitted(committed.prepared(),committed.receipt(),committed.head(),committed.payload());
    }
    /** Actual pre-final producer. It retains causal originals before any Close and grants no final continuation. */
    public LifecycleObservationPort.Snapshot preparePendingOriginals(ActionCommand parent,LifecycleObservationPort.Snapshot original) throws IOException {
        require(parent.operation().value().equals("continue-as-reconciled-successor")&&parent.origin() instanceof CommandOrigin.LifecycleTerminal,"only the actual original Continue parent may prepare pending originals");
        var same=borrowed();core().writer().requireSession(same);var previous=readDocument(same).orElseThrow(()->new IOException("original preclock capture is absent"));
        require(previous.ready().isEmpty()&&previous.pendingProjection().isEmpty(),"pre-final preparation is once-only; retain its existing canonical parent instead of retrying");
        var capture=previous.capture();checkPhysical(same,capture,parent.deadline());checkClock(same,capture,parent);
        var candidate=parent.lifecycleBefore().currentPlayer();var heir=NativePlayerHeirObservation12004.parseNativeResult(readExact(capture.rootResult()),capture.predecessorFrame());
        require(candidate instanceof LifecycleIdentity.Character player&&player.alive()&&heir.state()==NativePlayerHeirObservation12004.State.LIVING_CANDIDATE
                &&heir.component().observation().candidateCharacterId()==player.characterId().intValueExact(),"original preclock getter does not identify the actual living successor");
        ReadArtifact first=terminal().current(same,parent.lifecycleBefore(),parent.deadline(),lease->{requireSameOriginal(original,lease.snapshot());requireCaptureSubject(capture,lease.identity(),lease.snapshot().source());return timeline.read(same,lease,parent.deadline());});
        // Legal reads are retained even while a player event/modal is present. No UI disappearance or Close is inferred here.
        FinalMaterial retained=terminal().current(same,parent.lifecycleBefore(),parent.deadline(),lease->{
            requireCaptureSubject(capture,lease.identity(),lease.snapshot().source());
            var death=read(same,required().prisoner(),new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(lease.identity()),lease.snapshot().source(),lease.identity().sessionId(),required().prisoner().operation(),PrisonerTerminalQueries.arguments(lease.identity()),parent.deadline()));
            require(PrisonerTerminalQueries.decode(death.receipt()).retainedCustody().orElseThrow() instanceof PrisonerMaterial12004.Dead,"independent actual predecessor Dead is required before pending publication");
            var ready=new Ready(parent.actionId(),ActionCodec.bodySha256(parent),put(same,ActionCodec.encodeCommand(parent)),death.originalReceipt(),first,Optional.empty(),List.of(),lease.identity().nativeEvidence(),lease.originalSemantic(),lease.identity().evidence().originalDriver(),lease.sourceQualification().proof());
            return new FinalMaterial(new Document(capture,Optional.of(ready),Optional.empty(),lease.snapshot().actual().observedAt()),lease.snapshot(),lease.sourceQualification().guard());
        });
        publish(same,new Publication(same,retained.document(),same.head().digest(),retained.guard()));return retained.snapshot();
    }
    private final RootPendingNaturalSuccessionQualification.RootCausePort pendingCausePort=new RootPendingNaturalSuccessionQualification.RootCausePort(){
        @Override public RootPendingNaturalSuccessionQualification.CauseOriginals openQualified(ActionCommand parent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head head)throws IOException {
            var originals=RootNaturalSuccessionOriginals.this.openQualified(parent,actual,head);
            require(pendingEstateOriginals.get()==null,"first successor ROOT custody cannot be replaced during the same qualification");
            var estate=pendingEstate(parent,actual,head);pendingEstateOriginals.set(estate);
            return new RootPendingNaturalSuccessionQualification.CauseOriginals(originals,estate.compared(),estate.originals());
        }
        @Override public byte[] readExact(ExactRef ref)throws IOException{return RootNaturalSuccessionOriginals.this.readExact(ref);}
        @Override public void requireCurrent(RootPendingNaturalSuccessionQualification.CauseOriginals original,ActionCommand parent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head head)throws IOException {
            RootNaturalSuccessionOriginals.this.requireCurrent(original.originals(),parent,actual,head);
            var first=pendingEstateOriginals.get();require(first!=null&&first.compared()==original.estate()&&first.originals()==original.estateOriginals(),"pending estate originals lost the actual first read custody");
            var retained=first.originals();var archived=archive(borrowed()).loadRead(retained.readReference());
            require(archived.equals(retained.successorRootRead())&&Arrays.equals(readExact(retained.resultReference()),first.compared().originalRootResult())
                    &&Arrays.equals(readExact(retained.semanticReference()),first.compared().originalSemantic())
                    &&Arrays.equals(readExact(retained.originalKnown()),org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(actual.facts()).bytes()),"first actual ROOT/full Known originals changed during source revalidation");
            var current=pendingEstate(parent,actual,head).compared();require(Arrays.equals(current.wire(),original.estate().wire())
                    &&Arrays.equals(current.originalSemantic(),original.estate().originalSemantic())
                    &&Arrays.equals(current.predecessor().originalRootResult(),original.estate().predecessor().originalRootResult()),"actual pending estate/cause source changed during qualification");
            qualifiedPendingEstate.set(original.estate());
        }
    };
    /** The installed actual Root adapter, not a DATA proof decoder, owns the pre-final qualification port. */
    public RootPendingNaturalSuccessionQualification.RootCausePort pendingCausePort(){required();return pendingCausePort;}
    private PendingEstateMaterial pendingEstate(ActionCommand parent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head head)throws IOException {
        var same=borrowed();require(same.head().digest().equals(head.digest()),"pending estate must retain its actual caller writer head");
        var document=readDocument(same).orElseThrow(()->new IOException("pending causal originals are absent"));
        var ready=document.ready().orElseThrow(()->new IOException("pending causal preparation is absent"));
        require(document.pendingProjection().isEmpty()&&ready.closeReceipt().isEmpty()&&ready.subsequentTimeline().isEmpty()
                &&ready.parentActionId().equals(parent.actionId())&&ready.parentBodySha256().equals(ActionCodec.bodySha256(parent)),"pending cause must precede Close and initial pending publication");
        return terminal().current(same,parent.lifecycleBefore(),parent.deadline(),lease->{
            requireSameOriginal(actual,lease.snapshot());requireCaptureSubject(document.capture(),lease.identity(),lease.snapshot().source());
            var read=readCurrentCampaignRoot(lease,parent.deadline());var raw=read.receipt().original().originalResultToken().orElseThrow(()->new IOException("actual successor ROOT result is absent"));
            require(raw.equals(read.value()),"actual successor ROOT typed result differs from its archived original");
            var frozen=SuccessionNativeEstate12004.freeze(readExact(document.capture().rootResult()),readExact(document.capture().semantic()));
            var compared=SuccessionNativeEstate12004.reconcile(frozen,raw.bytes(),DriverJson.encode(lease.snapshot().semantic()));
            var originals=new RootPendingNaturalSuccessionQualification.EstateOriginals(read.receipt(),read.originalReceipt(),put(same,raw.bytes()),
                    put(same,compared.originalSemantic()),put(same,org.xar.ck3.control.application.driver.DriverSnapshotFacts.encodeKnownOriginal(actual.facts()).bytes()));
            lease.assertCurrent(same);return new PendingEstateMaterial(compared,originals);
        });
    }
    @Override public Preparation prepareOutcome(ActionCommand parent,LifecycleObservationPort.Snapshot original,CompositeActionPort.Children children)throws IOException,InterruptedException{return pendingUi().prepareOutcome(parent,original,children);}
    @Override public void requireCurrent(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token)throws IOException{pendingUi().requireCurrent(parent,same,token);}
    @Override public void requireFinalized(ActionCommand parent,ContinuityStorePort.Session same,FinalToken token)throws IOException{pendingUi().requireFinalized(parent,same,token);}
    @Override public Preparation resumeOutcome(ActionCommand parent,PendingToken token,CompositeActionPort.Children children)throws IOException,InterruptedException{return pendingUi().resumeOutcome(parent,token,children);}
    @Override public void requireChild(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token,ActionCommand child)throws IOException{pendingUi().requireChild(parent,same,token,child);}
    @Override public LifecycleObservationPort.Snapshot requireRetainedOriginalFrame(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token)throws IOException{return pendingUi().requireRetainedOriginalFrame(parent,same,token);}
    @Override public void requireCommittedPendingEpisode(ActionReceipt parent,ContinuityStorePort.Session same,LifecycleComposites.RecordedPendingEpisode identical)throws IOException{pendingUi().requireCommittedPendingEpisode(parent,same,identical);}
    RootPendingUiRuntime pendingRuntime()throws IOException{return pendingUi();}
    ExactRef requireRetainedParentKnown(ContinuityStorePort.Session same,RootPendingNaturalSuccessionQualification.PendingCause identical)throws IOException{return pendingUi().requireRetainedParentKnown(same,identical);}
    private record FinalMaterial(Document document,LifecycleObservationPort.Snapshot snapshot,
            java.util.Optional<org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceGuard> guard) { }
    /** Observation for choosing an attempt only. This record grants no transition or submit authority. */
    public record NaturalCandidate(int predecessor,int successor,ExactRef capture,ExactRef clockReceipt,ExactRef retainedDeath) { }
    public Optional<NaturalCandidate> inspectCandidate(RootLifecycleAuthority.Lease actual)throws IOException {
        var same=borrowed();actual.assertCurrent(same);var domain=same.readDomain(SLOT);
        if(domain instanceof DomainBodies.Unavailable unavailable) {require(unavailable.reason()==DomainBodies.Reason.UNIMPORTED,"original capture is corrupt or unregistered");return Optional.empty();}
        var available=(DomainBodies.Available)domain;var document=decode(available.canonicalBody());
        require(document.ready().isEmpty(),"retained natural preparation has already been attempted; no replay");var capture=document.capture();
        requireCaptureSubject(capture,actual.identity(),actual.snapshot().source());checkPhysical(same,capture,actual.validUntil());validateCapture(same,capture);
        int successor=((LifecycleIdentity.Character)actual.identity().currentPlayer()).characterId().intValueExact();
        var heir=NativePlayerHeirObservation12004.parseNativeResult(readExact(capture.rootResult()),capture.predecessorFrame());
        if(heir.state()!=NativePlayerHeirObservation12004.State.LIVING_CANDIDATE||heir.component().observation().candidateCharacterId()!=successor)return Optional.empty();
        ActionReceipt clock=originalClock(same,capture);var parent=find(same,capture.parentActionId());var execution=ActionTransitions.composite(parent.state()).orElseThrow();
        Set<String> permitted=new HashSet<>();permitted.add(capture.parentActionId());execution.children().forEach(child->permitted.add(child.actionId()));
        core().actions().withFrozen(same,lease->{for(var row:lease.snapshot().actions())if(row.sequence()>capture.ledgerSequenceBeforeCapture())require(permitted.contains(row.command().actionId()),"another mutation followed the retained engine clock");lease.assertCurrent();return null;});
        var death=read(same,required().prisoner(),new PlanningReadRequest(new CommandOrigin.LifecycleTerminal(actual.identity()),actual.snapshot().source(),actual.identity().sessionId(),required().prisoner().operation(),PrisonerTerminalQueries.arguments(actual.identity()),actual.validUntil()));
        require(PrisonerTerminalQueries.decode(death.receipt()).retainedCustody().orElseThrow() instanceof PrisonerMaterial12004.Dead,"actual original subject is not independently observed dead");
        actual.assertCurrent(same);return Optional.of(new NaturalCandidate(capture.predecessorFrame().actorCharacterId(),successor,available.reference().payload(),archive(same).preserveReceipt(clock),death.originalReceipt()));
    }
    @Override public String verify(ContinuityState head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original) throws IOException {
        Publication actual=publishing.get();require(actual!=null&&actual.session()==borrowed(),"detached capture JSON has no live Root publication authority");
        return verify(actual.session().head(),previous,request,original);
    }
    @Override public String verify(WriterContracts.Head head,Optional<DomainBodies.BodyRef> previous,DomainBodies.ImportRequest request,byte[] original)throws IOException {
        Publication actual=publishing.get();require(actual!=null&&actual.session()==borrowed()&&actual.predecessor().equals(head.digest())
                &&actual.session().head().digest().equals(head.digest()),"natural domain import escaped its actual writer head");
        Document decoded=decode(original);require(Arrays.equals(original,encode(actual.document()))&&decoded.equals(actual.document())
                &&request.slot()==SLOT&&request.contractSchema().equals(SCHEMA)&&request.evidence().equals(computedArtifacts(decoded))
                &&Arrays.equals(request.producerInput(),original),"actual native producer/body/evidence differs");
        requireGuard(actual.physical(),actual.session());for(var ref:computedArtifacts(decoded))readExact(ref);
        var old=readDocument(actual.session());require(old.isPresent()==previous.isPresent(),"original capture domain predecessor changed");
        if(decoded.pendingProjection().isPresent()&&old.isPresent()&&old.orElseThrow().pendingProjection().isPresent()) {
            pendingUi().verifyPendingMutation(head,old.orElseThrow(),decoded);
        } else if(decoded.pendingProjection().isPresent()) {
            var authority=pendingDomainAuthority.get();require(authority!=null&&old.isPresent()&&old.orElseThrow().pendingProjection().isEmpty()
                    &&old.orElseThrow().capture().equals(decoded.capture())&&old.orElseThrow().ready().equals(decoded.ready()),"pending publication needs the actual retained causal predecessor and private authority");
            var child=decoded.pendingProjection().orElseThrow();require(child.value().equals(authority.projection().projection())&&child.original().equals(authority.projection().originalRef())
                    &&authority.cause().precommitHead().digest().equals(head.digest())&&authority.terminal().originalEvidence().equals(authority.cause().precommitSnapshot())
                    &&child.value().qualifiedCause().sha256().equals(authority.cause().causeDigest()),"pending canonical child differs from the actual private M3 cause/projection");
        } else if(decoded.ready().isPresent())require(old.isPresent()&&old.orElseThrow().ready().isEmpty()&&old.orElseThrow().pendingProjection().isEmpty()&&old.orElseThrow().capture().equals(decoded.capture()),"ready publication cannot invent or replace the preclock capture");
        validateCapture(actual.session(),decoded.capture());
        return DriverJson.sha256(original);
    }
    @Override public Originals openQualified(ActionCommand parent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head head)throws IOException {
        var same=borrowed();require(same.head().digest().equals(head.digest()),"M3 caller did not retain the actual writer head");
        var domain=same.readDomain(SLOT);require(domain instanceof DomainBodies.Available,"durable original capture unavailable");
        var available=(DomainBodies.Available)domain;Document document=decode(available.canonicalBody());Ready ready=document.ready().orElseThrow(()->new IOException("actual natural preparation not retained"));Capture capture=document.capture();
        require(parent.actionId().equals(ready.parentActionId())&&ActionCodec.bodySha256(parent).equals(ready.parentBodySha256())
                &&Arrays.equals(ActionCodec.encodeCommand(parent),readExact(ready.parentCommand())),"natural parent is not the exact retained command");
        checkPhysical(same,capture,parent.deadline());validateCapture(same,capture);ActionReceipt clock=checkClock(same,capture,parent);
        PlanningReadReceipt death=archive(same).loadRead(ready.predecessorDeath());required().prisoner().decode(death);
        var replay=RootLifecycleGuardEvidence.replay(death.after().binding(),archive(same),same,core().originals());
        requireCaptureSubject(capture,replay.identity(),actual.source());
        require(actual.originalEvidence().equals(ready.finalNativePacket())&&sameNativeFrame(actual.actual(),replay.original().actual())
                &&actual.semantic().equals(replay.semantic())&&Arrays.equals(actual.facts().driver().encode(),readExact(ready.finalDriver()))
                &&Arrays.equals(DriverJson.encode(actual.semantic()),readExact(ready.finalSemantic()))
                &&actual.facts().stamp().driverVersion()==replay.identity().subject().driverVersion()
                &&actual.facts().stamp().episodeEpoch()==replay.identity().subject().episodeEpoch(),"final snapshot is not the real retained full Root/Driver/native projection");
        var qualified=required().sources().verifyLifecycle(same,actual.actual().session(),actual.source(),actual.originalEvidence(),required().game().nativeTransport().diagnostics(),parent.deadline());qualified.assertCurrent(same);
        Packet first=timeline.packet(ready.initialTimeline());Optional<Packet> close=ready.closeReceipt().map(ref->timeline.closePacket(archive(same).loadReceipt(ref)));
        List<Packet> posts=ready.subsequentTimeline().stream().map(timeline::packet).toList();
        ExactRef engine=put(same,NaturalEngineClockProof.encode(new NaturalEngineClockProof(capture.machineId(),actual.actual().observedAt(),head.digest(),clock.outcome(),false,
                available.reference().payload(),archive(same).preserveReceipt(clock),capture.clockCommand(),capture.rootResult(),actual.originalEvidence(),qualified.proof())));
        Originals result=new Originals(session(capture),capture.predecessorFrame(),capture.rootResult(),engine,death,first,close,posts);
        held.set(new Qualified(result,available.reference().payload(),head.digest()));return result;
    }
    @Override public void requireCurrent(Originals original,ActionCommand parent,LifecycleObservationPort.Snapshot actual,WriterContracts.Head head)throws IOException {
        Qualified before=held.get();require(before!=null&&before.originals()==original&&before.head().equals(head.digest()),"M3 retained original object/caller head changed");
        var second=openQualified(parent,actual,head);Qualified after=held.get();
        require(before.document().equals(after.document())&&second.session().equals(original.session())&&second.predecessorRoot().equals(original.predecessorRoot())
                &&second.predecessorDeath().equals(original.predecessorDeath())&&second.initialTimeline().equals(original.initialTimeline())&&second.close().equals(original.close())&&second.subsequentTimeline().equals(original.subsequentTimeline()),"original source/cause/query chain changed during M3 leaf rederivation");
        // The second actual source proof has a fresh observation timestamp; its identity is independently retained, not compared as a fake constant.
        readExact(original.engineClockAndActorProof());held.remove();
    }
    @Override public byte[] readExact(ExactRef original)throws IOException { return core().archive().readArtifact(borrowed(),original,Math.toIntExact(Math.min((long)LIMIT,Math.max(1,original.bytes())))); }
    ExactRef put(ContinuityStorePort.Session same,byte[] bytes)throws IOException { return core().archive().preserveArtifact(same,bytes,LIMIT); }
    /** Authorization belongs to this one actual source read; its failure callback retains DATA even after expiry. */
    <T> PlanningReadResult.Known<T> withPendingReadFailureEvidence(ContinuityStorePort.Session same,
            PendingUiEvent.Source actual,PendingUiEvent.Current current,ReadContract<T> contract,PlanningReadRequest request,
            PlanningReadPort.FailureEvidenceObserver observer,PendingUiEvent.ScopedWork<PlanningReadResult.Known<T>> work)throws IOException {
        core().writer().requireSession(same);Objects.requireNonNull(actual).requireCurrent(same);
        Objects.requireNonNull(current);Objects.requireNonNull(contract);Objects.requireNonNull(request);
        Objects.requireNonNull(observer);Objects.requireNonNull(work);
        require(pendingReadFailure.get()==null&&liveRead.get()==null,"private pending failure scope cannot nest another read");
        var frame=current.frame();
        require(required().runtime().readCatalog().containsIdentity(contract)&&request.operation().equals(contract.operation())
                &&request.origin() instanceof CommandOrigin.Gameplay&&request.before().equals(frame.identity())
                &&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId()),
                "pending failure observer needs its exact installed contract and actual source frame request");
        var scope=new PendingReadFailureScope(same,actual,current,contract,request,observer,same.head().digest());
        pendingReadFailure.set(scope);
        try{
            var result=work.run();require(scope.readStarted,"pending failure scope did not consume its actual read");return result;
        }finally{pendingReadFailure.remove();}
    }
    private void retainPendingReadFailure(PendingReadFailureScope scope,ContinuityStorePort.Session same,
            ReadContract<?> contract,PlanningReadRequest request,PlanningReadResult.Unavailable<?> unavailable,
            Optional<PlanningReadCoordinator.FailedReadAttempt> attempted,ActionPorts.OutcomeArchive originals)throws IOException {
        core().writer().requireSession(same);
        require(pendingReadFailure.get()==scope&&Boolean.TRUE.equals(liveRead.get())&&scope.readStarted&&!scope.callbackEntered
                &&scope.same==same&&scope.contract==contract&&scope.request==request&&scope.head.equals(same.head().digest()),
                "pending failed-read DATA escaped its original single read and writer head");
        scope.callbackEntered=true;
        // No fresh clock/Game/window check here. The actual coordinator supplies its original unavailable/attempt/archive.
        try{scope.observer.failed(same,contract,request,unavailable,attempted,originals);}
        finally{
            core().writer().requireSession(same);
            require(scope.head.equals(same.head().digest()),"pending failed-read DATA observer changed the canonical writer head");
        }
    }
    <T>PlanningReadResult.Known<T> read(ContinuityStorePort.Session same,ReadContract<T> contract,PlanningReadRequest request)throws IOException {
        require(liveRead.get()==null,"nested query dispatch is forbidden");liveRead.set(Boolean.TRUE);
        try{
            var scope=pendingReadFailure.get();
            if(scope==null)return known(core().planningReads().read(same,contract,request));
            require(scope.same==same&&scope.contract==contract&&scope.request==request&&!scope.readStarted
                    &&scope.head.equals(same.head().digest()),"pending failure scope changed its one exact source read");
            scope.readStarted=true;
            return known(core().planningReads().readWithFailureEvidence(same,contract,request,
                    (borrowed,identical,actual,unavailable,attempted,originals)->
                            retainPendingReadFailure(scope,borrowed,identical,actual,unavailable,attempted,originals)));
        }finally{liveRead.remove();}
    }
    ExactRef originalFrame(NativeActionPort.AckReceived ack)throws IOException {
        var archive=archive(borrowed());if(Boolean.TRUE.equals(liveRead.get()))archive.preserve(ack);
        ExactRef dispatch=archive.referenceOf(ack);var row=StrictJson.parse(readExact(dispatch));
        require(row.isObject()&&"ACK".equals(StrictJson.text(row.get("kind")))&&ack.requestId().equals(StrictJson.text(row.get("request_id"))),"actual archived native ACK required");
        ExactRef frame=ExactRef.fromJson(row.get("frame_ref"));require(Arrays.equals(readExact(frame),ack.originalFrame().bytes()),"actual original frame reference differs");return frame;
    }
    static <T>PlanningReadResult.Known<T> known(PlanningReadResult<T> result)throws IOException {if(result instanceof PlanningReadResult.Known<T> value)return value;throw new IOException("actual original query unavailable: "+((PlanningReadResult.Unavailable<T>)result).reason());}
    /** Explicit typed cause closure; nested source references are retained by the same canonical import. */
    List<ExactRef> computedArtifacts(Document document)throws IOException {
        var refs=new LinkedHashSet<>(document.artifacts());
        if(document.pendingProjection().isPresent()) {
            var cause=org.xar.ck3.control.runtime.lifecycle.PendingNaturalCauseProof.decode(
                    readExact(document.pendingProjection().orElseThrow().value().qualifiedCause()));
            refs.addAll(List.of(cause.predecessorRoot(),cause.engineClockProof(),cause.actualPrecommitSnapshot(),
                    cause.successorRootRead(),cause.successorRootResult(),cause.successorSemantic(),cause.originalKnown()));
            var finalProof=document.pendingProjection().orElseThrow().latestMutation().flatMap(NaturalClockOriginals.MutationArtifact::m3Finalization);
            if(finalProof.isPresent())refs.addAll(RootPendingNaturalSuccessionQualification.decodeFinalProof(readExact(finalProof.orElseThrow())).materialReferences());
            var state=org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec.decode(readExact(document.pendingProjection().orElseThrow().currentObligation()));
            var bindings=new LinkedHashSet<ExactRef>();
            state.rebind().map(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.Rebind::actualPrivateRebindProof).ifPresent(bindings::add);
            state.finalization().flatMap(org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.Finalization::continuityBinding).ifPresent(bindings::add);
            for(ExactRef binding:bindings){refs.add(binding);refs.addAll(org.xar.ck3.control.runtime.lifecycle.PendingSameGameContinuity.decode(readExact(binding)).materialReferences());}
        }
        require(refs.size()<=DomainBodies.maximumEvidence(SLOT),"complete typed natural evidence exceeds its finite canonical import contract");
        for(var ref:refs)readExact(ref);
        return List.copyOf(refs);
    }
    private DomainCommitted publish(ContinuityStorePort.Session same,Publication actual)throws IOException {
        require(publishing.get()==null&&same==actual.session()&&same.head().digest().equals(actual.predecessor()),"one actual source publication at its held writer head");
        byte[] body=encode(actual.document());ExactRef ref=put(same,body);var request=new DomainBodies.ImportRequest(SLOT,SCHEMA,ref,body,computedArtifacts(actual.document()),"natural-originals:"+actual.document().capture().clockActionId()+(actual.document().pendingProjection().isPresent()?":pending-"+actual.document().pendingProjection().orElseThrow().mutationSequence():actual.document().ready().isPresent()?":ready":":captured"));
        require(preparedOwner!=null&&preparedOwner.live.get()==null,"actual Core-lifetime publication router is unavailable or nested");
        preparedOwner.live.set(this);publishing.set(actual);
        try {
            var preview=same.previewImport(request);var receipt=same.commitImport(preview);var head=same.head();
            var domain=same.readDomain(SLOT);require(domain instanceof DomainBodies.Available,"committed actual original domain is unavailable");
            var available=(DomainBodies.Available)domain;
            require(Arrays.equals(body,available.canonicalBody())&&Arrays.equals(body,readExact(available.reference().payload()))
                    &&ContinuityJson.digest(receipt.head().toJson()).equals(head.digest()),"actual domain commit did not retain its exact original body/head");
            return new DomainCommitted(preview,receipt,head,available.reference().payload());
        } finally {publishing.remove();preparedOwner.live.remove();}
    }
    private Optional<Document> readDocument(ContinuityStorePort.Session same)throws IOException {
        var value=same.readDomain(SLOT);if(value instanceof DomainBodies.Available available){require(available.reference().contractSchema().equals(SCHEMA),"unsupported original capture schema");return Optional.of(decode(available.canonicalBody()));}
        var unavailable=(DomainBodies.Unavailable)value;require(unavailable.reason()==DomainBodies.Reason.UNIMPORTED,"registered natural original domain is corrupt/unavailable: "+unavailable);return Optional.empty();
    }
    private Optional<ActionReceipt> clockParent(ContinuityStorePort.Session same,ActionCommand child)throws IOException {
        var values=core().actions().withFrozen(same,lease->{var result=lease.snapshot().actions().stream().filter(row->row.state() instanceof ActionState.CompositeRunning running
                &&required().clockHandlers().contains(running.execution().handlerId())&&running.execution().children().contains(new CompositeExecution.Child(child.actionId(),ActionCodec.bodySha256(child)))).toList();lease.assertCurrent();return result;});
        require(values.size()<=1,"clock cannot have ambiguous original composite parents");if(values.isEmpty())return Optional.empty();ActionReceipt parent=values.getFirst();
        require(parent.command().source().equals(child.source())&&parent.command().sessionId().equals(child.sessionId())&&parent.command().origin() instanceof CommandOrigin.Gameplay,"clock parent crossed source/session/gameplay origin");return Optional.of(parent);
    }
    private ActionReceipt find(ContinuityStorePort.Session same,String id)throws IOException {return core().actions().withFrozen(same,lease->lease.find(id).orElseThrow(()->new IllegalArgumentException("original durable action missing: "+id)));}
    private ActionReceipt checkClock(ContinuityStorePort.Session same,Capture capture,ActionCommand natural)throws IOException {
        ActionReceipt clock=originalClock(same,capture),parent=find(same,capture.parentActionId());
        var execution=ActionTransitions.composite(parent.state()).orElseThrow();
        Set<String> allowed=new HashSet<>();allowed.add(capture.parentActionId());execution.children().forEach(child->allowed.add(child.actionId()));allowed.add(natural.actionId());
        var naturalReceipt=find(same,natural.actionId());require(naturalReceipt.bodySha256().equals(ActionCodec.bodySha256(natural))&&naturalReceipt.command().equals(natural)
                &&naturalReceipt.state() instanceof ActionState.CompositeRunning running&&running.execution().handlerId().equals("java-death-succession-next-episode/v1"),"natural preparation must retain its actual registered running canonical parent");
        core().actions().withFrozen(same,lease->{require(lease.activeActionId().filter(natural.actionId()::equals).isPresent(),"natural original producer escaped the actual coordinator parent scope");lease.assertCurrent();return null;});
        ActionTransitions.composite(naturalReceipt.state()).ifPresent(value->value.children().forEach(child->allowed.add(child.actionId())));
        core().actions().withFrozen(same,lease->{for(var row:lease.snapshot().actions())if(row.sequence()>capture.ledgerSequenceBeforeCapture())require(allowed.contains(row.command().actionId()),"intervening action/restore/actor mutation prevents natural clock qualification");lease.assertCurrent();return null;});return clock;
    }
    private ActionReceipt originalClock(ContinuityStorePort.Session same,Capture capture)throws IOException {
        ActionReceipt clock=find(same,capture.clockActionId()),parent=find(same,capture.parentActionId());
        require(clock.bodySha256().equals(capture.clockBodySha256())&&parent.bodySha256().equals(capture.parentBodySha256())
                &&clock.command().operation().value().equals("resume-map")&&clock.command().source().equals(capture.source())
                &&clock.command().before().frame().identity().player().intValueExact()==capture.predecessorFrame().actorCharacterId()
                &&Arrays.equals(ActionCodec.encodeCommand(clock.command()),readExact(capture.clockCommand()))
                &&Arrays.equals(ActionCodec.encodeCommand(parent.command()),readExact(capture.parentCommand())),"original real clock command/body/source changed");
        var execution=ActionTransitions.composite(parent.state()).orElseThrow(()->new IOException("original registered clock composite absent"));
        require(required().clockHandlers().contains(execution.handlerId())&&execution.children().contains(new CompositeExecution.Child(clock.command().actionId(),clock.bodySha256())),"original clock detached from its actual registered parent");
        var attempt=ActionTransitions.attempt(clock.state()).orElseThrow(()->new IOException("clock has no actual submission attempt"));
        var dispatch=ActionTransitions.dispatch(clock.state()).orElseThrow(()->new IOException("clock has no original return/unknown packet"));
        require(clock.outcome()!=ActionReceipt.Outcome.REJECTED_CONFIRMED&&clock.outcome()!=ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH,"a definitely rejected clock cannot establish the natural engine transition");
        require(attempt.preparedRequest().step().equals("resume-map")&&!(dispatch instanceof NativeActionPort.RejectedBeforeDispatch),"no original engine clock write exists");
        require(dispatch.equals(archive(same).load(archive(same).referenceOf(dispatch)))&&attempt.preparedRequest().equals(archive(same).loadRequest(archive(same).requestReferenceOf(attempt.preparedRequest()))),"original clock request/ACK/UNKNOWN archive differs");
        byte[] outbound=dispatch instanceof NativeActionPort.AckReceived ack?ack.outbound().orElseThrow(()->new IOException("clock historical ACK has no actual outbound packet")).originalPacket():((NativeActionPort.Unknown)dispatch).originalRequestPacket();
        var wire=org.xar.ck3.control.nativebridge.NativeWire.decodeExecuteRequest(outbound);
        require(wire.requestId().equals(attempt.requestId())&&wire.step().equals("resume-map")&&wire.expectedRevision().orElseThrow().equals(capture.predecessorFrame().nativeRevision())
                &&StrictJson.parse(wire.normalizedAdditionalFields().value()).equals(StrictJson.parse(attempt.preparedRequest().additionalFields().bytes())),"original clock outbound native request is not the captured real frame/primitive");
        var root=archive(same).loadRead(capture.rootRead());require(!root.after().binding().observedAt().isAfter(attempt.submittedAt()),"GetPlayerHeir was not captured before the actual clock write");return clock;
    }
    /** Reuses the original read/outbound/chronology validator for a genuinely retained historical cause. */
    ActionReceipt requireRetainedClock(ContinuityStorePort.Session same,Capture actual)throws IOException {
        core().writer().requireSession(same);validateCapture(same,actual);return originalClock(same,actual);
    }
    /** Replays the identical installed terminal ROOT decoder; no query or terminal lease is acquired. */
    PlanningReadReceipt requireRetainedRoot(ContinuityStorePort.Session same,ExactRef retainedReceipt)throws IOException {
        core().writer().requireSession(same);var receipt=archive(same).loadRead(retainedReceipt);
        require(receipt.contractId().equals(required().terminalRoot().contractId()),"retained successor ROOT must use its actual terminal profile");
        required().terminalRoot().decode(receipt);return receipt;
    }
    /** Borrows the actual current physical qualification; no caller-created deadline or old-subject observation. */
    void requireRetainedPhysical(ContinuityStorePort.Session same,Capture actual,
            org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source)throws IOException {
        core().writer().requireSession(same);source.assertCurrent(same);
        source.assertCurrent(same);required().game().verify();requireCapturedPhysicalIdentity(actual);source.assertCurrent(same);
    }
    void requireCanonicalAttempt(ActionReceipt proposed)throws IOException {
        var actual=find(borrowed(),proposed.command().actionId());require(actual.bodySha256().equals(proposed.bodySha256())&&actual.command().equals(proposed.command())
                &&ActionTransitions.attempt(actual.state()).equals(ActionTransitions.attempt(proposed.state()))&&ActionTransitions.dispatch(actual.state()).equals(ActionTransitions.dispatch(proposed.state())),"Close proof has no exact original canonical coordinator attempt and native return");
    }
    private void validateCapture(ContinuityStorePort.Session same,Capture capture)throws IOException {
        PlanningReadReceipt root=archive(same).loadRead(capture.rootRead());required().campaignRoot().decode(root);
        require(FinanceReadContracts.rootCapture(root.request().arguments())==FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS,"preclock original must retain its exact internal ROOT capture context");
        require(root.request().origin() instanceof CommandOrigin.Gameplay&&root.request().operation().value().equals("query-campaign-root-context-v1")
                &&root.request().source().equals(capture.source())&&root.request().sessionId().equals(capture.sessionId())
                &&root.request().before().frame().identity().player().intValueExact()==capture.predecessorFrame().actorCharacterId()
                &&root.before().binding().connectionGeneration().toString().equals(capture.connectionGeneration())
                &&Arrays.equals(root.original().originalResultToken().orElseThrow().bytes(),readExact(capture.rootResult())),"durable preclock GetPlayerHeir actual read drift");
        require(originalPredecessorFrame(readExact(capture.semantic()),capture.predecessorFrame().actorCharacterId()).equals(capture.predecessorFrame()),"original predecessor frame is unavailable");
        NativePlayerHeirObservation12004.parseNativeResult(readExact(capture.rootResult()),capture.predecessorFrame());
    }
    private void requireCommittedNaturalSuccessor(ContinuityStorePort.Session same,Document old,ActionCommand nextClock)throws IOException {
        Ready ready=old.ready().orElseThrow(()->new IOException("old-episode originals cannot be replaced without the actual natural continuation"));
        ActionReceipt continuation=find(same,ready.parentActionId());
        require(continuation.bodySha256().equals(ready.parentBodySha256())&&continuation.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied applied
                &&applied.proof().kind()==org.xar.ck3.control.application.lifecycle.LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,"only the actual canonical natural successor settlement permits a new episode capture");
        var proof=((ActionState.LifecycleApplied)((ActionState.CompositeSettled)continuation.state()).settlement()).proof();proof.validateParent(continuation.command());
        var death=archive(same).loadRead(ready.predecessorDeath());var successor=(LifecycleIdentity.Character)death.request().origin().requireLifecycleTerminal().currentPlayer();
        require(nextClock.before().frame().identity().player().equals(successor.characterId())&&!nextClock.before().frame().episodeRunId().equals(old.capture().episodeRunId())
                &&nextClock.before().game().equals(continuation.command().lifecycleBefore().game()),"new clock is not the same Game's actually committed living successor episode");
    }
    private void requireReplacement(ContinuityStorePort.Session same,ActionCommand clock)throws IOException {
        core().writer().requireSession(same);required().runtime().requireCurrent(clock.deadline());
        Replacement actual=replacement;
        require(actual!=null&&actual.game().equals(clock.before().game())
                &&actual.episode().equals(clock.before().frame().episodeRunId())
                &&actual.actor().equals(clock.before().frame().identity().player())
                &&clock.sessionId().equals(required().game().sessionId())&&clock.source().equals(required().runtime().source()),
                "historical capture cannot be rebound to a new Game without Root's actual restore/episode source admission");
        readExact(actual.proof());
        switch(actual.origin()) {
            case RestoredReplacement restored -> {
                required().runtime().requireRestorationOriginal(same,restored.binding());
                require(required().runtime().requireRestoredOrigin(same)==restored.origin(),
                        "natural clock lost the actual private original restore source");
            }
            case EpisodeReplacement episode -> {
                var original=episode.lifecycle();
                if(original.warmCommit().isPresent()) {
                    var warm=original.warmCommit().orElseThrow();same.requireCommitted(warm.prepared(),warm.receipt());
                } else {
                    same.requireHistoricalState(original.after().sequence(),ContinuityJson.digest(original.after().toJson()));
                    for(var pin:original.proofDocuments())same.verifyPin(pin);
                }
            }
        }
    }
    private void checkPhysical(ContinuityStorePort.Session same,Capture capture,Instant deadline)throws IOException {
        core().writer().requireSession(same);required().runtime().requireCurrent(deadline);
        requireCapturedPhysicalIdentity(capture);required().game().nativeTransport().verifyHeld(deadline);
    }
    private void requireCapturedPhysicalIdentity(Capture capture)throws IOException {
        var game=required().game();require(game.machineId().equals(capture.machineId())&&game.sessionId().equals(capture.sessionId())&&game.generation().pid()==capture.gamePid()
                &&game.generation().creationFiletime().value().toString().equals(capture.gameBirthFiletime())&&game.nativeTransport().diagnostics().session().orElseThrow().connectionGeneration().toString().equals(capture.connectionGeneration()),"retained preclock capture belongs to another physical Game/session/connection");
        ExactRef exe=executable();var actual=SharedSourceFiles.nativeFile(Path.of(exe.path()));require(exe.equals(capture.executable())&&actual.fileIdDecimal().equals(capture.executableFileId())&&mtime(actual).equals(capture.executableMtimeNs()),"actual executable identity differs");
    }
    private static void requireGuard(Optional<org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceGuard> guard,ContinuityStorePort.Session same)throws IOException {if(guard.isPresent())guard.orElseThrow().assertCurrent(same);}
    private ExactRef executable() {var file=required().game().launchPlan().sources().review().gameExecutable();return new ExactRef(file.path(),file.bytes(),file.sha256());}
    private static String mtime(SharedSourceFiles.NativeFile file) {return new BigInteger(file.lastWriteFiletimeDecimal()).subtract(new BigInteger("116444736000000000")).multiply(BigInteger.valueOf(100)).toString();}
    static Session session(Capture capture) {return new Session(capture.machineId(),capture.sessionId(),new G2RetainedNativeSourceProvider.GameIdentity(capture.gamePid(),capture.gameBirthFiletime()),capture.episodeRunId(),capture.connectionGeneration(),capture.executable(),capture.executableFileId(),capture.executableMtimeNs());}
    ExactRef currentCaptureDocument()throws IOException {var value=borrowed().readDomain(SLOT);require(value instanceof DomainBodies.Available,"actual preclock capture domain absent");return ((DomainBodies.Available)value).reference().payload();}
    @FunctionalInterface interface OriginalWork<T> {T run()throws IOException;}
    <T>T withRetainedCapture(ExactRef originalDocument,OriginalWork<T> work)throws IOException {
        Capture capture=decode(readExact(originalDocument)).capture();Capture prior=retainedReplay.get();
        require(prior==null||prior.equals(capture),"archived Close replay changed its retained original source session");retainedReplay.set(capture);
        try{return work.run();}finally{if(prior==null)retainedReplay.remove();else retainedReplay.set(prior);}
    }
    Session currentSession(LifecycleIdentity actual,G2Source actualSource)throws IOException {Capture capture=retainedReplay.get();if(capture==null){var document=readDocument(borrowed());if(document.isEmpty())return pendingUi().terminalDataSession(actual,actualSource);capture=document.orElseThrow().capture();}requireCaptureSubject(capture,actual,actualSource);return session(capture);}
    /** Complete retained SEM uses the existing bounded full Driver/RawJson lane; query envelopes keep their own smaller limits. */
    static Frame originalPredecessorFrame(byte[] originalSemantic,int actor) {
        return frame(DriverJson.object(originalSemantic,RawJson.MAXIMUM_BYTES),actor);
    }
    static Frame frame(OpportunityJson.Obj semantic,int actor) {return new Frame(OpportunityJson.text(semantic.get("snapshot_id"),"snapshot_id"),OpportunityJson.integer(semantic.get("revision"),"revision"),OpportunityJson.integer(semantic.get("native_revision"),"native_revision"),OpportunityJson.integer(semantic.get("date_raw"),"date_raw").intValueExact(),actor,OpportunityJson.integer(semantic.get("local_player_id"),"local_player_id").intValueExact());}
    static Frame frame(LifecycleIdentity actual,OpportunityJson.Obj semantic) {require(actual.currentPlayer() instanceof LifecycleIdentity.Character player&&player.alive(),"actual living successor required");return frame(semantic,((LifecycleIdentity.Character)actual.currentPlayer()).characterId().intValueExact());}
    private static byte[] stamp(org.xar.ck3.control.application.driver.DriverSnapshotFacts.Stamp value) {return StrictJson.canonical(StrictJson.object().put("driver_version",value.driverVersion()).put("episode_epoch",value.episodeEpoch()).put("driver_sha256",value.driverSha256()).put("episode_run_id",value.episodeRunId()));}
    private static void requireSameOriginal(LifecycleObservationPort.Snapshot original,LifecycleObservationPort.Snapshot actual) {require(original.actual().session().equals(actual.actual().session())&&original.source().equals(actual.source())&&original.facts().stamp().episodeEpoch()==actual.facts().stamp().episodeEpoch()&&original.facts().driver().session().equals(actual.facts().driver().session()),"natural preparation crossed the actual original episode");}
    static boolean sameNativeFrame(NativeObservationPort.ObservedFrame first,NativeObservationPort.ObservedFrame second) {return first.session().equals(second.session())&&first.snapshotId().equals(second.snapshotId())&&first.nativeRevision().equals(second.nativeRevision())&&first.state().equals(second.state())&&Arrays.equals(first.originalPacket(),second.originalPacket())&&first.observedAt().equals(second.observedAt());}
    private void requireCaptureSubject(Capture capture,LifecycleIdentity actual,G2Source source)throws IOException {
        require(source.equals(capture.source())&&actual.machineId().equals(capture.machineId())&&actual.sessionId().equals(capture.sessionId())&&actual.game().pid()==capture.gamePid()&&actual.game().creationFiletime().value().toString().equals(capture.gameBirthFiletime())&&actual.connectionGeneration().toString().equals(capture.connectionGeneration())&&actual.subject().episodeRunId().equals(capture.episodeRunId())&&actual.subject().characterId().intValueExact()==capture.predecessorFrame().actorCharacterId()&&actual.terminalReason()==LifecycleIdentity.TerminalReason.CHANGED&&actual.currentPlayer() instanceof LifecycleIdentity.Character player&&player.alive(),"actual terminal source/old subject/new living player differs from preclock originals");
        var stamp=StrictJson.object(StrictJson.parse(readExact(capture.driverStamp())),Set.of("driver_version","episode_epoch","driver_sha256","episode_run_id"));

        require(StrictJson.integer(stamp.get("episode_epoch"),0,StrictJson.MAX_SAFE_INTEGER)==actual.subject().episodeEpoch()&&StrictJson.integer(stamp.get("driver_version"),0,StrictJson.MAX_SAFE_INTEGER)<=actual.subject().driverVersion()
                &&StrictJson.text(stamp.get("episode_run_id")).equals(capture.episodeRunId())&&StrictJson.text(stamp.get("driver_sha256")).equals(capture.driver().sha256()),"actual terminal old-episode epoch/Driver changed or regressed");
    }
}

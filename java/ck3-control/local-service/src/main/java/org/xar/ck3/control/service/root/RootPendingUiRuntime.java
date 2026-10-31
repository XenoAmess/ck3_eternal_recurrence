package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.*;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.advance.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.checkpoint.RestoreCheckpointService;
import org.xar.ck3.control.application.planning.events.PendingUiEvent;
import org.xar.ck3.control.application.driver.*;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts.Known;
import org.xar.ck3.control.application.lifecycle.*;
import org.xar.ck3.control.application.lifecycle.NaturalSuccessionPreparation.*;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation.*;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.application.effects.NativeRecordedEvidenceVerifier;
import org.xar.ck3.control.application.session.SessionPorts;
import org.xar.ck3.control.application.session.ContinuityBatchJournal;
import org.xar.ck3.control.application.session.SameGameTransportContinuity;
import org.xar.ck3.control.runtime.lifecycle.PendingSameGameContinuity;
import org.xar.ck3.control.application.planning.finance.FinanceReadContracts;
import org.xar.ck3.control.continuity.writer.*;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.contracts.*;
import org.xar.ck3.control.g2.context.G2RetainedNativeSourceProvider;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification;
import org.xar.ck3.control.runtime.lifecycle.RootOriginalNaturalSuccessionVerifier.Packet;
import org.xar.ck3.control.wave2.governance.succession.NativeTimelineBlocker12004;
import org.xar.ck3.control.wave2.governance.succession.PendingModalClearance;
import org.xar.ck3.control.build.SharedSourceFiles;
import org.xar.ck3.control.service.mcp.PublicServiceFailure;

/** Actual per-Game custody of the private cause, canonical pending publications and finite continuation. */
public final class RootPendingUiRuntime implements RootDriverRegistryPublicProducts.Product,
        RootPendingNaturalSuccessionQualification.RootFinalPort,RootPendingNaturalSuccessionQualification.RootRetainedFinalizationPort {
    public static final String QUERY_CONTRACT="lifecycle/current-timeline-blocker-gameplay12004/v1";
    public static final String RECONCILIATION_QUERY_CONTRACT=RootPendingUiCloseReconciliation.CONTRACT;
    private static final OperationKey QUERY=new OperationKey(NativeTimelineBlocker12004.QUERY_STEP);
    private static final OperationKey CLOSE=new OperationKey(NativeTimelineBlocker12004.CLOSE_STEP);
    private static final OpportunityJson.Obj EMPTY=new OpportunityJson.Obj(Map.of());
    private final RootDriverLifecycleRuntimeInstaller.Prepared owner;
    private final RootRuntimeContext context;private final RootLifecycleRuntimeFactory.Installed lifecycle;
    private final RootNaturalSuccessionOriginals natural;private DriverStateAssembler assembler;
    private final RootPendingNaturalSuccessionQualification qualification;
    private final RootPendingUiColdQualification coldQualification;
    private final RootPendingUiContinuity continuity;
    private final ThreadLocal<RootPendingNaturalSuccessionQualification.ReconnectedCause> openingReconnected=new ThreadLocal<>();
    private final ReadContract<NativeTimelineBlocker12004.Query> query;
    private final ReadContract<NativeTimelineBlocker12004.Query> reconciliationQuery;
    private final RootDomainInstallation installation;
    private final ExactRef executable;private final String executableFileId,executableMtimeNs;
    private RootNaturalSuccessionOriginals.InitialCause initial;
    private volatile DriverStateAssembler.PendingEpisodePublication publication;private volatile boolean completedByCanonicalLifecycle;
    private volatile SuccessorUiObligation obligation;
    private DriverStateAssembler.QualifiedPendingCurrent qualifiedAfterChild;private ActionCommand completedChild;
    private final Set<String> incorporatedChildren=new HashSet<>();
    private MutationCapture mutation;private FinalToken completed;
    private final ThreadLocal<Current> executing=new ThreadLocal<>();
    private static final class ContinuationCall {
        final ActionCommand parent;final Current original;Current latest;
        ContinuationCall(ActionCommand parent,Current original){this.parent=parent;this.original=original;this.latest=original;}
    }
    private final ThreadLocal<ContinuationCall> continuationCall=new ThreadLocal<>();
    private final ThreadLocal<NaturalClockOriginals.DateIntent> enteringDate=new ThreadLocal<>();
    private final ThreadLocal<PendingDateSource> dateScope=new ThreadLocal<>();
    private NaturalClockOriginals.DateIntent actualDateIntent;private ActionCommand actualDateCommand;private ActionReceipt actualDateReceipt;
    private PendingDateSource actualDateSource;
    private final ThreadLocal<NaturalClockOriginals.EventIntent> enteringEvent=new ThreadLocal<>();
    private final ThreadLocal<PendingEventSource> eventScope=new ThreadLocal<>();
    private final ThreadLocal<ExactRef> enteringEventDiagnosis=new ThreadLocal<>();
    private final Map<String,EventEntry> eventEntries=new LinkedHashMap<>();private EventEntry latestEvent;
    private static final class RetainedLateAck {
        final ActionCommand command;final NativeActionPort.AckReceived ack;ExactRef original;ExactRef retainedProof;
        RetainedLateAck(ActionCommand command,NativeActionPort.AckReceived ack){this.command=command;this.ack=ack;}
    }
    private final Map<String,RetainedLateAck> lateCloseAcks=new LinkedHashMap<>();
    private record CloseQueryOriginal(PlanningReadReceipt receipt,ExactRef original) { }
    private final Map<String,List<CloseQueryOriginal>> closePostQueries=new LinkedHashMap<>();
    private final Map<ExactRef,PlanningReadReceipt> modalQueryOriginals=new LinkedHashMap<>();
    private RetainedLateAck originalLateCloseAck(ContinuityStorePort.Session same,ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome original)throws IOException {
        var retained=lateCloseAcks.get(command.actionId());if(retained!=null)return retained;
        var canonical=find(same,command.actionId());require(canonical.command().equals(command)&&canonical.state() instanceof ActionState.Unknown,"original late Close poll requires its canonical UNKNOWN child");
        for(var evidence:((ActionState.Unknown)canonical.state()).evidence()) {
            com.fasterxml.jackson.databind.JsonNode row;try{row=StrictJson.parse(archive(same).loadMaterial(evidence).bytes());}catch(RuntimeException unavailableOtherEvidence){continue;}
            if(!row.isObject()||!row.path("schema").asText().equals("xar.java.pending-close-original-ack/v1"))continue;
            var exact=StrictJson.object(row,Set.of("schema","machine_id","observed_at_utc","action_id","body_sha256","request_id","ack"));
            require(StrictJson.text(exact.get("machine_id")).equals(context.game().machineId())&&StrictJson.text(exact.get("action_id")).equals(command.actionId())&&StrictJson.text(exact.get("body_sha256")).equals(ActionCodec.bodySha256(command))&&StrictJson.text(exact.get("request_id")).equals(attempt.requestId()),"canonical retained ACK descriptor changed its original source/action");Instant.parse(StrictJson.text(exact.get("observed_at_utc")));
            var reference=ExactRef.fromJson(exact.get("ack"));var loaded=archive(same).load(reference);require(loaded instanceof NativeActionPort.AckReceived,"retained original ACK descriptor points to another outcome");
            retained=new RetainedLateAck(command,(NativeActionPort.AckReceived)loaded);retained.original=reference;retained.retainedProof=evidence;lateCloseAcks.put(command.actionId(),retained);new ReconciledControlAck(retained.ack).requireMatches(command,attempt,original);return retained;
        }
        var candidate=context.transport().pollOriginalOutcome(attempt.requestId());if(candidate.isEmpty())return null;
        retained=new RetainedLateAck(command,candidate.orElseThrow());lateCloseAcks.put(command.actionId(),retained);return retained;
    }
    private List<ExactRef> retainedCloseAckEvidence(ActionCommand command,ExactRef packet){var candidate=lateCloseAcks.get(command.actionId());var refs=new ArrayList<ExactRef>();refs.add(packet);if(candidate!=null){if(candidate.original!=null)refs.add(candidate.original);if(candidate.retainedProof!=null)refs.add(candidate.retainedProof);}closePostQueries.getOrDefault(command.actionId(),List.of()).forEach(value->refs.add(value.original()));return List.copyOf(refs);}
    private record Issued(Current current,ActionCommand child) { }
    private final Map<String,Issued> issued=new LinkedHashMap<>();
    private final ThreadLocal<RootDriverLifecyclePublicCodec.Close> publicRequest=new ThreadLocal<>();
    private final ThreadLocal<FinalScope> finalizing=new ThreadLocal<>();
    private record RecoveryInputs(ContinuityStorePort.Session same,WriterContracts.Head head,Known current,
            DriverPendingEpisodeSource.InitialMetadata initialMetadata,ExactRef initialSource) { }
    private final ThreadLocal<RecoveryInputs> recoveryInputs=new ThreadLocal<>();
    private final ThreadLocal<RecoveryCapture> recovering=new ThreadLocal<>();
    private record FinalRecoveryInputs(ContinuityStorePort.Session same,WriterContracts.Head head,
            RootLifecycleAuthority.SnapshotLease physical,RootNaturalSuccessionOriginals.InitialCause original,
            Optional<LifecycleComposites.RecordedPendingEpisode> lifecycle) { }
    private final ThreadLocal<FinalRecoveryInputs> finalRecoveryInputs=new ThreadLocal<>();
    private final ThreadLocal<RetainedFinalScope> openingRetainedFinal=new ThreadLocal<>();
    private RetainedFinalScope retainedFinalScope;
    private CommittedRecovery committedRecovery;
    private RootPendingUiAdmittedEpisodeQualification admittedQualification;
    private ContinuityBatchJournal transportJournal;
    private ContinuityBatchJournal.ReboundTransport transported;
    private BigInteger bootstrappedConnection;
    private AdmittedRecovery admittedRecovery;
    /** Actual new-Game SAVE/LOAD custody only; the completed auxiliary remains historical DATA. */
    private record RestoredFinalized(RestoreCheckpointService.ReboundOrigin origin,SuccessorUiObligation state,ActionReceipt parent) { }
    private RestoredFinalized restoredFinalized;
    private record AdmittedRead(AdmittedRecovery retained,LifecycleEpisodeInputs.CurrentAdoptionBinding actual,RootLifecycleAuthority.SnapshotLease lease) { }
    private final ThreadLocal<AdmittedRead> admittedReadScope=new ThreadLocal<>();
    private final class RetainedInitial implements DriverPendingEpisodeSource.RecordedCapture,RootNaturalSuccessionOriginals.InitialCause {
        private final RootPendingNaturalSuccessionQualification.PendingCause cause;
        private final RootPendingNaturalSuccessionQualification.RetainedOriginals original;
        private final org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004.ComparedEstate estate;
        private final LifecycleObservationPort.Snapshot parentFrame;
        private final DriverPendingEpisodeSource.InitialMetadata metadata;private final ExactRef source;
        private final DomainBodies.RecordedImport committed;private final SuccessorUiObligationReducer.PendingEpisode projection;
        private final DriverPendingEpisodeProjection child;
        private RetainedInitial(RootPendingNaturalSuccessionQualification.PendingCause cause,
                RootPendingNaturalSuccessionQualification.RetainedOriginals original,
                org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004.ComparedEstate estate,
                LifecycleObservationPort.Snapshot parentFrame,DriverPendingEpisodeSource.InitialMetadata metadata,
                ExactRef source,DomainBodies.RecordedImport committed,SuccessorUiObligationReducer.PendingEpisode projection,DriverPendingEpisodeProjection child) {
            this.cause=cause;this.original=original;this.estate=estate;this.parentFrame=parentFrame;this.metadata=metadata;this.source=source;this.committed=committed;this.projection=projection;this.child=child;
        }
        @Override public ActionCommand originalParent(){return original.parent();}
        @Override public RootPendingNaturalSuccessionQualification.PendingCause cause(){return cause;}
        @Override public org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004.ComparedEstate matchedEstate(){return estate;}
        @Override public LifecycleObservationPort.Snapshot terminalSnapshot(){return original.oldTerminal();}
        @Override public LifecycleObservationPort.Snapshot originalParentFrame(){return parentFrame;}
        @Override public Known actualKnown(){return original.oldTerminal().facts();}
        @Override public SuccessorUiObligationReducer.PendingEpisode pendingEpisode(){return projection;}
        @Override public ExactRef canonicalDomainRef(){return metadata.canonicalDomain();}
        @Override public DriverPendingEpisodeProjection canonicalProjection(){return child;}
        @Override public ExactRef projectionOriginal(){return metadata.projection();}
        @Override public ExactRef originalParentKnown(){return metadata.parentKnown();}
        @Override public ExactRef originalBeforeNative(){return metadata.beforeNative();}
        @Override public DomainBodies.RecordedImport recordedImport(){return committed;}
        @Override public ExactRef originalSource(){return source;}
    }
    private record RetainedMutation(Known actualKnown,SuccessorUiObligation beforeObligation,DriverPendingEpisodeSource.Change change,
            SuccessorUiObligation afterObligation,DriverPendingEpisodeMutations.Prepared preparedProjection,
            DomainBodies.RecordedImport recordedImport,ExactRef canonicalDomainRef,ExactRef originalSource,ExactRef originalBeforeNative,Instant actualObservedAtUtc)
            implements DriverPendingEpisodeSource.RecordedMutation { }
    private final class RecoveryCapture implements DriverPendingEpisodeSource.Recovery {
        private final ContinuityStorePort.Session same;private final WriterContracts.Head head;
        private final RootLifecycleAuthority.SnapshotLease physical;private final RetainedInitial original;
        private final List<DriverPendingEpisodeSource.RecoveryStep> steps;private final Known current;
        private DriverStateAssembler.PendingEpisodePublication published;
        private RecoveryCapture(ContinuityStorePort.Session same,WriterContracts.Head head,RootLifecycleAuthority.SnapshotLease physical,
                RetainedInitial original,List<DriverPendingEpisodeSource.RecoveryStep> steps,Known current) {
            this.same=same;this.head=head;this.physical=physical;this.original=original;this.steps=List.copyOf(steps);this.current=current;
        }
        @Override public DriverPendingEpisodeSource.RecordedCapture initialCapture(){return original;}
        @Override public List<DriverPendingEpisodeSource.RecoveryStep> transitions(){return steps;}
        @Override public Known actualCurrent(){return current;}
    }
    private record RecordedStage(DriverPendingEpisodeSource.RecoveryMetadata metadata,ExactRef originalSource,
            Known before,Known after,DomainBodies.RecordedImport committed,NaturalClockOriginals.Document document) { }
    private sealed interface RetainedStep permits RetainedMutationStage,RetainedActionStage { }
    private record RetainedMutationStage(RecordedStage stage) implements RetainedStep { }
    private record RetainedActionStage(ActionReceipt action,Known after) implements RetainedStep { }
    private record RetainedChain(RecordedStage initial,List<RetainedStep> steps) { }
    private DriverStateAssembler.PendingEpisodePublication recoveredPublication;private ExactRef recoveredDriver;
    private Known retainedKnown(DriverPendingEpisodeSource.RecoveryMetadata metadata)throws IOException {
        return retainedKnown(metadata.beforeKnown(),metadata.beforeNative());
    }
    private Known retainedKnown(ExactRef originalKnown,ExactRef originalNative)throws IOException {
        var raw=DriverSnapshotFacts.originalKnownJson(natural.readExact(originalKnown));var observation=DriverSnapshotFacts.observationOriginalReference(raw);
        Optional<DriverObservationFacts> replayed=Optional.empty();
        if(observation.isPresent()) {
            var reference=observation.orElseThrow();var manifest=RawJson.fullMaterial(natural.readExact(reference));
            var actual=DriverObservationEvidenceReader.nativeFrame(reference,manifest,natural.readExact(originalNative));
            var driver=DriverObservationEvidenceReader.currentDriverReference(reference,manifest);
            replayed=Optional.of(DriverObservationEvidenceReader.decode(reference,manifest,RawJson.fullMaterial(natural.readExact(driver)),actual));
        }
        return DriverSnapshotFacts.decodeKnownOriginal(raw,replayed);
    }
    private RecordedStage recordedStage(ContinuityStorePort.Session same,ExactRef reference,Known after)throws IOException {
        var metadata=DriverPendingEpisodeSource.decodeRecoveryMetadata(new RawJson(natural.readExact(reference)));
        require(metadata.machineId().equals(context.game().machineId()),"pending recovery machine changed");
        var committed=same.requireHistoricalImport(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,metadata.canonicalHeadSequence(),metadata.canonicalHeadSha256());
        require(committed.receipt().eventIdentity().equals(metadata.eventIdentity())&&committed.body().payload().equals(metadata.canonicalDomain())
                &&committed.request().contractSchema().equals(DriverPendingEpisodeSource.DOMAIN_SCHEMA),"pending metadata is not its exact historical canonical import");
        var bytes=natural.readExact(metadata.canonicalDomain());var document=NaturalClockOriginals.decode(bytes);
        require(Arrays.equals(committed.request().producerInput(),bytes)&&committed.request().evidence().equals(natural.computedArtifacts(document)),"historical pending import lost its complete typed original closure");
        var before=retainedKnown(metadata);require(metadata.observedAtUtc().equals(document.observedAtUtc()),"pending metadata observation time differs from its original canonical document");
        return new RecordedStage(metadata,reference,before,after,committed,document);
    }
    private static ExactRef pendingMetadataReference(Known known) {
        var values=known.auxiliary().members();var value=values.get(DriverPendingEpisodeSource.MUTATION_KEY);
        if(value==null)value=values.get(DriverPendingEpisodeSource.PUBLICATION_KEY);
        require(value!=null,"actual canonical pending Driver source metadata missing");return DriverObservationEvidenceReader.reference(value);
    }
    private DriverPendingEpisodeSource.Change retainedChange(DriverPendingEpisodeSource.MutationMetadata metadata,SuccessorUiObligation after)throws IOException {
        return switch(metadata.phase()) {
            case OBSERVE->new DriverPendingEpisodeSource.Observe(after.observation().orElseThrow());
            case CLOSE_ENTER->new DriverPendingEpisodeSource.EnterClose(after.closeAttempt().orElseThrow());
            case RETAIN_RESULT->new DriverPendingEpisodeSource.RetainResult(after.closeAttempt().orElseThrow().receipt().orElseThrow());
            case RETAIN_POSTCONDITIONS->new DriverPendingEpisodeSource.RetainPostconditions(after.closeAttempt().orElseThrow().receipt().orElseThrow());
            case RECONCILE->new DriverPendingEpisodeSource.Reconcile(after.closeAttempt().orElseThrow().receipt().orElseThrow().reconciliation().orElseThrow());
            case REBIND->new DriverPendingEpisodeSource.Rebind(after.rebind().orElseThrow());
            case FINALIZE->throw new IOException("cold final business publication needs its actual retained private finalization issuer; no Finalized token is decoded from DATA");
        };
    }
    private RetainedMutation retainedMutation(RecordedStage stage)throws IOException {
        var metadata=(DriverPendingEpisodeSource.MutationMetadata)stage.metadata();var pending=stage.document().pendingProjection().orElseThrow();
        var artifact=pending.latestMutation().orElseThrow(()->new IOException("actual mutation document has no original mutation artifact"));
        require(artifact.beforeObligation().equals(metadata.beforeObligation())&&artifact.afterObligation().equals(metadata.afterObligation()),"historical mutation metadata/obligation mismatch");
        var before=SuccessorUiObligationCodec.decode(natural.readExact(metadata.beforeObligation()));var after=SuccessorUiObligationCodec.decode(natural.readExact(metadata.afterObligation()));
        var change=metadata.phase()==DriverPendingEpisodeSource.MutationPhase.FINALIZE?retainedFinalChange(stage,after):retainedChange(metadata,after);var projected=DriverPendingEpisodeMutations.project(stage.before(),before,change);
        require(projected.obligation().equals(after),"historical mutation did not replay through the sole obligation reducer");
        var prepared=new DriverPendingEpisodeMutations.Prepared(projected,artifact.beforeDriver(),artifact.afterDriver(),artifact.afterAuxiliary(),artifact.beforeObligation(),artifact.afterObligation(),artifact.result());
        var replayed=new RetainedMutation(stage.before(),before,change,after,prepared,stage.committed(),metadata.canonicalDomain(),stage.originalSource(),metadata.beforeNative(),metadata.observedAtUtc());
        if(change instanceof DriverPendingEpisodeSource.Finalize){require(retainedFinalScope!=null&&retainedFinalScope.stage==stage,"final recovery lost its genuine private M3 scope");retainedFinalScope.replayed=replayed;}
        return replayed;
    }
    private Known beforeRetainedAction(ContinuityStorePort.Session same,Known after,ActionReceipt action)throws IOException {
        var actual=DriverActionHistoryState.findCommittedCoverage(same,action,archive(same)).orElseThrow(()->new IOException("retained ACTION has no canonical full Driver publication"));
        var edge=actual.publication();require(edge.afterVersion()==after.stamp().driverVersion()&&edge.episodeEpoch()==after.stamp().episodeEpoch()
                &&Arrays.equals(natural.readExact(edge.afterDriver()),after.driver().encode()),"retained ACTION is not the actual last full Driver transition");
        var rows=new ArrayList<>(after.actionRows());require(!rows.isEmpty(),"retained ACTION coverage is missing");var last=rows.removeLast();
        require(last.actionId().equals(action.command().actionId())&&last.bodySha256().equals(action.bodySha256())&&last.durableSequence()==action.sequence(),"retained ACTION order changed its exact canonical receipt");
        var driver=org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(natural.readExact(edge.beforeDriver()));
        var stamp=new DriverSnapshotFacts.Stamp(edge.beforeVersion(),edge.episodeEpoch(),after.stamp().game(),driver.session().episodeRunId(),edge.beforeDriver().sha256());
        return new Known(driver,stamp,after.originalHistoryBasis(),rows,after.auxiliary(),after.loop(),Optional.empty());
    }
    private Known canonicalBusinessKnown(ContinuityStorePort.Session same)throws IOException {
        var known=assembler().withFrozenFacts(same,frozen->{if(!(frozen.state() instanceof Known value))throw new IOException("canonical pending Known unavailable");return value;});
        var metadata=DriverPendingEpisodeSource.decodeRecoveryMetadata(new RawJson(natural.readExact(pendingMetadataReference(known))));
        if(metadata instanceof DriverPendingEpisodeSource.MutationMetadata mutation&&mutation.phase()==DriverPendingEpisodeSource.MutationPhase.FINALIZE) {
            var state=SuccessorUiObligationCodec.decode(DriverJson.encode(known.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
            var parent=find(same,state.binding().parentActionId());
            if(parent.state() instanceof ActionState.CompositeSettled||known.stamp().driverVersion()==Math.addExact(retainedKnown(mutation).stamp().driverVersion(),2)) {
                var edge=lifecycle.composite().recordedPendingEpisode(same,parent);edge.requireCurrent(same);
                return retainedKnown(edge.beforeKnownOriginal(),edge.beforeNativeOriginal());
            }
        }
        return known;
    }
    private void requireCanonicalRebind(ContinuityStorePort.Session same,SuccessorUiObligation state)throws IOException {
        var expected=state.rebind().orElseThrow(()->new IOException("canonical reconnect proof absent"));
        for(var item:retainedChain(same,canonicalBusinessKnown(same)).steps())if(item instanceof RetainedMutationStage mutation
                &&mutation.stage().metadata() instanceof DriverPendingEpisodeSource.MutationMetadata metadata
                &&metadata.phase()==DriverPendingEpisodeSource.MutationPhase.REBIND) {
            var before=SuccessorUiObligationCodec.decode(natural.readExact(metadata.beforeObligation()));
            var after=SuccessorUiObligationCodec.decode(natural.readExact(metadata.afterObligation()));
            if(after.rebind().filter(expected::equals).isEmpty())continue;
            require(expected.priorCanonicalObligation().equals(metadata.beforeObligation())
                    &&SuccessorUiObligationReducer.rebind(before,expected).equals(after),"canonical Rebind did not replay its original sole reducer");
            retainedMutation(mutation.stage());return;
        }
        throw new IOException("actual canonical Rebind import/original reducer is missing");
    }
    private void requireCanonicalFinalized(ContinuityStorePort.Session same,SuccessorUiObligation state)throws IOException {
        require(state.phase()==SuccessorUiObligation.Phase.FINALIZED,"actual finalized obligation required");
        for(var item:retainedChain(same,canonicalBusinessKnown(same)).steps())if(item instanceof RetainedMutationStage mutation
                &&mutation.stage().metadata() instanceof DriverPendingEpisodeSource.MutationMetadata metadata
                &&metadata.phase()==DriverPendingEpisodeSource.MutationPhase.FINALIZE) {
            var before=SuccessorUiObligationCodec.decode(natural.readExact(metadata.beforeObligation()));
            var after=SuccessorUiObligationCodec.decode(natural.readExact(metadata.afterObligation()));
            require(after.equals(state)&&SuccessorUiObligationReducer.finalizeVerified(before,after.finalization().orElseThrow()).equals(after),
                    "canonical finalization did not replay its original sole obligation reducer");return;
        }
        throw new IOException("actual canonical finalization import is missing");
    }
    private RetainedChain retainedChain(ContinuityStorePort.Session same,Known actualCurrent)throws IOException {
        var backwards=new ArrayList<RetainedStep>();var current=actualCurrent;var visited=new HashSet<ExactRef>();
        for(int count=0;count<65_536;count++) {
            var reference=pendingMetadataReference(current);var stage=recordedStage(same,reference,current);
            long expected=Math.addExact(stage.before().stamp().driverVersion(),1);
            require(current.stamp().driverVersion()>=expected,"pending source metadata is newer than its actual canonical Driver");
            if(current.stamp().driverVersion()>expected) {
                var row=current.actionRows().getLast();var action=find(same,row.actionId());
                backwards.add(new RetainedActionStage(action,current));current=beforeRetainedAction(same,current,action);continue;
            }
            require(visited.add(reference),"cyclic pending source metadata is not a historical chain");
            if(stage.metadata() instanceof DriverPendingEpisodeSource.InitialMetadata) {Collections.reverse(backwards);return new RetainedChain(stage,List.copyOf(backwards));}
            backwards.add(new RetainedMutationStage(stage));current=stage.before();
        }
        throw new IOException("pending recovery exceeds its finite actual canonical history bound");
    }
    ExactRef requireRetainedParentKnown(ContinuityStorePort.Session same,RootPendingNaturalSuccessionQualification.PendingCause cause)throws IOException {
        var inputs=recoveryInputs.get();require(inputs!=null&&inputs.same()==same&&same.head().digest().equals(inputs.head().digest()),"parent Known lacks its actual same-writer canonical recovery scope");
        var material=coldQualification.requireRetainedMaterial(same,cause);
        var body=NaturalClockOriginals.decode(natural.readExact(inputs.initialMetadata().canonicalDomain()));var child=body.pendingProjection().orElseThrow();
        require(child.value().qualifiedCause().sha256().equals(cause.causeDigest())&&cause.parentBodySha256().equals(ActionCodec.bodySha256(material.parent()))
                &&inputs.initialMetadata().projection().equals(child.original()),"retained parent Known belongs to a different actual cause/parent");
        assembler().withFrozenFacts(same,frozen->{require(frozen.state() instanceof Known,"actual current pending Driver is missing");requireSameKnown(inputs.current(),(Known)frozen.state());return null;});
        return inputs.initialMetadata().parentKnown();
    }
    private static void requireSameKnown(Known expected,Known actual) {
        require(expected.stamp().equals(actual.stamp())&&Arrays.equals(expected.driver().encode(),actual.driver().encode())
                &&expected.originalHistoryBasis().equals(actual.originalHistoryBasis())&&expected.actionRows().equals(actual.actionRows())&&expected.auxiliary().equals(actual.auxiliary()),"actual pending full Driver/history/auxiliary changed");
    }
    /** Historical source DATA is compared against this authority's genuine current qualification, never made live. */
    private void requireRetainedSource(ContinuityStorePort.Session same,Optional<ExactRef> original,
            org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification current)throws IOException {
        context.writer().requireSession(same);current.assertCurrent(same);
        // Provenance is optional DATA; actual frame/canonical pending-history custody is checked by the caller.
        Objects.requireNonNull(original);current.assertCurrent(same);
    }
    DriverPendingEpisodeSource.Recovery currentRecovery(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException {
        var actual=recovering.get();requireRecovery(same,expected,actual);return actual;
    }
    void requireRecovery(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Recovery identical)throws IOException {
        requireDriverContext();context.writer().requireSession(same);var actual=recovering.get();
        require(expected==assembler()&&actual!=null&&actual==identical&&actual.same==same&&actual.head.digest().equals(same.head().digest()),"cold DATA has no identical private Root/M3 recovery issuer");
        actual.physical.assertCurrent(same);var retained=coldQualification.requireRetainedMaterial(same,actual.original.cause());
        if(openingReconnected.get()!=null)qualification.requireReconnectedCauseCurrent(openingReconnected.get(),actual.physical.fullSnapshot(),same,actual.physical.sourceQualification(),actual.head);
        require(retained.parent().equals(actual.original.originalParent()),"retained recovery changed its actual original parent");
        assembler().withFrozenFacts(same,frozen->{require(frozen.state() instanceof Known,"actual pending Known missing");requireSameKnown(actual.current,(Known)frozen.state());return null;});
        for(var step:actual.steps)if(step instanceof DriverPendingEpisodeSource.RecoveryMutation value) {
            var edge=value.actual().recordedImport();var reopened=same.requireHistoricalImport(edge.body().slot(),edge.receipt().head().sequence(),ContinuityJson.digest(edge.receipt().head().toJson()));
            require(reopened.body().equals(edge.body())&&reopened.canonicalEvent().equals(edge.canonicalEvent()),"retained mutation canonical import changed during recovery");
            if(value.actual().change() instanceof DriverPendingEpisodeSource.Finalize) {
                var scope=retainedFinalScope;require(scope!=null&&scope.qualified()&&scope.replayed==value.actual()
                        &&scope.same==same&&scope.head.digest().equals(actual.head.digest()),"cold final DATA has no identical privately requalified M3 source");
                requireRetainedScopeCurrent(scope);
            }
        }
    }
    void requireRecovered(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Recovery identical,
            DriverStateAssembler.PendingEpisodePublication genuine,Known actualCurrent)throws IOException {
        requireRecovery(same,expected,identical);var actual=recovering.get();requireSameKnown(actual.current,actualCurrent);
        require(actual.published==null||actual.published==genuine,"one actual recovered publication only");
        require(genuine!=null,"recovery must bind the genuine assembler result without a Driver CAS");requireSameKnown(genuine.after(),actualCurrent);actual.published=genuine;
    }
    private void recoverPending(ContinuityStorePort.Session same,Instant deadline)throws IOException {
        var current=assembler().withFrozenFacts(same,frozen->{if(!(frozen.state() instanceof Known known))throw new IOException("actual pending Driver facts unavailable");return known;});
        if(!current.auxiliary().members().containsKey(SuccessorUiObligation.AUXILIARY_KEY))return;
        require(publication==null&&initial==null&&recovering.get()==null&&recoveryInputs.get()==null,"nested/replaced cold pending issuer forbidden");
        Optional<LifecycleComposites.RecordedPendingEpisode> lifecycleEdge=Optional.empty();Known replayCurrent=current;
        var lastMetadata=DriverPendingEpisodeSource.decodeRecoveryMetadata(new RawJson(natural.readExact(pendingMetadataReference(current))));
        if(lastMetadata instanceof DriverPendingEpisodeSource.MutationMetadata last&&last.phase()==DriverPendingEpisodeSource.MutationPhase.FINALIZE) {
            var before=retainedKnown(last);long afterBusiness=Math.addExact(before.stamp().driverVersion(),1);
            if(current.stamp().driverVersion()==Math.addExact(afterBusiness,1)) {
                var state=SuccessorUiObligationCodec.decode(DriverJson.encode(current.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
                var edge=lifecycle.composite().recordedPendingEpisode(same,find(same,state.binding().parentActionId()));edge.requirePublishedCurrent(same);
                replayCurrent=retainedKnown(edge.beforeKnownOriginal(),edge.beforeNativeOriginal());
                require(replayCurrent.stamp().driverVersion()==afterBusiness&&replayCurrent.auxiliary().equals(edge.beforeAuxiliary())
                        &&Arrays.equals(replayCurrent.driver().encode(),edge.beforeDriver().encode()),"recorded lifecycle lacks its complete original pre-metadata Known");
                lifecycleEdge=Optional.of(edge);
            }
        }
        var chain=retainedChain(same,replayCurrent);var first=chain.initial();var metadata=(DriverPendingEpisodeSource.InitialMetadata)first.metadata();var head=same.head();
        var actualLifecycle=lifecycleEdge;var replayedCurrent=replayCurrent;
        recoveryInputs.set(new RecoveryInputs(same,head,current,metadata,first.originalSource()));
        try {lifecycle.physical().withSnapshot(same,deadline,lease->continuity.withLease(same,lease,()->{
            lease.assertCurrent(same);requireSameKnown(current,lease.factsKnown());
            var document=NaturalClockOriginals.decode(natural.readExact(natural.currentCaptureDocument()));var pending=document.pendingProjection().orElseThrow();
            var state=SuccessorUiObligationCodec.decode(natural.readExact(pending.currentObligation()));
            require(state.equals(SuccessorUiObligationCodec.decode(DriverJson.encode(current.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY))))
                    &&state.binding().qualifiedCause().equals(pending.value().qualifiedCause()),"actual canonical obligation/full Driver mismatch");
            var transport=lease.fullSnapshot().actual().session();var old=state.binding().predecessor();
            boolean reconnected=!transport.sessionId().equals(old.sessionId())||!transport.connectionGeneration().equals(old.connectionGeneration());
            RootPendingNaturalSuccessionQualification.PendingCause cause;
            if(reconnected){var qualified=qualification.qualifyRetainedCauseReconnected(pending.value().qualifiedCause(),lease.fullSnapshot(),same,lease.sourceQualification(),head);openingReconnected.set(qualified);cause=qualified.historicalCause();}
            else cause=qualification.qualifyRetainedCause(pending.value().qualifiedCause(),lease.fullSnapshot(),same,lease.sourceQualification(),head);
            var original=coldQualification.requireRetainedMaterial(same,cause);var estate=coldQualification.requireRetainedCauseOriginals(same,cause).estate();
            var parentFrame=coldQualification.requireParentOriginalFrame(same,cause);var child=first.document().pendingProjection().orElseThrow();
            var projected=SuccessorUiObligationReducer.pendingEpisode(original.oldTerminal(),state.binding());
            var initial=new RetainedInitial(cause,original,estate,parentFrame,metadata,first.originalSource(),first.committed(),projected,child.value());
            requireSameKnown(initial.actualKnown(),first.before());var steps=new ArrayList<DriverPendingEpisodeSource.RecoveryStep>();
            require(finalRecoveryInputs.get()==null,"nested final recovery forbidden");finalRecoveryInputs.set(new FinalRecoveryInputs(same,head,lease,initial,actualLifecycle));
            try {for(var item:chain.steps()) {
                    if(item instanceof RetainedActionStage action)steps.add(new DriverPendingEpisodeSource.RecoveryAction(action.action(),action.after()));
                    else steps.add(new DriverPendingEpisodeSource.RecoveryMutation(retainedMutation(((RetainedMutationStage)item).stage())));
                }}finally{finalRecoveryInputs.remove();}
            var capture=new RecoveryCapture(same,head,lease,initial,steps,replayedCurrent);
            if(actualLifecycle.isPresent()) {
                var replayed=DriverPendingEpisodeSource.replayRecovery(same,capture,archive(same),natural.registration().producerSources());
                require(retainedFinalScope!=null&&retainedFinalScope.qualified()&&replayed.canonicalDomain().equals(natural.currentCaptureDocument()),"committed lifecycle recovery has no actual complete private final replay");
                this.initial=initial;obligation=state;committedRecovery=new CommittedRecovery(actualLifecycle.orElseThrow(),retainedFinalScope,replayed.actualDriverOriginal());
                committedRecovery.deadline=deadline;
                if(retainedFinalScope.proof.verifiedDateAdvance().isPresent())actualDateReceipt=archive(same).loadReceipt(retainedFinalScope.proof.verifiedDateAdvance().orElseThrow());
                try{lifecycle.composite().recoverCommittedPendingEpisode(same,actualLifecycle.orElseThrow().parent(),actualLifecycle.orElseThrow());lease.assertCurrent(same);return null;}
                catch(IOException|RuntimeException failure){this.initial=null;obligation=null;committedRecovery=null;retainedFinalScope=null;throw failure;}
            }
            recovering.set(capture);
            try {
                var genuine=assembler().recoverPendingEpisodePublication(same);require(capture.published==genuine,"actual source did not bind its recovered private publication");
                var replayed=DriverPendingEpisodeSource.replayRecovery(same,capture,archive(same),natural.registration().producerSources());
                require(replayed.canonicalDomain().equals(natural.currentCaptureDocument()),"recovery did not end at the actual canonical pending document");
                this.initial=initial;publication=genuine;recoveredPublication=genuine;recoveredDriver=replayed.actualDriverOriginal();obligation=state;
                try {restoreRetainedIntents(same,document,deadline);if(retainedFinalScope!=null)completed=new RetainedFinalTokenImpl(new Current(publication,obligation,deadline),retainedFinalScope);lease.assertCurrent(same);return null;}
                catch(IOException|RuntimeException incomplete){this.initial=null;publication=null;recoveredPublication=null;recoveredDriver=null;obligation=null;actualDateIntent=null;actualDateCommand=null;actualDateReceipt=null;actualDateSource=null;issued.clear();incorporatedChildren.clear();eventEntries.clear();latestEvent=null;retainedFinalScope=null;completed=null;throw incomplete;}
            } finally {recovering.remove();}
        }));}catch(IOException|RuntimeException failure){retainedFinalScope=null;completed=null;throw failure;} finally {recoveryInputs.remove();openingReconnected.remove();}
    }
    /** Reopen existing once intents only; no ID, command body, ACK or replacement attempt is synthesized. */
    private void restoreRetainedIntents(ContinuityStorePort.Session same,NaturalClockOriginals.Document document,Instant deadline)throws IOException {
        var current=new Current(publication,obligation,deadline);var parent=find(same,initial.originalParent().actionId());
        var children=ActionTransitions.composite(parent.state()).orElseThrow(()->new IOException("actual retained Continue cursor is missing")).children();
        if(obligation.closeAttempt().isPresent()) {
            var intent=obligation.closeAttempt().orElseThrow();var command=ActionCodec.decodeCommand(natural.readExact(intent.originalCommand()));
            require(command.actionId().equals(intent.actionId())&&ActionCodec.bodySha256(command).equals(intent.commandBodySha256())&&command.operation().equals(CLOSE),"retained once-Close body changed");
            var exact=new CompositeExecution.Child(command.actionId(),ActionCodec.bodySha256(command));require(children.contains(exact),"retained Close intent has no actual canonical parent reservation; pre-INTENT absence remains missing");
            var action=find(same,command.actionId());require(action.command().equals(command),"retained Close command is not the exact canonical child");
            if(action.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied)verifyCloseControl(action,archive(same));
            issued.put(command.actionId(),new Issued(new Current(publication,obligation,command.deadline()),command));
        }
        var pending=document.pendingProjection().orElseThrow();
        if(pending.dateIntent().isPresent()) {
            actualDateIntent=pending.dateIntent().orElseThrow();actualDateCommand=ActionCodec.decodeCommand(natural.readExact(actualDateIntent.command()));
            require(actualDateCommand.actionId().equals(actualDateIntent.actionId())&&ActionCodec.bodySha256(actualDateCommand).equals(actualDateIntent.bodySha256())&&AdvancePlan.decode(actualDateCommand).exactOneDay(),"retained date intent changed its actual exact-one-day body");
            require(children.contains(new CompositeExecution.Child(actualDateCommand.actionId(),actualDateIntent.bodySha256())),"retained date intent lacks its actual parent reservation");
            actualDateReceipt=find(same,actualDateCommand.actionId());require(actualDateReceipt.command().equals(actualDateCommand),"canonical date body differs from retained once intent");
            var close=archive(same).loadReceipt(actualDateIntent.closeReceipt());verifyCloseControl(close,archive(same));
            require(obligation.closeAttempt().flatMap(CloseAttempt::receipt).flatMap(CloseReceipt::effectiveMaterialClearance).filter(actualDateIntent.materialClearance()::equals).isPresent(),"retained date lost its actual Close clearance");
            var originalDate=new Current(publication,obligation,actualDateCommand.deadline());actualDateSource=new PendingDateSource(originalDate);var date=new DateCurrent(originalDate,actualDateSource);
            issued.put(actualDateCommand.actionId(),new Issued(date,actualDateCommand));
        }
        if(pending.eventIntent().isPresent()) {
            var event=pending.eventIntent().orElseThrow();var command=ActionCodec.decodeCommand(natural.readExact(event.command()));
            require(command.actionId().equals(event.actionId())&&ActionCodec.bodySha256(command).equals(event.bodySha256()),"retained event once body changed");
            require(children.contains(new CompositeExecution.Child(command.actionId(),event.bodySha256())),"retained event intent has no actual canonical parent reservation; no cold child is submitted");
            var action=find(same,command.actionId());require(action.command().equals(command),"retained event has no identical canonical child");
            var inputs=new RootPendingUiEventRecovery.Inputs(events().eventWindowContract(),context.interactions().definitions().pendingQuery());
            var original=new RootPendingUiEventRecovery.Original(event.command(),event.originalRead(),event.interaction()?RootPendingUiEventRecovery.Kind.INTERACTION:RootPendingUiEventRecovery.Kind.EVENT,event.instanceId(),event.sourceOriginals());
            var replayed=RootPendingUiEventRecovery.recover(inputs,original,context.originals(),same);
            if(replayed instanceof RootPendingUiEventRecovery.Missing missing)throw new IOException("retained event preparation remains missing: "+missing.reason()+": "+missing.detail());
            var prepared=((RootPendingUiEventRecovery.Recovered)replayed).prepared();
            require(prepared.command().equals(command)&&prepared.originalReadRef().equals(event.originalRead())&&prepared.presentation().instanceId()==event.instanceId()
                    &&prepared.sourceOriginals().equals(event.sourceOriginals()),"retained event preparation differs from the exact canonical once intent");
            var entry=new EventEntry(prepared,event);entry.source=new PendingEventSource(current);
            require(eventEntries.putIfAbsent(command.actionId(),entry)==null,"retained event was already privately restored");latestEvent=entry;
            issued.put(command.actionId(),new Issued(new EventCurrent(current,entry),command));
            if(action.settled())incorporatedChildren.add(command.actionId());
        }
        for(var row:current.actualKnown().actionRows())incorporatedChildren.add(row.actionId());
    }
    private RootPendingUiRuntime(RootDriverLifecycleRuntimeInstaller.Prepared owner,RootRuntimeContext context,
            RootLifecycleRuntimeFactory.Installed lifecycle)throws IOException {
        this.owner=owner;this.context=context;this.lifecycle=lifecycle;natural=lifecycle.natural();
        continuity=new RootPendingUiContinuity(context,natural,new RootPendingUiContinuity.CanonicalReplay(){
            public void requireRebind(ContinuityStorePort.Session same,SuccessorUiObligation state)throws IOException{requireCanonicalRebind(same,state);}
            public void requireFinalized(ContinuityStorePort.Session same,SuccessorUiObligation state)throws IOException{requireCanonicalFinalized(same,state);}
            public void requireOutsideObservation(ContinuityStorePort.Session same)throws IOException{lifecycle.physical().requireOutsideObservationScope(same);}
        });
        coldQualification=new RootPendingUiColdQualification(context,natural,(same,capture,source)->{
            var actual=context.transport().latestObservedSnapshot().orElseThrow(()->new IOException("actual retained Managed packet absent")).session();
            if(capture.sessionId().equals(actual.sessionId())&&capture.connectionGeneration().equals(actual.connectionGeneration().toString()))natural.requireRetainedPhysical(same,capture,source);
            else continuity.requireRetainedPhysical(same,capture,source);
        },(same,old,source)->{context.writer().requireSession(same);source.assertCurrent(same);
        });
        qualification=new RootPendingNaturalSuccessionQualification(natural.pendingCausePort(),this,coldQualification,this,continuity);
        var exe=context.game().launchPlan().sources().review().gameExecutable();executable=new ExactRef(exe.path(),exe.bytes(),exe.sha256());
        var actualFile=SharedSourceFiles.nativeFile(java.nio.file.Path.of(executable.path()));executableFileId=actualFile.fileIdDecimal();executableMtimeNs=new BigInteger(actualFile.lastWriteFiletimeDecimal()).subtract(new BigInteger("116444736000000000")).multiply(BigInteger.valueOf(100)).toString();
        query=new ReadContract<>(QUERY_CONTRACT,QUERY,Optional.empty(),"allow_private_current_timeline_blocker_query",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,
                ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.GAMEPLAY_PAUSED_MAP,owner.sources().queryDefinition(),(request,id)->{
                    require(request.arguments().members().isEmpty(),"original timeline query has no additional wire fields");
                    try{requireQuery(request);}catch(IOException failure){throw new UncheckedIOException(failure);}
                    return new NativeRequest(QUERY.value(),Optional.empty(),new RawJson(new byte[]{'{','}'}));
                },this::decodeQuery,this::decodeQuery);
        reconciliationQuery=new ReadContract<>(RECONCILIATION_QUERY_CONTRACT,QUERY,Optional.empty(),"allow_private_current_timeline_blocker_query",ReadContract.PermissionMode.SOURCE_QUALIFIED_PRIVATE,ReadContract.WireProfile.EXECUTE_STEP,ReadContract.GuardMode.RECONCILIATION_OBSERVATION,owner.sources().queryDefinition(),(request,id)->{
            require(request.origin() instanceof CommandOrigin.Reconciliation&&request.arguments().members().isEmpty(),"exact pending Close reconciliation source required");
            try{var command=context.core().actions().withFrozen(context.borrowedSession(),held->held.find(request.origin().requireReconciliation().pending().actionId()).orElseThrow().command());require(ActionReconciliationScope.requireIdentity(command).sameGuardFrame(request.origin().requireReconciliation()),"query escaped its actual same original reconciliation callback");}
            catch(IOException failure){throw new UncheckedIOException(failure);}
            return new NativeRequest(QUERY.value(),Optional.empty(),new RawJson(new byte[]{'{','}'}));
        },this::decodeReconciliationQuery,this::decodeReconciliationQuery);
        installation=new RootDomainInstallation("post-continue-successor-ui",List.of(),List.of(new RootReadContractCatalog.InstalledRead(query,owner.sources().runtime()),new RootReadContractCatalog.InstalledRead(reconciliationQuery,owner.sources().runtime())),List.of(),
                List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Set.of(),List.of(),List.of(),List.of(),List.of(),List.of());
    }
    static RootPendingUiRuntime create(RootDriverLifecycleRuntimeInstaller.Prepared owner,RootRuntimeContext context,RootLifecycleRuntimeFactory.Installed lifecycle)throws IOException {
        lifecycle.requireContext(context);var actual=new RootPendingUiRuntime(owner,context,lifecycle);actual.natural.bindPendingUi(actual);return actual;
    }
    @Override public RootDomainInstallation installation(){return installation;}
    @Override public synchronized void requireContext(RootRuntimeContext actual)throws IOException {
        require(actual==context&&context.core()==owner.lifecycle().installedFor(context).natural().core()
                &&owner.lifecycle().installedFor(context)==lifecycle,"pending UI crossed its actual per-Game Root/Driver issuer");
        lifecycle.requireContext(context);
        if(assembler!=null)require(context.adopted().authority()==assembler,"pending UI changed its bound actual Driver issuer");
    }
    /** Installation is pre-Driver; business use binds only the actual adopted authority, once. */
    private synchronized DriverStateAssembler assembler()throws IOException {
        requireContext(context);var actual=context.adopted().authority();
        require(assembler==null||assembler==actual,"pending UI cannot replace its bound actual Driver issuer");
        if(assembler==null)assembler=actual;return assembler;
    }
    private void requireDriverContext()throws IOException {assembler();}
    private synchronized RootPendingUiAdmittedEpisodeQualification admittedQualification()throws IOException {
        assembler();
        if(admittedQualification==null)admittedQualification=new RootPendingUiAdmittedEpisodeQualification(context,lifecycle,this::requireRetainedSource);
        return admittedQualification;
    }
    public RootNaturalSuccessionOriginals natural(){return natural;}
    public RootPendingNaturalSuccessionQualification qualification(){return qualification;}
    /** The actual Root installs this once after its Journal and session exist. */
    public void installTransportContinuity(ContinuityStorePort.Session same)throws IOException {
        requireDriverContext();context.writer().requireSession(same);var root=context.core().sessionAccess().current();
        context.core().requireCurrentForAccess(same,root);require(root.driver()==context.adopted(),"transport port belongs to another Root Driver");
        var journal=root.batchJournal();if(transportJournal!=null){require(transportJournal==journal,"transport port cannot replace its actual Journal");return;}
        journal.bindTransportRebindPort(new SameGameTransportContinuity.Port(){
            @Override public <T>T withCurrent(ContinuityStorePort.Session borrowed,SessionPorts.SessionIdentity beforeOwner,
                    SessionPorts.SessionIdentity afterOwner,ActionCommand parent,Instant deadline,SameGameTransportContinuity.Work<T> work)throws IOException {
                return withTransportCurrent(borrowed,beforeOwner,afterOwner,parent,deadline,work);
            }
            @Override public void requireRecorded(ContinuityStorePort.Session borrowed,SameGameTransportContinuity.Evidence evidence)throws IOException {
                requireRecordedTransport(borrowed,evidence);
            }
        });transportJournal=journal;
    }
    private RecordedStage transportStage(ContinuityStorePort.Session same,SuccessorUiObligation state)throws IOException {
        var phase=state.phase()==Phase.FINALIZED?DriverPendingEpisodeSource.MutationPhase.FINALIZE:DriverPendingEpisodeSource.MutationPhase.REBIND;
        for(var item:retainedChain(same,canonicalBusinessKnown(same)).steps())if(item instanceof RetainedMutationStage edge
                &&edge.stage().metadata() instanceof DriverPendingEpisodeSource.MutationMetadata metadata&&metadata.phase()==phase){
            var after=SuccessorUiObligationCodec.decode(natural.readExact(metadata.afterObligation()));
            if(phase==DriverPendingEpisodeSource.MutationPhase.FINALIZE?after.equals(state):after.rebind().equals(state.rebind()))return edge.stage();
        }
        throw new IOException("actual canonical transport Rebind/finalized import missing");
    }
    private ExactRef archivedDriver(ContinuityStorePort.Session same,Known known)throws IOException {
        var material=RawJson.fullMaterial(known.driver().encode());var ref=archive(same).materialReferenceOf(material);
        require(archive(same).loadFullMaterial(ref).equals(material),"actual historical full Driver original is missing");return ref;
    }
    private record TransportMaterial(RootPendingNaturalSuccessionQualification.ReconnectedCause custody,
            RootLifecycleAuthority.SnapshotLease lease,WriterContracts.Head head,SameGameTransportContinuity.Evidence evidence) { }
    private <T>T withTransportCurrent(ContinuityStorePort.Session same,SessionPorts.SessionIdentity beforeOwner,
            SessionPorts.SessionIdentity afterOwner,ActionCommand exactParent,Instant deadline,SameGameTransportContinuity.Work<T> work)throws IOException {
        context.writer().requireSession(same);lifecycle.physical().requireOutsideObservationScope(same);
        require(transportJournal!=null&&afterOwner.equals(context.core().sessionAccess().current().identity())
                &&beforeOwner.machineId().equals(afterOwner.machineId())&&beforeOwner.game().equals(afterOwner.game()),
                "transport scope needs the identical installed Journal and original OS Game owners");
        var parent=find(same,exactParent.actionId());require(Arrays.equals(ActionCodec.encodeCommand(parent.command()),ActionCodec.encodeCommand(exactParent)),"transport scope changed the original complete parent command");
        var prepared=lifecycle.physical().withSnapshot(same,deadline,lease->continuity.withLease(same,lease,()->{
            var state=SuccessorUiObligationCodec.decode(DriverJson.encode(lease.factsKnown().auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY)));
            require(state.binding().parentActionId().equals(exactParent.actionId())&&state.binding().parentBodySha256().equals(ActionCodec.bodySha256(exactParent)),"transport custody is for another original pending parent");
            var custody=qualification.qualifyRetainedCauseReconnected(state.binding().qualifiedCause(),lease.fullSnapshot(),same,lease.sourceQualification(),same.head());
            require(continuity.preparedRebind(custody.continuityBinding()).isEmpty(),"actual NS Rebind must commit before an Auto owner transfer");
            var stage=transportStage(same,state);var metadata=(DriverPendingEpisodeSource.MutationMetadata)stage.metadata();
            if(state.phase()==Phase.FINALIZED)requireCanonicalFinalized(same,state);else requireCanonicalRebind(same,state);
            var semantic=lifecycle.physical().semantic(same,afterOwner,lease);
            var binding=PendingSameGameContinuity.decode(natural.readExact(custody.continuityBinding()));
            var purpose=state.phase()==Phase.FINALIZED?SameGameTransportContinuity.Purpose.FINALIZED_METADATA_ONLY:SameGameTransportContinuity.Purpose.PENDING_REBIND;
            var evidence=new SameGameTransportContinuity.Evidence(purpose,beforeOwner,afterOwner,parent,semantic,metadata.canonicalHeadSequence(),
                    metadata.eventIdentity(),metadata.canonicalHeadSha256(),stage.originalSource(),archivedDriver(same,stage.before()),archivedDriver(same,stage.after()),
                    metadata.beforeObligation(),metadata.afterObligation(),custody.continuityBinding(),binding.materialReferences());
            requireRecordedTransport(same,evidence);return continuity.seal(new TransportMaterial(custody,lease,same.head(),evidence));
        }));
        var material=prepared.value();
        return continuity.withPrepared(prepared,()->work.run(new SameGameTransportContinuity.Scope(){
            private boolean committed;
            @Override public SameGameTransportContinuity.Evidence evidence(){return material.evidence();}
            @Override public void requireCurrent(ContinuityStorePort.Session borrowed)throws IOException {
                require(!committed&&borrowed==same,"transport prepared scope escaped its actual writer or committed head");
                qualification.requireReconnectedCauseCurrent(material.custody(),material.lease().fullSnapshot(),same,material.lease().sourceQualification(),material.head());
                requireRecordedTransport(same,material.evidence());
            }
            @Override public void requireCommitted(ContinuityStorePort.Session borrowed,WriterContracts.Receipt receipt)throws IOException {
                require(!committed&&borrowed==same&&receipt.head().sequence()==Math.addExact(material.head().state().sequence(),1)
                        &&same.head().digest().equals(ContinuityJson.digest(receipt.head().toJson())),"transport postcheck requires this scope's single actual canonical child");
                var pin=publicationEvent(same,receipt);var event=StrictJson.parse(natural.readExact(pin));var details=event.get("details");
                require(StrictJson.text(event.get("kind")).equals(WriterContracts.ORDINARY_CYCLE_KIND)
                        &&StrictJson.text(details.get("operation")).equals("TRANSPORT_REBIND")
                        &&StrictJson.text(details.get("predecessor_head_digest")).equals(material.head().digest())
                        &&details.get("transport_evidence").equals(material.evidence().toJson(archive(same))),"transport commit did not consume its exact actual private prepared source");
                var source=material.lease().sourceQualification();source.assertCurrent(same);
                context.game().verify();context.transport().verifyHeld(material.lease().validUntil());
                require(context.clock().instant().isBefore(material.lease().validUntil()),"transport commit physical observation expired");
                var actual=context.transport().latestObservedSnapshot().orElseThrow(()->new IOException("transport postcheck actual Managed packet missing"));
                require(actual.session().equals(material.lease().fullSnapshot().actual().session())&&Arrays.equals(actual.originalPacket(),material.lease().fullSnapshot().actual().originalPacket()),"transport commit changed its actual physical packet");
                assembler().withFrozenFacts(same,frozen->{require(frozen.state() instanceof Known,"transport postcheck canonical Known missing");require(Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(material.lease().factsKnown()).bytes(),DriverSnapshotFacts.encodeKnownOriginal((Known)frozen.state()).bytes()),"transport child changed any of the seven canonical Known fields");return null;});
                requireRecordedTransport(same,material.evidence());committed=true;
            }
        }));
    }
    /** Canonical history only. No Binding DATA, reader or public cold result can acquire a current scope here. */
    private void requireRecordedTransport(ContinuityStorePort.Session same,SameGameTransportContinuity.Evidence evidence)throws IOException {
        context.writer().requireSession(same);var parsed=DriverPendingEpisodeSource.decodeRecoveryMetadata(new RawJson(natural.readExact(evidence.canonicalMetadata())));
        require(parsed instanceof DriverPendingEpisodeSource.MutationMetadata,"transport history requires its actual mutation metadata");var metadata=(DriverPendingEpisodeSource.MutationMetadata)parsed;
        require(metadata.machineId().equals(context.game().machineId())
                &&metadata.canonicalHeadSequence()==evidence.canonicalSequence()&&metadata.canonicalHeadSha256().equals(evidence.canonicalHeadDigest())
                &&metadata.eventIdentity().equals(evidence.canonicalEventIdentity())&&metadata.beforeObligation().equals(evidence.beforeObligation())
                &&metadata.afterObligation().equals(evidence.afterObligation()),"transport history changed its actual NS canonical import tuple");
        var imported=same.requireHistoricalImport(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,metadata.canonicalHeadSequence(),metadata.canonicalHeadSha256());
        var document=NaturalClockOriginals.decode(natural.readExact(metadata.canonicalDomain()));
        var artifact=document.pendingProjection().orElseThrow().latestMutation().orElseThrow();
        require(imported.request().contractSchema().equals(DriverPendingEpisodeSource.DOMAIN_SCHEMA)&&imported.receipt().eventIdentity().equals(metadata.eventIdentity())&&imported.body().payload().equals(metadata.canonicalDomain())
                &&Arrays.equals(imported.request().producerInput(),NaturalClockOriginals.encode(document))&&imported.request().evidence().equals(natural.computedArtifacts(document))
                &&artifact.beforeDriver().equals(evidence.beforeDriver())&&artifact.afterDriver().equals(evidence.afterDriver())
                &&artifact.beforeObligation().equals(evidence.beforeObligation())&&artifact.afterObligation().equals(evidence.afterObligation()),"transport history lost its actual complete canonical source closure");
        var before=SuccessorUiObligationCodec.decode(natural.readExact(metadata.beforeObligation()));var after=SuccessorUiObligationCodec.decode(natural.readExact(metadata.afterObligation()));
        require(before.binding().equals(after.binding())&&after.binding().parentActionId().equals(evidence.canonicalParent().command().actionId())
                &&after.binding().parentBodySha256().equals(ActionCodec.bodySha256(evidence.canonicalParent().command())),"transport history changed its original parent/cause binding");
        if(evidence.purpose()==SameGameTransportContinuity.Purpose.PENDING_REBIND)
            require(metadata.phase()==DriverPendingEpisodeSource.MutationPhase.REBIND&&SuccessorUiObligationReducer.rebind(before,after.rebind().orElseThrow()).equals(after),"transport history failed the actual sole Rebind reducer");
        else require(metadata.phase()==DriverPendingEpisodeSource.MutationPhase.FINALIZE&&SuccessorUiObligationReducer.finalizeVerified(before,after.finalization().orElseThrow()).equals(after),"transport history failed the actual sole finalized reducer");
        var oldKnown=retainedKnown(metadata);require(Arrays.equals(natural.readExact(evidence.beforeDriver()),oldKnown.driver().encode()),"transport original before Driver changed");
        // The original domain import pins the exact after wire. Reopening that wire does not project a live Driver.
        org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.decodeComplete(natural.readExact(evidence.afterDriver()));
        var binding=PendingSameGameContinuity.decode(natural.readExact(evidence.privateProof()));
        require(binding.materialReferences().equals(evidence.privateMaterials())&&binding.retainedCauseProof().equals(after.binding().qualifiedCause())
                &&binding.currentSessionId().equals(evidence.afterOwner().sessionId())&&binding.machineId().equals(evidence.afterOwner().machineId())
                &&binding.gamePid()==evidence.afterOwner().game().pid()&&binding.gameCreationFiletimeDecimal().equals(evidence.afterOwner().game().creationFiletime().value().toString())
                &&binding.currentNative().equals(evidence.semantic().originalNativePacket()),"transport history changed its exact private binding material closure/actual current owner");

        var historical=same.requireHistoricalState(binding.writerHeadSequence(),binding.writerHeadSha256());
        require(ContinuityActionJournal.lookup(historical,evidence.canonicalParent().command().actionId(),archive(same)).filter(evidence.canonicalParent()::equals).isPresent(),"transport origin did not retain its actual canonical parent receipt");
        context.semanticVerifier().verify(same,evidence.afterOwner(),evidence.semantic());
        var captured=retainedKnown(binding.currentKnown(),binding.currentNative());
        require(Arrays.equals(natural.readExact(evidence.semantic().originalDriver()),captured.driver().encode())
                &&captured.observation().orElseThrow().semanticFactsEvidence().equals(binding.currentObservation())&&captured.stamp().driverVersion()==binding.driverVersion()
                &&captured.stamp().episodeEpoch()==binding.episodeEpoch()&&binding.successorCharacterId()==evidence.semantic().frame().frame().identity().player().intValueExact()
                &&binding.successorEpisodeRunId().equals(evidence.semantic().frame().frame().episodeRunId()),"transport current SEM lost its complete original Known/observation");
        var stamp=DriverJson.object(natural.readExact(evidence.semantic().driverStamp()),RawJson.MAXIMUM_BYTES);
        require(binding.currentConnectionGenerationDecimal().equals(OpportunityJson.integer(stamp.get("connection_generation"),"actual semantic transport").toString()),"transport binding changed its original semantic connection");
        var manifest=RawJson.fullMaterial(natural.readExact(binding.currentObservation()));
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(binding.currentObservation(),manifest,natural.readExact(binding.currentNative()));
        var projected=new DriverObservationAssembler().projectFull(nativeFrame,captured.observation().orElseThrow(),binding.currentNative());
        require(Arrays.equals(DriverJson.encode(projected.semantic()),natural.readExact(evidence.semantic().semantic())),"transport original current full projection differs from its actual SEM");
        for(var ref:evidence.privateMaterials())natural.readExact(ref);
        natural.readExact(evidence.semantic().originalDriver());natural.readExact(evidence.afterDriver());
    }
    /** Bootstrap runs this before starting the Controller; an active turn may only consume the returned private ticket. */
    public Optional<ContinuityBatchJournal.ReboundTransport> rebindPendingTransport(ContinuityStorePort.Session same,SessionPorts.SessionIdentity owner,Instant deadline)throws IOException,InterruptedException {
        require(owner.equals(new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId())),"pending transport bootstrap crossed its actual owner");
        if(retireRestoredFinalized(same,deadline))return Optional.empty();
        installTransportContinuity(same);if(completedByCanonicalLifecycle)return Optional.empty();
        var retained=assembler().withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof Known known))return Optional.<SuccessorUiObligation>empty();
            var value=known.auxiliary().members().get(SuccessorUiObligation.AUXILIARY_KEY);
            return value==null?Optional.<SuccessorUiObligation>empty():Optional.of(SuccessorUiObligationCodec.decode(DriverJson.encode(value)));
        });
        if(retained.isEmpty())return Optional.empty();var state=retained.orElseThrow();var original=state.binding().predecessor();
        var packet=context.transport().latestObservedSnapshot();
        if(packet.isEmpty())return Optional.empty();var physical=packet.orElseThrow().session();
        if(physical.sessionId().equals(original.sessionId())&&physical.connectionGeneration().equals(original.connectionGeneration()))return Optional.empty();
        var parent=find(same,state.binding().parentActionId());
        if(state.phase()==Phase.FINALIZED&&hasControllerAdoption(same,owner,parent)){completedByCanonicalLifecycle=true;return Optional.empty();}
        if(transported!=null&&transported.owner().equals(owner)&&physical.sessionId().equals(owner.sessionId())&&physical.connectionGeneration().equals(bootstrappedConnection)
                &&Arrays.equals(ActionCodec.encodeCommand(transported.parent()),ActionCodec.encodeCommand(parent.command()))){
            transportJournal.requireHistoricalTransport(same,transported);return Optional.empty();
        }
        if(state.phase()!=Phase.FINALIZED){var pending=current(same,deadline);if(pending.isEmpty())return Optional.empty();
            if(pending.orElseThrow().state.rebind().isEmpty())return Optional.empty();}
        var ticket=transportJournal.rebindTransport(same,owner,parent.command(),deadline);transported=ticket;bootstrappedConnection=physical.connectionGeneration();
        context.core().sessionAccess().current().controllerForPublication().adoptTransportRebound(same,ticket);return Optional.of(ticket);
    }
    public Optional<SessionPorts.PendingSuccessorUi> pendingTransportedSuccessorUi(ContinuityStorePort.Session same,SessionPorts.SessionIdentity owner,
            ContinuityBatchJournal.ReboundTransport ticket,Instant deadline)throws IOException {
        require(transportJournal!=null&&ticket.owner().equals(owner),"pending transport needs the identical installed actual Journal/owner");transportJournal.requireHistoricalTransport(same,ticket);
        require(Arrays.equals(ActionCodec.encodeCommand(find(same,ticket.parent().actionId()).command()),ActionCodec.encodeCommand(ticket.parent())),"transport pending parent changed");
        transported=ticket;return pendingSuccessorUi(same,owner,deadline);
    }
    boolean ownsInitialCause(RootNaturalSuccessionOriginals.InitialCause identical){return initial!=null&&initial==identical;}
    private ActionPorts.OutcomeArchive archive(ContinuityStorePort.Session same)throws IOException{context.writer().requireSession(same);return context.archive().withSession(same);}
    private ExactRef retain(ContinuityStorePort.Session same,byte[] body)throws IOException{return archive(same).preserveMaterial(new RawJson(body));}
    public ReadContract<NativeTimelineBlocker12004.Query> timelineContract(){return query;}
    public static void requireCloseReconciliationProfile(ReadContract<?> actual){RootPendingUiCloseReconciliation.requireProfile(actual);}
    public static void requireCloseReconciliationRequest(PlanningReadRequest request,ActionReceipt original,ActionState.Attempt attempt,DriverObservationAssembler.Complete before,DriverObservationAssembler.Complete actual,ActionPorts.OutcomeArchive originals)throws IOException {RootPendingUiCloseReconciliation.requireRequest(request,original,attempt,before,actual,originals);}
    /** Pure historical derivation. Unrelated original actions cause no private-current or Native access. */
    public RootReconciliationAuthority.QueryPolicy reconciliationReads(){return (original,identity,actual,deadline)->{
        if(!(original.command().origin() instanceof CommandOrigin.Gameplay)||!original.command().operation().equals(CLOSE)||!original.command().expected().observerSchema().equals(CLOSE_OBSERVER))return List.of();
        var same=context.borrowedSession();var attempt=ActionTransitions.attempt(original.state()).orElseThrow(()->new IOException("actual original Close attempt absent"));var originals=archive(same);
        var before=RootGuardEvidence.loadFrame(attempt.guard(),originals,context.frameLoader());
        var request=new PlanningReadRequest(new CommandOrigin.Reconciliation(identity),actual.source(),actual.sessionId(),QUERY,EMPTY,deadline);
        requireCloseReconciliationRequest(request,original,attempt,before,actual,originals);
        return List.of(new RootReconciliationAuthority.AllowedRead(reconciliationQuery,EMPTY,RootReconciliationAuthority.QueryKind.PENDING_SUCCESSOR_CLOSE_TIMELINE));
    };}
    void requireInitialParent(ContinuityStorePort.Session same,ActionCommand parent,LifecycleObservationPort.Snapshot actual)throws IOException {
        requireDriverContext();context.writer().requireSession(same);
        if(restoredFinalized!=null){
            requireRestoredFinalizedCurrent(same,restoredFinalized);var prior=restoredFinalized.state().binding();
            require(!parent.actionId().equals(prior.parentActionId())
                    &&parent.lifecycleBefore().subject().characterId().equals(prior.successorCharacterId())
                    &&parent.lifecycleBefore().subject().episodeRunId().equals(prior.successorEpisodeRunId())
                    &&actual.facts().driver().session().actorId().equals(prior.successorCharacterId())
                    &&actual.facts().driver().session().episodeRunId().equals(prior.successorEpisodeRunId()),
                    "next terminal cause must descend from the actual restored completed successor");
        }
        if(initial==null&&admittedRecovery!=null&&completedByCanonicalLifecycle){
            var retained=admittedRecovery;var prior=find(same,retained.actual.parent().command().actionId());
            require(hasControllerAdoption(same,retained.actual.owner(),prior)&&!parent.actionId().equals(prior.command().actionId())
                    &&parent.lifecycleBefore().subject().episodeRunId().equals(retained.actual.driver().session().episodeRunId())
                    &&parent.lifecycleBefore().subject().characterId().equals(retained.actual.driver().session().actorId())
                    &&actual.facts().driver().session().episodeRunId().equals(retained.actual.driver().session().episodeRunId()),
                    "new terminal cause did not descend from the actually adopted same-Game episode");
            admittedRecovery=null;obligation=null;completedByCanonicalLifecycle=false;
        }
        if(initial!=null&&completedByCanonicalLifecycle){
            var previous=find(same,initial.originalParent().actionId());require(previous.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied applied&&applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR,"prior pending transition lacks true canonical lifecycle completion");
            var proof=((ActionState.LifecycleApplied)((ActionState.CompositeSettled)previous.state()).settlement()).proof();proof.validateParent(initial.originalParent());
            var finalProof=committedRecovery!=null?committedRecovery.scope.proofReference:completed==null?null:completed.m3FinalizationProof();
            require(finalProof!=null&&proof.originalEvidence().contains(finalProof)&&!parent.actionId().equals(initial.originalParent().actionId())&&actual.facts().driver().session().episodeRunId().equals(obligation.binding().successorEpisodeRunId()),"new pending transition did not descend from the actual committed successor episode");
            natural.releaseCompletedPending(initial,parent);initial=null;publication=null;obligation=null;mutation=null;completed=null;retainedFinalScope=null;committedRecovery=null;admittedRecovery=null;qualifiedAfterChild=null;completedChild=null;actualDateIntent=null;actualDateCommand=null;actualDateReceipt=null;actualDateSource=null;issued.clear();incorporatedChildren.clear();eventEntries.clear();latestEvent=null;lateCloseAcks.clear();closePostQueries.clear();modalQueryOriginals.clear();completedByCanonicalLifecycle=false;
        }
        require(initial==null&&publication==null,"pending transition already has retained original custody");
        require(parent.origin() instanceof CommandOrigin.LifecycleTerminal&&parent.operation().value().equals("continue-as-reconciled-successor")
                &&parent.lifecycleBefore().game().equals(actual.actual().session().game())&&parent.lifecycleBefore().frame().snapshotId().equals(actual.actual().snapshotId())&&parent.lifecycleBefore().frame().nativeRevision().equals(actual.actual().nativeRevision())&&parent.lifecycleBefore().subject().driverVersion()==actual.facts().stamp().driverVersion()&&parent.source().equals(actual.source()),"only the genuine original terminal Continue may publish pending succession");
        var receipt=find(same,parent.actionId());require(receipt.command().equals(parent)&&ActionTransitions.composite(receipt.state()).isPresent(),"actual registered original composite parent is absent");
    }
    private ActionReceipt find(ContinuityStorePort.Session same,String id)throws IOException {
        return context.core().actions().withFrozen(same,held->held.find(id)).orElseThrow(()->new IOException("canonical action original absent"));
    }
    private ActionReceipt submitRetainingCanonicalResult(CompositeActionPort.Children children,ActionCommand child)throws IOException {
        try{return children.submit(child);}
        catch(RuntimeException stopped){
            var same=context.borrowedSession();var issuedOriginal=issued.get(child.actionId());require(issuedOriginal!=null&&issuedOriginal.child().equals(child),"failed child lost the actual private once issuance");
            var parent=find(same,initial.originalParent().actionId());var execution=ActionTransitions.composite(parent.state()).orElseThrow(()->new IOException("failed submission lost its original retained parent",stopped));
            require(execution.children().contains(new CompositeExecution.Child(child.actionId(),ActionCodec.bodySha256(child))),"failed child has no actual same-parent canonical reservation; no replacement receipt is invented");
            var actual=find(same,child.actionId());require(actual.command().equals(child)&&actual.bodySha256().equals(ActionCodec.bodySha256(child)),"failed submission canonical child differs from its exact once body");archive(same).preserveReceipt(actual);return actual;
        }
    }
    public Preparation prepareOutcome(ActionCommand parent,LifecycleObservationPort.Snapshot actual,CompositeActionPort.Children children)throws IOException,InterruptedException {
        var same=context.borrowedSession();requireInitialParent(same,parent,actual);
        String newRun="native-"+((LifecycleIdentity.Character)parent.lifecycleBefore().currentPlayer()).characterId()+"-"+UUID.randomUUID().toString().replace("-","").substring(0,12);
        initial=natural.preparePendingEpisode(parent,actual,newRun);publication=assembler().publishPendingEpisode(same);obligation=initial.pendingEpisode().obligation();restoredFinalized=null;
        var current=current(same,parent.deadline()).orElseThrow();return resumeOutcome(parent,current,children);
    }
    /** Only this installed issuer can mint a current token; its public getters expose DATA. */
    public class Current implements PendingToken {
        private final DriverStateAssembler.PendingEpisodePublication retained;private final SuccessorUiObligation state;private final Instant limit;
        private Current(DriverStateAssembler.PendingEpisodePublication retained,SuccessorUiObligation state,Instant limit){this.retained=retained;this.state=state;this.limit=limit;}
        @Override public ActionCommand originalParent(){return initial.originalParent();}
        @Override public SuccessorUiObligation obligation(){return state;}
        @Override public ExactRef canonicalDomain(){return retained.canonicalDomainRef();}
        @Override public ExactRef actualPublishedDriver(){return currentDriverRef(retained);}
        @Override public ExactRef canonicalPublicationProof(){return retained.originalSource();}
        public Known actualKnown(){return qualifiedAfterChild==null?retained.after():qualifiedAfterChild.actualKnown();}
        public ExactRef originalDriver(){return actualPublishedDriver();}
        public ExactRef originalHistoryBasis(){return actualKnown().originalHistoryBasis();}
        public ExactRef originalPendingPublication(){return canonicalPublicationProof();}
        public ExactRef actualCloseReceipt(){return state.closeAttempt().orElseThrow().receipt().orElseThrow().effectiveReceipt();}
        public ExactRef materialClearance(){return state.closeAttempt().orElseThrow().receipt().orElseThrow().effectiveMaterialClearance().orElseThrow();}

        @Override public List<ExactRef> evidence(){return List.of(canonicalDomain(),actualPublishedDriver(),canonicalPublicationProof(),state.binding().qualifiedCause());}
        @Override public Instant deadline(){return limit;}
        @Override public CompositeContinuationToken.Kind kind(){return CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE;}
        public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            requireDriverContext();context.writer().requireSession(same);
            require(publication==retained&&obligation==state&&initial!=null&&state.binding().causeDigest().equals(initial.cause().causeDigest())
                    &&state.binding().parentActionId().equals(originalParent().actionId())&&state.binding().parentBodySha256().equals(ActionCodec.bodySha256(originalParent())),"pending token changed its actual private issuer/cause/publication");
            require(!context.clock().instant().isAfter(limit),"pending physical read window expired");
            if(executing.get()==this&&ActionCommandScope.current().filter(value->value.origin() instanceof CommandOrigin.Gameplay).isPresent())qualifiedAfterChild=assembler().currentPendingEpisodeChildScope(same,retained);
            else if(qualifiedAfterChild!=null)qualifiedAfterChild.requireCurrent(same);
            else retained.requireCurrent(same);
            var document=NaturalClockOriginals.decode(natural.readExact(canonicalDomain()));require(document.pendingProjection().isPresent(),"canonical pending projection absent");
            require(Arrays.equals(natural.readExact(document.pendingProjection().orElseThrow().currentObligation()),SuccessorUiObligationCodec.encode(state)),"canonical obligation differs from private publication");
        }
        public void requireMayExecute(ContinuityStorePort.Session same,ActionCommand child)throws IOException {requireCurrent(same);requireChild(same,assembler(),retained,originalParent(),child);}
    }
    private ExactRef currentDriverRef(DriverStateAssembler.PendingEpisodePublication value){
        if(qualifiedAfterChild!=null)return qualifiedAfterChild.actualDriverOriginal();
        if(value==recoveredPublication){require(recoveredDriver!=null,"genuine recovered Driver original is missing");return recoveredDriver;}
        if(value instanceof DriverStateAssembler.PublishedPending first)return first.projection().afterDriver();
        require(mutation!=null&&value.canonicalDomainRef().equals(mutation.canonicalDomainRef()),"actual current mutation Driver original absent");return mutation.preparedProjection().afterDriver();
    }
    /** Distinct private date token. A Close token never acquires clock permission by a caller flag. */
    private final class DateCurrent extends Current {
        private final NaturalClockOriginals.DateIntent intent;private final PendingDateSource source;
        private DateCurrent(Current current,PendingDateSource source){super(current.retained,current.state,current.limit);this.intent=actualDateIntent;this.source=source;require((intent==null)==(actualDateCommand==null)&&current.state.closeAttempt().flatMap(CloseAttempt::receipt).flatMap(CloseReceipt::effectiveMaterialClearance).isPresent(),"private date stage lacks its actual cleared Close or consistent intent");}
        @Override public CompositeContinuationToken.Kind kind(){return CompositeContinuationToken.Kind.SUCCESSOR_UI_DATE_ADVANCE;}
        @Override public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            super.requireCurrent(same);require(intent==actualDateIntent&&source.runtime()==RootPendingUiRuntime.this,"date token lost private source/once intent");
            var doc=NaturalClockOriginals.decode(natural.readExact(canonicalDomain()));require(doc.pendingProjection().orElseThrow().dateIntent().equals(Optional.ofNullable(intent)),"canonical once-date original changed");
        }
    }
    private record LiveEventOrigin(Current before,Known beforeKnown) { }
    private final class EventEntry {
        final Optional<LiveEventOrigin> liveOrigin;final EventActionPreparation.PendingPrepared prepared;NaturalClockOriginals.EventIntent intent;PendingEventSource source;MutationCapture entered;
        EventEntry(Current before,Known beforeKnown,EventActionPreparation.PendingPrepared prepared,NaturalClockOriginals.EventIntent intent){this.liveOrigin=Optional.of(new LiveEventOrigin(before,beforeKnown));this.prepared=prepared;this.intent=intent;}
        /** Archived DATA retains an existing canonical action; it never supplies a fresh-preparation origin. */
        EventEntry(EventActionPreparation.PendingPrepared prepared,NaturalClockOriginals.EventIntent intent){this.liveOrigin=Optional.empty();this.prepared=prepared;this.intent=intent;}
    }
    private final class EventCurrent extends Current {
        private final EventEntry entry;
        private EventCurrent(Current actual,EventEntry entry){super(actual.retained,actual.state,actual.limit);this.entry=entry;}
        @Override public CompositeContinuationToken.Kind kind(){return CompositeContinuationToken.Kind.SUCCESSOR_UI_EVENT;}
        @Override public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            super.requireCurrent(same);require(latestEvent==entry&&eventEntries.get(entry.prepared.command().actionId())==entry,"event token lost its real private Root issuance");
            var doc=NaturalClockOriginals.decode(natural.readExact(canonicalDomain()));require(doc.pendingProjection().orElseThrow().eventIntent().orElseThrow().equals(entry.intent),"canonical once-event intent changed");
        }
    }
    private EventRuntimeInstaller events()throws IOException {var domains=context.remainingDomains();domains.requireContext(context);return domains.events();}
    private final class PendingEventSource implements PendingUiEvent.Source {
        private final Current original;private PendingUiEvent.Current lastData;private MutationFrame lastPhysical;private ActionCommand checkedFresh;
        private PendingEventSource(Current original){this.original=original;}
        private Current active(){var current=executing.get();return current instanceof EventCurrent event&&event.entry.source==this?current:original;}
        @Override public void requireCurrent(ContinuityStorePort.Session same)throws IOException {active().requireCurrent(same);}
        @Override public <T>T withCurrent(ContinuityStorePort.Session same,Instant deadline,PendingUiEvent.Work<T> work)throws IOException {
            var current=active();current.requireCurrent(same);require(!deadline.isAfter(current.deadline()),"event callback exceeded its actual private caller window");
            var prior=eventScope.get();require(prior==null||prior==this,"private event source crossed another issuer");eventScope.set(this);
            try {
                PhysicalWork<T> capture=lease->{var complete=lease.ordinary().orElseThrow();var data=new PendingUiEvent.Current(current.originalParent(),lease.fullSnapshot(),lease.factsKnown(),complete,current.actualPublishedDriver(),current.originalHistoryBasis(),current.canonicalPublicationProof(),current.canonicalDomain(),current.state.binding().qualifiedCause(),lease.bridgeCapabilities());lastData=data;lastPhysical=mutationFrame(lease);return work.run(data);};
                var held=physicalScope.get();if(held!=null){require(held.current()==current,"event callback borrowed another actual physical snapshot");return capture.run(held.lease());}
                return withPhysical(current,capture);
            }finally{if(prior==null)eventScope.remove();else eventScope.set(prior);}
        }
        @Override public <T>PlanningReadResult.Known<T> read(ContinuityStorePort.Session same,ReadContract<T> installed,PlanningReadRequest exact)throws IOException {
            requireCurrent(same);var held=physicalScope.get();require(eventScope.get()==this&&held!=null&&events().pendingUiReadContracts().stream().anyMatch(value->value==installed),"event read lacks the actual private callback or exact installed window/notification contract");
            var complete=held.lease().ordinary().orElseThrow();require(exact.origin() instanceof CommandOrigin.Gameplay&&exact.before().equals(complete.identity())&&exact.source().equals(complete.source())&&exact.sessionId().equals(complete.sessionId()),"event read changed its actual source/current full frame");
            return natural.read(same,installed,exact);
        }
        @Override public void requireOriginalPreparation(ContinuityStorePort.Session same,ActionCommand originalCommand,ActionCommand actualFresh)throws IOException {
            var current=active();current.requireCurrent(same);var entry=latestEvent;
            require(entry!=null&&entry.source==this&&entry.prepared.command()==originalCommand&&checkedFresh==actualFresh&&entry.intent.command().sha256().equals(ActionCodec.bodySha256(originalCommand))&&Arrays.equals(natural.readExact(entry.intent.command()),ActionCodec.encodeCommand(originalCommand)),"event DATA lacks the actual old preparation/new private source/once-command custody");
            var origin=entry.liveOrigin.orElseThrow(()->new IOException("an archived event action cannot authorize a new preparation or submission"));
            var captured=entry.entered;require(captured!=null,"event intent has no actual same Root committed mutation");
            same.requireCommitted(captured.originalPrepared(),captured.actualReceipt());
            require(captured.authority.predecessor()==origin.before()&&captured.actualKnown().stamp().equals(origin.beforeKnown().stamp())&&Arrays.equals(captured.actualKnown().driver().encode(),origin.beforeKnown().driver().encode())&&Arrays.equals(publication.after().driver().encode(),origin.beforeKnown().driver().encode()),"event original/post-intent actual Driver lineage changed");
            require(lastData!=null&&lastData.canonicalDomain().equals(publication.canonicalDomainRef())&&lastData.qualifiedCause().equals(origin.before().state.binding().qualifiedCause())&&actualFresh.before().equals(lastData.frame().identity())&&actualFresh.source().equals(context.source()),"fresh event preparation did not come from this actual private current native source");
        }
    }
    /** Actual source DATA is scoped to a real private physical lease; it never creates ordinary Ready. */
    private final class PendingDateSource implements PendingUiLifeAdvance.Source {
        private final Current original;
        private PendingDateSource(Current original){this.original=original;}
        private RootPendingUiRuntime runtime(){return RootPendingUiRuntime.this;}
        @Override public ActionCommand originalParent(){return original.originalParent();}
        @Override public void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            var active=executing.get();var held=active instanceof DateCurrent date&&date.source==this?active:original;
            held.requireCurrent(same);var close=held.state.closeAttempt().orElseThrow().receipt().orElseThrow();
            require(close.effectiveMaterialClearance().isPresent()&&close.effectiveReceipt().equals(held.actualCloseReceipt()),"date source has no independently cleared actual Close");
            var receipt=archive(same).loadReceipt(close.effectiveReceipt());verifyCloseControl(receipt,archive(same));
            require(receipt.equals(find(same,receipt.command().actionId())),"date source lost sole canonical Close original");
        }
        @Override public <T>T withCurrent(ContinuityStorePort.Session same,Instant deadline,PendingUiLifeAdvance.Work<T> work)throws IOException {
            requireCurrent(same);var active=executing.get();var held=active instanceof DateCurrent date&&date.source==this?active:original;
            require(!deadline.isAfter(held.deadline()),"date observation exceeded its real private caller window");
            var prior=dateScope.get();require(prior==null||prior==this,"date source crossed its private physical custody");dateScope.set(this);
            try {
                var scope=physicalScope.get();
                if(scope!=null){require(scope.current()==held,"date callback borrowed another private physical lease");return work.run(data(held,scope.lease()));}
                return withPhysical(held,false,lease->work.run(data(held,lease)));
            }finally{if(prior==null)dateScope.remove();else dateScope.set(prior);}
        }
        @Override public <T>T withNext(ContinuityStorePort.Session same,org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity after,Instant deadline,PendingUiLifeAdvance.Work<T> work)throws IOException {
            require(executing.get() instanceof DateCurrent date&&date.source==this,"next-date observation lacks actual same-parent finite continuation");
            return withCurrent(same,deadline,actual->{var now=actual.originalFrame().identity();require(now.game().equals(after.game())&&now.frame().episodeRunId().equals(after.frame().episodeRunId())&&now.frame().identity().player().equals(after.frame().identity().player())&&now.frame().identity().nativeRevision().compareTo(after.frame().identity().nativeRevision())>=0&&!now.frame().snapshotId().equals(after.frame().snapshotId()),"next-date capture did not obtain a fresh actual same-episode native frame");return work.run(actual);});
        }
        private PendingUiLifeAdvance.Current data(Current held,RootLifecycleAuthority.SnapshotLease lease)throws IOException {
            lease.assertCurrent(context.borrowedSession());var complete=lease.ordinary().orElseThrow();
            var identity=complete.identity();var frame=new AdvanceObservationPort.Frame(identity,complete.source(),complete.sessionId(),complete.semantic(),new ObservationProvenance.Push(identity.frame().snapshotId(),identity.frame().identity().nativeRevision(),complete.originalEvidence()),complete.observedAt(),complete.originalEvidence());
            var steps=new HashSet<OperationKey>();var origin=new CommandOrigin.Gameplay(identity);
            for(var installed:context.bindings().installed())if(installed.kind()!=ExecutableStepBindings.Kind.READ&&context.bindings().resolve(installed.operation(),origin).isPresent()&&installed.requiredCapability().map(lease.bridgeCapabilities()::contains).orElse(true))steps.add(installed.operation());
            for(String name:List.of("life-advance","life-advance-one-day"))context.bindings().resolve(new OperationKey(name),origin).ifPresent(value->steps.add(value.operation()));
            var original=held.actualCloseReceipt();var close=archive(context.borrowedSession()).loadReceipt(original);verifyCloseControl(close,archive(context.borrowedSession()));
            return new PendingUiLifeAdvance.Current(frame,lease.factsKnown(),held.actualPublishedDriver(),held.originalHistoryBasis(),held.canonicalPublicationProof(),original,held.materialClearance(),close,Set.copyOf(steps),lease.bridgeCapabilities());
        }
        @Override public NativeRequest preparePreclock(ContinuityStorePort.Session same,ActionCommand clock,String requestId,NativeRequest base)throws IOException {
            require(executing.get() instanceof DateCurrent date&&date.source==this&&clock.operation().value().equals("resume-map"),"date preclock lacks its actual private continuation/clock");
            return withCurrent(same,clock.deadline(),actual->{var scope=physicalScope.get();require(scope!=null,"date preclock lost its actual physical lease");return natural.preparePendingDateClock(same,actualDateCommand,clock,requestId,base,scope.lease(),publication.canonicalDomainRef());});
        }
    }
    public Optional<Current> current(ContinuityStorePort.Session same,Instant deadline)throws IOException {
        requireDriverContext();context.writer().requireSession(same);if(retireRestoredFinalized(same,deadline)||completedByCanonicalLifecycle)return Optional.empty();
        if(admittedRecovery!=null){var expected=new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId());
            if(hasControllerAdoption(same,expected,find(same,admittedRecovery.actual.parent().command().actionId()))){completedByCanonicalLifecycle=true;return Optional.empty();}
            refreshAdmittedRecovery(same,deadline);return Optional.empty();}
        if(committedRecovery!=null)return Optional.empty();
        if(publication==null){if(tryAdmittedRecovery(same,deadline))return Optional.empty();recoverPending(same,deadline);if(publication==null)return Optional.empty();}
        if(completed!=null) {
            var known=assembler().withFrozenFacts(same,frozen->{require(frozen.state() instanceof Known,"actual finalized Driver missing");return (Known)frozen.state();});
            if(known.stamp().driverVersion()==Math.addExact(completed.publishedFinal().stamp().driverVersion(),1)) {
                var edge=lifecycle.composite().recordedPendingEpisode(same,find(same,initial.originalParent().actionId()));edge.requirePublishedCurrent(same);
                require(edge.proof().originalEvidence().contains(completed.m3FinalizationProof())&&edge.proof().originalEvidence().contains(completed.canonicalFinalizationDomain())
                        &&Arrays.equals(known.driver().encode(),completed.publishedFinal().driver().encode()),"actual final metadata changed the genuine business publication/cause");
                initial=null;publication=null;obligation=null;completed=null;retainedFinalScope=null;qualifiedAfterChild=null;completedChild=null;mutation=null;recoveredPublication=null;recoveredDriver=null;
                recoverPending(same,deadline);require(committedRecovery!=null,"actual metadata completion has no private retained episode issuer");return Optional.empty();
            }
        }
        require(deadline.isAfter(context.clock().instant()),"fresh finite caller window required");
        if(completed instanceof RetainedFinalTokenImpl retained&&(retained.scope.same!=same||!retained.scope.head.digest().equals(same.head().digest())||retained.current.deadline().isBefore(deadline))) {
            var actual=new Current(publication,obligation,deadline);var stage=retained.scope.stage;
            withPhysical(actual,lease->{require(finalRecoveryInputs.get()==null,"nested retained-final refresh forbidden");finalRecoveryInputs.set(new FinalRecoveryInputs(same,same.head(),lease,initial,Optional.empty()));
                try{retainedFinalChange(stage,obligation);retainedFinalScope.replayed=retained.scope.replayed;completed=new RetainedFinalTokenImpl(actual,retainedFinalScope);return null;}
                finally{finalRecoveryInputs.remove();}});
        }
        if(completedChild==null) {
            for(var item:issued.values()) {
                var child=item.child();if(incorporatedChildren.contains(child.actionId()))continue;
                var actual=find(same,child.actionId());
                boolean modal=actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied&&child.operation().equals(CLOSE);
                if(modal)verifyCloseControl(actual,archive(same));
                if(modal||actual.settled()&&actual.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED){require(completedChild==null,"more than one unincorporated pending child settlement");completedChild=child;}
            }
        }
        if(completedChild!=null)qualifiedAfterChild=assembler().requirePendingEpisodeChildCurrent(same,publication,initial.originalParent(),completedChild);
        Current actual=ensureTransportRebound(new Current(publication,obligation,deadline));
        if(latestEvent!=null&&latestEvent.intent.originalReceipt().isEmpty())actual=new EventCurrent(actual,latestEvent);
        else if(obligation.closeAttempt().flatMap(CloseAttempt::receipt).flatMap(CloseReceipt::effectiveMaterialClearance).isPresent()
                &&obligation.closeAttempt().flatMap(CloseAttempt::receipt).flatMap(CloseReceipt::effectiveDateAdvance).isEmpty()
                &&(actualDateReceipt==null||settledZeroDate())){if(actualDateIntent==null||actualDateReceipt!=null)actualDateSource=new PendingDateSource(actual);require(actualDateSource!=null,"canonical date lacks its actual private source");actual=new DateCurrent(actual,actualDateSource);}
        actual.requireCurrent(same);return Optional.of(actual);
    }
    private record RebindMaterial(RootPendingNaturalSuccessionQualification.ReconnectedCause custody,
            SuccessorUiObligation.Rebind change,MutationFrame physical,DriverObservationAssembler.FullSnapshot full,
            org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source,WriterContracts.Head head) { }
    private Current ensureTransportRebound(Current before)throws IOException {
        if(before.state.phase()==Phase.FINALIZED)return before;
        var same=context.borrowedSession();
        var prepared=lifecycle.physical().withSnapshot(same,before.deadline(),lease->continuity.withLease(same,lease,()->{
            var transport=lease.fullSnapshot().actual().session();var b=before.state.binding();
            String session=before.state.rebind().map(value->value.resumed().sessionId()).orElse(b.predecessor().sessionId());
            BigInteger connection=before.state.rebind().map(value->value.resumed().connectionGeneration()).orElse(b.predecessor().connectionGeneration());
            if(session.equals(transport.sessionId())&&connection.equals(transport.connectionGeneration()))return Optional.<RootPendingUiContinuity.Prepared<RebindMaterial>>empty();
            before.requireCurrent(same);
            var custody=qualification.qualifyRetainedCauseReconnected(b.qualifiedCause(),lease.fullSnapshot(),same,lease.sourceQualification(),same.head());
            var change=continuity.preparedRebind(custody.continuityBinding()).orElseThrow(()->new IOException("fresh pending transport has no actual Rebind reducer preflight"));
            return Optional.of(continuity.seal(new RebindMaterial(custody,change,mutationFrame(lease),lease.fullSnapshot(),lease.sourceQualification(),same.head())));
        }));
        if(prepared.isEmpty())return before;
        var captured=prepared.orElseThrow();var material=captured.value();
        return continuity.withPrepared(captured,()->{
            qualification.requireReconnectedCauseCurrent(material.custody(),material.full(),same,material.source(),material.head());
            var projected=SuccessorUiObligationReducer.rebind(before.state,material.change());
            require(projected.rebind().equals(Optional.of(material.change())),"same-writer private Rebind reducer changed before actual CAS");
            return mutate(before,new DriverPendingEpisodeSource.Rebind(material.change()),material.physical());
        });
    }
    public Optional<SessionPorts.PendingSuccessorUi> pendingSuccessorUi(ContinuityStorePort.Session same,SessionPorts.SessionIdentity expected,Instant deadline)throws IOException {
        require(expected.machineId().equals(context.game().machineId())&&expected.game().equals(context.game().generation())&&expected.sessionId().equals(context.game().sessionId()),"pending probe crossed actual Game/session");
        if(completedByCanonicalLifecycle)return Optional.empty();
        if(publication==null&&committedRecovery==null&&admittedRecovery==null)current(same,deadline);
        if(admittedRecovery!=null) {
            var parent=find(same,admittedRecovery.actual.parent().command().actionId());
            if(hasControllerAdoption(same,expected,parent)){completedByCanonicalLifecycle=true;return Optional.empty();}
            refreshAdmittedRecovery(same,deadline);return Optional.of(new SessionPorts.PendingSuccessorUi(new AdmittedPendingToken(admittedRecovery,deadline)));
        }
        if(committedRecovery!=null) {
            var parent=find(same,initial.originalParent().actionId());
            if(parent.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied applied) {
                applied.proof().validateParent(initial.originalParent());
                require(applied.proof().kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR&&applied.proof().originalEvidence().contains(committedRecovery.scope.proofReference)
                        &&applied.proof().originalEvidence().contains(committedRecovery.scope.stage.metadata().canonicalDomain()),"canonical final parent lost its privately qualified M3/domain originals");
                if(hasControllerAdoption(same,expected,parent)){completedByCanonicalLifecycle=true;return Optional.empty();}
            }
            refreshCommittedRecovery(same,deadline);return Optional.of(new SessionPorts.PendingSuccessorUi(new CommittedPendingToken(committedRecovery,deadline)));
        }
        var actual=current(same,deadline);if(publicRequest.get()!=null&&actual.orElse(null) instanceof EventCurrent)return Optional.empty();
        return actual.map(SessionPorts.PendingSuccessorUi::new);
    }
    private boolean hasControllerAdoption(ContinuityStorePort.Session same,SessionPorts.SessionIdentity expected,ActionReceipt parent)throws IOException {
        var root=context.core().sessionAccess().current();context.core().requireCurrentForAccess(same,root);
        require(root.driver()==context.adopted(),"natural adoption receipt belongs to another actual Root Driver owner");
        var accepted=root.controllerForPublication().naturalEpisodeAdoption(parent);if(accepted.isEmpty())return false;
        var actual=accepted.orElseThrow();require(parent.state() instanceof ActionState.CompositeSettled parentState&&parentState.settlement() instanceof ActionState.LifecycleApplied,
                "Controller adoption requires the actual canonical lifecycle settlement");
        var proof=((ActionState.LifecycleApplied)((ActionState.CompositeSettled)parent.state()).settlement()).proof();
        require(actual.owner().equals(expected)&&actual.parent().sequence()==parent.sequence()
                &&Arrays.equals(ActionCodec.encodeCommand(actual.parent().command()),ActionCodec.encodeCommand(parent.command()))
                &&actual.parent().state() instanceof ActionState.CompositeSettled acceptedState&&acceptedState.settlement() instanceof ActionState.LifecycleApplied acceptedLifecycle
                &&Arrays.equals(LifecycleProofCodec.encode(acceptedLifecycle.proof()),LifecycleProofCodec.encode(proof)),
                "Controller accepted a different exact canonical natural parent/owner/proof");
        root.batchJournal().requireHistoricalEpisodeAdoption(same,actual.admission());return true;
    }
    private record Publishing(Current predecessor,Known actualBefore,DriverPendingEpisodeSource.Change change,DriverPendingEpisodeMutations.Prepared projected,Instant observedAt,ExactRef beforeNative) { }
    private final ThreadLocal<Publishing> importing=new ThreadLocal<>();
    private final class MutationCapture implements DriverPendingEpisodeSource.Mutation {
        private final Publishing authority;private final RootNaturalSuccessionOriginals.MutationCommitted committed;private Known published;
        private MutationCapture(Publishing authority,RootNaturalSuccessionOriginals.MutationCommitted committed){this.authority=authority;this.committed=committed;}
        @Override public Known actualKnown(){return authority.actualBefore();}
        @Override public SuccessorUiObligation beforeObligation(){return authority.predecessor().state;}
        @Override public DriverPendingEpisodeSource.Change change(){return authority.change();}
        @Override public SuccessorUiObligation afterObligation(){return authority.projected().projection().obligation();}
        @Override public DriverPendingEpisodeMutations.Prepared preparedProjection(){return authority.projected();}
        @Override public DomainBodies.PreparedImport originalPrepared(){return committed.prepared();}
        @Override public WriterContracts.Receipt actualReceipt(){return committed.receipt();}
        @Override public ExactRef canonicalDomainRef(){return committed.payload();}
        @Override public ExactRef originalBeforeNative(){return authority.beforeNative();}
        @Override public Instant actualObservedAtUtc(){return authority.observedAt();}
    }
    DriverPendingEpisodeSource.Mutation currentMutation(ContinuityStorePort.Session same,DriverStateAssembler expected)throws IOException {
        requireMutation(same,expected,mutation);return mutation;
    }
    void requireMutation(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Mutation identical)throws IOException {
        requireDriverContext();context.writer().requireSession(same);require(expected==assembler()&&identical==mutation&&mutation!=null,"mutation DATA lacks the actual private capture");
        var actual=mutation;require(actual.authority.predecessor().retained==publication&&actual.authority.predecessor().state==obligation,"mutation lost private predecessor");
        same.requireCommitted(actual.originalPrepared(),actual.actualReceipt());require(natural.currentCaptureDocument().equals(actual.canonicalDomainRef()),"actual current mutation domain changed");
        assembler().withFrozenFacts(same,frozen->{require(frozen.state() instanceof Known,"pending facts missing");var known=(Known)frozen.state();require(known.stamp().equals(actual.actualKnown().stamp())&&Arrays.equals(known.driver().encode(),actual.actualKnown().driver().encode())&&known.auxiliary().equals(actual.actualKnown().auxiliary()),"mutation original Driver changed before CAS");return null;});
    }
    void requirePublishedMutation(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverPendingEpisodeSource.Mutation identical,Known actualPublished)throws IOException {
        requireDriverContext();context.writer().requireSession(same);require(expected==assembler()&&identical==mutation&&mutation!=null,"published mutation lost private issuer");
        var actual=mutation;require(actualPublished.stamp().episodeEpoch()==actual.actualKnown().stamp().episodeEpoch()&&Arrays.equals(actualPublished.driver().encode(),actual.preparedProjection().projection().driver().encode()),"published mutation changed projected new-episode Driver");
        same.requireCommitted(actual.originalPrepared(),actual.actualReceipt());require(natural.currentCaptureDocument().equals(actual.canonicalDomainRef()),"published domain changed");
        require(actual.published==null||actual.published.stamp().equals(actualPublished.stamp()),"actual mutation CAS result replaced");actual.published=actualPublished;
    }
    private record MutationFrame(Known facts,Instant observedAt,org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source,ExactRef beforeNative) { }
    private static MutationFrame mutationFrame(RootLifecycleAuthority.SnapshotLease actual){return new MutationFrame(actual.factsKnown(),actual.fullSnapshot().actual().observedAt(),actual.sourceQualification(),actual.fullSnapshot().originalEvidence());}
    private Current mutate(Current before,DriverPendingEpisodeSource.Change change,MutationFrame actual)throws IOException {
        var same=context.borrowedSession();before.requireCurrent(same);actual.source().assertCurrent(same);
        var projected=DriverPendingEpisodeMutations.prepare(actual.facts(),before.state,change,archive(same));
        var token=new Publishing(before,actual.facts(),change,projected,actual.observedAt(),actual.beforeNative());
        require(importing.get()==null,"nested pending mutation forbidden");importing.set(token);
        RootNaturalSuccessionOriginals.MutationCommitted committed;
        try {committed=natural.publishPendingMutation(same,pendingDocument(before,projected,change,token.observedAt()),actual.source().guard());}
        finally {importing.remove();}
        mutation=new MutationCapture(token,committed);publication=assembler().publishPendingEpisodeMutation(same);obligation=projected.projection().obligation();if(completedChild!=null)incorporatedChildren.add(completedChild.actionId());qualifiedAfterChild=null;completedChild=null;
        var after=new Current(publication,obligation,before.deadline());var call=continuationCall.get();if(call!=null){require(before.retained==call.latest.retained&&before.state==call.latest.state,"continuation mutation lost its actual private predecessor");call.latest=after;}return after;
    }
    private NaturalClockOriginals.Document pendingDocument(Current before,DriverPendingEpisodeMutations.Prepared projected,
            DriverPendingEpisodeSource.Change change,Instant observedAt)throws IOException {
        var previous=NaturalClockOriginals.decode(natural.readExact(before.canonicalDomain()));var retained=previous.pendingProjection().orElseThrow();
        Optional<ExactRef> finalized=change instanceof DriverPendingEpisodeSource.Finalize value?Optional.of(value.value().finalM3Proof()):Optional.empty();
        var artifact=new NaturalClockOriginals.MutationArtifact(Math.addExact(retained.mutationSequence(),1),projected.beforeDriver(),projected.afterDriver(),projected.afterAuxiliary(),projected.beforeObligation(),projected.afterObligation(),projected.originalResult(),finalized);
        var date=Optional.ofNullable(enteringDate.get()).or(()->retained.dateIntent());var event=Optional.ofNullable(enteringEvent.get()).or(()->retained.eventIntent());
        var diagnosis=Optional.ofNullable(enteringEventDiagnosis.get()).or(()->retained.eventDiagnosis());
        return new NaturalClockOriginals.Document(previous.capture(),previous.ready(),Optional.of(new NaturalClockOriginals.PendingProjection(retained.value(),retained.original(),Optional.of(artifact),date,event,diagnosis)),observedAt);
    }
    void verifyPendingMutation(WriterContracts.Head head,NaturalClockOriginals.Document old,NaturalClockOriginals.Document actual)throws IOException {
        var held=importing.get();require(held!=null&&held.predecessor().retained==publication&&held.predecessor().state==obligation,"pending mutation import lacks its private actual producer");
        require(head.digest().equals(context.borrowedSession().head().digest())&&old.capture().equals(actual.capture())&&old.ready().equals(actual.ready())
                &&Arrays.equals(NaturalClockOriginals.encode(actual),NaturalClockOriginals.encode(pendingDocument(held.predecessor(),held.projected(),held.change(),held.observedAt()))),"pending mutation did not retain exact canonical predecessor/projection");
        held.predecessor().requireCurrent(context.borrowedSession());
        if(held.change() instanceof DriverPendingEpisodeSource.Finalize value){var scope=finalizing.get();require(scope!=null&&scope.finalized!=null&&Arrays.equals(value.value().finalM3Proof().sha256().getBytes(java.nio.charset.StandardCharsets.US_ASCII),scope.finalized.digest().getBytes(java.nio.charset.StandardCharsets.US_ASCII)),"final mutation lacks the actual private M3 Finalized issuer");}
    }
    private record Physical(Current current,RootLifecycleAuthority.SnapshotLease lease) { }
    private final ThreadLocal<Physical> physicalScope=new ThreadLocal<>();
    private record CommittedRead(CommittedRecovery retained,RootLifecycleAuthority.SnapshotLease lease) { }
    private final ThreadLocal<CommittedRead> committedReadScope=new ThreadLocal<>();
    private final ThreadLocal<RootLifecycleAuthority.SnapshotLease> committedPhysicalScope=new ThreadLocal<>();
    @FunctionalInterface private interface PhysicalWork<T>{T run(RootLifecycleAuthority.SnapshotLease actual)throws IOException;}
    private <T>T withPhysical(Current current,PhysicalWork<T> work)throws IOException {return withPhysical(current,true,work);}
    private <T>T withPhysical(Current current,boolean mustBePaused,PhysicalWork<T> work)throws IOException {
        var same=context.borrowedSession();current.requireCurrent(same);require(physicalScope.get()==null,"nested private pending physical scope");
        return lifecycle.physical().withSnapshot(same,current.deadline(),lease->continuity.withLease(same,lease,()->{
            lease.assertCurrent(same);var full=lease.fullSnapshot();var state=current.state;var b=state.binding();var facts=lease.factsKnown();
            var transport=full.actual().session();boolean fresh=!transport.sessionId().equals(b.predecessor().sessionId())||!transport.connectionGeneration().equals(b.predecessor().connectionGeneration());
            var priorConnection=openingReconnected.get();
            try {
            if(fresh)openingReconnected.set(qualification.qualifyRetainedCauseReconnected(b.qualifiedCause(),full,same,lease.sourceQualification(),same.head()));
            String expectedSession=state.rebind().map(value->value.resumed().sessionId()).orElse(b.predecessor().sessionId());
            BigInteger expectedConnection=state.rebind().map(value->value.resumed().connectionGeneration()).orElse(b.predecessor().connectionGeneration());
            require(full.actual().session().game().equals(b.predecessor().game())
                    &&(transport.sessionId().equals(expectedSession)&&transport.connectionGeneration().equals(expectedConnection)
                        ||fresh&&state.phase()==Phase.FINALIZED&&openingReconnected.get().purpose()==RootPendingNaturalSuccessionQualification.ContinuityPurpose.FINALIZED_METADATA_ONLY)
                    &&facts.stamp().episodeEpoch()==b.successorEpisodeEpoch()&&facts.driver().session().actorId().equals(b.successorCharacterId())&&facts.driver().session().episodeRunId().equals(b.successorEpisodeRunId())
,"private pending physical source/new episode differs");
            require(OpportunityJson.bool(full.semantic().get("map_ready"),"actual map ready")&&(!mustBePaused||OpportunityJson.bool(full.semantic().get("paused"),"actual paused")),"pending UI requires its actual physical map/paused predicate");
            require(mustBePaused||dateScope.get()!=null,"unpaused DATA capture requires the actual private Date source scope");
            var publicInput=publicRequest.get();if(publicInput!=null){require(publicInput.actor().equals(b.successorCharacterId())&&publicInput.episodeRunId().equals(b.successorEpisodeRunId()),"public Close request changed actual successor actor/run");
            }
            var player=OpportunityJson.object(full.semantic().get("played_character"),"actual living pending successor");require(OpportunityJson.bool(player.get("alive"),"alive")&&OpportunityJson.integer(player.get("character_id"),"actor").equals(b.successorCharacterId()),"pending native successor changed/died");
            physicalScope.set(new Physical(current,lease));try{var result=work.run(lease);lease.assertCurrent(same);return result;}
            finally{physicalScope.remove();}
            }finally{if(priorConnection==null)openingReconnected.remove();else openingReconnected.set(priorConnection);}
        }));
    }
    private void requireQuery(PlanningReadRequest request)throws IOException {
        requireDriverContext();require(request.operation().equals(QUERY)&&request.origin() instanceof CommandOrigin.Gameplay&&request.source().equals(context.source())&&request.sessionId().equals(context.game().sessionId())&&request.arguments().members().isEmpty(),"timeline query changed actual registered gameplay source");
        if(admittedRecovery!=null&&!completedByCanonicalLifecycle){var held=admittedReadScope.get();require(held!=null&&held.retained()==admittedRecovery&&request.before().equals(held.lease().ordinary().orElseThrow().identity()),"historically admitted query lacks its exact current physical read scope");held.actual().requireCurrent(context.borrowedSession());held.lease().assertCurrent(context.borrowedSession());return;}
        if(committedRecovery!=null&&!completedByCanonicalLifecycle){var held=committedReadScope.get();require(held!=null&&held.retained()==committedRecovery&&request.before().equals(held.lease().ordinary().orElseThrow().identity()),"committed successor query lacks its exact private physical read scope");held.lease().assertCurrent(context.borrowedSession());return;}
        if(publication!=null&&!completedByCanonicalLifecycle){var scope=physicalScope.get();require(scope!=null,"pending query needs its actual private physical scope");scope.current().requireCurrent(context.borrowedSession());require(request.before().equals(scope.lease().ordinary().orElseThrow().identity()),"pending query before differs from actual captured native frame");}
    }
    private G2RetainedNativeSourceProvider.Session session(DriverObservationAssembler.Complete frame){
        return new G2RetainedNativeSourceProvider.Session(frame.identity().machineId(),frame.sessionId(),new G2RetainedNativeSourceProvider.GameIdentity(frame.identity().game().pid(),frame.identity().game().creationFiletime().value().toString()),frame.identity().frame().episodeRunId(),frame.connectionGeneration().toString(),executable,executableFileId,executableMtimeNs);
    }
    private NativeTimelineBlocker12004.Query decodeQuery(PlanningReadReceipt receipt) {
        try {
            require(receipt.contractId().equals(QUERY_CONTRACT)&&receipt.request().operation().equals(QUERY)&&receipt.request().arguments().members().isEmpty(),"not this actual installed timeline query");
            var same=context.borrowedSession();var archive=archive(same);var first=RootGuardEvidence.loadFrame(receipt.before().binding(),archive,context.frameLoader());var last=RootGuardEvidence.loadFrame(receipt.after().binding(),archive,context.frameLoader());
            RootGuardEvidence.requireHistory(receipt.before().binding(),archive,same);RootGuardEvidence.requireHistory(receipt.after().binding(),archive,same);
            require(first.equals(last)&&receipt.before().originalBindingSha256().equals(receipt.after().originalBindingSha256())&&receipt.request().before().equals(first.identity())&&receipt.request().source().equals(first.source())&&receipt.before().binding().authorityId().equals(receipt.after().binding().authorityId()),"timeline query crossed actual full source/Driver/native frame");
            require(receipt.original().originalResultToken().isPresent()&&StrictJson.parse(receipt.original().originalFrame().bytes(),NativeTimelineBlocker12004.MAX_BYTES).get("result").equals(StrictJson.parse(receipt.original().originalResultToken().orElseThrow().bytes(),NativeTimelineBlocker12004.MAX_BYTES)),"original outer frame/result token differs");
            var raw=natural.originalFrame(receipt.original());
            var frame=RootNaturalSuccessionOriginals.frame(first.semantic(),first.identity().frame().identity().player().intValueExact());
            return NativeTimelineBlocker12004.parseQuery(receipt.original().originalFrame().bytes(),raw,new NativeTimelineBlocker12004.BoundFrame(session(first),frame,NativeTimelineBlocker12004.Scene.fromSnapshot(OpportunityJson.toNode(first.semantic()))),receipt.requestId());
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private NativeTimelineBlocker12004.Query decodeReconciliationQuery(PlanningReadReceipt receipt){
        try {
            require(receipt.contractId().equals(RECONCILIATION_QUERY_CONTRACT)&&receipt.request().origin() instanceof CommandOrigin.Reconciliation&&receipt.request().arguments().members().isEmpty(),"not the actual pure Close reconciliation profile");
            var same=context.borrowedSession();var archive=archive(same);var first=context.reconciliation().verifyArchived(receipt.before().binding(),archive,same,context.originals());var last=context.reconciliation().verifyArchived(receipt.after().binding(),archive,same,context.originals());
            require(first.equals(last)&&receipt.request().origin().requireReconciliation().sameGuardFrame(receipt.before().binding().origin().requireReconciliation()),"Close reconciliation query crossed its actual complete source frame");
            var raw=natural.originalFrame(receipt.original());var frame=RootNaturalSuccessionOriginals.frame(first.semantic(),first.identity().frame().identity().player().intValueExact());
            return NativeTimelineBlocker12004.parseQuery(receipt.original().originalFrame().bytes(),raw,new NativeTimelineBlocker12004.BoundFrame(session(first),frame,NativeTimelineBlocker12004.Scene.fromSnapshot(OpportunityJson.toNode(first.semantic()))),receipt.requestId());
        }catch(IOException failure){throw new UncheckedIOException(failure);}
    }
    private NativeTimelineBlocker12004.Query replayTimeline(PlanningReadReceipt receipt){return receipt.contractId().equals(RECONCILIATION_QUERY_CONTRACT)?reconciliationQuery.replay(receipt):query.replay(receipt);}
    private record Queried(PlanningReadResult.Known<NativeTimelineBlocker12004.Query> read,Observation observation,MutationFrame physical) { }
    private sealed interface ResumeRead permits ResumeObserved,ResumeReadFailed { }
    private record ResumeObserved(Queried value) implements ResumeRead { }
    private record ResumeReadFailed(IOException original) implements ResumeRead { }
    private Queried query(Current current)throws IOException {return withPhysical(current,lease->queryInside(current,lease));}
    private Queried queryInside(Current current,RootLifecycleAuthority.SnapshotLease lease)throws IOException {
            var frame=lease.ordinary().orElseThrow(()->new IOException("current pending successor is not a living ordinary native projection"));
            var read=natural.read(context.borrowedSession(),query,new PlanningReadRequest(new CommandOrigin.Gameplay(frame.identity()),frame.source(),frame.sessionId(),QUERY,EMPTY,current.deadline()));
            var parsed=read.value();var scene=parsed.context();var event=parsed.binding().scene();var state=!event.activeEventJson().equals("null")||!event.pendingInteractionJson().equals("null")?UiState.PLAYER_DECISION_PENDING:scene.clearedObserved()?UiState.CLEAR:scene.supportedCloseObserved()?UiState.CLOSE_REQUIRED:UiState.UNRESOLVED;
            var ref=archive(context.borrowedSession()).readReferenceOf(read.receipt());
            var observation=new Observation(uiFrame(lease),state,parsed.sequence(),parsed.observationRevision(),ref,natural.originalFrame(read.receipt().original()),Optional.empty(),Optional.empty());
            return new Queried(read,observation,mutationFrame(lease));
    }
    private UiFrame uiFrame(RootLifecycleAuthority.SnapshotLease lease){
        var full=lease.fullSnapshot();var facts=lease.factsKnown();var transport=full.actual().session();var b=obligation.binding();
        return new UiFrame(transport.machineId(),transport.game(),transport.sessionId(),transport.connectionGeneration(),b.sourceEpochSha256(),full.actual().snapshotId(),full.facts().publicRevision(),full.actual().nativeRevision(),OpportunityJson.integer(full.semantic().get("date_raw"),"date_raw"),facts.driver().session().actorId(),facts.driver().session().episodeRunId(),facts.stamp().episodeEpoch(),facts.stamp().driverVersion(),full.originalEvidence(),lease.originalSemantic(),lease.originalDriver(),lease.sourceQualification().proof(),full.actual().observedAt());
    }
    private void requireRead(Current current,PlanningReadRequest request,ReadContract<?> contract)throws IOException {
        current.requireCurrent(context.borrowedSession());require(context.readCatalog().containsIdentity(contract),"pending read is not the identical installed contract");
        boolean timeline=contract==query&&request.arguments().members().isEmpty();
        boolean root=contract==natural.campaignRootContract()
                &&FinanceReadContracts.rootCapture(request.arguments())==FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS;
        boolean status=executing.get() instanceof DateCurrent&&contract==lifecycle.life().infrastructure().statuses().contract();
        boolean event=eventScope.get()!=null&&events().pendingUiReadContracts().stream().anyMatch(value->value==contract);
        require(timeline||root||status||event,"pending UI permits only its exact source-bound finite UI/ROOT/date/event reads");
    }
    private GuardEvidence binding(Current current,RootLifecycleAuthority.SnapshotLease actual,OperationKey operation)throws IOException {
        var same=context.borrowedSession();current.requireCurrent(same);actual.assertCurrent(same);
        if(operation.equals(CLOSE)){var admission=queryInside(current,actual);require(admission.observation().state()==UiState.CLOSE_REQUIRED&&admission.read().value().context().supportedCloseObserved(),"actual current modal/event predicates no longer authorize Close");}
        if(current instanceof EventCurrent event&&operation.equals(event.entry.prepared.command().operation())){var fresh=events().preparePendingUiEvent(same,event.entry.source,event.entry.prepared.command().actionId(),event.entry.prepared.command().deadline());event.entry.source.checkedFresh=fresh.command();events().requirePendingUiEventCurrent(same,event.entry.source,event.entry.prepared,fresh);}
        var requested=publicRequest.get();if(requested!=null&&(operation.equals(CLOSE)||operation.value().equals("life-advance")))require(requested.expectedRevision().equals(actual.fullSnapshot().facts().publicRevision()),"public Close request revision changed before the actual top-level UI child guard");
        var frame=actual.ordinary().orElseThrow(()->new IOException("actual pending successor frame unavailable"));
        return physicalBinding(actual,frame,operation,current.state.binding().causeDigest());
    }
    private GuardEvidence physicalBinding(RootLifecycleAuthority.SnapshotLease actual,DriverObservationAssembler.Complete frame,OperationKey operation,String causeDigest)throws IOException {
        var same=context.borrowedSession();actual.assertCurrent(same);
        var semantic=lifecycle.physical().semantic(same,new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId()),actual);
        var capabilities=StrictJson.object();var names=capabilities.putArray("capabilities");actual.bridgeCapabilities().stream().sorted().forEach(names::add);
        var capRef=retain(same,StrictJson.canonical(capabilities));String authority="root-pending-successor-ui:"+causeDigest;
        var original=new RootGuardEvidence.PhysicalReadOriginals(frame,semantic,actual.originalHello(),actual.originalHeartbeat(),actual.sourceQualification().proof(),capRef);
        var basis=RootGuardEvidence.preservePhysicalRead(original,operation,authority,archive(same),same.head());actual.assertCurrent(same);
        return new GuardEvidence(new CommandOrigin.Gameplay(frame.identity()),frame.source(),frame.sessionId(),frame.connectionGeneration(),operation,frame.originalEvidence(),actual.originalHello(),authority,frame.observedAt(),actual.validUntil(),List.of(basis));
    }
    private PlanningReadGuard heldAdmittedRead(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract)throws IOException {
        var same=context.borrowedSession();var scope=admittedReadScope.get();
        require(scope!=null&&scope.retained()==admittedRecovery&&head.digest().equals(same.head().digest())&&contract==query
                &&context.readCatalog().containsIdentity(contract)&&request.operation().equals(QUERY)&&request.arguments().members().isEmpty(),
                "historically admitted completion permits only its identical installed timeline query");
        scope.actual().requireCurrent(same);scope.lease().assertCurrent(same);var full=scope.lease().fullSnapshot();var frame=scope.lease().ordinary().orElseThrow();
        var player=OpportunityJson.object(full.semantic().get("played_character"),"actual current player");
        require(request.before().equals(frame.identity())&&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId())
                &&OpportunityJson.bool(full.semantic().get("paused"),"paused")&&OpportunityJson.bool(full.semantic().get("map_ready"),"map ready")
                &&OpportunityJson.bool(player.get("alive"),"alive")&&OpportunityJson.integer(player.get("character_id"),"actor").equals(scope.actual().driver().session().actorId())
                &&full.facts().driver().session().episodeRunId().equals(scope.actual().driver().session().episodeRunId()),"historically admitted read lost its actual paused living current frame");
        return new PlanningReadGuard(physicalBinding(scope.lease(),frame,request.operation(),scope.retained().state.binding().causeDigest()),true,true,true,frame.fullBindingSha256());
    }
    private PlanningReadGuard heldCommittedRead(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract)throws IOException {
        var same=context.borrowedSession();var scope=committedReadScope.get();
        require(scope!=null&&scope.retained()==committedRecovery&&head.digest().equals(same.head().digest())&&contract==query
                &&context.readCatalog().containsIdentity(contract)&&request.operation().equals(QUERY)&&request.arguments().members().isEmpty(),"committed successor permits only its identical installed timeline query");
        requireCommittedPendingEpisode(find(same,initial.originalParent().actionId()),same,scope.retained().edge);scope.lease().assertCurrent(same);
        var full=scope.lease().fullSnapshot();var frame=scope.lease().ordinary().orElseThrow();var player=OpportunityJson.object(full.semantic().get("played_character"),"actual successor");
        require(request.before().equals(frame.identity())&&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId())
                &&OpportunityJson.bool(full.semantic().get("paused"),"paused")&&OpportunityJson.bool(full.semantic().get("map_ready"),"map ready")
                &&OpportunityJson.bool(player.get("alive"),"alive")&&OpportunityJson.integer(player.get("character_id"),"actor").equals(obligation.binding().successorCharacterId())
                &&full.facts().driver().session().episodeRunId().equals(obligation.binding().successorEpisodeRunId()),"committed timeline read lost its actual paused living successor frame");
        return new PlanningReadGuard(physicalBinding(scope.lease(),frame,request.operation(),obligation.binding().causeDigest()),true,true,true,frame.fullBindingSha256());
    }
    private boolean needsPendingGate()throws IOException {
        if(restoredFinalized!=null){requireRestoredFinalizedCurrent(context.borrowedSession(),restoredFinalized);return initial!=null||publication!=null;}
        if(completedByCanonicalLifecycle)return false;if(publication!=null||committedRecovery!=null||admittedRecovery!=null)return true;
        var same=context.borrowedSession();return assembler().withFrozenFacts(same,frozen->frozen.state() instanceof Known known&&known.auxiliary().members().containsKey(SuccessorUiObligation.AUXILIARY_KEY));
    }
    private boolean pendingGate(){try{return needsPendingGate();}catch(IOException failure){throw new UncheckedIOException(failure);}}
    private PlanningReadGuard heldRead(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract)throws IOException {
        var same=context.borrowedSession();require(same.head().digest().equals(head.digest()),"pending read lost the actual writer head");
        var scope=physicalScope.get();require(scope!=null,"held-only pending read has no active private physical source");
        requireRead(scope.current(),request,contract);var frame=scope.lease().ordinary().orElseThrow();require(request.before().equals(frame.identity())&&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId()),"pending read identity differs from the actual physical scope");
        return new PlanningReadGuard(binding(scope.current(),scope.lease(),request.operation()),true,true,true,frame.fullBindingSha256());
    }
    public PlanningReadCoordinator.ReadGuardPort wrapReads(PlanningReadCoordinator.ReadGuardPort ordinary) {
        Objects.requireNonNull(ordinary);return new PlanningReadCoordinator.ReadGuardPort(){
            @Override public PlanningReadGuard verify(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract){
                if(request.origin() instanceof CommandOrigin.PhysicalStatusOnly){require(contract.guardMode()==ReadContract.GuardMode.STATUS_ONLY,"physical status origin requires its exact finite status profile");PhysicalStatusIdentity.requireProfile(contract);return ordinary.verify(head,request,contract);}
                if(contract==reconciliationQuery)return ordinary.verify(head,request,contract);
                if(admittedReadScope.get()!=null)try{return heldAdmittedRead(head,request,contract);}catch(IOException failure){throw new UncheckedIOException(failure);}
                if(committedReadScope.get()!=null)try{return heldCommittedRead(head,request,contract);}catch(IOException failure){throw new UncheckedIOException(failure);}
                if(!pendingGate())return ordinary.verify(head,request,contract);
                try{if(physicalScope.get()!=null)return heldRead(head,request,contract);var current=current(context.borrowedSession(),request.deadline()).orElseThrow();return withPhysical(current,lease->heldRead(head,request,contract));}catch(IOException failure){throw new UncheckedIOException(failure);}
            }
            @Override public PlanningReadGuard verifyOriginalCurrent(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract){
                require(!(request.origin() instanceof CommandOrigin.PhysicalStatusOnly),"physical status cannot borrow held ordinary or pending originals");
                if(contract==reconciliationQuery)return ordinary.verifyOriginalCurrent(head,request,contract);
                if(admittedReadScope.get()!=null)try{return heldAdmittedRead(head,request,contract);}catch(IOException failure){throw new UncheckedIOException(failure);}
                if(committedReadScope.get()!=null)try{return heldCommittedRead(head,request,contract);}catch(IOException failure){throw new UncheckedIOException(failure);}
                if(!pendingGate())return ordinary.verifyOriginalCurrent(head,request,contract);
                try{return heldRead(head,request,contract);}catch(IOException failure){throw new UncheckedIOException(failure);}
            }
            @Override public void verifyFrontendReadContinuation(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract,PlanningReadGuard before,PlanningReadGuard after){
                if(!pendingGate()){ordinary.verifyFrontendReadContinuation(head,request,contract,before,after);return;}
                throw new IllegalArgumentException("pending successor UI cannot borrow frontend continuation");
            }
            @Override public <T> T withOriginalReadSource(WriterContracts.Head head,PlanningReadRequest request,ReadContract<?> contract,java.util.function.Supplier<T> work){
                Objects.requireNonNull(work);
                if(request.origin() instanceof CommandOrigin.PhysicalStatusOnly||contract==reconciliationQuery||admittedReadScope.get()==null&&committedReadScope.get()==null&&!pendingGate())return ordinary.withOriginalReadSource(head,request,contract,work);
                return work.get();
            }
        };
    }
    public ActionPorts.GuardPort wrapActions(ActionPorts.GuardPort ordinary) {
        Objects.requireNonNull(ordinary);return (head,command)->{
            if(!pendingGate())return ordinary.verify(head,command);
            try{var same=context.borrowedSession();require(head.digest().equals(same.head().digest()),"pending action lost writer head");
                var current=executing.get();require(current!=null,"ordinary actions/SAVE are blocked by actual pending UI");current.requireMayExecute(same,command);
                var date=current instanceof DateCurrent value?value:null;var previous=dateScope.get();if(date!=null)dateScope.set(date.source);
                try{return withPhysical(current,date==null||!command.operation().value().equals("pause-map"),lease->{var frame=lease.ordinary().orElseThrow();require(command.before().equals(frame.identity())&&command.source().equals(frame.source())&&command.sessionId().equals(frame.sessionId()),"pending action does not use actual new-episode frame");return binding(current,lease,command.operation());});}
                finally{if(previous==null)dateScope.remove();else dateScope.set(previous);}
            }catch(IOException failure){throw new UncheckedIOException(failure);}
        };
    }
    private static final String CLOSE_OBSERVER="xar.java.pending-successor-modal-close/v1";
    private static final List<org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedValue> CLOSE_VALUES=List.of(
            new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("native.gameplay_verified"),false),
            new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("timeline.advance_verified"),false),
            new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("timeline.checkpoint_eligible"),false),
            new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedBoolean(new org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey("lifecycle.death_modal_cleared"),true));
    private ActionCommand closeCommand(Current current,String actionId,Queried actual)throws IOException {
        require(actual.read().value().context().supportedCloseObserved(),"native current timeline exposes no legal Close");var request=actual.read().receipt().request();
        var expected=new org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition(1,request.before(),request.source(),CLOSE_OBSERVER,CLOSE_VALUES);
        var fields=StrictJson.object().put("expected_date_raw",actual.observation().frame().dateRaw()).put("expected_played_character_id",actual.observation().frame().actorCharacterId());
        return new ActionCommand(actionId,new CommandOrigin.Gameplay(request.before()),request.source(),request.sessionId(),CLOSE,OpportunityJson.object(OpportunityJson.parse(StrictJson.canonical(fields)),"Close arguments"),new CommandExpectation.Gameplay(expected),new org.xar.ck3.control.finance.jointbudget.JointBudgetSelector.Claims(Set.of(),Set.of(),Set.of(),Set.of()),current.deadline());
    }
    /** Read-only verification, safe inside the coordinator's actual frozen guard. No capture/observe/submit is performed. */
    void requireChild(ContinuityStorePort.Session same,DriverStateAssembler expected,DriverStateAssembler.PendingEpisodePublication genuine,
            ActionCommand parent,ActionCommand child)throws IOException {
        requireDriverContext();context.writer().requireSession(same);require(expected==assembler()&&genuine==publication&&initial!=null&&parent.equals(initial.originalParent()),"pending child lost its actual private publication/original parent");
        var current=executing.get();
        if(current==null){var original=issued.get(child.actionId());require(original!=null&&original.child().equals(child),"child has no actual retained private issuance");var fresh=new Current(genuine,obligation,original.current().limit);current=original.current() instanceof DateCurrent?new DateCurrent(fresh,actualDateSource):original.current() instanceof EventCurrent event?new EventCurrent(fresh,event.entry):fresh;}
        require(current.retained==genuine&&current.state==obligation,"pending child lost its exact private issuance/canonical state");
        require(child.origin() instanceof CommandOrigin.Gameplay,"pending continuation requires the actual new-episode Gameplay child");
        if(current instanceof DateCurrent date){requireDateChild(same,date,child);return;}
        if(current instanceof EventCurrent event){requireEventChild(same,event,child);return;}
        require(child.operation().equals(CLOSE)&&current.kind()==CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE,"Close token cannot authorize ordinary/SAVE/event/date actions");
        var intent=obligation.closeAttempt().orElseThrow(()->new IOException("canonical once-Close intent absent"));
        require((intent.receipt().isEmpty()||executing.get()==null)&&child.actionId().equals(intent.actionId())&&ActionCodec.bodySha256(child).equals(intent.commandBodySha256())
                &&Arrays.equals(natural.readExact(intent.originalCommand()),ActionCodec.encodeCommand(child))&&child.deadline().equals(current.deadline())
                &&child.before().frame().identity().player().equals(obligation.binding().successorCharacterId())&&child.before().frame().episodeRunId().equals(obligation.binding().successorEpisodeRunId()),"pending child differs from exact once intent/newactor/run/deadline");
        require(child.expected().observerSchema().equals(CLOSE_OBSERVER)&&child.expected().values().equals(CLOSE_VALUES),"Close cannot claim gameplay/day/SAVE completion");
        require(natural.currentCaptureDocument().equals(genuine.canonicalDomainRef())&&Arrays.equals(natural.readExact(obligation.binding().qualifiedCause()),initial.cause().originalProof()),"actual canonical pending cause changed");
    }
    private void requireEventChild(ContinuityStorePort.Session same,EventCurrent current,ActionCommand child)throws IOException {
        var entry=current.entry;require(entry==latestEvent&&eventEntries.get(child.actionId())==entry&&entry.prepared.command().equals(child)&&Arrays.equals(natural.readExact(entry.intent.command()),ActionCodec.encodeCommand(child)),"event child differs from its genuinely issued exact once command");
        require((entry.intent.originalReceipt().isEmpty()||executing.get()==null)&&!child.deadline().isAfter(current.deadline())&&child.before().frame().identity().player().equals(obligation.binding().successorCharacterId())&&child.before().frame().episodeRunId().equals(obligation.binding().successorEpisodeRunId()),"event child changed its actual once/newactor/run/deadline source");
        var document=NaturalClockOriginals.decode(natural.readExact(publication.canonicalDomainRef()));require(document.pendingProjection().orElseThrow().eventIntent().orElseThrow().equals(entry.intent)&&entry.intent.originalRead().equals(entry.prepared.originalReadRef())&&entry.intent.instanceId()==entry.prepared.presentation().instanceId()&&entry.intent.sourceOriginals().equals(entry.prepared.sourceOriginals()),"event original window/instance/source lineage changed");
        require(Arrays.equals(natural.readExact(obligation.binding().qualifiedCause()),initial.cause().originalProof()),"event child lost the genuine current private M3 cause");
        EventActionPreparation.prepare(child);
    }
    private void requireDateChild(ContinuityStorePort.Session same,DateCurrent current,ActionCommand child)throws IOException {
        require(current.intent==actualDateIntent&&current.source==actualDateSource&&(actualDateReceipt==null||executing.get()==null)&&AdvancePlan.decode(actualDateCommand).exactOneDay(),"date source lacks genuine once intent/exact one-day original");
        require(child.before().frame().identity().player().equals(obligation.binding().successorCharacterId())&&child.before().frame().episodeRunId().equals(obligation.binding().successorEpisodeRunId())&&!child.deadline().isAfter(current.deadline()),"date child changed actual successor/run/finite source window");
        require(Arrays.equals(natural.readExact(actualDateIntent.command()),ActionCodec.encodeCommand(actualDateCommand))&&actualDateIntent.bodySha256().equals(ActionCodec.bodySha256(actualDateCommand)),"actual canonical once-date command differs");
        if(child.actionId().equals(actualDateCommand.actionId()))require(child.equals(actualDateCommand),"date top child differs from actual once command");
        else {require(AdvancePrimitives.supports(child.operation()),"date token cannot grant an unrelated native action");var parent=find(same,actualDateCommand.actionId());var execution=ActionTransitions.composite(parent.state()).orElseThrow(()->new IOException("actual registered date Life composite absent"));require(parent.command().equals(actualDateCommand)&&execution.children().size()<=3&&execution.children().contains(new CompositeExecution.Child(child.actionId(),ActionCodec.bodySha256(child))),"date primitive has no actual bounded same-Life canonical reservation");}
        var close=archive(same).loadReceipt(actualDateIntent.closeReceipt());verifyCloseControl(close,archive(same));
        require(close.equals(find(same,close.command().actionId()))&&actualDateIntent.materialClearance().equals(current.materialClearance())&&natural.currentCaptureDocument().equals(publication.canonicalDomainRef()),"date source lost actual Close/current canonical pending material");
    }
    public void requireCurrent(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token)throws IOException {
        if(token instanceof AdmittedPendingToken retained){require(Arrays.equals(ActionCodec.encodeCommand(retained.originalParent()),ActionCodec.encodeCommand(parent)),"historically admitted completion changed its actual original parent");retained.requireCurrent(same);return;}
        if(token instanceof CommittedPendingToken retained){require(retained.originalParent().equals(parent),"committed continuation changed its actual original parent");retained.requireCurrent(same);return;}
        require(token instanceof RootPendingUiRuntime.Current,"DATA token has no private installed Root issuer");var actual=(Current)token;
        require(actual.originalParent().equals(parent),"continuation changed original parent body");var call=continuationCall.get();var active=executing.get();
        if(call!=null&&call.original==actual&&call.parent.equals(parent)&&active!=null){require(active.retained==call.latest.retained&&active.state==call.latest.state,"actual same-call continuation did not retain its own canonical mutation lineage");active.requireCurrent(same);return;}
        actual.requireCurrent(same);
    }
    public LifecycleObservationPort.Snapshot requireRetainedOriginalFrame(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token)throws IOException {
        requireCurrent(parent,same,token);var original=initial.originalParentFrame();
        require(original!=null&&initial.originalParent().equals(parent),"genuine retained original parent snapshot is missing");
        var row=find(same,parent.actionId());var execution=ActionTransitions.composite(row.state()).orElseThrow(()->new IOException("original parent composite is missing"));
        var replay=RootLifecycleGuardEvidence.replay(execution.guard(),archive(same),same,context.originals());
        var retained=replay.original().actual();var expected=original.actual();
        require(replay.identity().equals(parent.lifecycleBefore())&&retained.session().equals(expected.session())&&retained.snapshotId().equals(expected.snapshotId())
                &&retained.nativeRevision().equals(expected.nativeRevision())&&retained.observedAt().equals(expected.observedAt())
                &&Arrays.equals(retained.originalPacket(),expected.originalPacket())&&Arrays.equals(retained.state().bytes(),expected.state().bytes())
                &&replay.semantic().equals(original.semantic())&&Arrays.equals(replay.original().facts().driver().encode(),original.facts().driver().encode()),
                "retained parent frame differs from its actual canonical entry guard");
        requireCurrent(parent,same,token);return original;
    }
    public void requireChild(ActionCommand parent,ContinuityStorePort.Session same,PendingToken token,ActionCommand child)throws IOException {
        require(!(token instanceof CommittedPendingToken)&&!(token instanceof AdmittedPendingToken),"an already-committed/admitted successor cannot authorize another Native child");
        requireCurrent(parent,same,token);var active=executing.get();var call=continuationCall.get();require(active!=null&&(active==token||call!=null&&call.original==token&&call.parent.equals(parent)&&active.retained==call.latest.retained&&active.state==call.latest.state),"child was not issued inside the actual same private continuation lineage");requireChild(same,assembler(),publication,parent,child);
    }
    public void requireCloseOrigin(ContinuityStorePort.Session same,ActionCommand command)throws IOException {
        var actual=executing.get();require(actual!=null,"Close requires the actual private same-parent continuation source");actual.requireMayExecute(same,command);
    }
    public NativeRequest prepareClose(ActionCommand command)throws IOException {
        var same=context.borrowedSession();var current=executing.get();require(current!=null,"Close provider lacks actual private source scope");current.requireMayExecute(same,command);
        var intent=obligation.closeAttempt().orElseThrow();var fields=StrictJson.object().put("expected_date_raw",intent.before().dateRaw()).put("expected_played_character_id",intent.before().actorCharacterId());
        var admission=withPhysical(current,lease->{var value=queryInside(current,lease);require(value.observation().state()==UiState.CLOSE_REQUIRED&&value.read().value().context().supportedCloseObserved(),"actual private preparation has no legal current Close");return archive(same).readReferenceOf(value.read().receipt());});
        var originalDomain=retain(same,natural.readExact(current.canonicalDomain()));
        return new NativeRequest(CLOSE.value(),Optional.empty(),new RawJson(StrictJson.canonical(fields)),List.of(originalDomain,obligation.binding().qualifiedCause(),obligation.observation().orElseThrow().timelineRead(),intent.originalCommand(),admission));
    }
    private Packet closePacket(ActionState.Attempt attempt,NativeActionPort.AckReceived ack)throws IOException {
        require(attempt.requestId().equals(ack.requestId()),"Close actual native request/result identity changed");var same=context.borrowedSession();var frame=RootGuardEvidence.loadFrame(attempt.guard(),archive(same),context.frameLoader());
        RootGuardEvidence.requireHistory(attempt.guard(),archive(same),same);
        return new Packet(natural.originalFrame(ack),ack.requestId(),RootNaturalSuccessionOriginals.frame(frame.semantic(),frame.identity().frame().identity().player().intValueExact()),NativeTimelineBlocker12004.Scene.fromSnapshot(OpportunityJson.toNode(frame.semantic())));
    }
    public ActionPorts.PostconditionResult observeClose(ActionCommand command,ActionState.Attempt attempt,NativeActionPort.DispatchOutcome dispatch) {
        try {
            var same=context.borrowedSession();var current=executing.get();boolean reconciliation=current==null;
            if(reconciliation){
                require(ActionReconciliationScope.activeFor(command),"Close observer lacks the actual private source or canonical read-only reconciliation scope");
                var basis=ActionReconciliationScope.requireObservationGuard(command,attempt);var until=ActionObservationWindow.deadline(command);if(basis.validUntil().isBefore(until))until=basis.validUntil();
                current=current(same,until).orElseThrow();var issuedClose=issued.get(command.actionId());var intent=current.state.closeAttempt().orElseThrow();
                require(issuedClose!=null&&issuedClose.child().equals(command)&&intent.actionId().equals(command.actionId())&&intent.commandBodySha256().equals(ActionCodec.bodySha256(command)),"reconciliation is not this actual privately issued once-Close");
            }else current.requireMayExecute(same,command);
            require(attempt.preparedRequest().step().equals(CLOSE.value())&&attempt.preparedRequest().requiredCapability().isEmpty()&&attempt.preparedRequest().preparationEvidence().size()==5,"actual Close request changed after durable INTENT");
            NativeActionPort.AckReceived ack;Optional<ReconciledControlAck> reconciled=Optional.empty();
            if(dispatch instanceof NativeActionPort.AckReceived received)ack=received;
            else if(reconciliation&&dispatch instanceof NativeActionPort.Unknown){
                var candidate=originalLateCloseAck(same,command,attempt,dispatch);
                if(candidate==null)return new ActionPorts.Pending("original once-Close remains UNKNOWN; no original ACK is currently available, no replay",List.of(archive(same).preserve(dispatch)));
                require(candidate.command.equals(command),"retained original Close ACK changed complete action body");
                if(candidate.original==null)candidate.original=archive(same).preserve(candidate.ack);
                if(candidate.retainedProof==null){var row=StrictJson.object().put("schema","xar.java.pending-close-original-ack/v1").put("machine_id",context.game().machineId()).put("observed_at_utc",ActionReconciliationScope.requireFrame(command,attempt).observedAt().toString()).put("action_id",command.actionId()).put("body_sha256",ActionCodec.bodySha256(command)).put("request_id",attempt.requestId());row.set("ack",candidate.original.toJson());candidate.retainedProof=retain(same,StrictJson.canonical(row));}
                var checked=new ReconciledControlAck(candidate.ack);checked.requireMatches(command,attempt,dispatch);ack=candidate.ack;reconciled=Optional.of(checked);
            }else return new ActionPorts.Pending("original once-Close result is unknown; retain without replay",List.of(archive(same).preserve(dispatch)));
            var packet=closePacket(attempt,ack);var beforeFrame=RootGuardEvidence.loadFrame(attempt.guard(),archive(same),context.frameLoader());
            var submitted=NativeTimelineBlocker12004.parseClose(natural.readExact(packet.original()),packet.original(),new NativeTimelineBlocker12004.BoundFrame(session(beforeFrame),packet.actualFrame(),packet.actualScene()),attempt.requestId());
            if(submitted.state()!=NativeTimelineBlocker12004.CloseState.SUBMITTED_PENDING)return new ActionPorts.Pending("native Close did not establish submitted-pending; retain exact original",retainedCloseAckEvidence(command,packet.original()));
            var initial=archive(same).loadRead(attempt.preparedRequest().preparationEvidence().get(4));var first=query.replay(initial);var sequence=first.sequence();var revision=first.observationRevision();var binding=submitted.binding();var reads=new ArrayList<PlanningReadReceipt>();var retainedReads=new ArrayList<CloseQueryOriginal>();closePostQueries.put(command.actionId(),retainedReads);
            for(int count=0;count<8;count++){
                var next=reconciliation?queryCloseReconciliation(current,command,attempt):query(current).read();var value=next.value();reads.add(next.receipt());retainedReads.add(new CloseQueryOriginal(next.receipt(),next.originalReceipt()));
                require(value.sequence().compareTo(sequence)>0&&value.observationRevision().compareTo(revision)>0,"actual post-Close query repeated/regressed");sequence=value.sequence();revision=value.observationRevision();binding=value.binding();
                var scenes=new ArrayList<PendingModalClearance.SceneQuery>();for(var original:reads)scenes.add(modalSceneQuery(original,true));
                if(PendingModalClearance.inspect(first,submitted,scenes).state()==NativeTimelineBlocker12004.ClearanceState.CLEARED_OBSERVED)return new ActionPorts.ControlObserved(new ActionState.ControlApplied(next.receipt(),reads.subList(0,reads.size()-1),CLOSE_OBSERVER,CLOSE_VALUES,reconciled));
            }
            return new ActionPorts.Pending("Close ACK retained but independent native clearance remains unresolved",retainedCloseAckEvidence(command,packet.original()));
        }catch(IOException|RuntimeException failure){var ack=lateCloseAcks.get(command.actionId());return new ActionPorts.Pending("actual once-Close original/postquery qualification unavailable: "+failure.getMessage(),retainedCloseAckEvidence(command,ack==null||ack.original==null?obligation.binding().qualifiedCause():ack.original));}
    }
    private PlanningReadResult.Known<NativeTimelineBlocker12004.Query> queryCloseReconciliation(Current current,ActionCommand command,ActionState.Attempt attempt)throws IOException {
        var same=context.borrowedSession();var identity=ActionReconciliationScope.requireIdentity(command,attempt);var complete=ActionReconciliationScope.requireFrame(command,attempt);
        return withPhysical(current,lease->{require(lease.ordinary().orElseThrow().equals(complete),"read-only Close query borrowed another actual physical snapshot");
            return natural.read(same,reconciliationQuery,new PlanningReadRequest(new CommandOrigin.Reconciliation(identity),complete.source(),complete.sessionId(),QUERY,EMPTY,current.deadline()));});
    }
    public void verifyCloseControl(ActionReceipt receipt,ActionPorts.OutcomeArchive originals)throws IOException {
        require(receipt.command().operation().equals(CLOSE)&&receipt.command().origin() instanceof CommandOrigin.Gameplay&&receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied,"actual generic gameplay Close control settlement required");
        var settled=(ActionState.Settled)receipt.state();var actual=(ActionState.ControlApplied)settled.settlement();var acknowledgement=ActionEffects.controlAcknowledgement(receipt.command(),settled.attempt(),settled.dispatch(),actual);
        var prepared=settled.attempt().preparedRequest();require(prepared.preparationEvidence().size()==5,"Close needs exact retained source/once/query originals");
        var document=NaturalClockOriginals.decode(natural.readExact(prepared.preparationEvidence().get(0)));var pending=document.pendingProjection().orElseThrow();var state=SuccessorUiObligationCodec.decode(natural.readExact(pending.currentObligation()));var intent=state.closeAttempt().orElseThrow();
        require(intent.actionId().equals(receipt.command().actionId())&&intent.commandBodySha256().equals(receipt.bodySha256())&&intent.receipt().isEmpty()&&intent.originalCommand().equals(prepared.preparationEvidence().get(3))
                &&state.binding().qualifiedCause().equals(prepared.preparationEvidence().get(1))&&state.observation().orElseThrow().timelineRead().equals(prepared.preparationEvidence().get(2)),"archived Close replaced canonical once intent/cause/query");
        var first=query.replay(originals.loadRead(prepared.preparationEvidence().get(4)));require(first.context().supportedCloseObserved(),"actual archived preparation did not observe a legal Close");var packet=closePacket(settled.attempt(),acknowledgement);var frame=RootGuardEvidence.loadFrame(settled.attempt().guard(),originals,context.frameLoader());
        var submitted=NativeTimelineBlocker12004.parseClose(natural.readExact(packet.original()),packet.original(),new NativeTimelineBlocker12004.BoundFrame(session(frame),packet.actualFrame(),packet.actualScene()),packet.requestId());
        var scenes=new ArrayList<PendingModalClearance.SceneQuery>();
        var all=new ArrayList<>(actual.supportingReads());all.add(actual.read());require(all.size()>0&&all.size()<=8&&actual.observerSchema().equals(CLOSE_OBSERVER)&&actual.actual().equals(CLOSE_VALUES),"Close strict bounded control contract changed");
        for(var read:all)scenes.add(modalSceneQuery(read));
        require(PendingModalClearance.inspect(first,submitted,scenes).state()==NativeTimelineBlocker12004.ClearanceState.CLEARED_OBSERVED,"Close settlement lacks original independent source-bound modal clearance");
    }
    /** Incorporate only the central settlement of the identical retained UNKNOWN. This method never submits or polls. */
    private Current retainCanonicalCloseReconciliation(Current current)throws IOException {
        var same=context.borrowedSession();
        if(current.state.closeAttempt().isPresent()&&current.state.closeAttempt().orElseThrow().receipt().isEmpty()) {
            var intent=current.state.closeAttempt().orElseThrow();var actual=find(same,intent.actionId());var original=issued.get(intent.actionId());
            require(original!=null&&original.child().equals(actual.command())&&actual.bodySha256().equals(intent.commandBodySha256()),"missing Close result has no identical privately retained canonical once child");
            Optional<ExactRef> clearance=Optional.empty();if(actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied){verifyCloseControl(actual,archive(same));clearance=Optional.of(archive(same).preserveReceipt(actual));}
            var frame=withPhysical(current,RootPendingUiRuntime::mutationFrame);
            current=mutate(current,new DriverPendingEpisodeSource.RetainResult(new CloseReceipt(actual.outcome(),archive(same).preserveReceipt(actual),clearance,Optional.empty(),Optional.empty())),frame);
        }
        var retained=current.state.closeAttempt().flatMap(CloseAttempt::receipt);
        if(retained.isEmpty()||retained.orElseThrow().outcome()!=ActionReceipt.Outcome.UNRESOLVED)return current;
        var original=retained.orElseThrow();if(original.reconciliation().isPresent())return current;
        var old=archive(same).loadReceipt(original.canonicalReceipt());var actual=find(same,old.command().actionId());
        if(!actual.settled())return current;
        require(old.state() instanceof ActionState.Unknown&&old.command().equals(actual.command())&&old.bodySha256().equals(actual.bodySha256())
                &&actual.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied,"retained UNKNOWN did not become the same canonical Close control");
        var unknown=(ActionState.Unknown)old.state();var settled=(ActionState.Settled)actual.state();
        require(unknown.attempt().equals(Optional.of(settled.attempt()))&&unknown.dispatch().equals(Optional.of(settled.dispatch())),"read-only reconciliation replaced the original attempt/UNKNOWN dispatch");
        verifyCloseControl(actual,archive(same));var confirmed=archive(same).preserveReceipt(actual);
        var material=withPhysical(current,RootPendingUiRuntime::mutationFrame);
        var proof=StrictJson.object().put("schema","xar.java.pending-close-read-only-reconciliation/v1").put("machine_id",context.game().machineId())
                .put("observed_at_utc",material.observedAt().toString()).put("action_id",actual.command().actionId()).put("body_sha256",actual.bodySha256()).put("request_id",settled.attempt().requestId());
        proof.set("original_unknown_receipt",original.canonicalReceipt().toJson());proof.set("confirmed_receipt",confirmed.toJson());proof.set("canonical_pending_domain",current.canonicalDomain().toJson());
        proof.set("qualified_cause",current.state.binding().qualifiedCause().toJson());var preparation=proof.putArray("original_preparation");settled.attempt().preparedRequest().preparationEvidence().forEach(value->preparation.add(value.toJson()));
        var reconciliation=new ReadOnlyReconciliation(original.canonicalReceipt(),confirmed,retain(same,StrictJson.canonical(proof)),Optional.of(confirmed),Optional.empty());
        return mutate(current,new DriverPendingEpisodeSource.Reconcile(reconciliation),material);
    }
    private DriverPendingEpisodeSource.Change retainDateChange(CloseReceipt close,ExactRef original) {
        if(close.reconciliation().isPresent()) {
            var prior=close.reconciliation().orElseThrow();return new DriverPendingEpisodeSource.Reconcile(new ReadOnlyReconciliation(prior.originalUnknownReceipt(),prior.confirmedReceipt(),prior.sameOriginalActionProof(),prior.materialClearance(),Optional.of(original)));
        }
        return new DriverPendingEpisodeSource.RetainPostconditions(new CloseReceipt(close.outcome(),close.canonicalReceipt(),close.materialClearance(),Optional.of(original),Optional.empty()));
    }
    public Preparation resumeOutcome(ActionCommand parent,PendingToken supplied,CompositeActionPort.Children children)throws IOException,InterruptedException {
        require(!(supplied instanceof CommittedPendingToken)&&!(supplied instanceof AdmittedPendingToken),"retained committed/admitted lifecycle cannot repeat the final business or metadata producer");
        require(continuationCall.get()==null,"nested pending continuation forbidden");requireCurrent(parent,context.borrowedSession(),supplied);var actual=(Current)supplied;
        continuationCall.set(new ContinuationCall(parent,actual));try{return resumeInside(parent,supplied,children);}finally{continuationCall.remove();}
    }
    private Preparation resumeInside(ActionCommand parent,PendingToken supplied,CompositeActionPort.Children children)throws IOException,InterruptedException {
        var same=context.borrowedSession();requireCurrent(parent,same,supplied);var current=(Current)supplied;
        if(completed!=null){requireFinalized(parent,same,completed);return new PendingFinalized(completed);}
        current=retainCanonicalCloseReconciliation(current);
        current=retainCanonicalDateResult(current);
        var fresh=query(current);
        // A public modal Close may retain and observe its own result, but it cannot choose an
        // event that appeared after that Close. The ordinary pending turn owns that decision.
        if(publicRequest.get()!=null&&(supplied instanceof EventCurrent||fresh.observation().state()==UiState.PLAYER_DECISION_PENDING))
            return new PendingPreparation(mutate(current,new DriverPendingEpisodeSource.Observe(fresh.observation()),fresh.physical()));
        if(supplied instanceof EventCurrent event)return executeEvent(parent,event,children);
        if(fresh.observation().state()==UiState.PLAYER_DECISION_PENDING)return prepareEvent(current,fresh,children);
        if(fresh.observation().state()==UiState.CLEAR&&current.state.closeAttempt().isEmpty())return finalizeClear(current,fresh);
        if(current.state.closeAttempt().flatMap(CloseAttempt::receipt).flatMap(CloseReceipt::effectiveDateAdvance).isPresent()&&fresh.observation().state()==UiState.CLEAR)return finalizeClear(current,fresh);
        if(supplied instanceof DateCurrent){actualDateSource=new PendingDateSource(current);return advanceDate(parent,new DateCurrent(current,actualDateSource),children);}
        current=mutate(current,new DriverPendingEpisodeSource.Observe(fresh.observation()),fresh.physical());
        if(current.state.closeCanBeConsidered()) {
            // Build the exact central child ID/body before committing its durable once intent; no native action has occurred yet.
            var beforeClose=query(current);var command=closeCommand(current,children.nextActionId(),beforeClose);
            var intent=new CloseAttempt(command.actionId(),ActionCodec.bodySha256(command),retain(same,ActionCodec.encodeCommand(command)),beforeClose.observation().frame(),beforeClose.observation().frame().observedAtUtc(),Optional.empty());
            // The Close-enter source uses the already retained actual observation. Publish it separately, then reacquire its exact frame before EnterClose.
            current=mutate(current,new DriverPendingEpisodeSource.Observe(beforeClose.observation()),beforeClose.physical());
            var qualified=query(current);command=closeCommand(current,command.actionId(),qualified);
            // EnterClose.before must be the exact observation already retained; its frame remains the original independent query, never a requested before substitute.
            intent=new CloseAttempt(command.actionId(),ActionCodec.bodySha256(command),retain(same,ActionCodec.encodeCommand(command)),current.state.observation().orElseThrow().frame(),qualified.observation().frame().observedAtUtc(),Optional.empty());
            current=mutate(current,new DriverPendingEpisodeSource.EnterClose(intent),qualified.physical());
            require(executing.get()==null&&issued.size()<4096,"nested/unbounded same-parent UI continuation forbidden");
            require(issued.putIfAbsent(command.actionId(),new Issued(current,command))==null,"actual once child was already issued");executing.set(current);
            ActionReceipt receipt;
            try{var exact=command;receipt=assembler().withPendingEpisodeChildScope(same,publication,parent,exact,()->submitRetainingCanonicalResult(children,exact));}
            finally{executing.remove();}
            require(receipt.command().equals(command)&&receipt.equals(find(same,command.actionId())),"Close result is not the actual sole canonical child receipt");
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied){completedChild=command;qualifiedAfterChild=assembler().requirePendingEpisodeChildCurrent(same,publication,parent,command);}
            var after=current(same,supplied.deadline()).orElseThrow();var frame=withPhysical(after,RootPendingUiRuntime::mutationFrame);
            var original=archive(same).preserveReceipt(receipt);Optional<ExactRef> clearance=Optional.empty();
            if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied){verifyCloseControl(receipt,archive(same));clearance=Optional.of(original);}
            current=mutate(after,new DriverPendingEpisodeSource.RetainResult(new CloseReceipt(receipt.outcome(),original,clearance,Optional.empty(),Optional.empty())),frame);
        }
        // A subsequent DATE continuation prepares its exact command using that call's actual fresh deadline.
        return new PendingPreparation(current);
    }
    private DateCurrent prepareDateIntent(Current current,CompositeActionPort.Children children)throws IOException {
            var same=context.borrowedSession();var entry=query(current);require(entry.observation().state()==UiState.CLEAR,"a pending player decision/modal must be handled before the formal date child");
            var source=new PendingDateSource(current);var command=lifecycle.life().commands().preparePendingUiDateAdvance(source,children.nextActionId(),current.deadline());
            var date=new NaturalClockOriginals.DateIntent(command.actionId(),ActionCodec.bodySha256(command),retain(same,ActionCodec.encodeCommand(command)),current.actualCloseReceipt(),current.materialClearance(),entry.observation().frame().observedAtUtc(),actualDateIntent==null?Optional.empty():Optional.of(retain(same,natural.readExact(current.canonicalDomain()))),actualDateReceipt==null?Optional.empty():Optional.of(archive(same).preserveReceipt(actualDateReceipt)));
            require(enteringDate.get()==null,"nested once-date intent forbidden");enteringDate.set(date);
            try{
                var after=mutate(current,new DriverPendingEpisodeSource.Observe(entry.observation()),entry.physical());actualDateIntent=date;actualDateCommand=command;actualDateReceipt=null;actualDateSource=new PendingDateSource(after);
                var rebuilt=lifecycle.life().commands().preparePendingUiDateAdvance(actualDateSource,command.actionId(),command.deadline());
                require(Arrays.equals(ActionCodec.encodeCommand(command),ActionCodec.encodeCommand(rebuilt))&&date.bodySha256().equals(ActionCodec.bodySha256(rebuilt)),"actual post-intent Driver/frame changed the original one-day command; zero submit, originals retained");
                return new DateCurrent(after,actualDateSource);
            }
            finally{enteringDate.remove();}
    }
    private Preparation prepareEvent(Current current,Queried fresh,CompositeActionPort.Children children)throws IOException {
        var same=context.borrowedSession();
        if(latestEvent!=null&&latestEvent.intent.originalReceipt().isPresent()) {
            var original=archive(same).loadReceipt(latestEvent.intent.originalReceipt().orElseThrow());var canonical=find(same,original.command().actionId());
            if(!canonical.settled())return new PendingPreparation(current);
        }
        var source=new PendingEventSource(current);EventActionPreparation.PendingPrepared prepared;
        try{prepared=events().preparePendingUiEvent(same,source,children.nextActionId(),current.deadline());}
        catch(EventActionPreparation.PendingSelectionRejected denied){
            require(source.lastData!=null&&source.lastPhysical!=null,"rejected event selection lost its actual private read/source");
            var diagnosis=StrictJson.object().put("schema","xar.java.pending-ui-selection-diagnosis/v1").put("machine_id",context.game().machineId()).put("observed_at_utc",source.lastData.full().actual().observedAt().toString());
            diagnosis.set("original_read",denied.originalRead().toJson());diagnosis.set("diagnosis",retain(same,DriverJson.encode(denied.diagnosis())).toJson());diagnosis.set("canonical_pending_domain",current.canonicalDomain().toJson());diagnosis.set("qualified_cause",current.state.binding().qualifiedCause().toJson());
            enteringEventDiagnosis.set(retain(same,StrictJson.canonical(diagnosis)));try{return new PendingPreparation(mutate(current,new DriverPendingEpisodeSource.Observe(fresh.observation()),source.lastPhysical));}finally{enteringEventDiagnosis.remove();}}
        require(source.lastData!=null&&source.lastPhysical!=null,"event preparation lost its actual private full-frame callback");
        if(latestEvent!=null&&latestEvent.intent.instanceId()==prepared.presentation().instanceId()&&latestEvent.intent.interaction()==(prepared.presentation() instanceof EventActionPreparation.InteractionPresentation))return new PendingPreparation(current);
        var previous=latestEvent==null?Optional.<ExactRef>empty():Optional.of(retain(same,NaturalClockOriginals.encodeEventIntent(latestEvent.intent)));
        var intent=new NaturalClockOriginals.EventIntent(context.game().machineId(),latestEvent==null?1:Math.addExact(latestEvent.intent.ordinal(),1),prepared.command().actionId(),ActionCodec.bodySha256(prepared.command()),retain(same,ActionCodec.encodeCommand(prepared.command())),prepared.originalReadRef(),prepared.presentation().instanceId(),prepared.presentation() instanceof EventActionPreparation.InteractionPresentation,prepared.sourceOriginals(),previous,Optional.empty(),Optional.empty(),source.lastData.full().actual().observedAt());
        var entry=new EventEntry(current,source.lastData.known(),prepared,intent);require(enteringEvent.get()==null,"nested once-event import forbidden");enteringEvent.set(intent);Current after;
        try{after=mutate(current,new DriverPendingEpisodeSource.Observe(fresh.observation()),source.lastPhysical);entry.entered=mutation;}
        finally{enteringEvent.remove();}
        require(eventEntries.putIfAbsent(intent.actionId(),entry)==null,"once event action ID was already issued");latestEvent=entry;entry.source=new PendingEventSource(after);
        var check=events().preparePendingUiEvent(same,entry.source,prepared.command().actionId(),prepared.command().deadline());entry.source.checkedFresh=check.command();events().requirePendingUiEventCurrent(same,entry.source,prepared,check);
        return new PendingPreparation(new EventCurrent(after,entry));
    }
    private Preparation executeEvent(ActionCommand parent,EventCurrent current,CompositeActionPort.Children children)throws IOException {
        var same=context.borrowedSession();var entry=current.entry;require(entry.intent.originalReceipt().isEmpty()&&executing.get()==null,"event already has an original result; no replay");
        ActionReceipt receipt;if(issued.containsKey(entry.prepared.command().actionId()))receipt=find(same,entry.prepared.command().actionId());
        else {require(issued.putIfAbsent(entry.prepared.command().actionId(),new Issued(current,entry.prepared.command()))==null,"once-event child was already issued");executing.set(current);
            try{receipt=assembler().withPendingEpisodeChildScope(same,publication,parent,entry.prepared.command(),()->events().withPendingEventSource(same,entry.source,()->submitRetainingCanonicalResult(children,entry.prepared.command())));}
            finally{executing.remove();}}
        require(receipt.command().equals(entry.prepared.command())&&receipt.equals(find(same,receipt.command().actionId())),"event result differs from its actual canonical child");
        if(receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED&&!incorporatedChildren.contains(receipt.command().actionId())){completedChild=receipt.command();qualifiedAfterChild=assembler().requirePendingEpisodeChildCurrent(same,publication,parent,receipt.command());}
        var actual=current(same,current.deadline()).orElseThrow();var fresh=query(actual);var original=archive(same).preserveReceipt(receipt);
        var next=new NaturalClockOriginals.EventIntent(entry.intent.machineId(),entry.intent.ordinal(),entry.intent.actionId(),entry.intent.bodySha256(),entry.intent.command(),entry.intent.originalRead(),entry.intent.instanceId(),entry.intent.interaction(),entry.intent.sourceOriginals(),entry.intent.previous(),Optional.of(original),Optional.empty(),entry.intent.observedAtUtc());
        enteringEvent.set(next);Current after;try{after=mutate(actual,new DriverPendingEpisodeSource.Observe(fresh.observation()),fresh.physical());entry.intent=next;}finally{enteringEvent.remove();}
        return new PendingPreparation(after);
    }
    private Preparation advanceDate(ActionCommand parent,DateCurrent current,CompositeActionPort.Children children)throws IOException,InterruptedException {
        var prepared=actualDateIntent==null||settledZeroDate()?prepareDateIntent(current,children):current;
        return advancePreparedDate(parent,prepared,children);
    }
    private Preparation advancePreparedDate(ActionCommand parent,DateCurrent current,CompositeActionPort.Children children)throws IOException,InterruptedException {
        var same=context.borrowedSession();require(actualDateIntent!=null&&actualDateReceipt==null&&executing.get()==null,"actual once-date continuation absent or already returned");
        ActionReceipt receipt;if(issued.containsKey(actualDateCommand.actionId()))receipt=find(same,actualDateCommand.actionId());
        else {require(issued.putIfAbsent(actualDateCommand.actionId(),new Issued(current,actualDateCommand))==null,"once-date child already issued; only read-only canonical reconciliation is legal");executing.set(current);
            try{receipt=assembler().withPendingEpisodeChildScope(same,publication,parent,actualDateCommand,()->lifecycle.life().pendingUiScope().within(current.source,()->submitRetainingCanonicalResult(children,actualDateCommand)));}
            finally{executing.remove();}}
        require(receipt.command().equals(actualDateCommand)&&receipt.equals(find(same,actualDateCommand.actionId())),"date result is not the sole actual canonical child original");
        archive(same).preserveReceipt(receipt);actualDateReceipt=receipt;
        if(!receipt.settled())return new PendingPreparation(current);
        completedChild=actualDateCommand;qualifiedAfterChild=assembler().requirePendingEpisodeChildCurrent(same,publication,parent,actualDateCommand);
        var after=current(same,current.deadline()).orElseThrow();if(settledZeroDate())return new PendingPreparation(after);var original=verifyDate(receipt,after);var close=after.state.closeAttempt().orElseThrow().receipt().orElseThrow();
        var material=withPhysical(after,RootPendingUiRuntime::mutationFrame);
        var result=mutate(after,retainDateChange(close,original),material);
        return new PendingPreparation(result);
    }
    private boolean settledZeroDate()throws IOException {
        if(actualDateReceipt==null||!actualDateReceipt.settled())return false;
        var same=context.borrowedSession();require(actualDateReceipt.equals(find(same,actualDateCommand.actionId())),"zero-date result differs from the actual canonical child");
        var recorded=lifecycle.life().replay().readRecorded(actualDateReceipt,archive(same));
        return recorded.starting().identity().frame().identity().dateRaw().equals(recorded.ending().identity().frame().identity().dateRaw());
    }
    private Current retainCanonicalDateResult(Current current)throws IOException {
        if(actualDateReceipt==null)return current;var same=context.borrowedSession();var canonical=find(same,actualDateCommand.actionId());
        if(!canonical.settled())return current;
        require(canonical.command().equals(actualDateReceipt.command()),"date reconciliation changed its original body");archive(same).preserveReceipt(actualDateReceipt);actualDateReceipt=canonical;
        if(settledZeroDate()||current.state.closeAttempt().flatMap(CloseAttempt::receipt).flatMap(CloseReceipt::effectiveDateAdvance).isPresent())return current;
        var original=verifyDate(canonical,current);var material=withPhysical(current,RootPendingUiRuntime::mutationFrame);return mutate(current,retainDateChange(current.state.closeAttempt().orElseThrow().receipt().orElseThrow(),original),material);
    }
    private ExactRef verifyDate(ActionReceipt receipt,Current current)throws IOException {
        var same=context.borrowedSession();require(actualDateCommand!=null&&receipt.command().equals(actualDateCommand)&&receipt.equals(find(same,actualDateCommand.actionId()))&&receipt.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,"date proof lacks an actual canonical applied Life child");
        var recorded=lifecycle.life().replay().readRecorded(receipt,archive(same));var start=recorded.starting().identity();var end=recorded.ending().identity();
        var advanced=end.frame().identity().dateRaw().subtract(start.frame().identity().dateRaw());
        require(AdvancePlan.decode(receipt.command()).exactOneDay()&&advanced.signum()>0&&advanced.compareTo(BigInteger.valueOf(24))<=0&&end.frame().identity().player().equals(current.state.binding().successorCharacterId())&&end.frame().episodeRunId().equals(current.state.binding().successorEpisodeRunId()),"actual bounded Life proof lacks a positive date advance for this living successor");
        require(start.frame().identity().dateRaw().compareTo(current.state.closeAttempt().orElseThrow().before().dateRaw())>=0,"date proof preceded the actual Close frame");
        return archive(same).preserveReceipt(receipt);
    }
    private static final class FinalScope {
        final Current current;final RootLifecycleAuthority.SnapshotLease lease;final Queried timeline;final ExactRef root;
        final RootPendingNaturalSuccessionQualification.FinalOriginals originals;RootPendingNaturalSuccessionQualification.Finalized finalized;
        RootPendingNaturalSuccessionQualification.ReconnectedCause connection;
        FinalScope(Current current,RootLifecycleAuthority.SnapshotLease lease,Queried timeline,ExactRef root,RootPendingNaturalSuccessionQualification.FinalOriginals originals){this.current=current;this.lease=lease;this.timeline=timeline;this.root=root;this.originals=originals;}
    }
    /** Private historical custody. A current source guard remains real; no closed snapshot lease is revived. */
    private final class RetainedFinalScope implements RootPendingNaturalSuccessionQualification.RetainedFinalEvidence {
        final ContinuityStorePort.Session same;final WriterContracts.Head head;final RootNaturalSuccessionOriginals.InitialCause original;
        final DriverObservationAssembler.FullSnapshot current,before;final Known actualKnown;final RecordedStage stage;
        final Optional<LifecycleComposites.RecordedPendingEpisode> lifecycleMetadata;
        final org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source;
        final ExactRef proofReference;final RootPendingNaturalSuccessionQualification.FinalProofDocument proof;
        final RootPendingNaturalSuccessionQualification.RetainedFinalizationOriginals originals;
        final Map<ExactRef,PlanningReadReceipt> modalReads=new LinkedHashMap<>();
        RootPendingNaturalSuccessionQualification.RetainedFinalized qualified;RetainedMutation replayed;
        final RootPendingNaturalSuccessionQualification.ReconnectedCause connection;
        RootPendingNaturalSuccessionQualification.ReconnectedFinalized reconnectedQualified;
        boolean qualified(){return qualified!=null||reconnectedQualified!=null;}
        byte[] qualifiedProof(){return reconnectedQualified==null?qualified.originalProof():reconnectedQualified.originalProof();}
        RootPendingNaturalSuccessionQualification.PendingCause actualCause(){return connection==null?original.cause():connection.historicalCause();}
        RetainedFinalScope(FinalRecoveryInputs inputs,RecordedStage stage,SuccessorUiObligation after)throws IOException {
            this.same=inputs.same();this.head=inputs.head();this.original=inputs.original();this.current=inputs.physical().fullSnapshot();
            this.connection=openingReconnected.get();
            this.actualKnown=inputs.physical().factsKnown();this.source=inputs.physical().sourceQualification();this.stage=stage;
            this.lifecycleMetadata=inputs.lifecycle();
            var finalization=after.finalization().orElseThrow(()->new IOException("retained FINALIZE has no original finalization"));proofReference=finalization.finalM3Proof();
            proof=RootPendingNaturalSuccessionQualification.decodeFinalProof(natural.readExact(proofReference));
            require(proof.actualOrdinarySnapshot().equals(((DriverPendingEpisodeSource.MutationMetadata)stage.metadata()).beforeNative())
                    &&Arrays.equals(natural.readExact(proof.originalKnown()),natural.readExact(stage.metadata().beforeKnown())),"retained final Known/native differs from its actual canonical import");
            before=retainedFinalFrame(proof,stage.before());
            if(lifecycleMetadata.isPresent()) {
                var edge=lifecycleMetadata.orElseThrow();edge.requirePublishedCurrent(same);
                requireSameKnown(stage.after(),retainedKnown(edge.beforeKnownOriginal(),edge.beforeNativeOriginal()));
                require(Arrays.equals(stage.after().driver().encode(),actualKnown.driver().encode()),"final metadata changed the already-published business Driver");
            } else requireSameKnown(stage.after(),actualKnown);
            var previous=recordedStage(same,pendingMetadataReference(stage.before()),stage.before());
            require(previous.committed().canonicalEvent().equals(proof.pendingContinueReceipt())&&previous.originalSource().equals(proof.canonicalPublication())
                    &&Arrays.equals(natural.readExact(proof.pendingContinueDriver()),stage.before().driver().encode()),"retained final proof changed its real predecessor publication/Driver");
            var materials=new RootPendingNaturalSuccessionQualification.FinalMaterials(natural.requireRetainedRoot(same,proof.currentRootRead()),proof.currentRootRead(),
                    proof.originalKnown(),proof.originalSemantic(),stage.before(),proof.actualObservation());
            NativeRecordedEvidenceVerifier.requireRead(materials.currentRootRead(),archive(same));
            for(var guard:List.of(materials.currentRootRead().before().binding(),materials.currentRootRead().after().binding())) {
                RootGuardEvidence.requireHistory(guard,archive(same),same);RootGuardEvidence.loadFrame(guard,archive(same),context.frameLoader());
                require(RootGuardEvidence.sourceQualification(guard,archive(same)).equals(proof.sourceQualification()),"retained final ROOT read lost its original same-scope source qualification");
            }
            var last=archive(same).loadRead(after.observation().orElseThrow().timelineRead());var first=packet(last);
            Optional<Packet> close=Optional.empty(),afterDate=Optional.empty();var post=new ArrayList<Packet>();
            if(proof.close().isPresent()) {
                var receipt=archive(same).loadReceipt(finalization.actualCloseReceipt().orElseThrow());verifyCloseControl(receipt,archive(same));
                require(receipt.equals(find(same,receipt.command().actionId())),"retained final Close is not the actual canonical original");
                var settled=(ActionState.Settled)receipt.state();var control=(ActionState.ControlApplied)settled.settlement();
                first=packet(archive(same).loadRead(settled.attempt().preparedRequest().preparationEvidence().get(4)));
                close=Optional.of(closePacket(settled.attempt(),ActionEffects.controlAcknowledgement(receipt.command(),settled.attempt(),settled.dispatch(),control)));
                var reads=new ArrayList<>(control.supportingReads());reads.add(control.read());
                for(var read:reads){var packet=packet(read);post.add(packet);modalReads.put(packet.original(),read);}
                var advance=archive(same).loadReceipt(proof.verifiedDateAdvance().orElseThrow());
                require(advance.equals(find(same,advance.command().actionId()))&&AdvancePlan.decode(advance.command()).exactOneDay(),"retained final date proof has no exact canonical one-day child");
                var parent=find(same,original.originalParent().actionId());require(ActionTransitions.composite(parent.state()).orElseThrow().children().contains(new CompositeExecution.Child(advance.command().actionId(),advance.bodySha256())),"retained final date has no original parent reservation");
                var date=lifecycle.life().replay().readRecorded(advance,archive(same));
                var advanced=date.ending().identity().frame().identity().dateRaw().subtract(date.starting().identity().frame().identity().dateRaw());
                require(date.ending().identity().frame().episodeRunId().equals(before.facts().driver().session().episodeRunId())
                        &&date.ending().identity().frame().identity().player().equals(before.facts().driver().session().actorId())
                        &&advanced.signum()>0&&advanced.compareTo(BigInteger.valueOf(24))<=0
                        &&date.starting().identity().frame().identity().dateRaw().compareTo(after.closeAttempt().orElseThrow().before().dateRaw())>=0,
                        "retained final date proof changed its actual successor episode or positive advance");
                afterDate=Optional.of(packet(last));
            }
            require(first.original().equals(proof.initialTimeline())&&close.map(Packet::original).equals(proof.close())
                    &&post.stream().map(Packet::original).toList().equals(proof.postqueries())&&afterDate.map(Packet::original).equals(proof.finalTimelineAfterDateAdvance()),
                    "retained final proof changed the original independent timeline/Close/date read chain");
            var session=before.actual().session();var game=new G2RetainedNativeSourceProvider.GameIdentity(session.game().pid(),session.game().creationFiletime().value().toString());
            var retainedSession=new G2RetainedNativeSourceProvider.Session(session.machineId(),session.sessionId(),game,before.facts().driver().session().episodeRunId(),session.connectionGeneration().toString(),executable,executableFileId,executableMtimeNs);
            var originals=new RootPendingNaturalSuccessionQualification.FinalOriginals(retainedSession,RootNaturalSuccessionOriginals.frame(before.semantic(),before.facts().driver().session().actorId().intValueExact()),
                    first,close,post,proof.currentRoot(),proof.pendingContinueReceipt(),proof.pendingContinueDriver(),proof.canonicalPublication(),proof.verifiedDateAdvance(),afterDate,materials);
            var canonical=lifecycleMetadata.map(edge->new RootPendingNaturalSuccessionQualification.CanonicalLifecycle(edge.eventPin().reference(),edge.proof()));
            this.originals=new RootPendingNaturalSuccessionQualification.RetainedFinalizationOriginals(before,stage.committed().predecessor(),proof.sourceQualification(),originals,this,stage.metadata().canonicalDomain(),canonical);
        }
        @Override public byte[] readExact(ExactRef reference)throws IOException {
            require(reference.equals(proofReference)||proof.materialReferences().contains(reference),"historical final reader is outside the exact typed original closure");return natural.readExact(reference);
        }
        @Override public PendingModalClearance.SceneQuery openQualifiedModalQuery(Packet original,ContinuityStorePort.Session borrowed)throws IOException {
            require(borrowed==same,"historical modal read escaped its actual writer session");var receipt=modalReads.get(original.original());
            require(receipt!=null&&packet(receipt).equals(original),"historical modal packet was not the original canonical Close support read");return modalSceneQuery(receipt);
        }
    }
    private DriverObservationAssembler.FullSnapshot retainedFinalFrame(RootPendingNaturalSuccessionQualification.FinalProofDocument proof,Known known)throws IOException {
        var manifest=RawJson.fullMaterial(natural.readExact(proof.actualObservation()));
        var actual=DriverObservationEvidenceReader.nativeFrame(proof.actualObservation(),manifest,natural.readExact(proof.actualOrdinarySnapshot()));
        var driver=DriverObservationEvidenceReader.currentDriverReference(proof.actualObservation(),manifest);
        var facts=DriverObservationEvidenceReader.decode(proof.actualObservation(),manifest,RawJson.fullMaterial(natural.readExact(driver)),actual);
        require(Arrays.equals(facts.driver().encode(),known.driver().encode())&&facts.driverVersion()==known.stamp().driverVersion()&&facts.episodeEpoch()==known.stamp().episodeEpoch(),"actual final observation differs from its complete original Driver/stamp");
        var full=new DriverObservationAssembler().projectFull(actual,facts,proof.actualOrdinarySnapshot());
        require(Arrays.equals(DriverJson.encode(full.semantic()),natural.readExact(proof.originalSemantic())),"retained final full semantic differs from the actual sole projection");return full;
    }
    private DriverPendingEpisodeSource.Finalize retainedFinalChange(RecordedStage stage,SuccessorUiObligation after)throws IOException {
        var inputs=finalRecoveryInputs.get();require(inputs!=null&&openingRetainedFinal.get()==null,"retained final DATA has no actual private cause/current physical recovery scope");
        var scope=new RetainedFinalScope(inputs,stage,after);openingRetainedFinal.set(scope);
        try{if(scope.connection==null)scope.qualified=qualification.qualifyRetainedFinalization(inputs.original().cause(),scope.proofReference,scope.current,inputs.same(),scope.source,inputs.head());
            else scope.reconnectedQualified=qualification.qualifyRetainedFinalizationReconnected(scope.connection,scope.proofReference,scope.current,inputs.same(),scope.source,inputs.head());}
        finally{openingRetainedFinal.remove();}
        require(scope.qualified()&&Arrays.equals(scope.qualifiedProof(),natural.readExact(scope.proofReference)),"retained finalization was not privately requalified from identical original bytes");
        retainedFinalScope=scope;return new DriverPendingEpisodeSource.Finalize(after.finalization().orElseThrow(),after.observation().orElseThrow(),scope.before,new RawJson(inputs.original().matchedEstate().wire()),stage.metadata().observedAtUtc());
    }
    private void requireRetainedScopeCurrent(RetainedFinalScope scope)throws IOException {
        if(scope.reconnectedQualified==null)qualification.requireRetainedFinalizedCurrent(scope.qualified,scope.current,scope.same,scope.source,scope.head);
        else qualification.requireReconnectedFinalizedCurrent(scope.reconnectedQualified,scope.current,scope.same,scope.source,scope.head);
    }
    @Override public RootPendingNaturalSuccessionQualification.RetainedFinalizationOriginals openRetainedQualified(RootPendingNaturalSuccessionQualification.PendingCause cause,ExactRef proof,
            DriverObservationAssembler.FullSnapshot current,ContinuityStorePort.Session same,org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source,WriterContracts.Head head)throws IOException {
        var scope=openingRetainedFinal.get();if(scope==null)scope=retainedFinalScope;
        require(scope!=null&&scope.actualCause()==cause&&scope.proofReference.equals(proof)&&scope.current==current&&scope.source==source&&scope.same==same&&scope.head.digest().equals(head.digest()),"historical final DATA has no identical private Root issuer");
        requireRetainedCurrent(scope.originals,cause,proof,current,same,source,head);return scope.originals;
    }
    @Override public void requireRetainedCurrent(RootPendingNaturalSuccessionQualification.RetainedFinalizationOriginals originals,RootPendingNaturalSuccessionQualification.PendingCause cause,ExactRef proof,
            DriverObservationAssembler.FullSnapshot current,ContinuityStorePort.Session same,org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source,WriterContracts.Head head)throws IOException {
        var scope=openingRetainedFinal.get();if(scope==null)scope=retainedFinalScope;
        require(scope!=null&&scope.originals==originals&&scope.actualCause()==cause&&scope.current==current&&scope.source==source&&scope.proofReference.equals(proof)
                &&scope.same==same&&scope.head.digest().equals(head.digest())&&head.digest().equals(same.head().digest()),"retained final scope/source/head changed");
        context.writer().requireSession(same);source.assertCurrent(same);requireRetainedSource(same,scope.proof.sourceQualification(),source);
        var edge=scope.stage.committed();var actual=same.requireHistoricalImport(edge.body().slot(),edge.receipt().head().sequence(),ContinuityJson.digest(edge.receipt().head().toJson()));
        require(actual.body().equals(edge.body())&&actual.canonicalEvent().equals(edge.canonicalEvent())&&Arrays.equals(actual.request().producerInput(),NaturalClockOriginals.encode(scope.stage.document()))
                &&actual.request().evidence().equals(natural.computedArtifacts(scope.stage.document())),"historical final canonical import changed");
        for(var pin:actual.currentInputs())same.verifyPin(pin);
        if(scope.lifecycleMetadata.isPresent())scope.lifecycleMetadata.orElseThrow().requirePublishedCurrent(same);
        final Known expectedKnown=scope.actualKnown;
        assembler().withFrozenFacts(same,frozen->{require(frozen.state() instanceof Known,"retained final current Known missing");requireSameKnown(expectedKnown,(Known)frozen.state());return null;});
        for(var reference:scope.proof.materialReferences())natural.readExact(reference);source.assertCurrent(same);
    }
    private ExactRef publicationEvent(ContinuityStorePort.Session same,WriterContracts.Receipt receipt)throws IOException {
        String name=String.format(java.util.Locale.ROOT,"%08d.json",receipt.head().sequence());
        var pin=same.head().documents().stream().filter(value->java.nio.file.Path.of(value.reference().path()).getFileName().toString().equals(name)).findFirst().orElseThrow(()->new IOException("actual canonical Pending publication event pin missing"));
        same.verifyPin(pin);var original=StrictJson.parse(same.readPinned(pin,org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES),org.xar.ck3.control.continuity.ContinuityJson.DOCUMENT_MAX_BYTES);
        require(receipt.eventIdentity().equals(StrictJson.text(original.get("identity"))),"Pending publication receipt/event identity differs");same.verifyPin(pin);return pin.reference();
    }
    private Packet packet(PlanningReadResult.Known<NativeTimelineBlocker12004.Query> value)throws IOException {
        return packet(value.receipt());
    }
    private Packet packet(PlanningReadReceipt receipt)throws IOException {
        var value=replayTimeline(receipt);var same=context.borrowedSession();var originals=archive(same);var frame=receipt.request().origin() instanceof CommandOrigin.Reconciliation?context.reconciliation().verifyArchived(receipt.after().binding(),originals,same,context.originals()):RootGuardEvidence.loadFrame(receipt.after().binding(),originals,context.frameLoader());
        var packet=new Packet(natural.originalFrame(receipt.original()),receipt.requestId(),RootNaturalSuccessionOriginals.frame(frame.semantic(),frame.identity().frame().identity().player().intValueExact()),value.binding().scene());modalQueryOriginals.put(packet.original(),receipt);return packet;
    }
    private PendingModalClearance.SceneQuery modalSceneQuery(PlanningReadReceipt receipt)throws IOException {
        return modalSceneQuery(receipt,false);
    }
    private PendingModalClearance.SceneQuery modalSceneQuery(PlanningReadReceipt receipt,boolean retainActualRead)throws IOException {
        var value=replayTimeline(receipt);var same=context.borrowedSession();var originals=archive(same);
        var complete=receipt.request().origin() instanceof CommandOrigin.Reconciliation?context.reconciliation().verifyArchived(receipt.after().binding(),originals,same,context.originals()):RootGuardEvidence.loadFrame(receipt.after().binding(),originals,context.frameLoader());
        var semantic=DriverJson.encode(complete.semantic());var material=RawJson.fullMaterial(semantic);
        var reference=retainActualRead?originals.preserveMaterial(material):originals.materialReferenceOf(material);
        require(originals.loadFullMaterial(reference).equals(material),"actual modal semantic original is missing or changed; archived replay cannot repair it");
        return PendingModalClearance.capture(value,originals.readReferenceOf(receipt),reference,complete.originalEvidence(),semantic,complete.observedAt());
    }
    @Override public PendingModalClearance.SceneQuery openQualifiedModalQuery(Packet original,ContinuityStorePort.Session same)throws IOException {
        var scope=finalizing.get();require(scope!=null&&same==context.borrowedSession(),"modal Scene DATA lacks the actual final Root private source scope");scope.current.requireCurrent(same);scope.lease.assertCurrent(same);
        require(scope.originals.postqueries().contains(original)||scope.originals.initialTimeline().equals(original)||scope.originals.finalTimelineAfterDateAdvance().equals(Optional.of(original)),"modal query was not retained by this actual same finalization");
        var receipt=modalQueryOriginals.get(original.original());require(receipt!=null&&packet(receipt).equals(original),"modal query replaced its original actual read/guard/frame/Scene");return modalSceneQuery(receipt);
    }
    private record FinalMaterial(FinalScope scope,Finalization value,DriverPendingEpisodeSource.Finalize change,MutationFrame physical) { }
    private Preparation finalizeClear(Current current,Queried observed)throws IOException {
        require(observed.observation().state()==UiState.CLEAR,"finalization requires the actual independently cleared native UI");
        var same=context.borrowedSession();var prepared=withPhysical(current,lease->{
            var last=queryInside(current,lease);require(last.observation().state()==UiState.CLEAR,"native UI clearance changed before final qualification");
            var frame=lease.ordinary().orElseThrow();var contract=natural.campaignRootContract();
            var root=natural.read(same,contract,new PlanningReadRequest(new CommandOrigin.Gameplay(frame.identity()),frame.source(),frame.sessionId(),contract.operation(),FinanceReadContracts.rootArguments(FinanceReadContracts.RootCapture.INTERNAL_PRECLOCK_ORIGINALS),current.deadline()));
            var raw=root.receipt().original().originalResultToken().orElseThrow(()->new IOException("actual current native ROOT result absent"));var rootRef=retain(same,raw.bytes());
            var first=packet(last.read());Optional<Packet> closePacket=Optional.empty();var postqueries=new ArrayList<Packet>();Optional<ExactRef> date=Optional.empty();Optional<Packet> afterDate=Optional.empty();
            if(current.state.closeAttempt().isPresent()) {
                var retained=current.state.closeAttempt().orElseThrow().receipt().orElseThrow();var receipt=archive(same).loadReceipt(retained.effectiveReceipt());verifyCloseControl(receipt,archive(same));
                require(actualDateReceipt!=null&&retained.effectiveDateAdvance().equals(Optional.of(verifyDate(actualDateReceipt,current))),"final source lacks the actual original one-day canonical Life proof");
                var settled=(ActionState.Settled)receipt.state();var control=(ActionState.ControlApplied)settled.settlement();
                var admission=archive(same).loadRead(settled.attempt().preparedRequest().preparationEvidence().get(4));first=packet(admission);
                closePacket=Optional.of(closePacket(settled.attempt(),ActionEffects.controlAcknowledgement(receipt.command(),settled.attempt(),settled.dispatch(),control)));
                var reads=new ArrayList<>(control.supportingReads());reads.add(control.read());for(var value:reads)postqueries.add(packet(value));
                date=retained.effectiveDateAdvance();afterDate=Optional.of(packet(last.read()));
            }
            var finalMaterials=new RootPendingNaturalSuccessionQualification.FinalMaterials(root.receipt(),archive(same).readReferenceOf(root.receipt()),
                    archive(same).preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(lease.factsKnown())),archive(same).preserveMaterial(RawJson.fullMaterial(DriverJson.encode(lease.fullSnapshot().semantic()))),
                    lease.factsKnown(),lease.fullSnapshot().facts().semanticFactsEvidence());
            var originals=new RootPendingNaturalSuccessionQualification.FinalOriginals(session(frame),RootNaturalSuccessionOriginals.frame(frame.semantic(),frame.identity().frame().identity().player().intValueExact()),first,closePacket,postqueries,rootRef,publicationEvent(same,publication.actualReceipt()),current.actualPublishedDriver(),publication.originalSource(),date,afterDate,finalMaterials);
            var scope=new FinalScope(current,lease,last,rootRef,originals);require(finalizing.get()==null,"nested final qualification forbidden");finalizing.set(scope);
            scope.connection=openingReconnected.get();
            try{scope.finalized=scope.connection==null?qualification.finalizeAfterPendingContinue(initial.cause(),lease.fullSnapshot(),same,lease.sourceQualification(),same.head()):
                    qualification.finalizeAfterReconnectedPendingContinue(scope.connection,lease.fullSnapshot(),same,lease.sourceQualification(),same.head());}
            finally{finalizing.remove();}
            var proof=retain(same,scope.finalized.originalProof());var finalization=new Finalization(initial.cause().causeDigest(),proof,last.observation().frame(),current.state.closeAttempt().map(value->value.receipt().orElseThrow().effectiveReceipt()),date,lease.fullSnapshot().actual().observedAt(),scope.finalized.continuityBinding());
            var change=new DriverPendingEpisodeSource.Finalize(finalization,last.observation(),lease.fullSnapshot(),new RawJson(initial.matchedEstate().wire()),lease.fullSnapshot().actual().observedAt());
            return continuity.seal(new FinalMaterial(scope,finalization,change,mutationFrame(lease)));
        });
        var material=prepared.value();
        finalizing.set(material.scope());Current result;
        try{result=continuity.withPrepared(prepared,()->{
            var scope=material.scope();
            if(scope.connection!=null)qualification.requireReconnectedFinalCurrent(scope.connection,scope.finalized,scope.lease.fullSnapshot(),same,scope.lease.sourceQualification(),same.head());
            return mutate(current,material.change(),material.physical());
        });}finally{finalizing.remove();}
        var published=withPhysical(result,lease->lease.fullSnapshot());
        require(published.actual().snapshotId().equals(material.scope().lease.fullSnapshot().actual().snapshotId())&&published.actual().nativeRevision().equals(material.scope().lease.fullSnapshot().actual().nativeRevision()),"native frame changed during final business CAS; original final proof retained without false completion");
        completed=new FinalTokenImpl(result,material,publication.before(),publication.after(),published,mutation);
        return new PendingFinalized(completed);
    }
    @Override public RootPendingNaturalSuccessionQualification.FinalOriginals openQualified(RootPendingNaturalSuccessionQualification.PendingCause cause,
            DriverObservationAssembler.FullSnapshot current,ContinuityStorePort.Session same,org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source,WriterContracts.Head head)throws IOException {
        var scope=finalizing.get();require(scope!=null&&cause==(scope.connection==null?initial.cause():scope.connection.historicalCause())&&scope.current.retained==publication&&scope.lease.fullSnapshot()==current&&scope.lease.sourceQualification()==source&&same==context.borrowedSession()&&head.digest().equals(same.head().digest()),"final DATA lacks actual private Root cause/current physical publication scope");
        scope.current.requireCurrent(same);continuity.requireCurrentFrame(same,current,source,head);
        // Both branches retain a real canonical receipt; cold capture has no warm Prepared to reconstruct.
        WriterContracts.Receipt initialReceipt;
        if(initial instanceof DriverPendingEpisodeSource.Capture warm)initialReceipt=warm.actualReceipt();
        else if(initial instanceof DriverPendingEpisodeSource.RecordedCapture recorded)initialReceipt=recorded.recordedImport().receipt();
        else throw new IOException("actual initial pending source has no original warm or recorded canonical receipt");
        same.requireHistoricalState(initialReceipt.head().sequence(),org.xar.ck3.control.continuity.ContinuityJson.digest(initialReceipt.head().toJson()));
        require(Arrays.equals(natural.readExact(scope.current.actualPublishedDriver()),scope.lease.factsKnown().driver().encode())&&Arrays.equals(natural.readExact(scope.current.state.binding().qualifiedCause()),cause.originalProof()),"final current Driver/cause originals differ");
        return scope.originals;
    }
    @Override public void requireCurrent(RootPendingNaturalSuccessionQualification.PendingCause cause,DriverObservationAssembler.FullSnapshot current,
            ContinuityStorePort.Session same,org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification source,WriterContracts.Head head,RootPendingNaturalSuccessionQualification.FinalOriginals original)throws IOException {
        require(openQualified(cause,current,same,source,head)==original,"final source changed its actual retained original objects");
    }
    private final class FinalTokenImpl implements FinalToken {
        private final Current current;private final FinalMaterial material;private final Known before,after;private final DriverObservationAssembler.FullSnapshot frame;private final MutationCapture capture;
        private FinalTokenImpl(Current current,FinalMaterial material,Known before,Known after,DriverObservationAssembler.FullSnapshot frame,MutationCapture capture){this.current=current;this.material=material;this.before=before;this.after=after;this.frame=frame;this.capture=capture;}
        @Override public ActionCommand originalParent(){return current.originalParent();}
        @Override public Instant deadline(){return current.deadline();}
        @Override public CompositeContinuationToken.Kind kind(){return current.kind();}
        @Override public SuccessorUiObligation obligation(){return current.obligation();}
        @Override public ExactRef canonicalDomain(){return current.canonicalDomain();}
        @Override public ExactRef actualPublishedDriver(){return capture.preparedProjection().afterDriver();}
        @Override public ExactRef canonicalPublicationProof(){return current.canonicalPublicationProof();}
        @Override public List<ExactRef> evidence(){var refs=new LinkedHashSet<>(List.of(canonicalDomain(),actualPublishedDriver(),canonicalPublicationProof(),m3FinalizationProof(),obligation().binding().qualifiedCause()));refs.addAll(RootPendingNaturalSuccessionQualification.decodeFinalProof(material.scope().finalized.originalProof()).materialReferences());return List.copyOf(refs);}
        @Override public LifecycleReducer.Reduction finalReduction(){return new LifecycleReducer.Reduction(capture.preparedProjection().projection().driver(),capture.preparedProjection().projection().auxiliary(),capture.preparedProjection().projection().result().orElseThrow().bytes());}
        @Override public Known beforeFinal(){return before;}
        @Override public Known publishedFinal(){return after;}
        @Override public DriverObservationAssembler.FullSnapshot qualifiedFinalFrame(){return frame;}
        @Override public RawJson matchedEstate(){return material.change().matchedEstate();}
        @Override public ExactRef m3FinalizationProof(){return material.value().finalM3Proof();}
        @Override public WriterContracts.Receipt finalizationReceipt(){return capture.actualReceipt();}
        @Override public ExactRef canonicalFinalizationDomain(){return capture.canonicalDomainRef();}
    }
    private final class RetainedFinalTokenImpl implements FinalToken {
        private Current current;private RetainedFinalScope scope;
        private RetainedFinalTokenImpl(Current current,RetainedFinalScope scope){this.current=current;this.scope=scope;require(scope.qualified()&&scope.replayed!=null,"retained final token requires genuine M3 and canonical pure replay");}
        @Override public ActionCommand originalParent(){return current.originalParent();}
        @Override public Instant deadline(){return current.deadline();}
        @Override public CompositeContinuationToken.Kind kind(){return current.kind();}
        @Override public SuccessorUiObligation obligation(){return current.obligation();}
        @Override public ExactRef canonicalDomain(){return current.canonicalDomain();}
        @Override public ExactRef actualPublishedDriver(){return scope.replayed.preparedProjection().afterDriver();}
        @Override public ExactRef canonicalPublicationProof(){return current.canonicalPublicationProof();}
        @Override public List<ExactRef> evidence(){var refs=new LinkedHashSet<>(List.of(canonicalDomain(),actualPublishedDriver(),canonicalPublicationProof(),m3FinalizationProof(),obligation().binding().qualifiedCause()));refs.addAll(scope.proof.materialReferences());return List.copyOf(refs);}
        @Override public LifecycleReducer.Reduction finalReduction(){var value=scope.replayed.preparedProjection().projection();return new LifecycleReducer.Reduction(value.driver(),value.auxiliary(),value.result().orElseThrow().bytes());}
        @Override public Known beforeFinal(){return scope.stage.before();}
        @Override public Known publishedFinal(){return current.actualKnown();}
        @Override public DriverObservationAssembler.FullSnapshot qualifiedFinalFrame(){return scope.current;}
        @Override public RawJson matchedEstate(){return ((DriverPendingEpisodeSource.Finalize)scope.replayed.change()).matchedEstate();}
        @Override public ExactRef m3FinalizationProof(){return scope.proofReference;}
        @Override public WriterContracts.Receipt finalizationReceipt(){return scope.stage.committed().receipt();}
        @Override public ExactRef canonicalFinalizationDomain(){return scope.stage.metadata().canonicalDomain();}
    }
    /** Actual paired SAVE/LOAD retires only the completed old issuer; no old child, Driver CAS or auxiliary deletion. */
    private boolean retireRestoredFinalized(ContinuityStorePort.Session same,Instant deadline)throws IOException {
        requireDriverContext();context.writer().requireSession(same);
        if(restoredFinalized!=null){requireRestoredFinalizedCurrent(same,restoredFinalized);
            require(initial==null&&publication==null,"following terminal pending publication is unresolved; completed retirement cannot report it clear");return true;}
        var marker=finalizedMarker(same);if(marker.isEmpty())return false;
        var state=marker.orElseThrow();var binding=state.binding();
        if(binding.predecessor().game().equals(context.game().generation()))return false;
        require(initial==null&&publication==null&&admittedRecovery==null&&committedRecovery==null&&transported==null,
                "new-Game completed retirement cannot replace an active pending issuer");
        var origin=context.requireRestoredOrigin(same);var evidence=origin.evidence();
        var original=context.restorationOriginal(same);var material=original.material();var saved=material.savedDriver();
        require(evidence.savedOwner().equals(material.session())&&!evidence.savedOwner().game().equals(context.game().generation())
                &&evidence.restoredOwner().equals(new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId()))
                &&evidence.source().equals(context.source())&&evidence.pair().equals(material.pair())
                &&evidence.materialWitness().equals(material.witness())&&evidence.originalSavedHeadDigest().equals(material.originalHeadDigest())
                &&original.game().equals(context.game().generation())&&original.semantic().equals(evidence.originalRestoredSemantic()),
                "completed retirement needs the actual private replacement and identical original paired SAVE");
        require(saved.session().actorId().equals(binding.successorCharacterId())&&saved.session().episodeRunId().equals(binding.successorEpisodeRunId())
                &&evidence.pair().frame().frame().identity().player().equals(binding.successorCharacterId())
                &&evidence.pair().frame().frame().episodeRunId().equals(binding.successorEpisodeRunId()),
                "completed SAVE belongs to another successor actor or episode");
        var parent=find(same,binding.parentActionId());
        require(parent.command().lifecycleBefore().sameGuardFrame(binding.predecessor())
                &&ActionCodec.bodySha256(parent.command()).equals(binding.parentBodySha256())
                &&parent.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied,
                "UNKNOWN or unfinished original Continue cannot retire across a restored Game");
        var proof=((ActionState.LifecycleApplied)((ActionState.CompositeSettled)parent.state()).settlement()).proof();proof.validateParent(parent.command());
        require(proof.kind()==LifecycleTransitionProof.Kind.CONTINUE_SUCCESSOR
                &&proof.originalEvidence().contains(state.finalization().orElseThrow().finalM3Proof()),
                "completed retirement lost its actual finalized M3 and canonical lifecycle parent");
        var savedSemantic=DriverJson.object(natural.readExact(material.sourceSemantic().semantic()),DriverJson.MAX_NATIVE_BYTES);
        var restoredSemantic=DriverJson.object(natural.readExact(evidence.originalRestoredSemantic().semantic()),DriverJson.MAX_NATIVE_BYTES);
        require(restoredMarker(savedSemantic).equals(state)&&restoredMarker(restoredSemantic).equals(state),
                "completed UI marker must come from the identical saved and actually restored full SEM");
        var restored=DriverStateSnapshot.decodeComplete(natural.readExact(evidence.originalRestoredSemantic().originalDriver()));
        require(sameRetainedSlot(saved.campaignGoal(),restored.campaignGoal())&&sameRetainedSlot(saved.successionLifecycle(),restored.successionLifecycle()),
                "actual completed restoration changed the original campaign goal or lifecycle");
        var savedDate=evidence.pair().frame().frame().identity().dateRaw();
        requireRestoredClear(savedSemantic,binding.successorCharacterId(),savedDate);
        requireRestoredClear(restoredSemantic,binding.successorCharacterId(),savedDate);
        var retained=new RestoredFinalized(origin,state,parent);
        lifecycle.physical().withSnapshot(same,deadline,lease->{
            lease.assertCurrent(same);var full=lease.fullSnapshot();var known=lease.factsKnown();
            require(full.actual().session().game().equals(context.game().generation())&&full.actual().session().sessionId().equals(context.game().sessionId())
                    &&full.actual().session().connectionGeneration().toString().equals(evidence.restoredConnectionGeneration())
                    &&known.driver().session().actorId().equals(binding.successorCharacterId())
                    &&known.driver().session().episodeRunId().equals(binding.successorEpisodeRunId())
                    &&sameRetainedSlot(saved.campaignGoal(),known.driver().campaignGoal())
                    &&sameRetainedSlot(saved.successionLifecycle(),known.driver().successionLifecycle())
                    &&restoredMarker(known.auxiliary()).equals(state),
                    "current held completed successor differs from its actual restored Driver and original goal");
            requireRestoredClear(full.semantic(),binding.successorCharacterId(),savedDate);
            lease.assertCurrent(same);return null;
        });
        restoredFinalized=retained;return true;
    }
    private static SuccessorUiObligation restoredMarker(OpportunityJson.Obj original){
        var state=SuccessorUiObligationCodec.decode(DriverJson.encode(Objects.requireNonNull(original.get(SuccessorUiObligation.AUXILIARY_KEY),"actual restored UI marker missing")));
        require(state.phase()==Phase.FINALIZED,"only actual FINALIZED UI material can retire");return state;
    }
    private static boolean sameRetainedSlot(DriverStateSnapshot.Slot first,DriverStateSnapshot.Slot second){
        if(first instanceof DriverStateSnapshot.Value a&&second instanceof DriverStateSnapshot.Value b)
            return StrictJson.parse(a.json(),DriverJson.MAX_NATIVE_BYTES).equals(StrictJson.parse(b.json(),DriverJson.MAX_NATIVE_BYTES));
        return first.getClass()==second.getClass();
    }
    private static void requireRestoredClear(OpportunityJson.Obj semantic,BigInteger actor,BigInteger date){
        var player=OpportunityJson.object(semantic.get("played_character"),"actual completed restored player");
        require(OpportunityJson.bool(semantic.get("paused"),"actual paused")&&OpportunityJson.bool(semantic.get("map_ready"),"actual map ready")
                &&OpportunityJson.bool(player.get("alive"),"actual alive")&&OpportunityJson.integer(player.get("character_id"),"actual restored actor").equals(actor)
                &&OpportunityJson.integer(semantic.get("date_raw"),"actual restored date").equals(date)
                &&semantic.get("active_event")==OpportunityJson.Nil.INSTANCE&&semantic.get("pending_character_interaction")==OpportunityJson.Nil.INSTANCE
                &&semantic.get("one_life_terminal_reason")==OpportunityJson.Nil.INSTANCE,
                "completed restoration requires its actual paused living clear native checkpoint frame");
    }
    /** Later ordinary turns may advance, change goals, or reach the next terminal; retirement grants no live Native permission. */
    private void requireRestoredFinalizedCurrent(ContinuityStorePort.Session same,RestoredFinalized retained)throws IOException {
        require(context.requireRestoredOrigin(same)==retained.origin(),"completed restored issuer changed its actual private origin");
        require(find(same,retained.state().binding().parentActionId()).equals(retained.parent()),
                "completed restored parent changed its original settled result; UNKNOWN cannot acquire retirement");
        assembler().withFrozenFacts(same,frozen->{
            require(frozen.state() instanceof Known,"actual restored successor Driver facts unavailable");var known=(Known)frozen.state();var binding=retained.state().binding();
            require(restoredMarker(known.auxiliary()).equals(retained.state())
                    &&known.driver().session().actorId().equals(binding.successorCharacterId())
                    &&known.driver().session().episodeRunId().equals(binding.successorEpisodeRunId()),
                    "completed retirement changed its original marker or actual successor Driver binding");return null;
        });
    }
    private Optional<SuccessorUiObligation> finalizedMarker(ContinuityStorePort.Session same)throws IOException {
        return assembler().withFrozenFacts(same,frozen->{if(!(frozen.state() instanceof Known known))return Optional.empty();
            var value=known.auxiliary().members().get(SuccessorUiObligation.AUXILIARY_KEY);if(value==null)return Optional.empty();
            var state=SuccessorUiObligationCodec.decode(DriverJson.encode(value));return state.phase()==SuccessorUiObligation.Phase.FINALIZED?Optional.of(state):Optional.empty();});
    }
    /** Later READ/BATCH recovery requires a real historical Cycle admission and an independent current binding. */
    public Optional<LifecycleEpisodeInputs.CurrentAdoptionBinding> admittedCurrent(ContinuityStorePort.Session same,ActionReceipt exactParent,Instant deadline)throws IOException {
        if(retireRestoredFinalized(same,deadline))return Optional.empty();
        if(transported!=null)return admittedTransportedCurrent(same,exactParent,transported,deadline);
        requireDriverContext();context.writer().requireSession(same);var marker=finalizedMarker(same);if(marker.isEmpty())return Optional.empty();
        var state=marker.orElseThrow();if(!state.binding().parentActionId().equals(exactParent.command().actionId()))return Optional.empty();
        require(state.binding().parentBodySha256().equals(ActionCodec.bodySha256(exactParent.command()))
                &&exactParent.command().lifecycleBefore().sameGuardFrame(state.binding().predecessor()),"finalized marker changed its actual old lifecycle parent/body");
        if(!(exactParent.state() instanceof ActionState.CompositeSettled settled&&settled.settlement() instanceof ActionState.LifecycleApplied))return Optional.empty();
        var physical=context.transport().latestObservedSnapshot();var originalTransport=state.binding().predecessor();
        boolean fresh=originalTransport.game().equals(context.game().generation())&&(!originalTransport.sessionId().equals(context.game().sessionId())
                ||physical.filter(value->!value.session().connectionGeneration().equals(originalTransport.connectionGeneration())).isPresent());
        if(fresh){
            installTransportContinuity(same);var root=context.core().sessionAccess().current();
            try{var ticket=transportJournal.rebindTransport(same,root.identity(),exactParent.command(),deadline);return admittedTransportedCurrent(same,exactParent,ticket,deadline);}
            catch(InterruptedException interrupted){Thread.currentThread().interrupt();var failure=new java.io.InterruptedIOException("actual current transport admission interrupted");failure.initCause(interrupted);throw failure;}
        }
        var qualified=admittedQualification().bind(same,exactParent,deadline);if(qualified.isEmpty())return Optional.empty();
        var actual=qualified.orElseThrow();
        if(admittedRecovery==null)admittedRecovery=new AdmittedRecovery(actual,state);else {
            require(admittedRecovery.state.equals(state)&&admittedRecovery.actual.parent().command().actionId().equals(exactParent.command().actionId()),"actual historical admission cannot replace another pending episode");admittedRecovery.actual=actual;
        }
        obligation=state;return Optional.of(actual);
    }
    /** New transport history and the present physical observation are independently qualified. */
    public Optional<LifecycleEpisodeInputs.CurrentAdoptionBinding> admittedTransportedCurrent(ContinuityStorePort.Session same,ActionReceipt exactParent,
            ContinuityBatchJournal.ReboundTransport prior,Instant deadline)throws IOException {
        installTransportContinuity(same);transportJournal.requireHistoricalTransport(same,prior);
        require(Arrays.equals(ActionCodec.encodeCommand(prior.parent()),ActionCodec.encodeCommand(exactParent.command())),"transported admission changed its original complete parent");
        var marker=finalizedMarker(same);if(marker.isEmpty())return Optional.empty();var state=marker.orElseThrow();
        require(state.binding().parentActionId().equals(exactParent.command().actionId())&&exactParent.outcome()==ActionReceipt.Outcome.APPLIED_CONFIRMED,
                "transported admission needs its actual finalized canonical parent");
        // The pending ticket predates Close/date/final metadata. The actual Journal alone
        // creates or reopens the zero-credit finalized origin before capturing current again.
        final ContinuityBatchJournal.ReboundTransport latest;
        try{latest=transportJournal.rebindTransport(same,prior.owner(),exactParent.command(),deadline);}
        catch(InterruptedException interrupted){Thread.currentThread().interrupt();var failure=new java.io.InterruptedIOException("actual finalized transport admission interrupted");failure.initCause(interrupted);throw failure;}
        transported=latest;
        var bound=withTransportedAdmittedPhysical(same,exactParent,latest,deadline,(actual,held)->actual);
        if(bound.isPresent()){
            var actual=bound.orElseThrow();if(admittedRecovery==null)admittedRecovery=new AdmittedRecovery(actual,state);
            else{require(admittedRecovery.state.equals(state),"transported admission cannot replace another finalized obligation");admittedRecovery.actual=actual;}
            obligation=state;
        }
        return bound;
    }
    private <T>Optional<T> withTransportedAdmittedPhysical(ContinuityStorePort.Session same,ActionReceipt parent,
            ContinuityBatchJournal.ReboundTransport ticket,Instant deadline,RootPendingUiAdmittedEpisodeQualification.CurrentWork<T> work)throws IOException {
        return lifecycle.physical().withSnapshot(same,deadline,lease->continuity.withLease(same,lease,()->{
            var state=finalizedMarker(same).orElseThrow(()->new IOException("transported final marker missing"));
            var custody=qualification.qualifyRetainedCauseReconnected(state.binding().qualifiedCause(),lease.fullSnapshot(),same,lease.sourceQualification(),same.head());
            require(custody.purpose()==RootPendingNaturalSuccessionQualification.ContinuityPurpose.FINALIZED_METADATA_ONLY,
                    "transported current must use actual finalized metadata custody");
            var value=admittedQualification().withTransportedCurrent(same,parent,ticket,lease,work);
            qualification.requireReconnectedCauseCurrent(custody,lease.fullSnapshot(),same,lease.sourceQualification(),same.head());return value;
        }));
    }
    /** Exposes the identical real producer only after its own opaque current binding has been revalidated. */
    public LifecycleEpisodeInputs requireAdmittedCurrentProducer(ContinuityStorePort.Session same,LifecycleEpisodeInputs.CurrentAdoptionBinding identical)throws IOException {
        requireDriverContext();return admittedQualification().requireCurrentProducer(same,identical);
    }
    private boolean tryAdmittedRecovery(ContinuityStorePort.Session same,Instant deadline)throws IOException {
        var marker=finalizedMarker(same);if(marker.isEmpty())return false;
        var parent=find(same,marker.orElseThrow().binding().parentActionId());return admittedCurrent(same,parent,deadline).isPresent();
    }
    private final class AdmittedRecovery {
        LifecycleEpisodeInputs.CurrentAdoptionBinding actual;final SuccessorUiObligation state;
        AdmittedRecovery(LifecycleEpisodeInputs.CurrentAdoptionBinding actual,SuccessorUiObligation state){this.actual=actual;this.state=state;}
    }
    private void refreshAdmittedRecovery(ContinuityStorePort.Session same,Instant deadline)throws IOException {
        var retained=admittedRecovery;require(retained!=null,"actual historically admitted episode source is absent");
        var parent=find(same,retained.actual.parent().command().actionId());
        require((transported==null?admittedCurrent(same,parent,deadline):admittedTransportedCurrent(same,parent,transported,deadline)).isPresent(),"actual historical adoption/current qualification is missing");
    }
    private <T>T withAdmittedPhysical(ContinuityStorePort.Session same,Instant deadline,RootPendingUiAdmittedEpisodeQualification.CurrentWork<T> work)throws IOException {
        var retained=admittedRecovery;require(retained!=null,"actual historical episode/current physical source is absent");
        if(transported!=null)return withTransportedAdmittedPhysical(same,find(same,retained.actual.parent().command().actionId()),transported,deadline,(actual,held)->{
            require(finalizedMarker(same).filter(retained.state::equals).isPresent(),"transported current finalized marker changed");retained.actual=actual;return work.run(actual,held);
        }).orElseThrow(()->new IOException("transported current admission is unavailable"));
        return admittedQualification().withCurrent(same,find(same,retained.actual.parent().command().actionId()),deadline,(actual,held)->{
            require(finalizedMarker(same).filter(retained.state::equals).isPresent(),"historically admitted current episode marker changed");
            retained.actual=actual;return work.run(actual,held);
        }).orElseThrow(()->new IOException("actual canonical Cycle admission is absent; historical DATA cannot qualify the current episode"));
    }
    /** Completion-only carrier for an already settled parent; it never provides a Native child source. */
    private final class AdmittedPendingToken implements PendingToken {
        final AdmittedRecovery retained;final Instant limit;
        AdmittedPendingToken(AdmittedRecovery retained,Instant limit){this.retained=retained;this.limit=limit;}
        @Override public ActionCommand originalParent(){return retained.actual.parent().command();}
        @Override public Instant deadline(){return limit;}
        @Override public CompositeContinuationToken.Kind kind(){return CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE;}
        @Override public SuccessorUiObligation obligation(){return retained.state;}
        private com.fasterxml.jackson.databind.JsonNode originalFinalization(){return retained.actual.recorded().publication().detailsObject().get("delta").get("pending_ui_finalization");}
        @Override public ExactRef canonicalDomain(){return ExactRef.fromJson(originalFinalization().get("canonical_finalization_domain"));}
        @Override public ExactRef actualPublishedDriver(){return retained.actual.semantic().originalDriver();}
        @Override public ExactRef canonicalPublicationProof(){return ExactRef.fromJson(originalFinalization().get("canonical_pending_publication_proof"));}
        @Override public List<ExactRef> evidence(){return List.of(canonicalDomain(),actualPublishedDriver(),canonicalPublicationProof(),retained.state.binding().qualifiedCause(),retained.actual.recorded().publication().committedDocuments().get(0).reference());}
        void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            require(admittedRecovery==retained&&context.clock().instant().isBefore(limit),"historically admitted completion lost its private source or finite window");
            refreshAdmittedRecovery(same,limit);retained.actual.requireCurrent(same);
        }
    }
    private final class CommittedRecovery {
        final LifecycleComposites.RecordedPendingEpisode edge;final ExactRef originalDriver;
        RetainedFinalScope scope;Instant deadline;
        CommittedRecovery(LifecycleComposites.RecordedPendingEpisode edge,RetainedFinalScope scope,ExactRef originalDriver) {
            this.edge=edge;this.scope=scope;this.originalDriver=originalDriver;
            require(scope.qualified()&&scope.replayed!=null&&scope.lifecycleMetadata.orElseThrow()==edge,"committed DATA has no actual private M3/reducer custody");
        }
    }
    /** Private completion carrier. It cannot expose a Native child scope or pretend to be a pending publication. */
    private final class CommittedPendingToken implements PendingToken {
        final CommittedRecovery retained;final Instant limit;
        CommittedPendingToken(CommittedRecovery retained,Instant limit){this.retained=retained;this.limit=limit;}
        @Override public ActionCommand originalParent(){return retained.scope.original.originalParent();}
        @Override public Instant deadline(){return limit;}
        @Override public CompositeContinuationToken.Kind kind(){return CompositeContinuationToken.Kind.SUCCESSOR_UI_CLOSE;}
        @Override public SuccessorUiObligation obligation(){return obligation;}
        @Override public ExactRef canonicalDomain(){return retained.scope.stage.metadata().canonicalDomain();}
        @Override public ExactRef actualPublishedDriver(){return retained.originalDriver;}
        @Override public ExactRef canonicalPublicationProof(){return retained.scope.stage.originalSource();}
        @Override public List<ExactRef> evidence(){return List.of(canonicalDomain(),actualPublishedDriver(),canonicalPublicationProof(),retained.scope.proofReference,retained.edge.eventPin().reference());}
        void requireCurrent(ContinuityStorePort.Session same)throws IOException {
            require(committedRecovery==retained&&initial==retained.scope.original&&context.clock().instant().isBefore(limit),"committed completion carrier lost its actual private issuer or finite caller window");
            refreshCommittedRecovery(same,limit);requireCommittedPendingEpisode(find(same,originalParent().actionId()),same,retained.edge);
        }
    }
    private void refreshCommittedRecovery(ContinuityStorePort.Session same,Instant deadline)throws IOException {
        var retained=committedRecovery;require(retained!=null&&deadline.isAfter(context.clock().instant()),"actual committed recovery requires a fresh finite caller window");
        retained.deadline=deadline;if(committedPhysicalScope.get()==null)withCommittedPhysical(same,deadline,lease->null);
    }
    private <T>T withCommittedPhysical(ContinuityStorePort.Session same,Instant deadline,PhysicalWork<T> work)throws IOException {
        var retained=committedRecovery;require(retained!=null,"actual committed source missing");
        if(committedPhysicalScope.get()!=null)return work.run(committedPhysicalScope.get());
        return lifecycle.physical().withSnapshot(same,deadline,lease->continuity.withLease(same,lease,()->{
            var prior=openingReconnected.get();var transport=lease.fullSnapshot().actual().session();var old=obligation.binding().predecessor();
            try {
                if(!transport.sessionId().equals(old.sessionId())||!transport.connectionGeneration().equals(old.connectionGeneration()))
                    openingReconnected.set(qualification.qualifyRetainedCauseReconnected(obligation.binding().qualifiedCause(),lease.fullSnapshot(),same,lease.sourceQualification(),same.head()));
                else openingReconnected.remove();
                require(finalRecoveryInputs.get()==null,"nested committed final recovery forbidden");
                finalRecoveryInputs.set(new FinalRecoveryInputs(same,same.head(),lease,initial,Optional.of(retained.edge)));
                try{var previous=retained.scope;retainedFinalChange(previous.stage,obligation);retainedFinalScope.replayed=previous.replayed;retained.scope=retainedFinalScope;retained.deadline=deadline;}
                finally{finalRecoveryInputs.remove();}
                committedPhysicalScope.set(lease);
                try{var result=work.run(lease);requireRetainedScopeCurrent(retained.scope);lease.assertCurrent(same);return result;}
                finally{committedPhysicalScope.remove();}
            }finally{if(prior==null)openingReconnected.remove();else openingReconnected.set(prior);}
        }));
    }
    public void requireCommittedPendingEpisode(ActionReceipt parent,ContinuityStorePort.Session same,LifecycleComposites.RecordedPendingEpisode edge)throws IOException {
        context.writer().requireSession(same);var retained=committedRecovery;
        if(retained!=null&&committedPhysicalScope.get()==null){withCommittedPhysical(same,retained.deadline,lease->{requireCommittedPendingEpisode(parent,same,edge);return null;});return;}
        require(retained!=null&&retained.edge==edge&&parent.command().equals(retained.scope.original.originalParent())
                &&Arrays.equals(ActionReceiptCodec.encodeReceipt(parent,archive(same)),ActionReceiptCodec.encodeReceipt(find(same,parent.command().actionId()),archive(same))),"recorded lifecycle DATA has no identical actual private Root issuer/canonical parent");
        require(retained.deadline!=null&&retained.deadline.isAfter(context.clock().instant()),"retained lifecycle source needs the actual finite completion window");
        refreshCommittedRecovery(same,retained.deadline);var scope=retained.scope;edge.requirePublishedCurrent(same);
        requireRetainedScopeCurrent(scope);
        var pure=DriverPendingEpisodeMutations.project(scope.stage.before(),scope.replayed.beforeObligation(),scope.replayed.change());
        require(Arrays.equals(pure.driver().encode(),edge.beforeDriver().encode())&&Arrays.equals(pure.driver().encode(),edge.afterDriver().encode())
                &&pure.result().orElseThrow().equals(scope.replayed.preparedProjection().projection().result().orElseThrow())
                &&scope.stage.metadata().canonicalDomain().equals(scope.originals.canonicalFinalizationDomain()),"actual sole final business reducer does not reproduce the original metadata predecessor; no Goal/Driver CAS is allowed");
        edge.proof().validateParent(parent.command());edge.requirePublishedCurrent(same);
    }
    public void requireFinalized(ActionCommand parent,ContinuityStorePort.Session same,FinalToken actual)throws IOException {
        requireDriverContext();context.writer().requireSession(same);require(actual==completed&&completed!=null&&actual.originalParent().equals(parent),"final DATA has no actual private Root issuer");
        if(actual instanceof RetainedFinalTokenImpl retained){
            var prepared=prepareRetainedFinalCheck(same,retained.current,retained.scope.stage,retained.scope.replayed);
            retained.scope=prepared.value();
            continuity.withPrepared(prepared,()->{
                retained.current.requireCurrent(same);var scope=retained.scope;requireRetainedScopeCurrent(scope);
                var replayed=DriverPendingEpisodeMutations.project(scope.stage.before(),scope.replayed.beforeObligation(),scope.replayed.change());
                require(Arrays.equals(replayed.driver().encode(),retained.publishedFinal().driver().encode())&&replayed.result().orElseThrow().equals(scope.replayed.preparedProjection().projection().result().orElseThrow()),"retained final business projection changed; no CAS or Goal reapply is allowed");return null;
            });return;
        }
        var token=(FinalTokenImpl)actual;token.current.requireCurrent(same);same.requireCommitted(token.capture.originalPrepared(),token.finalizationReceipt());
        require(token.frame.facts().driverVersion()==token.after.stamp().driverVersion()&&token.frame.facts().episodeEpoch()==token.after.stamp().episodeEpoch()&&Arrays.equals(token.frame.facts().driver().encode(),token.after.driver().encode())
                &&Arrays.equals(natural.readExact(token.m3FinalizationProof()),token.material.scope().finalized.originalProof()),"final token lost genuine M3/current published full Driver frame");
        var recalculated=SuccessorUiObligationReducer.finalEpisode(token.before,token.material.scope().current.state,token.material.value(),token.material.change().currentFrame(),token.matchedEstate(),token.material.change().observedAtUtc());
        require(Arrays.equals(recalculated.driver().encode(),token.after.driver().encode())&&Arrays.equals(recalculated.result(),token.finalReduction().result()),"final reducer no longer matches actual sole business CAS");
        if(token.material.scope().connection!=null){
            var stage=recordedStage(same,token.current.canonicalPublicationProof(),token.after);
            var prepared=prepareRetainedFinalCheck(same,token.current,stage,null);
            continuity.withPrepared(prepared,()->{requireRetainedScopeCurrent(prepared.value());return null;});
        }
    }
    private RootPendingUiContinuity.Prepared<RetainedFinalScope> prepareRetainedFinalCheck(ContinuityStorePort.Session same,Current actual,
            RecordedStage stage,RetainedMutation originalReplay)throws IOException {
        return withPhysical(actual,lease->{
            require(finalRecoveryInputs.get()==null,"nested actual retained final current check");
            finalRecoveryInputs.set(new FinalRecoveryInputs(same,same.head(),lease,initial,Optional.empty()));
            try{
                var change=retainedFinalChange(stage,obligation);var scope=retainedFinalScope;
                if(originalReplay!=null)scope.replayed=originalReplay;
                else{
                    var before=SuccessorUiObligationCodec.decode(natural.readExact(((DriverPendingEpisodeSource.MutationMetadata)stage.metadata()).beforeObligation()));
                    var artifact=stage.document().pendingProjection().orElseThrow().latestMutation().orElseThrow();
                    var projected=DriverPendingEpisodeMutations.project(stage.before(),before,change);
                    var projection=new DriverPendingEpisodeMutations.Prepared(projected,artifact.beforeDriver(),artifact.afterDriver(),artifact.afterAuxiliary(),artifact.beforeObligation(),artifact.afterObligation(),artifact.result());
                    scope.replayed=new RetainedMutation(stage.before(),before,change,obligation,projection,stage.committed(),stage.metadata().canonicalDomain(),stage.originalSource(),stage.metadata().beforeNative(),stage.metadata().observedAtUtc());
                }
                requireRetainedScopeCurrent(scope);return continuity.seal(scope);
            }finally{finalRecoveryInputs.remove();}
        });
    }
    private void requireNoUnrecoveredPending(ContinuityStorePort.Session same)throws IOException {
        if(restoredFinalized!=null){requireRestoredFinalizedCurrent(same,restoredFinalized);
            require(initial==null&&publication==null,"following terminal pending publication is unresolved; ordinary work cannot consume completed retirement");return;}
        assembler().withFrozenFacts(same,frozen->{if(frozen.state() instanceof Known known&&known.auxiliary().members().containsKey(SuccessorUiObligation.AUXILIARY_KEY))throw new IOException("canonical successor UI state requires its actual qualified private Root recovery; DATA cannot report clear or recreate a cause/publication");return null;});
    }
    public boolean hasPending()throws IOException {
        return context.withSession(same->{
            if(restoredFinalized!=null){requireRestoredFinalizedCurrent(same,restoredFinalized);return initial!=null||publication!=null;}
            if(completedByCanonicalLifecycle)return false;if(publication!=null||admittedRecovery!=null)return true;
            return assembler().withFrozenFacts(same,frozen->frozen.state() instanceof Known known&&known.auxiliary().members().containsKey(SuccessorUiObligation.AUXILIARY_KEY));
        });
    }
    /** Canonical/private custody refresh only. No native observation or ordinary readiness is requested. */
    public boolean refreshPendingStatus(Instant deadline)throws IOException {return context.withSession(same->{var current=current(same,deadline);
        if(committedRecovery!=null||admittedRecovery!=null)return pendingSuccessorUi(same,new SessionPorts.SessionIdentity(context.game().machineId(),context.game().generation(),context.game().sessionId()),deadline).isPresent();return current.isPresent();});}
    @FunctionalInterface public interface PublicWork<T>{T run()throws IOException,InterruptedException;}
    public <T>T withPublicCloseRequest(RootDriverLifecyclePublicCodec.Close actual,PublicWork<T> work)throws IOException,InterruptedException {
        Objects.requireNonNull(actual);Objects.requireNonNull(work);
        if(!hasPending())throw publicCloseFailure(CloseFailure.PENDING_REQUIRED);
        require(publicRequest.get()==null,"nested public Close request forbidden");
        publicRequest.set(actual);try{return work.run();}finally{publicRequest.remove();}
    }
    /** The final business/metadata edge has no live Pending Current. Reopen its actual original
     * Close result under an independent physical lease; this path cannot execute another child. */
    public Optional<RootDriverLifecyclePublicCodec.View> publicRetainedClose(RootDriverLifecyclePublicCodec.Close input,Instant deadline)throws IOException {
        Objects.requireNonNull(input);Objects.requireNonNull(deadline);
        return context.withSession(same->{
            if(!hasPending())return Optional.empty();
            requirePublicCloseInput(same,input,deadline);
            current(same,deadline);
            if(completedByCanonicalLifecycle)return Optional.empty();
            if(admittedRecovery!=null)return withAdmittedPhysical(same,deadline,(actual,held)->{
                var full=held.fullSnapshot();requirePublicCloseFrame(input,full);
                var resumed=RootDriverLifecycleResumeCodec.clear(RawJson.fullMaterial(DriverJson.encode(full.semantic())));
                return Optional.of(retainedCloseView(full,resumed));
            });
            if(committedRecovery==null)return Optional.empty();
            refreshCommittedRecovery(same,deadline);var retained=committedRecovery;
            return lifecycle.physical().withSnapshot(same,deadline,held->{
                requireCommittedPendingEpisode(find(same,initial.originalParent().actionId()),same,retained.edge);
                var full=held.fullSnapshot();requirePublicCloseFrame(input,full);
                var resumed=resumeMaterial(full,obligation,retained.scope.stage.metadata().canonicalDomain(),Optional.empty(),true,
                        "actual final lifecycle is recorded; the original Controller episode adoption is still pending");
                var result=retainedCloseView(full,resumed);
                requireCommittedPendingEpisode(find(same,initial.originalParent().actionId()),same,retained.edge);held.assertCurrent(same);
                return Optional.of(result);
            });
        });
    }
    private static void requirePublicCloseFrame(RootDriverLifecyclePublicCodec.Close input,DriverObservationAssembler.FullSnapshot full) {
        var played=full.semantic().members().get("played_character");
        if(!(input.expectedRevision().equals(full.facts().publicRevision())
                &&played instanceof OpportunityJson.Obj player&&new OpportunityJson.IntegerValue(input.actor()).equals(player.get("character_id"))
                &&input.episodeRunId().equals(full.facts().driver().session().episodeRunId())))
            throw publicCloseFailure(CloseFailure.FRAME_DIFFERENT);
    }
    private void requirePublicCloseInput(ContinuityStorePort.Session same,RootDriverLifecyclePublicCodec.Close input,Instant deadline)throws IOException {
        lifecycle.physical().withSnapshot(same,deadline,lease->{requirePublicCloseFrame(input,lease.fullSnapshot());lease.assertCurrent(same);return null;});
    }
    enum CloseFailure { PENDING_REQUIRED,FRAME_DIFFERENT,NO_LEGAL_CLOSE }
    static PublicServiceFailure publicCloseFailure(CloseFailure reason){
        String message=switch(reason){
            case PENDING_REQUIRED->"successor typed Close requires the App's verified pending transition";
            case FRAME_DIFFERENT->"successor typed Close request differs from its actual successor";
            case NO_LEGAL_CLOSE->"successor UI has no currently legal verified modal Close";
        };return new PublicServiceFailure(PublicServiceFailure.Kind.VALUE_ERROR,message,Optional.empty());
    }
    private RootDriverLifecyclePublicCodec.View retainedCloseView(DriverObservationAssembler.FullSnapshot full,RootDriverLifecycleResumeCodec.ResumeResult resumed)throws IOException {
        require(resumed.originalNumericSnapshot().equals(RawJson.fullMaterial(DriverJson.encode(full.semantic()))),
                "retained Close resume crossed the independently captured actual frame");
        var material=retainedResumeCloseMaterial(resumed);
        var original=presentClose(RawJson.fullMaterial(DriverJson.encode(full.semantic())),full.actual().session().machineId(),full.actual().observedAt(),false);
        return RootDriverLifecyclePublicCodec.withCloseMaterial(original,material);
    }
    static RootDriverLifecyclePublicCodec.CloseMaterial retainedResumeCloseMaterial(RootDriverLifecycleResumeCodec.ResumeResult resumed){
        return resumed.transition().flatMap(RootDriverLifecycleResumeCodec.TransitionMaterial::timelineContinuation)
                .flatMap(RootDriverLifecycleResumeCodec.TimelineContinuation::closeResult)
                .orElseThrow(()->publicCloseFailure(CloseFailure.NO_LEGAL_CLOSE));
    }
    public <T>T withPublicCloseRequest(RootDriverLifecyclePublicCodec.Close actual,Instant deadline,PublicWork<T> work)throws IOException,InterruptedException {
        if(!hasPending())throw publicCloseFailure(CloseFailure.PENDING_REQUIRED);
        context.withSession(same->{requirePublicCloseInput(same,actual,deadline);var current=current(same,deadline).orElseThrow(()->new IOException("actual verified pending transition absent"));
            return withPhysical(current,lease->{requirePublicCloseFrame(actual,lease.fullSnapshot());
                if(current instanceof EventCurrent)throw publicCloseFailure(CloseFailure.NO_LEGAL_CLOSE);
                if(current.state.closeAttempt().isEmpty()){var query=queryInside(current,lease);if(!(query.observation().state()==UiState.CLOSE_REQUIRED&&query.read().value().context().supportedCloseObserved()))throw publicCloseFailure(CloseFailure.NO_LEGAL_CLOSE);}return null;});});
        return withPublicCloseRequest(actual,work);
    }
    public RootDriverLifecyclePublicCodec.Timeline publicTimeline(RootDriverLifecyclePublicCodec.Query input,Instant deadline)throws IOException {
        return context.withSession(same->{var candidate=current(same,deadline);
            if(admittedRecovery!=null)return withAdmittedPhysical(same,deadline,(actual,held)->{
                require(admittedReadScope.get()==null,"nested historically admitted timeline lease forbidden");
                require(input.expectedRevision().equals(held.fullSnapshot().facts().publicRevision()),"historically admitted timeline source revision changed");
                var frame=held.ordinary().orElseThrow();admittedReadScope.set(new AdmittedRead(admittedRecovery,actual,held));
                try{var value=natural.read(same,query,new PlanningReadRequest(new CommandOrigin.Gameplay(frame.identity()),frame.source(),frame.sessionId(),QUERY,EMPTY,deadline));held.assertCurrent(same);return new RootDriverLifecyclePublicCodec.Timeline(value.receipt(),value.value(),held.fullSnapshot().actual().session().machineId(),held.fullSnapshot().actual().observedAt());}
                finally{admittedReadScope.remove();}
            });
            if(committedRecovery!=null) {
                refreshCommittedRecovery(same,deadline);var retained=committedRecovery;
                return lifecycle.physical().withSnapshot(same,deadline,lease->{
                    require(committedReadScope.get()==null,"nested committed timeline lease forbidden");requireCommittedPendingEpisode(find(same,initial.originalParent().actionId()),same,retained.edge);
                    var frame=lease.ordinary().orElseThrow();require(input.expectedRevision().equals(lease.fullSnapshot().facts().publicRevision()),"committed timeline source revision changed");
                    committedReadScope.set(new CommittedRead(retained,lease));
                    try{var value=natural.read(same,query,new PlanningReadRequest(new CommandOrigin.Gameplay(frame.identity()),frame.source(),frame.sessionId(),QUERY,EMPTY,deadline));lease.assertCurrent(same);return new RootDriverLifecyclePublicCodec.Timeline(value.receipt(),value.value(),lease.fullSnapshot().actual().session().machineId(),lease.fullSnapshot().actual().observedAt());}
                    finally{committedReadScope.remove();}
                });
            }
            var current=candidate.orElseThrow(()->new IOException("actual pending timeline source absent"));
            return withPhysical(current,lease->{require(input.expectedRevision().equals(lease.fullSnapshot().facts().publicRevision()),"timeline source revision changed before query");var value=queryInside(current,lease);return new RootDriverLifecyclePublicCodec.Timeline(value.read().receipt(),value.read().value(),lease.fullSnapshot().actual().session().machineId(),lease.fullSnapshot().actual().observedAt());});});
    }
    public RootDriverLifecyclePublicCodec.Timeline publicTimelineResult(PlanningReadResult.Known<NativeTimelineBlocker12004.Query> result){
        return new RootDriverLifecyclePublicCodec.Timeline(result.receipt(),result.value(),result.receipt().request().origin().machineId(),result.receipt().after().binding().observedAt());
    }
    public RootDriverLifecyclePublicCodec.View publicResume(RootDriverLifecyclePublicCodec.Resume input,Instant deadline)throws IOException {
        return context.withSession(same->{var current=current(same,deadline).orElseThrow(()->new IOException("actual pending source absent"));
            var fresh=withPhysical(current,lease->{input.original().expected().ifPresent(value->require(value.equals(lease.fullSnapshot().facts().publicRevision()),"successor UI resume revision changed"));return queryInside(current,lease);});
            var after=mutate(current,new DriverPendingEpisodeSource.Observe(fresh.observation()),fresh.physical());
            return withPhysical(after,lease->{var complete=lease.ordinary().orElseThrow();return attachCloseMaterial(view(PublicSnapshotCodec.exportSemanticOnly(complete),lease.fullSnapshot().actual().session().machineId(),lease.fullSnapshot().actual().observedAt(),false),rawBinding(complete));});
        });
    }
    /** Complete original App read result; a qualified cause is explicitly pre-final and cannot claim Goal/day credit. */
    public RootDriverLifecycleResumeCodec.ResumeResult publicResumeMaterial(RootDriverLifecyclePublicCodec.Resume input,Instant deadline)throws IOException {
        return context.withSession(same->{
            var candidate=current(same,deadline);
            if(admittedRecovery!=null)return withAdmittedPhysical(same,deadline,(actual,held)->{
                input.original().expected().ifPresent(value->require(value.equals(held.fullSnapshot().facts().publicRevision()),"successor UI resume revision changed"));
                return RootDriverLifecycleResumeCodec.clear(RawJson.fullMaterial(DriverJson.encode(held.fullSnapshot().semantic())));
            });
            if(committedRecovery!=null) {
                refreshCommittedRecovery(same,deadline);var retained=committedRecovery;requireCommittedPendingEpisode(find(same,initial.originalParent().actionId()),same,retained.edge);
                input.original().expected().ifPresent(value->require(value.equals(retained.scope.current.facts().publicRevision()),"successor UI resume revision changed"));
                return resumeMaterial(retained.scope.current,obligation,retained.scope.stage.metadata().canonicalDomain(),Optional.empty(),true,
                        "actual final lifecycle is recorded; the original Controller episode adoption is still pending");
            }
            var before=candidate.orElseThrow(()->new IOException("actual pending source absent"));
            if(completed!=null) {
                requireFinalized(initial.originalParent(),same,completed);
                return withPhysical(before,lease->{input.original().expected().ifPresent(value->require(value.equals(lease.fullSnapshot().facts().publicRevision()),"successor UI resume revision changed"));
                    return resumeMaterial(lease.fullSnapshot(),before.state,before.canonicalDomain(),Optional.empty(),true,"actual final business publication is retained; its original lifecycle metadata completion is pending");});
            }
            ResumeRead observed=withPhysical(before,lease->{
                input.original().expected().ifPresent(value->require(value.equals(lease.fullSnapshot().facts().publicRevision()),"successor UI resume revision changed"));
                // Only the original timeline query stage becomes ui_unresolved. The enclosing
                // private source/current/lease qualification must still fail normally.
                try{return new ResumeObserved(queryInside(before,lease));}
                catch(IOException originalReadFailure){return new ResumeReadFailed(originalReadFailure);}
            });
            if(observed instanceof ResumeReadFailed failed)
                return withPhysical(before,lease->resumeMaterial(before,lease,Optional.of(failed.original())));
            var fresh=((ResumeObserved)observed).value();
            var after=mutate(before,new DriverPendingEpisodeSource.Observe(fresh.observation()),fresh.physical());
            return withPhysical(after,lease->resumeMaterial(after,lease,Optional.empty()));
        });
    }
    private RootDriverLifecycleResumeCodec.ResumeResult resumeMaterial(Current current,RootLifecycleAuthority.SnapshotLease lease,
            Optional<IOException> originalReadFailure)throws IOException {
        current.requireCurrent(context.borrowedSession());var full=lease.fullSnapshot();var state=current.state;
        return resumeMaterial(full,state,current.canonicalDomain(),originalReadFailure,false,"");
    }
    private RootDriverLifecycleResumeCodec.ResumeResult resumeMaterial(DriverObservationAssembler.FullSnapshot full,SuccessorUiObligation state,ExactRef domain,
            Optional<IOException> originalReadFailure,boolean finalized,String finalStage)throws IOException {
        var observed=state.observation();var ui=observed.map(Observation::state).orElse(UiState.UNRESOLVED);
        var status=ui==UiState.CLOSE_REQUIRED?RootDriverLifecycleResumeCodec.Status.CLOSE_REQUIRED:
                ui==UiState.PLAYER_DECISION_PENDING?RootDriverLifecycleResumeCodec.Status.DEFERRED_PLAYER_DECISION:RootDriverLifecycleResumeCodec.Status.UI_UNRESOLVED;
        if(originalReadFailure.isPresent())status=RootDriverLifecycleResumeCodec.Status.UI_UNRESOLVED;
        if(finalized)status=RootDriverLifecycleResumeCodec.Status.UI_UNRESOLVED;
        var document=NaturalClockOriginals.decode(natural.readExact(domain));var ready=document.ready().orElseThrow();
        var first=archive(context.borrowedSession()).loadRead(ready.initialTimeline().receipt());natural.timeline().decode(first);
        var initialQuery=first.original().originalResultToken().orElseThrow(()->new IOException("actual initial timeline result absent"));
        var close=originalCloseMaterial(rawBinding(full.semantic(),full.actual().snapshotId(),full.facts().publicRevision(),full.actual().nativeRevision()));
        String timelineStatus=ui==UiState.CLOSE_REQUIRED?"close_required":ui==UiState.PLAYER_DECISION_PENDING?"deferred_player_decision":
                ui==UiState.CLEAR?(state.closeAttempt().flatMap(CloseAttempt::receipt).flatMap(CloseReceipt::effectiveMaterialClearance).isPresent()?"materially_cleared":"already_clear"):"independent_identity_unverified";
        var timeline=new RootDriverLifecycleResumeCodec.TimelineContinuation(timelineStatus,
                initialQuery,close,Optional.empty(),Optional.empty(),close.isPresent()?Optional.of(true):Optional.empty(),Optional.empty(),Optional.empty());
        var predecessor=initial.originalParentFrame();
        var retainedFrame=firstRetainedSuccessorFrame(context.borrowedSession());
        RawJson retainedBinding;
        if(retainedFrame.isPresent()){var oldFrame=retainedFrame.orElseThrow();
            var retainedSemantic=DriverJson.object(natural.readExact(oldFrame.semantic()),RawJson.MAXIMUM_BYTES);
            var retainedTransport=new NativeObservationPort.TransportSession(oldFrame.machineId(),oldFrame.game(),oldFrame.connectionGeneration(),oldFrame.sessionId());
            retainedBinding=resumeBinding(retainedSemantic,retainedTransport);
        }else retainedBinding=resumeBinding(full.semantic(),full.actual().session());
        var lifecycleValue=initial.terminalSnapshot().semantic().members().get("succession_lifecycle");
        if(lifecycleValue==null)throw new IOException("actual retained succession lifecycle original is missing");
        var transition=new RootDriverLifecycleResumeCodec.TransitionMaterial(finalized?RootDriverLifecycleResumeCodec.Qualification.VERIFIED:RootDriverLifecycleResumeCodec.Qualification.CAUSE_QUALIFIED,
                initial.cause().predecessorCharacterId(),initial.cause().successorCharacterId(),initial.cause().oldEpisodeRunId(),state.binding().successorEpisodeRunId(),
                retainedFrame.map(value->value.dateRaw().intValueExact()).orElseGet(()->OpportunityJson.integer(full.semantic().get("date_raw"),"actual date").intValueExact()),new RawJson(DriverJson.encode(lifecycleValue)),new RawJson(initial.matchedEstate().wire()),
                resumeBinding(predecessor.semantic(),predecessor.actual().session()),retainedBinding,Optional.of(timeline),Optional.empty());
        Optional<RootDriverLifecycleResumeCodec.Diagnostic> diagnostic=Optional.empty();
        if(status==RootDriverLifecycleResumeCodec.Status.UI_UNRESOLVED) {
            String message=originalReadFailure.map(value->Objects.toString(value.getMessage(),"")).orElse(finalized?finalStage:ui==UiState.CLEAR?
                    "modal clearance is observed; actual date/estate/final lifecycle completion is still pending":"actual successor UI remains unresolved");
            diagnostic=Optional.of(new RootDriverLifecycleResumeCodec.Diagnostic(message,List.of(new RootDriverLifecycleResumeCodec.Failure(
                    originalReadFailure.isPresent()?"ordinary_successor_timeline_query":"successor_ui_observation",originalReadFailure.isPresent()?"read_failed":"pending_finalization",message,
                    originalReadFailure.map(value->value.getClass().getName()),originalReadFailure.map(value->Objects.toString(value.getMessage(),""))))));
        }
        var transport=full.actual().session();
        var resumed=new RootDriverLifecycleResumeCodec.ColdFrame(transport.game().pid(),transport.connectionGeneration(),full.actual().snapshotId(),full.facts().publicRevision(),full.actual().nativeRevision(),
                OpportunityJson.integer(full.semantic().get("date_raw"),"actual date").intValueExact(),full.facts().driver().session().actorId().intValueExact(),full.facts().driver().session().episodeRunId());
        Optional<RootDriverLifecycleResumeCodec.ColdBinding> cold=Optional.empty();
        if(retainedFrame.isPresent()){var oldFrame=retainedFrame.orElseThrow();
            var retained=new RootDriverLifecycleResumeCodec.ColdFrame(oldFrame.game().pid(),oldFrame.connectionGeneration(),oldFrame.snapshotId(),oldFrame.revision(),oldFrame.nativeRevision(),
                    oldFrame.dateRaw().intValueExact(),oldFrame.actorCharacterId().intValueExact(),oldFrame.episodeRunId());
            cold=Optional.of(RootDriverLifecycleResumeCodec.formatColdBinding(new RootDriverLifecycleResumeCodec.ColdBindingMaterial(transition,Optional.empty(),retained,resumed,transport.machineId(),state.binding().sourceEpochSha256(),
                    new RootDriverLifecycleResumeCodec.ColdGame(transport.game().pid(),transport.game().creationFiletime().value().toString(),executable.path()),domain,
                    !retained.connectionGeneration().equals(resumed.connectionGeneration()))));
        }
        if(retainedFrame.isEmpty()&&(!transport.sessionId().equals(state.binding().predecessor().sessionId())
                ||!transport.connectionGeneration().equals(state.binding().predecessor().connectionGeneration()))){
            // Initial publication deliberately has no post-pending facts manifest. Its
            // old public revision cannot be reconstructed from a new connection's read.
            String missing="original transport has no archived successor UI frame; retained cold public binding is MISSING";
            var failures=new ArrayList<RootDriverLifecycleResumeCodec.Failure>();diagnostic.ifPresent(value->failures.addAll(value.failures()));
            failures.add(new RootDriverLifecycleResumeCodec.Failure("cold_original_successor_binding","original_missing",missing,Optional.empty(),Optional.empty()));
            diagnostic=Optional.of(new RootDriverLifecycleResumeCodec.Diagnostic(missing,failures));status=RootDriverLifecycleResumeCodec.Status.UI_UNRESOLVED;
        }
        return new RootDriverLifecycleResumeCodec.ResumeResult(status,true,status==RootDriverLifecycleResumeCodec.Status.DEFERRED_PLAYER_DECISION,false,
                RawJson.fullMaterial(DriverJson.encode(full.semantic())),Optional.of(transition),cold,diagnostic);
    }
    private Optional<UiFrame> firstRetainedSuccessorFrame(ContinuityStorePort.Session same)throws IOException {
        for(var item:retainedChain(same,canonicalBusinessKnown(same)).steps())if(item instanceof RetainedMutationStage mutation) {
            var pending=mutation.stage().document().pendingProjection().orElseThrow();
            var state=SuccessorUiObligationCodec.decode(natural.readExact(pending.currentObligation()));
            if(state.observation().isPresent()){
                var frame=state.observation().orElseThrow().frame();var original=state.binding().predecessor();
                if(frame.sessionId().equals(original.sessionId())&&frame.connectionGeneration().equals(original.connectionGeneration()))return Optional.of(frame);
            }
        }
        return Optional.empty();
    }
    private static RawJson resumeBinding(OpportunityJson.Obj semantic,NativeObservationPort.TransportSession session) {
        var fields=new LinkedHashMap<String,OpportunityJson.Value>();
        for(String key:List.of("snapshot_id","revision","native_revision","date_raw","episode_run_id","episode_character_id","one_life_terminal","one_life_terminal_reason"))
            fields.put(key,Objects.requireNonNull(semantic.members().get(key),"actual resume binding field absent: "+key));
        var player=OpportunityJson.object(semantic.get("played_character"),"actual played character");fields.put("played_character_id",player.get("character_id"));fields.put("played_character_alive",player.get("alive"));
        var control=semantic.members().get("native_session_control");for(String key:List.of("episode_binding_state","driver_state_restore_kind"))
            fields.put(key,control instanceof OpportunityJson.Obj actual?actual.members().getOrDefault(key,OpportunityJson.Nil.INSTANCE):OpportunityJson.Nil.INSTANCE);
        var diagnostics=OpportunityJson.object(semantic.get("diagnostics"),"actual snapshot diagnostics");
        var pid=OpportunityJson.integer(diagnostics.get("bridge_pid"),"actual bridge pid");var generation=OpportunityJson.integer(diagnostics.get("connection_generation"),"actual connection generation");
        require(pid.equals(BigInteger.valueOf(session.game().pid()))&&generation.equals(session.connectionGeneration()),"resume binding diagnostics differ from actual physical session");
        fields.put("bridge_pid",new OpportunityJson.IntegerValue(pid));fields.put("connection_generation",new OpportunityJson.IntegerValue(generation));return new RawJson(DriverJson.encode(new OpportunityJson.Obj(fields)));
    }
    public RootDriverLifecyclePublicCodec.View clearView(RawJson snapshot,String machine,Instant observed){return new RootDriverLifecyclePublicCodec.View(RootDriverLifecyclePublicCodec.Status.CLEAR,false,false,false,snapshot,Optional.empty(),Optional.empty(),machine,observed);}
    private RootDriverLifecyclePublicCodec.View view(RawJson snapshot,String machine,Instant observed,boolean submitted)throws IOException {
        Optional<RootDriverLifecyclePublicCodec.CloseResult> close=Optional.empty();if(obligation!=null&&obligation.closeAttempt().flatMap(CloseAttempt::receipt).isPresent()){
            var value=obligation.closeAttempt().orElseThrow();var receipt=value.receipt().orElseThrow();close=Optional.of(new RootDriverLifecyclePublicCodec.CloseResult(receipt.outcome(),value.actionId(),receipt.canonicalReceipt(),receipt.effectiveMaterialClearance().isPresent(),receipt.effectiveDateAdvance(),receipt.reconciliation()));}
        var state=obligation==null?UiState.CLEAR:obligation.observation().map(Observation::state).orElse(UiState.UNRESOLVED);
        var status=state==UiState.CLOSE_REQUIRED?RootDriverLifecyclePublicCodec.Status.CLOSE_REQUIRED:state==UiState.PLAYER_DECISION_PENDING?RootDriverLifecyclePublicCodec.Status.DEFERRED_PLAYER_DECISION:state==UiState.CLEAR?RootDriverLifecyclePublicCodec.Status.CLEAR:RootDriverLifecyclePublicCodec.Status.UI_UNRESOLVED;
        var diagnosis=publication==null?Optional.<ExactRef>empty():NaturalClockOriginals.decode(natural.readExact(publication.canonicalDomainRef())).pendingProjection().flatMap(NaturalClockOriginals.PendingProjection::eventDiagnosis);
        return new RootDriverLifecyclePublicCodec.View(status,hasPending(),state==UiState.PLAYER_DECISION_PENDING,submitted,snapshot,Optional.ofNullable(obligation),close,machine,observed,diagnosis);
    }
    public RootDriverLifecyclePublicCodec.View presentClose(RawJson snapshot,String machine,Instant observed,boolean actualNewChild)throws IOException {
        require(obligation!=null&&obligation.closeAttempt().flatMap(CloseAttempt::receipt).isPresent(),"successor UI has no actual retained legal once Close result");return view(snapshot,machine,observed,actualNewChild);
    }
    public RootDriverLifecyclePublicCodec.View presentClose(DriverObservationAssembler.Complete actual,boolean actualNewChild)throws IOException {
        require(actual.source().equals(context.source())&&actual.sessionId().equals(context.game().sessionId())&&actual.identity().game().equals(context.game().generation()),"public Close material crossed its actual installed Game/source");
        var original=presentClose(PublicSnapshotCodec.exportSemanticOnly(actual),actual.identity().machineId(),actual.observedAt(),actualNewChild);
        return attachCloseMaterial(original,rawBinding(actual));
    }
    public RootDriverLifecyclePublicCodec.View presentPendingClose(Instant deadline,boolean actualNewChild)throws IOException {
        return context.withSession(same->{var current=current(same,deadline);require(current.isPresent()||committedRecovery!=null,"actual pending Close presentation source absent");
            if(committedRecovery!=null){refreshCommittedRecovery(same,deadline);requireCommittedPendingEpisode(find(same,initial.originalParent().actionId()),same,committedRecovery.edge);}
            return lifecycle.physical().withSnapshot(same,deadline,lease->{if(current.isPresent())current.orElseThrow().requireCurrent(same);else requireCommittedPendingEpisode(find(same,initial.originalParent().actionId()),same,committedRecovery.edge);lease.assertCurrent(same);var full=lease.fullSnapshot();
                require(full.actual().session().game().equals(context.game().generation())&&full.actual().session().sessionId().equals(context.game().sessionId())&&full.facts().source().equals(context.source()),"pending Close DATA presentation changed actual physical Game/source");
                var snapshot=lease.ordinary().isPresent()?PublicSnapshotCodec.exportSemanticOnly(lease.ordinary().orElseThrow()):PublicSnapshotCodec.exportSemanticOnly(full,lease.terminalIdentity().orElseThrow());
                var original=presentClose(snapshot,full.actual().session().machineId(),full.actual().observedAt(),actualNewChild);
                if(lease.ordinary().isEmpty())original=new RootDriverLifecyclePublicCodec.View(RootDriverLifecyclePublicCodec.Status.UI_UNRESOLVED,true,false,actualNewChild,snapshot,original.transition(),original.close(),original.machineId(),original.observedAtUtc(),original.eventDiagnosis());
                return attachCloseMaterial(original,rawBinding(full.semantic(),full.actual().snapshotId(),full.facts().publicRevision(),full.actual().nativeRevision()));});});
    }
    private static RawJson rawBinding(DriverObservationAssembler.Complete actual){return rawBinding(actual.semantic(),actual.identity().frame().snapshotId(),actual.identity().frame().revision(),actual.identity().frame().identity().nativeRevision());}
    private static RawJson rawBinding(OpportunityJson.Obj actual,String snapshot,BigInteger revision,BigInteger nativeRevision){
        var row=StrictJson.object().put("snapshot_id",snapshot).put("revision",revision).put("native_revision",nativeRevision);
        for(String name:List.of("date_raw","paused","map_ready","episode_character_id","episode_run_id")){var value=actual.members().get(name);if(value==null)row.putNull(name);else row.set(name,OpportunityJson.toNode(value));}
        var played=actual.get("played_character");if(played instanceof OpportunityJson.Obj player){for(String name:List.of("character_id","alive")){var value=player.members().get(name);String target=name.equals("character_id")?"played_character_id":"played_character_alive";if(value==null)row.putNull(target);else row.set(target,OpportunityJson.toNode(value));}}else{row.putNull("played_character_id");row.putNull("played_character_alive");}
        return new RawJson(StrictJson.canonical(row));
    }
    private RootDriverLifecyclePublicCodec.View attachCloseMaterial(RootDriverLifecyclePublicCodec.View original,RawJson actualEnding)throws IOException {
        var material=originalCloseMaterial(actualEnding);return material.isPresent()?RootDriverLifecyclePublicCodec.withCloseMaterial(original,material.orElseThrow()):original;
    }
    private Optional<RootDriverLifecyclePublicCodec.CloseMaterial> originalCloseMaterial(RawJson ending)throws IOException {
        if(obligation==null||obligation.closeAttempt().flatMap(CloseAttempt::receipt).isEmpty())return Optional.empty();
        var same=context.borrowedSession();var retained=obligation.closeAttempt().orElseThrow().receipt().orElseThrow();var receipt=archive(same).loadReceipt(retained.effectiveReceipt());var attempt=ActionTransitions.attempt(receipt.state()).orElse(null);if(attempt==null||attempt.preparedRequest().preparationEvidence().size()!=5)return Optional.empty();
        NativeActionPort.AckReceived acknowledgement=null;
        if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied control)acknowledgement=ActionEffects.controlAcknowledgement(receipt.command(),attempt,settled.dispatch(),control);
        else if(receipt.ack().isPresent())acknowledgement=receipt.ack().orElseThrow();
        else {var cached=lateCloseAcks.get(receipt.command().actionId());if(cached!=null){var dispatch=ActionTransitions.dispatch(receipt.state()).orElseThrow();new ReconciledControlAck(cached.ack).requireMatches(receipt.command(),attempt,dispatch);acknowledgement=cached.ack;}}
        if(acknowledgement==null)return Optional.empty();
        var packet=closePacket(attempt,acknowledgement);var before=RootGuardEvidence.loadFrame(attempt.guard(),archive(same),context.frameLoader());
        var close=NativeTimelineBlocker12004.parseClose(natural.readExact(packet.original()),packet.original(),new NativeTimelineBlocker12004.BoundFrame(session(before),packet.actualFrame(),packet.actualScene()),attempt.requestId());
        var initialRead=archive(same).loadRead(attempt.preparedRequest().preparationEvidence().get(4));var initialResult=initialRead.original().originalResultToken().orElseThrow();query.replay(initialRead);
        if(close.state()!=NativeTimelineBlocker12004.CloseState.SUBMITTED_PENDING){var outbound=acknowledgement.outbound().orElseThrow();org.xar.ck3.control.nativebridge.NativeWire.decodeExecuteRequest(outbound.originalPacket());var request=new RawJson(Arrays.copyOfRange(outbound.originalPacket(),4,outbound.originalPacket().length));Optional<RawJson> inner=Optional.empty();
            if(close.ack().isPresent()){var frame=DriverJson.object(acknowledgement.originalFrame().bytes(),NativeTimelineBlocker12004.MAX_BYTES);var diagnostic=OpportunityJson.object(frame.get("death_succession_close_failure_v1"),"actual reclaim diagnostic");var exact=OpportunityJson.text(diagnostic.get("submitted_ack_frame_exact_json"),"actual retained ACK JSON").getBytes(java.nio.charset.StandardCharsets.UTF_8);inner=Optional.of(new RawJson(org.xar.ck3.control.nativebridge.NativeWire.token(exact,"result")));}
            return Optional.of(new RootDriverLifecyclePublicCodec.ReclaimClose(request,acknowledgement.originalFrame(),RawJson.fullMaterial(DriverJson.encode(before.semantic())),initialResult,inner,close.retainedAckValidationFailure()));}
        var reads=new ArrayList<PlanningReadReceipt>();if(receipt.state() instanceof ActionState.Settled settled&&settled.settlement() instanceof ActionState.ControlApplied control){reads.addAll(control.supportingReads());reads.add(control.read());}else closePostQueries.getOrDefault(receipt.command().actionId(),List.of()).forEach(value->reads.add(value.receipt()));
        var attempts=new ArrayList<RootDriverLifecyclePublicCodec.PostQueryAttempt>();for(var read:reads){replayTimeline(read);var frame=read.request().origin() instanceof CommandOrigin.Reconciliation?context.reconciliation().verifyArchived(read.after().binding(),archive(same),same,context.originals()):RootGuardEvidence.loadFrame(read.after().binding(),archive(same),context.frameLoader());attempts.add(new RootDriverLifecyclePublicCodec.PostQueryAttempt(attempts.size()+1,read.original().originalResultToken(),Optional.empty(),Optional.of(rawBinding(frame))));}
        Optional<RawJson> life=Optional.empty();if(actualDateReceipt!=null&&actualDateReceipt.settled())life=lifecycle.life().replay().readRecorded(actualDateReceipt,archive(same)).originalCompatible().map(LifeAdvanceEvidence.OriginalResult::body);
        var endingFields=StrictJson.parse(ending.bytes());var endingActor=endingFields.get("played_character_id");var endingAlive=endingFields.get("played_character_alive");var endingRun=endingFields.get("episode_run_id");var endingDate=endingFields.get("date_raw");
        boolean sameEnding=endingActor!=null&&endingActor.isIntegralNumber()&&endingActor.bigIntegerValue().equals(obligation.binding().successorCharacterId())&&endingAlive!=null&&endingAlive.isBoolean()&&endingAlive.booleanValue()&&endingRun!=null&&endingRun.isTextual()&&endingRun.textValue().equals(obligation.binding().successorEpisodeRunId())&&endingDate!=null&&endingDate.isIntegralNumber()&&endingDate.bigIntegerValue().compareTo(obligation.closeAttempt().orElseThrow().before().dateRaw())>0;
        boolean verified=retained.effectiveMaterialClearance().isPresent()&&retained.effectiveDateAdvance().isPresent()&&sameEnding;var phase=verified?RootDriverLifecyclePublicCodec.ClosePhase.MATERIALLY_VERIFIED:life.isPresent()?RootDriverLifecyclePublicCodec.ClosePhase.POST_ADVANCE_UNCONFIRMED:RootDriverLifecyclePublicCodec.ClosePhase.SUBMITTED_UNCONFIRMED;
        Optional<String> failure=verified?Optional.empty():Optional.of(receipt.state() instanceof ActionState.Unknown unknown?unknown.reason():"actual independent date advance or final successor UI remains unconfirmed");
        return Optional.of(new RootDriverLifecyclePublicCodec.SubmittedClose(phase,acknowledgement.originalResultToken().orElseThrow(),initialResult,attempts,obligation.closeAttempt().orElseThrow().before().dateRaw().intValueExact(),new RootDriverLifecyclePublicCodec.EndingBinding(ending),life,failure));
    }
    G2RetainedNativeSourceProvider.Session terminalDataSession(LifecycleIdentity actual,org.xar.ck3.control.g2.common.G2Source source)throws IOException {
        requireDriverContext();require(actual.machineId().equals(context.game().machineId())&&actual.game().equals(context.game().generation())&&actual.sessionId().equals(context.game().sessionId())&&source.equals(context.source()),"terminal DATA timeline source differs from actual installed Game");
        return new G2RetainedNativeSourceProvider.Session(actual.machineId(),actual.sessionId(),new G2RetainedNativeSourceProvider.GameIdentity(actual.game().pid(),actual.game().creationFiletime().value().toString()),actual.subject().episodeRunId(),actual.connectionGeneration().toString(),executable,executableFileId,executableMtimeNs);
    }
    public RootDriverLifecyclePublicCodec.Timeline publicTerminalTimeline(LifecycleIdentity identity,RootDriverLifecyclePublicCodec.Query input,Instant deadline)throws IOException {
        var same=context.borrowedSession();return natural.terminal().current(same,identity,deadline,lease->{require(input.expectedRevision().equals(lease.identity().frame().revision()),"terminal timeline public source revision changed");var artifact=natural.timeline().read(same,lease,deadline);var receipt=archive(same).loadRead(artifact.receipt());return new RootDriverLifecyclePublicCodec.Timeline(receipt,natural.timeline().decode(receipt),identity.machineId(),lease.snapshot().actual().observedAt());});
    }
}

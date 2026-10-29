package org.xar.ck3.control.service.root;

import static org.xar.ck3.control.contracts.StrictJson.require;
import java.io.IOException;
import java.util.*;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.driver.DriverJson;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverObservationAssembler.FullSnapshot;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer;
import org.xar.ck3.control.application.readiness.NativeReadinessCollector.SourceQualification;
import org.xar.ck3.control.application.readiness.NativeSourceProofCodec;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.runtime.lifecycle.PendingSameGameContinuity;
import org.xar.ck3.control.runtime.lifecycle.RootPendingNaturalSuccessionQualification.*;

/** The installed Root's actual held Managed lease supplies continuity. Neither the archived
 * Binding nor the public cold-binding JSON is an issuer or a replacement physical guard. */
final class RootPendingUiContinuity implements RootRetainedContinuityPort {
    interface CanonicalReplay {
        void requireRebind(ContinuityStorePort.Session same,SuccessorUiObligation state)throws IOException;
        void requireFinalized(ContinuityStorePort.Session same,SuccessorUiObligation state)throws IOException;
        void requireOutsideObservation(ContinuityStorePort.Session same)throws IOException;
    }
    @FunctionalInterface interface Work<T>{T run()throws IOException;}
    private final RootRuntimeContext context;
    private final RootNaturalSuccessionOriginals natural;
    private final CanonicalReplay replay;
    private final ThreadLocal<Held> held=new ThreadLocal<>();
    private static final class Held {
        final ContinuityStorePort.Session same;
        final RootLifecycleAuthority.SnapshotLease lease;
        final WriterContracts.Head head;
        final Map<ExactRef,Issued> issued=new LinkedHashMap<>();
        final Set<ExactRef> historical=new LinkedHashSet<>();
        boolean sealed;boolean prepared;boolean consumed;
        Held(ContinuityStorePort.Session same,RootLifecycleAuthority.SnapshotLease lease,WriterContracts.Head head){this.same=same;this.lease=lease;this.head=head;}
    }
    private record Issued(ContinuityOriginals value,PendingCause cause,Optional<SuccessorUiObligation.Rebind> preflight,
            ExactRef canonicalDomain,ExactRef canonicalObligation) { }
    static final class Prepared<T> {
        private final RootPendingUiContinuity owner;private final Held scope;private final T value;
        private Prepared(RootPendingUiContinuity owner,Held scope,T value){this.owner=owner;this.scope=scope;this.value=value;}
        T value(){return value;}
    }

    RootPendingUiContinuity(RootRuntimeContext context,RootNaturalSuccessionOriginals natural,CanonicalReplay replay){
        this.context=Objects.requireNonNull(context);this.natural=Objects.requireNonNull(natural);this.replay=Objects.requireNonNull(replay);
    }
    <T>T withLease(ContinuityStorePort.Session same,RootLifecycleAuthority.SnapshotLease lease,Work<T> work)throws IOException {
        if(held.get()!=null){var current=held.get();require(!current.prepared&&current.same==same&&current.lease==lease,"continuity may borrow only its identical actual lease");return work.run();}
        require(held.get()==null,"nested same-Game continuity lease forbidden");context.writer().requireSession(same);lease.assertCurrent(same);
        var scope=new Held(same,lease,same.head());held.set(scope);
        try{return work.run();}finally{held.remove();}
    }
    <T>Prepared<T> seal(T value)throws IOException {
        var scope=held.get();require(scope!=null&&!scope.sealed&&!scope.prepared,"only the actual held physical issuer can seal prepared continuity");
        scope.lease.assertCurrent(scope.same);scope.sealed=true;return new Prepared<>(this,scope,Objects.requireNonNull(value));
    }
    <T>T withPrepared(Prepared<?> prepared,Work<T> work)throws IOException {
        Objects.requireNonNull(prepared);var scope=prepared.scope;
        require(prepared.owner==this&&held.get()==null&&scope.sealed&&!scope.prepared&&!scope.consumed,
                "prepared continuity is not this actual private one-use capture");
        replay.requireOutsideObservation(scope.same);scope.prepared=true;held.set(scope);
        try{active(scope.same,scope.lease.fullSnapshot(),scope.lease.sourceQualification(),scope.head);return work.run();}
        finally{scope.consumed=true;held.remove();}
    }
    private Held active(ContinuityStorePort.Session same,FullSnapshot current,SourceQualification source,WriterContracts.Head head)throws IOException {
        var actual=held.get();require(actual!=null&&actual.same==same&&actual.lease.fullSnapshot()==current
                &&actual.lease.sourceQualification()==source&&actual.head.digest().equals(head.digest())
                &&same.head().digest().equals(head.digest()),"continuity escaped its identical actual writer/physical lease/source/head");
        context.writer().requireSession(same);
        if(actual.prepared)replay.requireOutsideObservation(same);else actual.lease.assertCurrent(same);
        source.assertCurrent(same);
        context.game().verify();
        require(context.clock().instant().isBefore(actual.lease.validUntil()),"prepared physical continuity window expired");
        context.transport().verifyHeld(actual.lease.validUntil());
        var transport=current.actual().session();
        require(transport.machineId().equals(context.game().machineId())&&transport.game().equals(context.game().generation())
                &&transport.sessionId().equals(context.game().sessionId())&&current.facts().source().equals(context.source()),
                "continuity crossed the installed actual Game/source/session");
        var managed=context.transport().latestObservedSnapshot().orElseThrow(()->new IOException("actual Managed continuity packet missing"));
        require(managed.session().equals(transport)&&Arrays.equals(managed.originalPacket(),current.actual().originalPacket()),
                "continuity did not retain the actual Managed transport packet");
        context.adopted().authority().withFrozenFacts(same,frozen->{
            if(!(frozen.state() instanceof DriverSnapshotFacts.Known known))throw new IOException("actual continuity Known missing");
            require(Arrays.equals(DriverSnapshotFacts.encodeKnownOriginal(known).bytes(),DriverSnapshotFacts.encodeKnownOriginal(actual.lease.factsKnown()).bytes()),
                    "continuity current full Known differs from the sole canonical writer");return null;
        });return actual;
    }
    void requireCurrentFrame(ContinuityStorePort.Session same,FullSnapshot current,SourceQualification source,WriterContracts.Head head)throws IOException {
        active(same,current,source,head);
    }
    private NaturalClockOriginals.Document document()throws IOException{return NaturalClockOriginals.decode(natural.readExact(natural.currentCaptureDocument()));}
    private SuccessorUiObligation state(DriverSnapshotFacts.Known current)throws IOException {
        var pending=document().pendingProjection().orElseThrow(()->new IOException("canonical pending continuity domain missing"));
        var state=SuccessorUiObligationCodec.decode(natural.readExact(pending.currentObligation()));
        require(Arrays.equals(SuccessorUiObligationCodec.encode(state),DriverJson.encode(current.auxiliary().get(SuccessorUiObligation.AUXILIARY_KEY))),
                "continuity domain obligation differs from actual full Known");return state;
    }
    /** Historical qualification uses this same actual lease before M3 creates its private custody. */
    void requireRetainedPhysical(ContinuityStorePort.Session same,NaturalClockOriginals.Capture capture,SourceQualification source)throws IOException {
        var scope=held.get();require(scope!=null&&scope.same==same,"fresh transport has no actual continuity lease");
        var current=scope.lease.fullSnapshot();active(same,current,source,scope.head);
        require(capture.machineId().equals(current.actual().session().machineId())&&capture.gamePid()==current.actual().session().game().pid()
                &&capture.gameBirthFiletime().equals(current.actual().session().game().creationFiletime().value().toString()),
                "fresh transport cannot replace the retained actual OS Game/image");
        requireSources(same,capture.sourceQualification(),source,capture.sessionId());
    }
    void requireSources(ContinuityStorePort.Session same,Optional<ExactRef> original,SourceQualification source,String originalSession)throws IOException {
        var scope=held.get();require(scope!=null&&scope.same==same,"fresh source comparison lacks its physical lease");
        active(same,scope.lease.fullSnapshot(),source,scope.head);
        source.assertCurrent(same);
    }
    @Override public ContinuityOriginals openQualified(PendingCause cause,ExactRef proof,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,WriterContracts.Head head)throws IOException {
        var scope=active(same,current,source,head);var state=state(scope.lease.factsKnown());var predecessor=state.binding().predecessor();
        require(!scope.prepared,"closed physical loan cannot open or issue new continuity custody");
        require(state.binding().qualifiedCause().equals(proof)&&proof.sha256().equals(cause.causeDigest())
                &&state.binding().successorCharacterId().intValueExact()==cause.successorCharacterId(),"continuity changed the canonical original cause/successor");
        var transport=current.actual().session();
        ExactRef known=context.archive().withSession(same).preserveMaterial(DriverSnapshotFacts.encodeKnownOriginal(scope.lease.factsKnown()));
        var binding=new PendingSameGameContinuity.Binding(transport.machineId(),current.actual().observedAt(),Math.toIntExact(transport.game().pid()),
                transport.game().creationFiletime().value().toString(),document().capture().executable(),proof,predecessor.sessionId(),predecessor.connectionGeneration().toString(),
                transport.sessionId(),transport.connectionGeneration().toString(),predecessor.evidence().completeSourceQualification(),source.proof(),
                context.sources().optionalMetadata(same,source).map(value->value.epochManifest()),
                cause.precommitSnapshot(),current.originalEvidence(),known,current.facts().semanticFactsEvidence(),cause.successorCharacterId(),
                current.facts().driver().session().episodeRunId(),current.facts().episodeEpoch(),current.facts().driverVersion(),head.digest(),head.state().sequence());
        ExactRef ref=context.archive().withSession(same).preserveMaterial(new RawJson(PendingSameGameContinuity.encode(binding)));
        var purpose=state.phase()==SuccessorUiObligation.Phase.FINALIZED?ContinuityPurpose.FINALIZED_METADATA_ONLY:ContinuityPurpose.PENDING_UI;
        var originals=new ContinuityOriginals(ref,binding,purpose,scope.lease.factsKnown());var preflight=preflight(same,state,current,ref);
        var issued=new Issued(originals,cause,preflight,natural.currentCaptureDocument(),document().pendingProjection().orElseThrow().currentObligation());
        scope.issued.put(ref,issued);requireCurrent(originals,cause,proof,current,same,source,head);return originals;
    }
    private Optional<SuccessorUiObligation.Rebind> preflight(ContinuityStorePort.Session same,SuccessorUiObligation state,FullSnapshot current,ExactRef proof)throws IOException {
        if(state.phase()==SuccessorUiObligation.Phase.FINALIZED){replay.requireFinalized(same,state);return Optional.empty();}
        var transport=current.actual().session();
        if(state.rebind().filter(value->value.resumed().sessionId().equals(transport.sessionId())
                &&value.resumed().connectionGeneration().equals(transport.connectionGeneration())).isPresent()){
            replay.requireRebind(same,state);return Optional.empty();
        }
        var lease=held.get().lease;var facts=lease.factsKnown();
        var resumed=new SuccessorUiObligation.UiFrame(transport.machineId(),transport.game(),transport.sessionId(),transport.connectionGeneration(),state.binding().sourceEpochSha256(),
                current.actual().snapshotId(),current.facts().publicRevision(),current.actual().nativeRevision(),OpportunityJson.integer(current.semantic().get("date_raw"),"actual native date"),
                facts.driver().session().actorId(),facts.driver().session().episodeRunId(),facts.stamp().episodeEpoch(),facts.stamp().driverVersion(),current.originalEvidence(),
                lease.originalSemantic(),lease.originalDriver(),lease.sourceQualification().proof(),current.actual().observedAt());
        var prior=document().pendingProjection().orElseThrow().currentObligation();
        var value=state.observation().isPresent()?new SuccessorUiObligation.Rebind(state.observation().orElseThrow().frame(),resumed,prior,proof)
                :SuccessorUiObligation.Rebind.unobserved(state.binding(),resumed,prior,proof);
        SuccessorUiObligationReducer.rebind(state,value);return Optional.of(value);
    }
    Optional<SuccessorUiObligation.Rebind> preparedRebind(ExactRef binding)throws IOException {
        var scope=held.get();var actual=scope==null?null:scope.issued.get(binding);
        require(actual!=null,"prepared Rebind escaped its identical private Root scope");return actual.preflight();
    }
    @Override public void requireCurrent(ContinuityOriginals originals,PendingCause cause,ExactRef proof,FullSnapshot current,
            ContinuityStorePort.Session same,SourceQualification source,WriterContracts.Head head)throws IOException {
        var scope=active(same,current,source,head);var issued=scope.issued.get(originals.binding());
        require(issued!=null&&issued.value()==originals&&issued.cause()==cause&&originals.document().retainedCauseProof().equals(proof)
                &&issued.canonicalDomain().equals(natural.currentCaptureDocument())&&issued.canonicalObligation().equals(document().pendingProjection().orElseThrow().currentObligation()),
                "continuity lost its actual private issuer/canonical predecessor");
        require(Arrays.equals(natural.readExact(originals.binding()),PendingSameGameContinuity.encode(originals.document())),"continuity original bytes changed");
        var state=state(scope.lease.factsKnown());var repeated=preflight(same,state,current,originals.binding());
        require(repeated.equals(issued.preflight()),"actual same-writer Rebind reducer preflight changed");
        for(ExactRef reference:originals.document().materialReferences())same.verifyPin(same.capturePin(reference,Math.toIntExact(reference.bytes())));
        same.verifyPin(same.capturePin(originals.binding(),PendingSameGameContinuity.MAX_BYTES));
        source.assertCurrent(same);if(!scope.prepared)scope.lease.assertCurrent(same);
    }
    @Override public ContinuityOriginals openHistoricalFinalQualified(ContinuityOriginals currentContinuity,PendingCause cause,ExactRef proof,
            RetainedFinalizationOriginals historical,FullSnapshot current,ContinuityStorePort.Session same,SourceQualification source,WriterContracts.Head head)throws IOException {
        requireCurrent(currentContinuity,cause,proof,current,same,source,head);
        var domain=NaturalClockOriginals.decode(natural.readExact(historical.canonicalFinalizationDomain()));
        var state=SuccessorUiObligationCodec.decode(natural.readExact(domain.pendingProjection().orElseThrow().currentObligation()));
        var ref=state.finalization().flatMap(SuccessorUiObligation.Finalization::continuityBinding)
                .orElseThrow(()->new IOException("historical reconnected FINAL lacks its actual canonical final continuity binding"));
        var value=new ContinuityOriginals(ref,PendingSameGameContinuity.decode(natural.readExact(ref)),ContinuityPurpose.PENDING_UI,historical.originals().materials().actualKnown());
        var scope=held.get();scope.historical.add(ref);scope.historical.addAll(value.document().materialReferences());
        requireHistoricalFinalCurrent(value,currentContinuity,cause,proof,historical,current,same,source,head);return value;
    }
    @Override public void requireHistoricalFinalCurrent(ContinuityOriginals historicalContinuity,ContinuityOriginals currentContinuity,PendingCause cause,ExactRef proof,
            RetainedFinalizationOriginals historical,FullSnapshot current,ContinuityStorePort.Session same,SourceQualification source,WriterContracts.Head head)throws IOException {
        requireCurrent(currentContinuity,cause,proof,current,same,source,head);
        var domain=NaturalClockOriginals.decode(natural.readExact(historical.canonicalFinalizationDomain()));
        var state=SuccessorUiObligationCodec.decode(natural.readExact(domain.pendingProjection().orElseThrow().currentObligation()));
        require(state.finalization().flatMap(SuccessorUiObligation.Finalization::continuityBinding).filter(historicalContinuity.binding()::equals).isPresent()
                &&historicalContinuity.purpose()==ContinuityPurpose.PENDING_UI,"historical FINAL continuity is not its original canonical Rebind");
        replay.requireRebind(same,state);require(Arrays.equals(natural.readExact(historicalContinuity.binding()),PendingSameGameContinuity.encode(historicalContinuity.document())),"historical continuity bytes changed");
    }
    @Override public byte[] readExact(ExactRef reference)throws IOException {
        var scope=held.get();require(scope!=null,"continuity reader escaped its actual physical scope");
        boolean allowed=scope.issued.values().stream().anyMatch(value->value.value().binding().equals(reference)||value.value().document().materialReferences().contains(reference));
        if(scope.historical.contains(reference)){
            var pin=scope.same.head().documents().stream().filter(value->value.reference().equals(reference)).findFirst().orElseThrow(()->new IOException("historical continuity material lacks its original canonical pin"));
            scope.same.verifyPin(pin);allowed=true;
        }
        if(!allowed){var domain=document();var ref=domain.pendingProjection().flatMap(value->{try{return SuccessorUiObligationCodec.decode(natural.readExact(value.currentObligation())).rebind().map(SuccessorUiObligation.Rebind::actualPrivateRebindProof);}catch(IOException failure){throw new java.io.UncheckedIOException(failure);}});
            allowed=ref.filter(reference::equals).isPresent();}
        require(allowed,"continuity read is outside its exact finite actual binding closure");return natural.readExact(reference);
    }
}

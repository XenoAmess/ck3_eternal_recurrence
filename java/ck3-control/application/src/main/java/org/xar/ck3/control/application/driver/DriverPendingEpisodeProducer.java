package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.action.RawJson;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationCodec;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligationReducer;
import org.xar.ck3.control.application.lifecycle.SuccessorUiObligation;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Deterministic initial pending projection of the actual installed Root's already committed natural-domain child. */
final class DriverPendingEpisodeProducer {
    static final String SOURCE_KEY=DriverPendingEpisodeSource.PUBLICATION_KEY;
    record Publication(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after,ExactRef originalSource) { }
    record MutationPublication(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after,ExactRef originalSource,
            java.util.Optional<ExactRef> originalResult) { }
    private DriverPendingEpisodeProducer(){ }
    static Publication prepare(ContinuityStorePort.Session same,DriverPendingEpisodeSource.Capture actual,
            OutcomeArchive originals,List<ExactRef> sources) throws IOException {
        requireCommitted(same,actual,sources,true);
        return initial(same,actual,actual.actualReceipt(),originals,sources,java.util.Optional.empty());
    }
    private static Publication initial(ContinuityStorePort.Session same,DriverPendingEpisodeSource.InitialData actual,WriterContracts.Receipt receipt,
            OutcomeArchive originals,List<ExactRef> sources,java.util.Optional<ExactRef> recordedSource) throws IOException {
        var before=actual.actualKnown();var terminal=actual.terminalSnapshot();var pending=actual.pendingEpisode();var child=actual.canonicalProjection();
        StrictJson.require(terminal.facts()==before&&terminal.originalEvidence().equals(actual.originalBeforeNative()),"pending terminal snapshot must retain the actual original Known/native object");
        var expected=SuccessorUiObligationReducer.pendingEpisode(terminal,pending.obligation().binding());
        StrictJson.require(Arrays.equals(expected.driver().encode(),pending.driver().encode())&&expected.auxiliary().equals(pending.auxiliary())
                &&expected.obligation().equals(pending.obligation()),"pending Driver differs from the sole non-final pure projection");
        StrictJson.require(child.beforeVersion()==before.stamp().driverVersion()&&child.beforeEpoch()==before.stamp().episodeEpoch()
                &&child.beforeDriverSha256().equals(before.stamp().driverSha256())&&child.game().equals(before.stamp().game())
                &&child.machineId().equals(pending.obligation().binding().predecessor().machineId())
                &&child.observedAtUtc().equals(pending.obligation().binding().qualifiedAtUtc())
                &&child.oldEpisodeRunId().equals(before.driver().session().episodeRunId())&&child.oldActor().equals(before.driver().session().actorId())
                &&child.newEpisodeRunId().equals(pending.driver().session().episodeRunId())&&child.newActor().equals(pending.driver().session().actorId())
                &&child.qualifiedCause().equals(pending.obligation().binding().qualifiedCause()),"canonical pending child changed its original subject/cause");
        requireMaterial(originals,child.beforeDriver(),RawJson.fullMaterial(before.driver().encode()));
        requireMaterial(originals,child.afterDriver(),RawJson.fullMaterial(pending.driver().encode()));
        requireMaterial(originals,child.auxiliary(),RawJson.fullMaterial(DriverJson.encode(pending.auxiliary())));
        requireMaterial(originals,child.obligation(),new RawJson(SuccessorUiObligationCodec.encode(pending.obligation())));
        requireMaterial(originals,actual.projectionOriginal(),new RawJson(child.encode()));
        StrictJson.require(DriverPendingEpisodeProjection.decode(originals.loadMaterial(actual.projectionOriginal()).bytes()).equals(child),"canonical pending child roundtrip changed");
        originals.loadFullMaterial(child.qualifiedCause());
        ExactRef beforeKnown=knownOriginal(originals,before,recordedSource.isEmpty());
        requireBeforeNative(originals,actual.originalBeforeNative(),before);
        DriverSnapshotFacts.originalKnownJson(originals.loadFullMaterial(actual.originalParentKnown()).bytes());
        var metadata=new DriverPendingEpisodeSource.InitialMetadata(child.machineId(),child.observedAtUtc(),beforeKnown,
                actual.originalBeforeNative(),actual.originalParentKnown(),actual.canonicalDomainRef(),receipt.head().sequence(),
                ContinuityJson.digest(receipt.head().toJson()),receipt.eventIdentity(),actual.projectionOriginal(),sources);
        ExactRef reference=sourceOriginal(originals,metadata,recordedSource);
        var stamp=new DriverSnapshotFacts.Stamp(child.afterVersion(),child.afterEpoch(),child.game(),child.newEpisodeRunId(),child.afterDriver().sha256());
        var after=new DriverSnapshotFacts.Known(pending.driver(),stamp,before.originalHistoryBasis(),List.of(),
                pending.auxiliary().with(SOURCE_KEY,DriverObservationEvidenceReader.reference(reference)),before.loop(),java.util.Optional.empty());
        return new Publication(before,after,reference);
    }
    static void requireCommitted(ContinuityStorePort.Session same,DriverPendingEpisodeSource.Capture actual,List<ExactRef> sources,
            boolean exactCurrentHead) throws IOException {
        requireDomain(same,actual.originalPrepared(),actual.actualReceipt(),actual.canonicalDomainRef(),sources,exactCurrentHead);
        for(ExactRef original:List.of(actual.projectionOriginal(),actual.canonicalProjection().qualifiedCause())) {
            var pin=same.capturePin(original,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);
        }
    }
    static MutationPublication prepareMutation(ContinuityStorePort.Session same,DriverPendingEpisodeSource.Mutation actual,
            OutcomeArchive originals,List<ExactRef> sources) throws IOException {
        requireMutationCommitted(same,actual,sources,true);
        return mutation(same,actual,actual.actualReceipt(),originals,sources,java.util.Optional.empty());
    }
    private static MutationPublication mutation(ContinuityStorePort.Session same,DriverPendingEpisodeSource.MutationData actual,WriterContracts.Receipt receipt,
            OutcomeArchive originals,List<ExactRef> sources,java.util.Optional<ExactRef> recordedSource) throws IOException {
        var before=actual.actualKnown();var retained=actual.preparedProjection();
        var projection=DriverPendingEpisodeMutations.project(before,actual.beforeObligation(),actual.change());
        StrictJson.require(projection.obligation().equals(actual.afterObligation())&&projection.obligation().equals(retained.projection().obligation())
                &&Arrays.equals(projection.driver().encode(),retained.projection().driver().encode())
                &&projection.auxiliary().equals(retained.projection().auxiliary())&&projection.result().equals(retained.projection().result()),
                "actual canonical pending mutation differs from its sole deterministic projection");
        requireMaterial(originals,retained.beforeDriver(),RawJson.fullMaterial(before.driver().encode()));
        requireMaterial(originals,retained.afterDriver(),RawJson.fullMaterial(projection.driver().encode()));
        requireMaterial(originals,retained.afterAuxiliary(),RawJson.fullMaterial(DriverJson.encode(projection.auxiliary())));
        requireMaterial(originals,retained.beforeObligation(),new RawJson(SuccessorUiObligationCodec.encode(actual.beforeObligation())));
        requireMaterial(originals,retained.afterObligation(),new RawJson(SuccessorUiObligationCodec.encode(projection.obligation())));
        StrictJson.require(projection.result().isPresent()==retained.originalResult().isPresent(),"pending final result source presence changed");
        if(projection.result().isPresent())requireMaterial(originals,retained.originalResult().orElseThrow(),projection.result().orElseThrow());
        ExactRef beforeKnown=knownOriginal(originals,before,recordedSource.isEmpty());
        requireBeforeNative(originals,actual.originalBeforeNative(),before);
        var metadata=new DriverPendingEpisodeSource.MutationMetadata(projection.obligation().binding().predecessor().machineId(),
                actual.actualObservedAtUtc(),beforeKnown,actual.originalBeforeNative(),
                actual.canonicalDomainRef(),receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()),receipt.eventIdentity(),
                actual.change().phase(),retained.beforeObligation(),retained.afterObligation(),sources);
        ExactRef reference=sourceOriginal(originals,metadata,recordedSource);
        var stamp=before.stamp();var afterStamp=new DriverSnapshotFacts.Stamp(Math.addExact(stamp.driverVersion(),1),stamp.episodeEpoch(),stamp.game(),
                stamp.episodeRunId(),DriverJson.sha256(projection.driver().encode()));
        var after=new DriverSnapshotFacts.Known(projection.driver(),afterStamp,before.originalHistoryBasis(),before.actionRows(),
                projection.auxiliary().with(DriverPendingEpisodeSource.MUTATION_KEY,DriverObservationEvidenceReader.reference(reference)),before.loop(),java.util.Optional.empty());
        return new MutationPublication(before,after,reference,retained.originalResult());
    }
    static void requireMutationCommitted(ContinuityStorePort.Session same,DriverPendingEpisodeSource.Mutation actual,List<ExactRef> sources,
            boolean exactCurrentHead) throws IOException {
        requireDomain(same,actual.originalPrepared(),actual.actualReceipt(),actual.canonicalDomainRef(),sources,exactCurrentHead);
        var projection=actual.preparedProjection();
        var originals=new java.util.ArrayList<>(List.of(projection.beforeDriver(),projection.afterDriver(),projection.afterAuxiliary(),projection.beforeObligation(),projection.afterObligation()));
        projection.originalResult().ifPresent(originals::add);
        for(ExactRef original:originals){var pin=same.capturePin(original,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
    }
    private static void requireDomain(ContinuityStorePort.Session same,DomainBodies.PreparedImport prepared,WriterContracts.Receipt receipt,
            ExactRef domain,List<ExactRef> sources,boolean exactCurrentHead) throws IOException {
        StrictJson.require(prepared.request().slot()==DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS
                &&prepared.request().contractSchema().equals(DriverPendingEpisodeSource.DOMAIN_SCHEMA)
                &&prepared.originalBody().reference().equals(prepared.request().originalBody())
                &&prepared.request().originalBody().bytes()==domain.bytes()
                &&prepared.request().originalBody().sha256().equals(domain.sha256())
                &&receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE
                &&receipt.head().sequence()==Math.addExact(prepared.predecessor().state().sequence(),1),"pending episode requires its actual v2 natural-domain commit");
        String committed=ContinuityJson.digest(receipt.head().toJson());same.requireHistoricalState(receipt.head().sequence(),committed);
        if(exactCurrentHead)StrictJson.require(same.head().digest().equals(committed),"pending publication lost its immediate actual commit head");
        same.verifyPin(prepared.originalBody());for(var pin:prepared.sources())same.verifyPin(pin);for(var pin:prepared.evidence())same.verifyPin(pin);
        var read=same.readDomain(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS);
        StrictJson.require(read instanceof DomainBodies.Available,"actual canonical pending natural document unavailable");
        var current=(DomainBodies.Available)read;
        StrictJson.require(current.reference().payload().equals(domain)
                &&current.reference().contractSchema().equals(DriverPendingEpisodeSource.DOMAIN_SCHEMA)
                &&DomainBodies.reference(receipt.head(),DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS).orElseThrow().equals(current.reference())
                &&Arrays.equals(current.canonicalBody(),prepared.request().producerInput())
                &&current.canonicalBody().length==domain.bytes()
                &&DriverJson.sha256(current.canonicalBody()).equals(domain.sha256()),"pending projection is not the actual current canonical natural document");
        for(ExactRef original:List.of(domain)) {
            var pin=same.capturePin(original,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);
        }
        for(ExactRef source:sources){var pin=same.capturePin(source,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
    }
    /** Historical DATA replay uses the actual recorded reducer edge, never a reconstructed warm PreparedImport. */
    static Publication replayInitial(ContinuityStorePort.Session same,DriverPendingEpisodeSource.RecordedCapture actual,
            OutcomeArchive originals,List<ExactRef> sources)throws IOException {
        requireRecorded(same,actual.recordedImport(),actual.canonicalDomainRef(),sources);
        return initial(same,actual,actual.recordedImport().receipt(),originals,sources,java.util.Optional.of(actual.originalSource()));
    }
    static MutationPublication replayMutation(ContinuityStorePort.Session same,DriverPendingEpisodeSource.RecordedMutation actual,
            OutcomeArchive originals,List<ExactRef> sources)throws IOException {
        requireRecorded(same,actual.recordedImport(),actual.canonicalDomainRef(),sources);
        return mutation(same,actual,actual.recordedImport().receipt(),originals,sources,java.util.Optional.of(actual.originalSource()));
    }
    static void requireRecorded(ContinuityStorePort.Session same,DomainBodies.RecordedImport actual,ExactRef domain,List<ExactRef> sources)throws IOException {
        var receipt=actual.receipt();String digest=ContinuityJson.digest(receipt.head().toJson());
        var replayed=same.requireHistoricalImport(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS,receipt.head().sequence(),digest);
        StrictJson.require(replayed.receipt().equals(receipt)&&replayed.predecessor().digest().equals(actual.predecessor().digest())
                &&replayed.body().equals(actual.body())&&replayed.canonicalEvent().equals(actual.canonicalEvent())
                &&Arrays.equals(replayed.request().producerInput(),actual.request().producerInput())
                &&replayed.request().slot()==DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS
                &&replayed.request().contractSchema().equals(DriverPendingEpisodeSource.DOMAIN_SCHEMA)
                &&replayed.body().payload().equals(domain)&&replayed.request().producerInput().length==domain.bytes()
                &&DriverJson.sha256(replayed.request().producerInput()).equals(domain.sha256()),"pending recovery is not the exact actual recorded natural-domain reducer edge");
        for(var pin:replayed.currentInputs())same.verifyPin(pin);
        for(ExactRef source:sources){var pin=same.capturePin(source,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
    }
    private static ExactRef knownOriginal(OutcomeArchive originals,DriverSnapshotFacts.Known before,boolean preserve) {
        var raw=DriverSnapshotFacts.encodeKnownOriginal(before);ExactRef ref=preserve?originals.preserveMaterial(raw):originals.materialReferenceOf(raw);
        requireMaterial(originals,ref,raw);return ref;
    }
    private static ExactRef sourceOriginal(OutcomeArchive originals,DriverPendingEpisodeSource.RecoveryMetadata metadata,
            java.util.Optional<ExactRef> recorded) {
        RawJson raw=metadata.encode();ExactRef ref=recorded.orElseGet(()->originals.preserveMaterial(raw));requireMaterial(originals,ref,raw);
        StrictJson.require(DriverPendingEpisodeSource.decodeRecoveryMetadata(originals.loadMaterial(ref)).equals(metadata),"pending v2 source metadata differs from its sole typed codec/replayed originals");return ref;
    }
    private static void requireBeforeNative(OutcomeArchive originals,ExactRef nativeRef,DriverSnapshotFacts.Known before) {
        byte[] packet=originals.loadNativeFrame(nativeRef);
        if(before.observation().isPresent()) {
            ExactRef manifestRef=before.observation().orElseThrow().semanticFactsEvidence();RawJson manifest=originals.loadFullMaterial(manifestRef);
            var nativeFrame=DriverObservationEvidenceReader.nativeFrame(manifestRef,manifest,packet);
            var replayed=DriverObservationEvidenceReader.decode(manifestRef,manifest,RawJson.fullMaterial(before.driver().encode()),nativeFrame);
            StrictJson.require(replayed.equals(before.observation().orElseThrow()),"pending before Known/native observation original differs");
        }
    }
    private static void requireMaterial(OutcomeArchive originals,ExactRef reference,RawJson body) {
        StrictJson.require(reference.equals(originals.materialReferenceOf(body))&&Arrays.equals(originals.loadFullMaterial(reference).bytes(),body.bytes()),
                "pending original material differs from its exact complete producer");
    }
}

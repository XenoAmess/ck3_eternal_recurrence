package org.xar.ck3.control.application.driver;

import java.io.IOException;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.DomainBodies;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.succession.SuccessionNativeEstate12004;

/** Deterministic full Driver projection from the installed source's already committed original preclock domain. */
final class DriverPreclockExpectationProducer {
    static final String SOURCE_KEY="driver_preclock_expectation_source";
    record Publication(DriverSnapshotFacts.Known before,DriverStateSnapshot.Complete replacement,
            OpportunityJson.Obj auxiliary,ExactRef source) { }
    private DriverPreclockExpectationProducer() { }

    static Publication prepare(ContinuityStorePort.Session same,DriverPreclockExpectationSource.Capture capture,
            ActionPorts.OutcomeArchive archive,List<ExactRef> installedSources) throws IOException {
        var before=capture.actualKnown();var frame=capture.actualComplete();var prepared=capture.originalPrepared();var receipt=capture.actualReceipt();
        StrictJson.require(prepared.request().slot()==DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS
                &&prepared.originalBody().reference().equals(prepared.request().originalBody())
                &&prepared.request().originalBody().bytes()==capture.canonicalDomainRef().bytes()
                &&prepared.request().originalBody().sha256().equals(capture.canonicalDomainRef().sha256())
                &&receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE
                &&receipt.head().sequence()==Math.addExact(prepared.predecessor().state().sequence(),1)
                &&same.head().digest().equals(ContinuityJson.digest(receipt.head().toJson())),"expectation requires the exact current committed natural preclock domain");
        same.requireHistoricalState(receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()));
        same.verifyPin(prepared.originalBody());for(var pin:prepared.sources())same.verifyPin(pin);for(var pin:prepared.evidence())same.verifyPin(pin);
        var canonical=same.readDomain(DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS);
        StrictJson.require(canonical instanceof DomainBodies.Available,"actual canonical preclock domain unavailable");
        var current=(DomainBodies.Available)canonical;
        StrictJson.require(current.reference().payload().equals(capture.canonicalDomainRef())
                &&current.reference().contractSchema().equals(prepared.request().contractSchema())
                &&Arrays.equals(current.canonicalBody(),prepared.request().producerInput())
                &&current.canonicalBody().length==capture.canonicalDomainRef().bytes()
                &&DriverJson.sha256(current.canonicalBody()).equals(capture.canonicalDomainRef().sha256())
                &&DomainBodies.reference(receipt.head(),DomainBodies.Slot.NATURAL_CLOCK_ORIGINALS).orElseThrow().equals(current.reference()),
                "preclock expectation source is not the actual committed canonical body");
        var canonicalPin=same.capturePin(capture.canonicalDomainRef(),WriterContracts.MAX_PIN_BYTES);same.verifyPin(canonicalPin);
        for(ExactRef source:installedSources){var pin=same.capturePin(source,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        var observed=before.observation().orElseThrow(()->new IOException("preclock expectation requires its original complete Driver observation"));
        StrictJson.require(frame.identity().game().equals(before.stamp().game())&&frame.identity().frame().episodeRunId().equals(before.stamp().episodeRunId())
                &&frame.identity().frame().identity().player().equals(before.driver().session().actorId())
                &&frame.source().equals(observed.source())&&frame.sessionId().equals(observed.transport().sessionId())
                &&frame.connectionGeneration().equals(observed.transport().connectionGeneration()),"preclock expectation crossed its actual full Driver subject/source/session");
        var nativeFrame=DriverObservationEvidenceReader.nativeFrame(observed.semanticFactsEvidence(),archive.loadMaterial(observed.semanticFactsEvidence()),archive.loadNativeFrame(frame.originalEvidence()));
        var assembled=new DriverObservationAssembler().assemble(nativeFrame,observed,frame.originalEvidence());
        StrictJson.require(assembled instanceof DriverObservationAssembler.Complete&&assembled.equals(frame),"preclock expectation semantic must be the complete original manifest/native projection");
        var root=capture.originalRootReceipt();var request=root.request();var clock=capture.originalClock();
        StrictJson.require(request.origin() instanceof CommandOrigin.Gameplay&&request.operation().value().equals("query-campaign-root-context-v1")
                &&request.before().equals(frame.identity())&&request.source().equals(frame.source())&&request.sessionId().equals(frame.sessionId())
                &&root.original().originalResultToken().orElseThrow().equals(capture.originalRootResult())
                &&root.before().binding().nativeEvidence().equals(frame.originalEvidence())
                &&root.after().binding().nativeEvidence().equals(frame.originalEvidence())
                &&root.before().binding().connectionGeneration().equals(frame.connectionGeneration())
                &&root.after().binding().connectionGeneration().equals(frame.connectionGeneration())
                &&clock.origin() instanceof CommandOrigin.Gameplay&&clock.operation().value().equals("resume-map")
                &&clock.before().equals(frame.identity())&&clock.source().equals(frame.source())&&clock.sessionId().equals(frame.sessionId()),
                "preclock expectation lost its real ROOT read or fixed original clock command");
        ExactRef rootRead=archive.readReferenceOf(root);StrictJson.require(archive.loadRead(rootRead).equals(root),"preclock original ROOT receipt archive changed");
        StrictJson.require(Arrays.equals(archive.loadMaterial(capture.clockCommandRef()).bytes(),ActionCodec.encodeCommand(clock)),"preclock fixed child body changed");
        archive.loadMaterial(capture.parentCommandRef());
        var estate=SuccessionNativeEstate12004.freeze(capture.originalRootResult().bytes(),DriverJson.encode(frame.semantic()));
        var replacement=replace(before.driver(),estate);
        ExactRef beforeRef=archive.materialReferenceOf(new RawJson(before.driver().encode()));
        ExactRef afterRef=archive.preserveMaterial(new RawJson(replacement.encode()));
        ExactRef expectation=archive.preserveMaterial(new RawJson(estate.wire()));
        StrictJson.require(Arrays.equals(archive.loadMaterial(beforeRef).bytes(),before.driver().encode())
                &&Arrays.equals(archive.loadMaterial(afterRef).bytes(),replacement.encode())
                &&Arrays.equals(archive.loadMaterial(expectation).bytes(),estate.wire()),"preclock full Driver/expectation archive readback differs");
        var source=new LinkedHashMap<String,OpportunityJson.Value>();
        source.put("schema",new OpportunityJson.Text("xar.driver-preclock-expectation-source/v1"));
        source.put("canonical_event_identity",new OpportunityJson.Text(receipt.eventIdentity()));
        source.put("canonical_head_sha256",new OpportunityJson.Text(ContinuityJson.digest(receipt.head().toJson())));
        for(var entry:java.util.Map.of("canonical_domain",capture.canonicalDomainRef(),"root_read",rootRead,"root_result",archive.materialReferenceOf(capture.originalRootResult()),
                "before_driver",beforeRef,"after_driver",afterRef,"expectation",expectation,"parent_command",capture.parentCommandRef(),"clock_command",capture.clockCommandRef()).entrySet())
            source.put(entry.getKey(),DriverObservationEvidenceReader.reference(entry.getValue()));
        source.put("original_manifest",DriverObservationEvidenceReader.reference(observed.semanticFactsEvidence()));
        source.put("original_native",DriverObservationEvidenceReader.reference(frame.originalEvidence()));
        source.put("producer_sources",new OpportunityJson.Arr(installedSources.stream().<OpportunityJson.Value>map(DriverObservationEvidenceReader::reference).toList()));
        ExactRef proof=archive.preserveMaterial(new RawJson(DriverJson.encode(new OpportunityJson.Obj(source))));
        var auxiliary=before.auxiliary().with(SOURCE_KEY,DriverObservationEvidenceReader.reference(proof));
        return new Publication(before,replacement,auxiliary,proof);
    }
    /** Pure estate data has no publication authority. Root's installed source and the original writer own the caller. */
    static DriverStateSnapshot.Complete replace(DriverStateSnapshot.Complete before,SuccessionNativeEstate12004.FrozenEstate estate) {
        var expected=estate.expectation().binding();
        StrictJson.require(expected.episodeRunId().equals(before.session().episodeRunId())
                &&before.session().actorId().equals(java.math.BigInteger.valueOf(expected.episodeCharacterId())),"preclock estate belongs to another Driver episode/actor");
        return new DriverStateSnapshot.Complete(before.session(),before.commandHistory(),before.lastCheckpoint(),before.rollbackWarFailure(),
                before.managedRestoreTransaction(),new DriverStateSnapshot.Value(estate.wire()),before.successionLifecycle(),before.campaignGoal(),before.rollbackWarFailures());
    }
}

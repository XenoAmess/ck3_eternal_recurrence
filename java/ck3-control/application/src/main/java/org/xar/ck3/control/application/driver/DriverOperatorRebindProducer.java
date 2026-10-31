package org.xar.ck3.control.application.driver;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** Reopens the one committed operator Window transition and actual original Native/Driver evidence before its sole CAS. */
final class DriverOperatorRebindProducer {
    static final String SCHEMA="xar.java.operator-driver-publication/v2";
    record Publication(DriverSnapshotFacts.Known before,DriverSnapshotFacts.Known after,ExactRef originalSource,
            ExactRef originalDriver,EpisodeWindow.OperatorRebind transition) { }
    private DriverOperatorRebindProducer(){ }
    static Publication prepare(ContinuityStorePort.Session same,DriverOperatorRebindSource.Capture actual,
            OutcomeArchive archive,List<ExactRef> sources,ActionReceipt canonical) throws IOException {
        var change=requireCommitted(same,actual,sources,true);var before=actual.actualKnown();var command=actual.originalCommand();
        StrictJson.require(command.expectation() instanceof CommandExpectation.OperatorRebind,"actual typed operator expectation required");
        var expectation=((CommandExpectation.OperatorRebind)command.expectation()).expected();expectation.validateCommand(command);
        StrictJson.require(expectation.request().equals(actual.request())&&expectation.episodeEpoch()==before.stamp().episodeEpoch()
                &&expectation.episodeRunId().equals(before.stamp().episodeRunId())&&expectation.beforeDriver().equals(change.originals().beforeDriver()),
                "operator expectation differs from its actual Driver/window predecessor");
        StrictJson.require(canonical.command().equals(command)&&!canonical.settled(),"operator CAS requires its original unresolved canonical action");
        ExactRef receipt=archive.receiptReferenceOf(canonical);
        StrictJson.require(archive.loadReceipt(receipt).equals(canonical),"original operator receipt/prepared-outbound archive differs");
        var attempt=ActionTransitions.attempt(canonical.state()).orElseThrow();var dispatch=ActionTransitions.dispatch(canonical.state()).orElseThrow();
        StrictJson.require(dispatch instanceof NativeActionPort.AckReceived,"actual original operator ACK required");
        var ack=(NativeActionPort.AckReceived)dispatch;
        StrictJson.require(ack.nativeOk()&&ack.outbound().isPresent()&&attempt.requestId().equals(change.requestId())
                &&ack.requestId().equals(change.requestId())&&attempt.preparedRequest().step().equals(actual.request().step())
                &&attempt.preparedRequest().requiredCapability().filter(org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch.CAPABILITY::equals).isPresent()
                &&attempt.preparedRequest().additionalFields().objectFieldNames().isEmpty(),"operator original ACK/prepared request differs");
        StrictJson.require(archive.referenceOf(ack).equals(change.originals().ack())&&archive.load(change.originals().ack()).equals(ack),"operator Window ACK is not the original canonical ACK");
        var nativeResult=DriverJson.object(ack.originalResultToken().orElseThrow().bytes(),DriverJson.MAX_NATIVE_BYTES);
        String status=text(nativeResult.get("status"),"actual operator status");
        StrictJson.require(java.util.Set.of("switched","already_played").contains(status),"operator did not return a supported identity resolution");
        StrictJson.require(change.actionId().equals(command.actionId())&&change.bodySha256().equals(ActionCodec.bodySha256(command))
                &&change.source().equals(command.source().sourceRef())&&change.requestId().equals(attempt.requestId()),"operator Window changed its actual action/source/body/request");
        requireFrame(actual.actualBefore(),before,change.originals().beforeNative(),archive);
        requireFrame(actual.actualAfter(),before,change.originals().afterNative(),archive);
        var first=actual.actualBefore();var last=actual.actualAfter();
        StrictJson.require(first.actual().session().equals(last.actual().session())&&first.facts().source().equals(command.source())
                &&last.facts().source().equals(command.source())&&first.actual().session().sessionId().equals(command.sessionId())
                &&first.actual().session().game().equals(before.stamp().game())
                &&first.facts().publicRevision().equals(actual.request().expectedRevision())
                &&!last.actual().observedAt().isBefore(first.actual().observedAt()),"operator raw observations crossed source/session/revision/chronology");
        var oldNative=DriverObservationAssembler.canonicalNativeState(first.actual()).semantic();
        var newNative=DriverObservationAssembler.canonicalNativeState(last.actual()).semantic();
        for(var frame:List.of(oldNative,newNative))StrictJson.require(bool(frame.get("paused"),"paused")&&bool(frame.get("map_ready"),"map_ready"),"operator requires actual paused map frames");
        var oldActor=before.driver().session().actorId();
        // The original operator accepts a null player or a player already different from the bound episode actor.
        // Its old Window subject is the actual Driver actor; the independent raw packet retains the current native player unchanged.
        var newPlayer=object(newNative.get("played_character"),"played_character");var actor=integer(newPlayer.get("character_id"),"character_id");
        StrictJson.require(actor.equals(java.math.BigInteger.valueOf(actual.request().characterId()))
                &&bool(newPlayer.get("alive"),"alive"),"operator independent after did not actually play its living target");
        requireIdentity(change.before(),first,before,oldActor);requireIdentity(change.after(),last,before,actor);
        StrictJson.require(change.beforeDriverVersion()==before.stamp().driverVersion()&&change.afterDriverVersion()==Math.addExact(before.stamp().driverVersion(),1),"operator version differs from actual owner");
        var replacement=DriverOperatorRebindProjection.propose(before,actual.request());
        StrictJson.require(replacement.rebindPerformed(),"same actor requires no Window event or Driver CAS");
        requireMaterial(archive,change.originals().beforeDriver(),RawJson.fullMaterial(before.driver().encode()));
        requireMaterial(archive,change.originals().afterDriver(),RawJson.fullMaterial(replacement.driver().encode()));
        requireMaterial(archive,change.originals().beforeAuxiliary(),RawJson.fullMaterial(DriverJson.encode(before.auxiliary())));
        requireMaterial(archive,change.originals().afterAuxiliary(),RawJson.fullMaterial(DriverJson.encode(replacement.auxiliary())));
        archive.readOriginalPacket(change.originals().hello());
        var row=new LinkedHashMap<String,Value>();row.put("schema",new Text(SCHEMA));
        row.put("machine_id",new Text(command.source().machineId()));row.put("observed_at_utc",new Text(last.actual().observedAt().toString()));
        row.put("transition",DriverJson.fromNode(change.toJson()));row.put("canonical_head_sha256",new Text(ContinuityJson.digest(actual.actualReceipt().head().toJson())));
        row.put("predecessor_head_sha256",new Text(actual.originalPrepared().predecessor().digest()));
        row.put("canonical_sequence",new OpportunityJson.IntegerValue(java.math.BigInteger.valueOf(actual.actualReceipt().head().sequence())));
        row.put("event_identity",new Text(actual.actualReceipt().eventIdentity()));row.put("original_receipt",DriverObservationEvidenceReader.reference(receipt));
        row.put("fresh_read_proof",DriverObservationEvidenceReader.reference(actual.originalFreshReadProof()));
        archive.loadMaterial(actual.originalFreshReadProof());
        row.put("producer_sources",new Arr(sources.stream().<Value>map(DriverObservationEvidenceReader::reference).toList()));
        RawJson source=new RawJson(DriverJson.encode(new Obj(row)));ExactRef original=archive.preserveMaterial(source);requireMaterial(archive,original,source);
        var stamp=new DriverSnapshotFacts.Stamp(change.afterDriverVersion(),before.stamp().episodeEpoch(),before.stamp().game(),before.stamp().episodeRunId(),DriverJson.sha256(replacement.driver().encode()));
        var after=new DriverSnapshotFacts.Known(replacement.driver(),stamp,before.originalHistoryBasis(),before.actionRows(),replacement.auxiliary(),before.loop(),Optional.empty());
        return new Publication(before,after,original,change.originals().afterDriver(),change);
    }
    static EpisodeWindow.OperatorRebind requireCommitted(ContinuityStorePort.Session same,DriverOperatorRebindSource.Capture actual,List<ExactRef> sources,
            boolean exactHead) throws IOException {
        var prepared=actual.originalPrepared();var receipt=actual.actualReceipt();var change=EpisodeWindow.operatorRebind(prepared.request());
        StrictJson.require(receipt.disposition()!=WriterContracts.Disposition.NO_CHANGE,"operator requires its actual durable changed-actor Window transition");
        same.requireCommitted(prepared,receipt);
        EpisodeWindow.requireReduction(prepared.predecessor().state(),prepared.reduced(),prepared.request(),false);
        EpisodeWindow.requireReduction(prepared.predecessor().state(),receipt.head(),prepared.request(),true);
        same.requireHistoricalState(receipt.head().sequence(),ContinuityJson.digest(receipt.head().toJson()));
        if(exactHead)StrictJson.require(same.head().digest().equals(ContinuityJson.digest(receipt.head().toJson())),"operator publication must consume its immediate actual Window head");
        var installedCodeRefs=java.util.Set.copyOf(sources);
        for(var pin:prepared.sources())if(!installedCodeRefs.contains(pin.reference()))same.verifyPin(pin);
        for(var pin:prepared.evidence())same.verifyPin(pin);
        for(ExactRef ref:change.originals().references()){var pin=same.capturePin(ref,WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
        StrictJson.require(prepared.request().evidence().contains(actual.originalFreshReadProof()),"operator canonical request omitted its actual fresh receive proof");
        var freshPin=same.capturePin(actual.originalFreshReadProof(),WriterContracts.MAX_PIN_BYTES);same.verifyPin(freshPin);
        StrictJson.require(prepared.sources().stream().map(WriterContracts.Pin::reference).toList().containsAll(sources),"operator canonical transition omitted installed producer sources");
        return change;
    }
    private static void requireIdentity(EpisodeWindow.Identity identity,DriverObservationAssembler.FullSnapshot frame,DriverSnapshotFacts.Known before,java.math.BigInteger actor) {
        StrictJson.require(identity.machineId().equals(frame.actual().session().machineId())&&identity.game().equals(before.stamp().game())
                &&identity.sessionId().equals(frame.actual().session().sessionId())&&identity.episodeRunId().equals(before.stamp().episodeRunId())
                &&identity.epoch()==before.stamp().episodeEpoch()&&java.math.BigInteger.valueOf(identity.actorId()).equals(actor)
                &&java.math.BigInteger.valueOf(identity.dateRaw()).equals(integer(frame.semantic().get("date_raw"),"date_raw")),"operator Window/raw identity differs");
    }
    private static void requireFrame(DriverObservationAssembler.FullSnapshot frame,DriverSnapshotFacts.Known before,ExactRef original,OutcomeArchive archive) {
        StrictJson.require(frame.facts().driverVersion()==before.stamp().driverVersion()&&frame.facts().episodeEpoch()==before.stamp().episodeEpoch()
                &&Arrays.equals(frame.facts().driver().encode(),before.driver().encode())&&frame.originalEvidence().equals(original)
                &&Arrays.equals(frame.actual().originalPacket(),archive.loadNativeFrame(original)),"operator actual raw Native/Driver originals differ");
        var replay=new DriverObservationAssembler().projectFull(frame.actual(),frame.facts(),original);
        StrictJson.require(replay.equals(frame),"operator FullSnapshot differs from the actual sole original projection");
    }
    private static void requireMaterial(OutcomeArchive archive,ExactRef original,RawJson actual) {
        StrictJson.require(archive.materialReferenceOf(actual).equals(original)&&Arrays.equals(archive.loadFullMaterial(original).bytes(),actual.bytes()),"operator full original material differs");
    }
}

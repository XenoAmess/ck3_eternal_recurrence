package org.xar.ck3.control.application.driver;

import static org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import java.util.Set;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.action.ActionPorts.OutcomeArchive;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot;
import org.xar.ck3.control.application.planning.identity.OperatorPlayerSwitch;
import org.xar.ck3.control.continuity.ContinuityJson;
import org.xar.ck3.control.continuity.EpisodeWindow;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort.Session;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.*;

/** The exact no-recorder policy of the original explicit operator interface. These replay methods grant no current frame. */
public final class DriverOperatorRebindOriginals {
    private DriverOperatorRebindOriginals(){ }
    public record PublicationOriginal(EpisodeWindow.OperatorRebind transition,long canonicalSequence,String canonicalHeadSha256,
            String predecessorHeadSha256,String eventIdentity,ExactRef originalReceipt,ExactRef freshReadProof,List<ExactRef> producerSources) {
        public PublicationOriginal {
            java.util.Objects.requireNonNull(transition);StrictJson.safe(canonicalSequence,1);
            for(String digest:List.of(canonicalHeadSha256,predecessorHeadSha256,eventIdentity))
                StrictJson.require(digest.matches("[0-9a-f]{64}"),"exact original operator digest required");
            java.util.Objects.requireNonNull(originalReceipt);java.util.Objects.requireNonNull(freshReadProof);producerSources=List.copyOf(producerSources);
            StrictJson.require(freshReadProof.bytes()>0&&originalReceipt.bytes()>0&&!producerSources.isEmpty()&&producerSources.size()<=128
                    &&producerSources.stream().distinct().count()==producerSources.size()&&producerSources.stream().allMatch(ref->ref.bytes()>0),
                    "finite nonempty original operator source closure required");
        }
    }
    public static PublicationOriginal decodePublication(RawJson original) {
        Obj row=DriverJson.object(original.bytes(),DriverJson.MAX_NATIVE_BYTES);
        StrictJson.require(row.members().keySet().equals(Set.of("schema","machine_id","observed_at_utc","transition","canonical_head_sha256",
                "canonical_sequence","predecessor_head_sha256","event_identity","original_receipt","fresh_read_proof","producer_sources"))
                &&new Text(DriverOperatorRebindProducer.SCHEMA).equals(row.get("schema")),"exact operator publication source required");
        var transition=EpisodeWindow.OperatorRebind.fromJson(DriverJson.toNode(row.get("transition")));
        StrictJson.require(transition.after().machineId().equals(text(row.get("machine_id"),"machine_id")),"operator source machine differs");
        java.time.Instant.parse(text(row.get("observed_at_utc"),"observed_at_utc"));
        String head=digest(row.get("canonical_head_sha256")),predecessor=digest(row.get("predecessor_head_sha256")),event=digest(row.get("event_identity"));
        long sequence=integer(row.get("canonical_sequence"),"canonical_sequence").longValueExact();StrictJson.safe(sequence,1);
        var sources=array(row.get("producer_sources"),"producer_sources").stream().map(DriverObservationEvidenceReader::reference).toList();
        StrictJson.require(!sources.isEmpty()&&sources.size()<=128&&sources.stream().distinct().count()==sources.size(),"finite original operator producer sources required");
        return new PublicationOriginal(transition,sequence,head,predecessor,event,DriverObservationEvidenceReader.reference(row.get("original_receipt")),DriverObservationEvidenceReader.reference(row.get("fresh_read_proof")),sources);
    }
    public static OperatorPlayerSwitch.Completion requireOriginals(ActionReceipt actual,OutcomeArchive archive) {
        StrictJson.require(actual.command().expectation() instanceof CommandExpectation.OperatorRebind&&actual.state() instanceof ActionState.Settled,
                "exact settled original operator action required");
        var settled=(ActionState.Settled)actual.state();StrictJson.require(settled.settlement() instanceof ActionState.OperatorRebound,"actual typed operator identity settlement required");
        var completion=((ActionState.OperatorRebound)settled.settlement()).observation();
        var expectation=((CommandExpectation.OperatorRebind)actual.command().expectation()).expected();
        expectation.validateCommand(actual.command());expectation.validateCompletion(completion);
        completion.validate(actual.command(),settled.attempt(),settled.dispatch());
        var refs=completion.originals();
        StrictJson.require(archive.referenceOf(settled.dispatch()).equals(refs.ack())&&archive.load(refs.ack()).equals(settled.dispatch()),"operator original ACK differs");
        archive.readOriginalPacket(refs.hello());
        for(ExactRef nativeRef:List.of(refs.beforeNative(),refs.afterNative()))archive.loadNativeFrame(nativeRef);
        var rebound=archive.loadFullMaterial(refs.reboundNative());
        OperatorPlayerSwitch.requireRebound(completion.request(),completion.episodeRunId(),DriverJson.toNode(DriverJson.object(rebound.bytes(),DriverJson.MAX_NATIVE_BYTES)));
        var before=DriverStateSnapshot.decodeComplete(archive.loadFullMaterial(refs.beforeDriver()).bytes());
        var after=DriverStateSnapshot.decodeComplete(archive.loadFullMaterial(refs.afterDriver()).bytes());
        var auxiliary=DriverJson.object(archive.loadFullMaterial(refs.beforeAuxiliary()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var afterAuxiliary=DriverJson.object(archive.loadFullMaterial(refs.afterAuxiliary()).bytes(),DriverJson.MAX_NATIVE_BYTES);
        var expected=DriverOperatorRebindProjection.propose(before,auxiliary,completion.request());
        StrictJson.require(Arrays.equals(expected.driver().encode(),after.encode())&&expected.auxiliary().equals(afterAuxiliary)
                &&expected.rebindPerformed()==completion.rebindPerformed(),"operator original full Driver/auxiliary changed its sole projection");
        StrictJson.require(before.session().episodeRunId().equals(completion.episodeRunId())&&after.session().episodeRunId().equals(completion.episodeRunId())
                &&before.session().actorId().longValueExact()==completion.priorActor()&&after.session().actorId().longValueExact()==completion.request().characterId(),
                "operator originals crossed their actual old/new subject");
        if(completion.rebindPerformed()) {
            var original=decodePublication(archive.loadMaterial(refs.privateProof()));var change=original.transition();
            archive.loadMaterial(original.freshReadProof());
            StrictJson.require(change.actionId().equals(actual.command().actionId())&&change.bodySha256().equals(actual.bodySha256())
                    &&change.requestId().equals(completion.requestId())&&change.beforeDriverVersion()==completion.beforeDriverVersion()
                    &&change.afterDriverVersion()==completion.afterDriverVersion()&&change.source().equals(actual.command().source().sourceRef())
                    &&change.originals().equals(new EpisodeWindow.OperatorOriginals(refs.hello(),refs.beforeNative(),refs.ack(),refs.afterNative(),
                            refs.beforeDriver(),refs.afterDriver(),refs.beforeAuxiliary(),refs.afterAuxiliary())),"operator private publication differs from its actual completion originals");
            var pending=archive.loadReceipt(original.originalReceipt());
            StrictJson.require(pending.command().equals(actual.command())&&!pending.settled()&&ActionTransitions.attempt(pending.state()).filter(settled.attempt()::equals).isPresent()
                    &&ActionTransitions.dispatch(pending.state()).filter(settled.dispatch()::equals).isPresent(),"operator publication lost the actual original unresolved receipt");
            archive.loadMaterial(refs.canonicalCommit());
        }else {
            StrictJson.require(refs.beforeDriver().equals(refs.afterDriver())&&refs.beforeAuxiliary().equals(refs.afterAuxiliary()),"already-bound operator must preserve exact Driver/auxiliary originals");
            var pending=archive.loadReceipt(refs.canonicalCommit());
            StrictJson.require(pending.command().equals(actual.command())&&!pending.settled()&&ActionTransitions.attempt(pending.state()).filter(settled.attempt()::equals).isPresent()
                    &&ActionTransitions.dispatch(pending.state()).filter(settled.dispatch()::equals).isPresent(),"unchanged operator must retain its genuine original ACK receipt locator");
            archive.loadMaterial(refs.privateProof()); // The installed archive verifier owns the strict no-change private Root schema.
        }
        return completion;
    }
    /** Same-writer historical Window membership, never an archive-directory or latest-file inference. */
    public static void requireCanonical(Session same,ActionReceipt actual,OutcomeArchive archive) throws IOException {
        var completion=requireOriginals(actual,archive);
        if(!completion.rebindPerformed())return; // Exact same-actor private source remains mandatory in the receipt archive verifier.
        var original=decodePublication(archive.loadMaterial(completion.originals().privateProof()));var change=original.transition();
        var before=same.requireHistoricalState(Math.subtractExact(original.canonicalSequence(),1),original.predecessorHeadSha256());
        var after=same.requireHistoricalState(original.canonicalSequence(),original.canonicalHeadSha256());
        EpisodeWindow.requireReduction(before,after,change.request(),true);
        var lineage=EpisodeWindow.operatorLineage(after);
        StrictJson.require(!lineage.isEmpty()&&lineage.getLast().equals(change)&&after.toJson().get("last_event_identity").asText().equals(original.eventIdentity()),
                "operator completion lacks its actual canonical Window lineage member");
        var canonical=archive.loadMaterial(completion.originals().canonicalCommit());
        StrictJson.require(ContinuityJson.same(ContinuityJson.parseObject(canonical.bytes(),ContinuityJson.LEDGER_MAX_BYTES),after.toJson()),
                "operator canonical commit artifact differs from the actual historical Window head");
        archive.loadMaterial(original.freshReadProof());var freshPin=same.capturePin(original.freshReadProof(),org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);same.verifyPin(freshPin);
        for(ExactRef source:original.producerSources()){var pin=same.capturePin(source,org.xar.ck3.control.continuity.writer.WriterContracts.MAX_PIN_BYTES);same.verifyPin(pin);}
    }
    /** Coverage check for the Bootstrap's actual private current Driver. Arguments alone never issue a current owner or Ready. */
    public static void requireCoveredBy(Session same,ActionReceipt actual,OutcomeArchive archive,DriverStateSnapshot.Complete actualDriver,
            long actualVersion,long actualEpoch,org.xar.ck3.control.contracts.GameGeneration actualGame,String actualSessionId) throws IOException {
        String head=same.head().digest();DriverActionHistoryCodec.verifyOperator(same,actual,archive);
        var completion=requireOriginals(actual,archive);var original=DriverStateSnapshot.decodeComplete(archive.loadFullMaterial(completion.originals().afterDriver()).bytes());
        StrictJson.require(actualGame.equals(completion.transport().game())&&actualSessionId.equals(completion.transport().sessionId())
                &&actualEpoch==completion.episodeEpoch()&&actualVersion>=completion.afterDriverVersion()
                &&actualDriver.session().pipeName().equals(original.session().pipeName())&&actualDriver.session().bridgePid()==actualGame.pid()
                &&actualDriver.session().episodeRunId().equals(completion.episodeRunId()),"operator coverage crossed its actual private current Game/session/run/epoch/version");
        requireHistoryPrefix(original,actualDriver);
        java.math.BigInteger actor=original.session().actorId();long version=completion.afterDriverVersion();var preceding=original;
        var lineage=EpisodeWindow.operatorLineage(same.head().state());int start=0;
        if(completion.rebindPerformed()) {
            var transition=decodePublication(archive.loadMaterial(completion.originals().privateProof())).transition();
            int at=lineage.indexOf(transition);StrictJson.require(at>=0,"current canonical operator lineage lost this original operator");start=at+1;
        }else {
            // A no-op has no Window descriptor. Only later true operator transitions can change its actor.
            while(start<lineage.size()&&lineage.get(start).afterDriverVersion()<=version)start++;
        }
        for(int index=start;index<lineage.size();index++) {
            var change=lineage.get(index);
            StrictJson.require(change.before().game().equals(actualGame)&&change.before().sessionId().equals(actualSessionId)
                    &&change.before().episodeRunId().equals(completion.episodeRunId())&&change.before().epoch()==actualEpoch
                    &&java.math.BigInteger.valueOf(change.before().actorId()).equals(actor)&&change.beforeDriverVersion()>=version,
                    "current operator coverage requires its exact subsequent canonical actor lineage");
            var before=DriverStateSnapshot.decodeComplete(archive.loadFullMaterial(change.originals().beforeDriver()).bytes());
            var after=DriverStateSnapshot.decodeComplete(archive.loadFullMaterial(change.originals().afterDriver()).bytes());
            var auxiliary=DriverJson.object(archive.loadFullMaterial(change.originals().beforeAuxiliary()).bytes(),DriverJson.MAX_NATIVE_BYTES);
            StrictJson.require(before.session().actorId().equals(actor)&&before.session().episodeRunId().equals(completion.episodeRunId())
                    &&before.session().pipeName().equals(original.session().pipeName())&&before.session().bridgePid()==actualGame.pid(),"operator successor original Driver subject differs");
            requireHistoryPrefix(preceding,before);
            var projected=DriverOperatorRebindProjection.propose(before,auxiliary,
                    // This is only the pure actor-state projection. The actual prepared revision/ACK was already checked by the canonical source authority.
                    new OperatorPlayerSwitch.Request(change.after().actorId(),java.math.BigInteger.ZERO));
            StrictJson.require(projected.rebindPerformed()&&Arrays.equals(projected.driver().encode(),after.encode())
                    &&projected.auxiliary().equals(DriverJson.object(archive.loadFullMaterial(change.originals().afterAuxiliary()).bytes(),DriverJson.MAX_NATIVE_BYTES)),
                    "subsequent canonical operator changed an unrelated original Driver/auxiliary slot");
            actor=after.session().actorId();version=change.afterDriverVersion();preceding=after;
        }
        StrictJson.require(actor.equals(actualDriver.session().actorId())&&actualVersion>=version,"current actor lacks its actual canonical operator successor chain");
        requireHistoryPrefix(preceding,actualDriver);
        StrictJson.require(same.head().digest().equals(head),"operator coverage changed the actual writer head");
    }
    private static void requireHistoryPrefix(DriverStateSnapshot.Complete original,DriverStateSnapshot.Complete current) {
        StrictJson.require(original.commandHistory().size()<=current.commandHistory().size(),"current Driver lost original operator history");
        for(int i=0;i<original.commandHistory().size();i++)StrictJson.require(Arrays.equals(original.commandHistory().get(i).originalRow().json(),
                current.commandHistory().get(i).originalRow().json()),"current Driver rewrote an original operator history row");
    }
    private static String digest(Value value){String result=text(value,"digest");StrictJson.require(result.matches("[0-9a-f]{64}"),"original digest required");return result;}
}

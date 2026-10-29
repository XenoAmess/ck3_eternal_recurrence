package org.xar.ck3.control.application.advance;

import static org.junit.jupiter.api.Assertions.*;
import java.nio.file.Path;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.xar.ck3.control.application.action.*;
import org.xar.ck3.control.application.effects.NativeEffectEvidence;
import org.xar.ck3.control.application.effects.RootGuardEvidence;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.nativebridge.ActionWriterIntegrationFixture;
import org.xar.ck3.control.nativebridge.NativeWire;

/** The real guarded writer/barrier/archive supplies the zero-write receipt. Negative
 * response mutations below are explicit archived DATA: they never grant a canonical
 * action, Root permission, actual request custody or a successful native rejection.
 * The public parent's actual known-negative endpoint matrix is a separate mandatory
 * RootPublicPauseRuntimeTest input; it is not replaced by these boundary tests.
 */
final class AdvancePrimitiveNegativeReplayTest {
    @TempDir Path root;
    private static ActionCommand pause(ActionCommand actual) {
        return new ActionCommand(actual.actionId(),actual.before(),actual.source(),actual.sessionId(),actual.operation(),actual.arguments(),
                AdvancePrimitives.expected(actual.before(),actual.source(),actual.operation(),actual.arguments()),actual.claims(),actual.deadline());
    }
    private static AdvanceObservationPort.Frame originalFrame(ActionState.Attempt attempt,ActionPorts.OutcomeArchive archive,
            NativeEffectEvidence.FrameLoader frames) {
        var actual=RootGuardEvidence.loadFrame(attempt.guard(),archive,frames);
        return new AdvanceObservationPort.Frame(actual.identity(),actual.source(),actual.sessionId(),actual.semantic(),
                new ObservationProvenance.Push(actual.identity().frame().snapshotId(),actual.identity().frame().identity().nativeRevision(),actual.originalEvidence()),
                actual.observedAt(),actual.originalEvidence());
    }
    private static AdvancePlan plan(AdvanceObservationPort.Frame actual) {
        var start=actual.identity().frame().identity().dateRaw();
        return new AdvancePlan(start,start.add(AdvancePlan.DAY),1,1,"negative-replay-regression",false,
                AdvancePlan.ClockMode.POLLED,Optional.empty(),Optional.empty());
    }
    @Test void actualCanonicalZeroWriteRetainsItsOriginalStateAndColdReplayDoesNotWriteOrResend()throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(root.resolve("canonical-zero-pause"),false)) {
            var command=pause(actual.command("canonical-zero-pause"));
            var replay=new AdvancePrimitiveArchivedReplay(actual.physicalInputs().frameLoader());
            actual.stopAtIntentBarrier.set(4);
            actual.writer.locked(same->{
                var failure=assertThrows(ReadPublicationRequiredException.class,()->actual.coordinator.execute(same,command));
                var receipt=failure.zeroDispatchReceipt().orElseThrow();
                var zero=assertInstanceOf(ActionState.RejectedBeforeDispatch.class,receipt.state());
                assertEquals(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,zero.dispatch().proof().stage());
                assertEquals(0,zero.dispatch().proof().requestBytesWritten());
                var archive=actual.archive.withSession(same);var ref=archive.receiptReferenceOf(receipt);
                assertEquals(receipt,ContinuityActionJournal.lookup(same.head().state(),command.actionId(),archive).orElseThrow());
                long sequence=same.head().state().sequence();byte[] ledger=actual.ledgerBytes();
                int writes=actual.nativeActionWrites(),reads=actual.nativeReadWrites();
                replay.verify(same.head(),receipt,archive);
                var cold=archive.loadReceipt(ref);replay.verify(cold,archive);
                assertEquals(ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH,cold.outcome());
                assertFalse(cold.visibleGameplay());assertFalse(cold.eligibleAdvance());assertTrue(cold.ack().isEmpty());
                var frame=originalFrame(zero.attempt(),archive,actual.physicalInputs().frameLoader());
                var clockError=assertThrows(IllegalArgumentException.class,()->AdvanceClockArchivedReplay.verifySequence(plan(frame),frame,frame,
                        AdvanceClock.ProgressStatus.POSTCONDITION,Optional.empty(),List.of(cold)));
                assertTrue(clockError.getMessage().contains("zero-write"),"valid zero-write control evidence cannot complete Life/Battle clock recovery");
                assertEquals(receipt,actual.coordinator.execute(same,command));
                assertEquals(sequence,same.head().state().sequence());assertArrayEquals(ledger,actual.ledgerBytes());
                assertEquals(writes,actual.nativeActionWrites());assertEquals(reads,actual.nativeReadWrites());assertEquals(0,writes);
                var forged=new ActionReceipt(receipt.version(),receipt.sequence()+1,command,receipt.bodySha256(),receipt.state());
                assertThrows(IllegalArgumentException.class,()->replay.verify(same.head(),forged,archive));
                var unknown=new ActionReceipt(receipt.version(),receipt.sequence(),command,receipt.bodySha256(),
                        new ActionState.Unknown(Optional.of(zero.attempt()),Optional.of(zero.dispatch()),"DATA cannot relabel zero-write as native settlement",List.of()));
                assertThrows(IllegalArgumentException.class,()->replay.verify(unknown,archive));
                return null;
            });
        }
    }
    @Test void anActualPositiveAckCannotBeRelabelledAsANativePauseRejection()throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(root.resolve("positive-ack-is-not-rejection"),false)) {
            var command=pause(actual.command("actual-positive-ack"));
            actual.writer.locked(same->{
                var receipt=actual.coordinator.execute(same,command);var attempt=ActionTransitions.attempt(receipt.state()).orElseThrow();
                var ack=receipt.ack().orElseThrow();assertTrue(ack.nativeOk());
                var archive=actual.archive.withSession(same);var original=archive.referenceOf(ack);
                var data=new ActionReceipt(receipt.version(),receipt.sequence(),command,receipt.bodySha256(),
                        new ActionState.Settled(attempt,ack,new ActionState.Rejected(attempt.requestId(),"DATA-only rejection",original)));
                var replay=new AdvancePrimitiveArchivedReplay(actual.physicalInputs().frameLoader());
                long sequence=same.head().state().sequence();int writes=actual.nativeActionWrites();
                assertThrows(IllegalArgumentException.class,()->replay.verify(same.head(),data,archive));
                assertEquals(sequence,same.head().state().sequence());assertEquals(writes,actual.nativeActionWrites());return null;
            });
        }
    }
    @Test void archivedNegativeDataWithoutActualRequestCustodyCannotEnterThePrimitiveReplay()throws Exception {
        try(var actual=new ActionWriterIntegrationFixture(root.resolve("missing-rejection-custody"),false)) {
            var command=pause(actual.command("original-before-negative-DATA"));
            actual.writer.locked(same->{
                var original=actual.coordinator.execute(same,command);var attempt=ActionTransitions.attempt(original.state()).orElseThrow();
                var accepted=original.ack().orElseThrow();var archive=actual.archive.withSession(same);
                // This is intentionally a new DATA packet, not an endpoint response. Retaining
                // the genuine outbound alone cannot invent its missing receive chronology.
                var node=StrictJson.object().put("type","command_result").put("protocol_version",1)
                        .put("request_id",attempt.requestId()).put("ok",false).put("error","DATA-only native rejection");
                var frame=new RawJson(StrictJson.canonical(node));
                var dataAck=new NativeActionPort.AckReceived(attempt.requestId(),false,Optional.empty(),frame,
                        NativeWire.packet(frame.bytes()),accepted.outbound(),Optional.empty());
                var reference=archive.preserve(dataAck);
                var data=new ActionReceipt(original.version(),original.sequence(),command,original.bodySha256(),
                        new ActionState.Settled(attempt,dataAck,new ActionState.Rejected(attempt.requestId(),"DATA-only native rejection",reference)));
                var ref=archive.preserveReceipt(data);var cold=archive.loadReceipt(ref);
                var replay=new AdvancePrimitiveArchivedReplay(actual.physicalInputs().frameLoader());
                long sequence=same.head().state().sequence();int writes=actual.nativeActionWrites();
                var error=assertThrows(IllegalArgumentException.class,()->replay.verify(cold,archive));
                assertTrue(error.getMessage().contains("custody"));
                var before=originalFrame(attempt,archive,actual.physicalInputs().frameLoader());
                var clockError=assertThrows(IllegalArgumentException.class,()->AdvanceClockArchivedReplay.verifySequence(plan(before),before,before,
                        AdvanceClock.ProgressStatus.POSTCONDITION,Optional.empty(),List.of(cold)));
                assertTrue(clockError.getMessage().contains("map-unavailable"),"general known rejection support does not widen the clock retry profile");
                // Supplying the real head additionally refuses this noncanonical DATA receipt.
                assertThrows(IllegalArgumentException.class,()->replay.verify(same.head(),cold,archive));
                assertEquals(sequence,same.head().state().sequence());assertEquals(writes,actual.nativeActionWrites());return null;
            });
        }
    }
}

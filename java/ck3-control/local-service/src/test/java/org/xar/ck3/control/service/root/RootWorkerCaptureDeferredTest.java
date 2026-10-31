package org.xar.ck3.control.service.root;

import java.io.IOException;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.ContinuityBatchJournal.CleanRestartTicket;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.MissingDriverObservation;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import static org.junit.jupiter.api.Assertions.*;

/** Actual production capture helper; callback data is synthetic and submits no Native or writer work. */
final class RootWorkerCaptureDeferredTest {
    private static final ExactRef REF = new ExactRef("unit-captured-head",1,"1".repeat(64));
    private static RootOrdinaryWorkerLoop.Result result(RootOrdinaryWorkerLoop.StopReason stop,
            BatchReport.Terminal terminal, Optional<String> detail) {
        var owner=new SessionIdentity("fixture-machine",new GameGeneration(1,new PythonOnlyUInt64(BigInteger.valueOf(100))),"same-session");
        var tick=new SessionClock.Tick(0,Instant.parse("2026-10-28T00:00:00Z"));
        var report=new BatchReport(owner,"unit-batch-48",terminal,"unit actual boundary",tick,tick,
                List.of(),List.of(),List.of(),List.of(),List.of(),List.of(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.empty(),Optional.of(REF),
                0,0,true,List.of(),List.of(),List.of());
        return new RootOrdinaryWorkerLoop.Result(Optional.of(report),49,stop,detail);
    }
    private static RootOrdinaryWorkerLoop.Result stopped() {
        return result(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,BatchReport.Terminal.CHECKPOINT_DEFERRED,Optional.empty());
    }
    @Test void actualCaptureTicketIsReturnedUnchangedForStopAndNoProgress()throws Exception {
        var ticket=new CleanRestartTicket(REF,1,"2".repeat(64),REF);var calls=new AtomicInteger();
        var captured=RootOrdinaryWorkerMain.captureForStop(stopped(),()->{calls.incrementAndGet();return ticket;});
        assertSame(ticket,captured.orElseThrow());
        var noProgress=result(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS,BatchReport.Terminal.WALL_TIMEOUT,Optional.empty());
        assertSame(ticket,RootOrdinaryWorkerMain.captureForStop(noProgress,()->{calls.incrementAndGet();return ticket;}).orElseThrow());
        assertEquals(2,calls.get());
    }
    @Test void onlyTypedMissingObservationOnBenignStopReturnsNoTicket()throws Exception {
        var calls=new AtomicInteger();
        assertTrue(RootOrdinaryWorkerMain.captureForStop(stopped(),()->{calls.incrementAndGet();throw new MissingDriverObservation();}).isEmpty());
        assertEquals(1,calls.get());
    }
    @Test void ordinaryIoEvenWithIdenticalTextIsNotConvertedToDeferred() {
        var failure=new IOException(new MissingDriverObservation().getMessage());
        assertSame(failure,assertThrows(IOException.class,()->RootOrdinaryWorkerMain.captureForStop(stopped(),()->{throw failure;})));
    }
    @Test void unknownOrFailureDetailCannotUseTheBenignDeferral() {
        var failure=new MissingDriverObservation();
        var unknown=result(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,BatchReport.Terminal.ACTION_UNKNOWN,Optional.empty());
        assertSame(failure,assertThrows(MissingDriverObservation.class,()->RootOrdinaryWorkerMain.captureForStop(unknown,()->{throw failure;})));
        var failed=result(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,BatchReport.Terminal.CHECKPOINT_DEFERRED,Optional.of("actual failure"));
        assertSame(failure,assertThrows(MissingDriverObservation.class,()->RootOrdinaryWorkerMain.captureForStop(failed,()->{throw failure;})));
    }
    @Test void noProgressMissingObservationRemainsAnError() {
        var failure=new MissingDriverObservation();
        var noProgress=result(RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS,BatchReport.Terminal.WALL_TIMEOUT,Optional.empty());
        assertSame(failure,assertThrows(MissingDriverObservation.class,()->RootOrdinaryWorkerMain.captureForStop(noProgress,()->{throw failure;})));
    }
    @Test void interruptionAndUnresolvedInvariantRemainOriginalFailures() {
        var interrupted=new InterruptedException("actual drain interrupted");
        assertSame(interrupted,assertThrows(InterruptedException.class,()->RootOrdinaryWorkerMain.captureForStop(stopped(),()->{throw interrupted;})));
        var unresolved=new IllegalArgumentException("unresolved original action remains retained without replay");
        assertSame(unresolved,assertThrows(IllegalArgumentException.class,()->RootOrdinaryWorkerMain.captureForStop(stopped(),()->{throw unresolved;})));
    }
}

package org.xar.ck3.control.service.root;

import java.util.Optional;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.application.session.SessionPorts.SessionIdentity;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import java.math.BigInteger;
import java.time.Instant;
import java.util.List;

final class RootOrdinaryWorkerMainClassificationTest {
    private static final ExactRef HEAD = new ExactRef("fixture-ledger-head", 1, "1".repeat(64));

    private static BatchReport report(BatchReport.Terminal terminal) {
        var identity = new SessionIdentity("fixture-machine", new GameGeneration(1L, new PythonOnlyUInt64(BigInteger.valueOf(100))), "same-session-id");
        var tick = new SessionClock.Tick(0, Instant.parse("2026-10-28T00:00:00Z"));
        return new BatchReport(identity, "batch-01", terminal, "fixture boundary",
                tick, tick, List.of(), List.of(), List.of(), List.of(), List.of(), List.of(),
                Optional.empty(), Optional.empty(), Optional.empty(), Optional.empty(), Optional.of(HEAD),
                0, 0, false, List.of(), List.of(), List.of());
    }

    @Test void operatorStopWithCheckpointDeferredIsNotFailure() {
        var result = new RootOrdinaryWorkerLoop.Result(
            Optional.of(report(BatchReport.Terminal.CHECKPOINT_DEFERRED)),
            1L,
            RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,
            Optional.empty()
        );
        assertFalse(RootOrdinaryWorkerMain.classifyFailureStop(result));
    }

    @Test void operatorStopWithCheckpointDeferredAndFailureDetailIsFailure() {
        var result = new RootOrdinaryWorkerLoop.Result(
            Optional.of(report(BatchReport.Terminal.CHECKPOINT_DEFERRED)),
            1L,
            RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,
            Optional.of("some failure")
        );
        assertTrue(RootOrdinaryWorkerMain.classifyFailureStop(result));
    }

    @Test void terminalFailureWithCheckpointDeferredIsFailure() {
        var result = new RootOrdinaryWorkerLoop.Result(
            Optional.of(report(BatchReport.Terminal.CHECKPOINT_DEFERRED)),
            1L,
            RootOrdinaryWorkerLoop.StopReason.TERMINAL_FAILURE,
            Optional.empty()
        );
        assertTrue(RootOrdinaryWorkerMain.classifyFailureStop(result));
    }

    @Test void operatorStopWithTurnBoundIsNotFailure() {
        var result = new RootOrdinaryWorkerLoop.Result(
            Optional.of(report(BatchReport.Terminal.TURN_BOUND)),
            1L,
            RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,
            Optional.empty()
        );
        assertFalse(RootOrdinaryWorkerMain.classifyFailureStop(result));
    }

    @Test void operatorStopWithActionUnknownIsFailure() {
        var result = new RootOrdinaryWorkerLoop.Result(
            Optional.of(report(BatchReport.Terminal.ACTION_UNKNOWN)),
            1L,
            RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP,
            Optional.empty()
        );
        assertTrue(RootOrdinaryWorkerMain.classifyFailureStop(result));
    }

    @Test void noProgressWithCheckpointDeferredIsFailure() {
        var result = new RootOrdinaryWorkerLoop.Result(
            Optional.of(report(BatchReport.Terminal.CHECKPOINT_DEFERRED)),
            1L,
            RootOrdinaryWorkerLoop.StopReason.NO_PROGRESS,
            Optional.empty()
        );
        assertTrue(RootOrdinaryWorkerMain.classifyFailureStop(result));
    }
}
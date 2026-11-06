package org.xar.ck3.control.service.root;

import static org.junit.jupiter.api.Assertions.*;
import static org.xar.ck3.control.application.session.SessionPorts.*;

import java.io.IOException;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.action.ActionCodec;
import org.xar.ck3.control.application.action.ActionReceipt;
import org.xar.ck3.control.application.action.ActionReceiptCodec;
import org.xar.ck3.control.application.planning.PlanTrace;
import org.xar.ck3.control.application.session.BatchReport;
import org.xar.ck3.control.application.session.SessionClock;
import org.xar.ck3.control.contracts.StrictJson;

/** Frozen receipt DATA and existing STOP/default-denial seams; never a Root/Native authority fixture. */
final class OriginalLifeWarmObservationDataTest {
    @Test void frozenFailureQualificationAndStopNeverDispatch() throws Exception {
        byte[] parentBytes = fixture("receipt-754.json", "896b54ed5e1454dc8fff7e2d93cb4dc3ea78fd1fce070af1d8df5816153be87f");
        byte[] runningBytes = fixture("receipt-749.json", "9939118ac797dcbebf4feba3951a6ebe20c9b36e8e8f9e07bd3543266a4cbcea");
        byte[] childBytes = fixture("receipt-753.json", "3cd59508cbacfed5ae0d4b91056e265b9ec4625830ae36cb0e3a092d04842144");
        // These composite DATA branches decode without resolving any archive reference.
        ActionReceipt parent = ActionReceiptCodec.decodeReceipt(parentBytes, null);
        ActionReceipt running = ActionReceiptCodec.decodeReceipt(runningBytes, null);
        var command = parent.command();
        byte[] originalCommand = ActionCodec.encodeCommand(command);
        var owner = new SessionIdentity(command.origin().machineId(), command.origin().game(), command.sessionId());
        var tick = new SessionClock.Tick(0L, Instant.parse("2026-11-06T00:00:00Z"));
        var returned = new BatchReport.PhaseSpan(BatchReport.Phase.ACTION, tick, tick, BatchReport.PhaseTerminal.RETURNED);
        var turn = turn(parent, 1);
        BatchReport failure = report(owner, BatchReport.Terminal.ACTION_UNKNOWN, "original action remains UNRESOLVED", tick, List.of(returned), List.of(turn));
        assertSame(parent, RootOrdinaryWorkerLoop.postAckLifeReadFailure(failure).orElseThrow());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, BatchReport.Terminal.WRITER_UNKNOWN, failure.detail(), tick, List.of(returned), List.of(turn))).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), "foreign failure", tick, List.of(returned), List.of(turn))).isEmpty());
        var foreign = new SessionIdentity(owner.machineId(), owner.game(), "foreign-session");
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(foreign, failure.terminal(), failure.detail(), tick, List.of(returned), List.of(turn))).isEmpty());
        var failed = new BatchReport.PhaseSpan(BatchReport.Phase.ACTION, tick, tick, BatchReport.PhaseTerminal.FAILED);
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), failure.detail(), tick, List.of(failed), List.of(turn))).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), failure.detail(), tick, List.of(returned), List.of())).isEmpty());
        assertTrue(RootOrdinaryWorkerLoop.postAckLifeReadFailure(report(owner, failure.terminal(), failure.detail(), tick, List.of(returned), List.of(turn(running, 1), turn(parent, 2)))).isEmpty());

        // A reason is only a scheduling filter, never proof of Native ACK/custody or a permit.
        String reason = StrictJson.parse(childBytes).path("state").path("reason").asText();
        assertTrue(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason.replace("native_ok=false", "native_ok=true")));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason.replace("fresh_full_state_native_read_unavailable", "other_native_error")));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason + "; guard rejected"));
        assertFalse(RootOrdinaryWorkerLoop.knownNegativeFreshRead("postcondition unavailable:java.io.IOException: guard rejected"));
        assertTrue(RootOrdinaryWorkerLoop.knownNegativeFreshRead(reason));

        AtomicInteger dispatched = new AtomicInteger();
        RootOrdinaryWorkerLoop.BatchCall refusing = limits -> { dispatched.incrementAndGet(); throw new AssertionError("new batch dispatched"); };
        assertFalse(refusing.recoverPostAckLifeRead(failure, 23L, tick.utc().plusSeconds(300)));
        assertEquals(0, dispatched.get());
        AtomicInteger accesses = new AtomicInteger();
        AtomicInteger callbacks = new AtomicInteger();
        var control = new RootOrdinaryWorkerLoop.Control() {
            @Override public boolean stopRequested() { return true; }
            @Override public void onBatchCompleted(BatchReport report, long next) { callbacks.incrementAndGet(); }
        };
        var configuration = new RootOrdinaryWorkerLoop.Configuration("warm-data", 1, Duration.ofMinutes(20), Duration.ofMinutes(2), Duration.ofMillis(100), 1);
        var loop = new RootOrdinaryWorkerLoop(configuration, control, Clock.fixed(tick.utc(), ZoneOffset.UTC));
        RootOrdinaryWorkerLoop.BatchAccess access = () -> { accesses.incrementAndGet(); throw new AssertionError("STOP opened a Root"); };
        var stopped = loop.run(access, 23L);
        assertEquals(RootOrdinaryWorkerLoop.StopReason.OPERATOR_STOP, stopped.stopReason());
        assertEquals(23L, stopped.nextBatchSequence());
        assertTrue(stopped.lastReport().isEmpty());
        assertTrue(stopped.failureDetail().isEmpty());
        assertEquals(0, accesses.get()); assertEquals(0, callbacks.get()); assertEquals(0, dispatched.get());
        assertSame(parent, RootOrdinaryWorkerLoop.postAckLifeReadFailure(failure).orElseThrow());
        assertArrayEquals(originalCommand, ActionCodec.encodeCommand(parent.command()));
        assertEquals(Instant.parse("2026-11-05T21:53:40.942612100Z"), parent.command().deadline());
        assertArrayEquals(parentBytes, fixture("receipt-754.json", ActionCodec.sha256(parentBytes)));
        assertArrayEquals(runningBytes, fixture("receipt-749.json", ActionCodec.sha256(runningBytes)));
        assertArrayEquals(childBytes, fixture("receipt-753.json", ActionCodec.sha256(childBytes)));
        System.out.println("WARM_DATA_PASS original_receipts=3 report_denials=6 reason_denials=4 stop_access=0 default_dispatch=0 original_command_preserved=true private_root_recovery_exercised=false");
    }

    private static BatchReport.Turn turn(ActionReceipt receipt, int index) {
        var before = receipt.command().before();
        return new BatchReport.Turn(index, before, new PlanTrace(before, List.of(), Optional.empty()), receipt, new TurnFacts(false, false, List.of()));
    }

    private static BatchReport report(SessionIdentity owner, BatchReport.Terminal terminal, String detail,
            SessionClock.Tick tick, List<BatchReport.PhaseSpan> phases, List<BatchReport.Turn> turns) {
        return new BatchReport(owner, "warm-data-22", terminal, detail, tick, tick, phases, turns,
                List.of(), List.of(), List.of(), List.of(), Optional.empty(), Optional.empty(), Optional.empty(),
                Optional.empty(), Optional.empty(), 0L, 0, true, List.of(), List.of(), List.of());
    }

    private static byte[] fixture(String name, String sha) throws IOException {
        try (var input = OriginalLifeWarmObservationDataTest.class.getResourceAsStream("/warm-life-observation/" + name)) {
            if (input == null) throw new IOException("missing exact frozen receipt resource: " + name);
            byte[] bytes = input.readAllBytes(); assertEquals(sha, ActionCodec.sha256(bytes)); return bytes;
        }
    }
}

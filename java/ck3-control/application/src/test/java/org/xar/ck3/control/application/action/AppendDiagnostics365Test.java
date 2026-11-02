package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.file.Path;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Optional;
import java.util.Set;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.xar.ck3.control.continuity.writer.WriterContracts.*;

/** Real public Journal adapter over controlled memory DATA ports, not physical writer/Root qualification. */
final class AppendDiagnostics365Test {
    private static final String MACHINE = "postcommit322-software";
    private static final Instant DEADLINE = Instant.parse("2023-01-01T00:00:30Z");

    @Test void submittingReportsCompletedStagesWhileOtherStatesStaySilent() throws Exception {
        Memory memory = new Memory();
        var journal = new ContinuityActionJournal(memory, memory.archive);
        ActionCommand command = command("timed-365");
        var output = new java.io.ByteArrayOutputStream();
        java.io.PrintStream original = System.err;
        try (var capture = new java.io.PrintStream(output, true, java.nio.charset.StandardCharsets.UTF_8)) {
            System.setErr(capture);
            journal.locked(memory, view -> {
                ActionReceipt intent = view.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
                assertTrue(output.toString(java.nio.charset.StandardCharsets.UTF_8).isEmpty());
                ActionState.Submitting next = submitting(command);
                ActionReceipt actual = view.append(command, ActionCodec.bodySha256(command), next);
                assertEquals(next, actual.state());
                assertEquals(intent.sequence() + 1, actual.sequence());
                assertEquals(actual, view.find(command.actionId()).orElseThrow());
                assertEquals(memory.expected(), view.snapshot().actions());
                return null;
            });
        } finally { System.setErr(original); }
        List<String> lines = output.toString(java.nio.charset.StandardCharsets.UTF_8).lines().toList();
        assertEquals(1, lines.size(), "one completed Submitting, no Intent output");
        String line = lines.getFirst();
        assertTrue(line.startsWith("ACTION_APPEND_PHASE action=timed-365 thread="));
        assertTrue(line.endsWith(" returned=true"));
        assertTrue(line.length() < 1024, "bounded scalar line, not a raw packet");
        Map<String,String> fields = new HashMap<>();
        for (String part : line.split(" ")) if (part.contains("=")) {
            int equals = part.indexOf('='); fields.put(part.substring(0, equals), part.substring(equals + 1));
        }
        assertEquals("6", fields.get("phase"));
        long sum = 0;
        for (String key : List.of("validation_ns", "materials_ns", "preview_ns", "commit_ns", "history_ns", "selection_ns")) {
            long duration = Long.parseLong(fields.get(key)); assertTrue(duration >= 0, key); sum = Math.addExact(sum, duration);
        }
        assertTrue(Long.parseLong(fields.get("elapsed_ns")) >= sum);
        assertFalse(Thread.currentThread().isInterrupted());
    }

    @Test void loggerFailureNeverReplacesAppendOutcomeAndPreexistingInterruptSkipsIO() {
        java.io.PrintStream original = System.err;
        var writes = new java.util.concurrent.atomic.AtomicInteger();
        AssertionError diagnosticFailure = new AssertionError("diagnostic-only failure marker");
        try (var hostile = new java.io.PrintStream(java.io.OutputStream.nullOutputStream()) {
            @Override public void println(String value) { writes.incrementAndGet(); throw diagnosticFailure; }
        }) {
            System.setErr(hostile);
            Memory success = new Memory(); var journal = new ContinuityActionJournal(success, success.archive);
            ActionCommand command = command("logger-success");
            journal.locked(success, view -> {
                view.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
                ActionState.Submitting next = submitting(command);
                assertEquals(next, view.append(command, ActionCodec.bodySha256(command), next).state());
                return null;
            });
            assertEquals(1, writes.get(), "logger Error was caught after successful append");
            Memory before = new Memory(); var beforeJournal = new ContinuityActionJournal(before, before.archive);
            beforeJournal.locked(before, view -> {
                view.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
                before.headFailure = new IOException("original validation read failure");
                assertSame(before.headFailure, assertThrows(UncheckedIOException.class,
                        () -> view.append(command, ActionCodec.bodySha256(command), submitting(command))).getCause());
                before.headFailure = null; return null;
            });
            Memory during = new Memory(); var duringJournal = new ContinuityActionJournal(during, during.archive);
            RuntimeException commitFailure = new IllegalStateException("original commit failure marker");
            duringJournal.locked(during, view -> {
                view.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
                during.commitFailure = commitFailure;
                assertSame(commitFailure, assertThrows(IllegalStateException.class,
                        () -> view.append(command, ActionCodec.bodySha256(command), submitting(command))));
                return null;
            });
            assertEquals(3, writes.get(), "both original failures still attempted one isolated diagnostic");
            boolean initialInterrupted = Thread.currentThread().isInterrupted();
            assertFalse(initialInterrupted, "controlled test thread starts clear");
            try {
                Thread.currentThread().interrupt();
                Memory interrupted = new Memory(); var interruptedJournal = new ContinuityActionJournal(interrupted, interrupted.archive);
                interruptedJournal.locked(interrupted, view -> {
                    view.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
                    assertTrue(view.append(command, ActionCodec.bodySha256(command), submitting(command)).state() instanceof ActionState.Submitting);
                    return null;
                });
                assertTrue(Thread.currentThread().isInterrupted(), "production does not consume the caller flag");
                assertEquals(3, writes.get(), "already interrupted thread performs no diagnostic IO");
            } finally {
                Thread.interrupted(); // Restore only this controlled software test thread.
                if (initialInterrupted) Thread.currentThread().interrupt();
            }
        } finally { System.setErr(original); }
        assertFalse(Thread.currentThread().isInterrupted());
    }

    private static ActionState.Submitting submitting(ActionCommand command) {
        var guard = new GuardEvidence(command.origin(), command.source(), command.sessionId(), BigInteger.ONE,
                command.operation(), new ExactRef("D:/software-only/postcommit322/native", 1, "a".repeat(64)),
                new ExactRef("D:/software-only/postcommit322/capability", 1, "b".repeat(64)), "software-only", DEADLINE.minusSeconds(2), DEADLINE);
        var request = new NativeRequest("pause-map", Optional.empty(), new RawJson("{}".getBytes(java.nio.charset.StandardCharsets.UTF_8)));
        return new ActionState.Submitting(new ActionState.Attempt(RequestIds.forCommand(command), DEADLINE.minusSeconds(1), guard, request));
    }

    private static Head head(ContinuityState state) { return new Head(state, List.of(), List.of(), List.of(), false); }
    private static ContinuityState state(long sequence, Optional<ExactRef> record, String marker) {
        ObjectNode row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1")
                .put("machine_id", MACHINE).put("sequence", sequence).put("window_id", 1)
                .put("start_date_raw", 0).put("target_date_raw", 24).put("target_days", 1)
                .put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 0)
                .put("software_marker", marker);
        record.ifPresent(r -> row.set(ContinuityActionJournal.STATE_FIELD, r.toJson()));
        return ContinuityState.fromJson(row, MACHINE);
    }
    private static ActionCommand command(String id) {
        var before = new ProposalLifecycle.ObservationIdentity(MACHINE,
                new GameGeneration(123, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.ONE, BigInteger.ONE, BigInteger.ONE), "snapshot", BigInteger.ONE, "episode"), 1);
        var source = new G2Source(MACHINE, "2023-01-01T00:00:00Z", "software-only",
                new ExactRef("D:/software-only/postcommit322/source", 1, "1".repeat(64)));
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(id, before, source, "session", new OperationKey("pause-map"),
                new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), DEADLINE);
    }

    private static final class Memory implements ContinuityStorePort, ContinuityStorePort.Session {
        private final Map<ExactRef, ActionRecord> records = new HashMap<>();
        private Head current = AppendDiagnostics365Test.head(state(0, Optional.empty(), "initial"));
        private int loads, heads, keys;
        private IOException headFailure;
        private RuntimeException commitFailure;
        private ExactRef failAt, failAfterPreserve, commitWrongHead;
        private final UncheckedIOException archiveFailure = new UncheckedIOException(new IOException("first original full-tail read unavailable"));
        private final ActionPorts.OutcomeArchive archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(
                ActionPorts.OutcomeArchive.class.getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    return switch (method.getName()) {
                        case "inSession" -> {
                            assertSame(this, args[0]);
                            try { yield Function.class.getMethod("apply", Object.class).invoke(args[1], proxy); }
                            catch (InvocationTargetException failure) { throw failure.getCause(); }
                        }
                        case "preserveRequest", "requestReferenceOf" -> { NativeRequest.class.cast(args[0]); yield new ExactRef("D:/software-only/postcommit322/prepared", 1, "c".repeat(64)); }
                        case "preserveReceipt" -> { ActionReceipt.class.cast(args[0]); yield ref(); }
                        case "preserveRecord" -> {
                            var record = ActionRecord.class.cast(args[0]);
                            var result = add(record.receipt(), record.previous());
                            failAt = failAfterPreserve;
                            yield result;
                        }
                        case "loadRecord" -> {
                            loads++;
                            var key = ExactRef.class.cast(args[0]);
                            if (key.equals(failAt)) throw archiveFailure;
                            var result = records.get(key);
                            if (result == null) throw new NoSuchElementException("software record missing");
                            yield result;
                        }
                        default -> throw new AssertionError("unexpected archive call " + method.getName());
                    };
                });
        private ExactRef ref() { return new ExactRef("D:/software-only/postcommit322/" + ++keys, 1, String.format("%064x", keys)); }
        private ExactRef add(ActionReceipt receipt, Optional<ExactRef> previous) {
            ExactRef key = ref(); records.put(key, new ActionRecord(receipt, previous)); return key;
        }
        private List<ActionReceipt> expected() {
            var copy = Map.copyOf(records);
            var edge = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        if (!method.getName().equals("loadRecord")) throw new AssertionError(method.getName());
                        return copy.get(ExactRef.class.cast(args[0]));
                    });
            return ContinuityActionJournal.receipts(current.state(), edge);
        }
        @Override public Head head() throws IOException { heads++; if (headFailure != null) throw headFailure; return current; }
        @Override public Prepared preview(Request request) {
            assertEquals(ContinuityActionJournal.KIND, request.kind());
            ExactRef next = commitWrongHead != null ? commitWrongHead : ExactRef.fromJson(request.detailsObject().get("receipt_ref"));
            return new Prepared(current, request, List.of(), List.of(),
                    state(current.state().sequence() + 1, Optional.of(next), "software commit"), current.digest());
        }
        @Override public Receipt commit(Prepared prepared) {
            if (commitFailure != null) throw commitFailure;
            assertSame(current, prepared.predecessor()); current = AppendDiagnostics365Test.head(prepared.reduced());
            return new Receipt(Disposition.COMMITTED, current.state(), prepared.request().identity(), 0, false);
        }
        @Override public <T> T locked(SessionWork<T> work) throws IOException { return work.run(this); }
        @Override public ExactRef persistedHead() { throw new AssertionError("no filesystem head"); }
        @Override public void requireWriter(Path lock) { throw new AssertionError("no physical writer authority"); }
        @Override public Pin capturePin(ExactRef reference, int maximum) { throw new AssertionError("no physical pin authority"); }
        @Override public void verifyPin(Pin pin) { throw new AssertionError("no physical pin authority"); }
    }
}

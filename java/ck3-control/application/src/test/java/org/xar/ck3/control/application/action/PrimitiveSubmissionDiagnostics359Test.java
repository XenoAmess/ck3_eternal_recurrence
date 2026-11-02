package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.OutputStream;
import java.io.PrintStream;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.time.Clock;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.parallel.Execution;
import org.junit.jupiter.api.parallel.ExecutionMode;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.continuity.writer.WriterContracts;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.presentation.TransportKind;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** New diagnostic-failure behavior on public RAM ports; no Root/Writer/Native authority or old352 RUN. */
@Execution(ExecutionMode.SAME_THREAD)
class PrimitiveSubmissionDiagnostics359Test {
    private static final Instant NOW = Instant.parse("2026-10-26T19:00:00Z");

    @Test
    void brokenDiagnosticSinkKeepsLazyCallbacksOriginalPermitAndSingleSubmission() {
        for (Throwable diagnosticFailure : List.of(new IllegalStateException("diagnostic-runtime"),
                new AssertionError("diagnostic-error"))) {
            Journal journal = new Journal();
            AtomicInteger hooks = new AtomicInteger();
            AtomicInteger submits = new AtomicInteger();
            AtomicReference<SubmissionPermit> issued = new AtomicReference<>();
            var custom = callback((same, command, guard, history, queue) -> {
                journal.trace.add("hook-enter");
                List<ActionReceipt> receipts = history.get();
                assertTrue(receipts.stream().anyMatch(r -> r.command().equals(command)
                        && r.state() instanceof ActionState.Submitting));
                assertThrows(UnsupportedOperationException.class, receipts::clear);
                hooks.incrementAndGet();
                journal.trace.add("hook-exit");
            });
            var actual = coordinator(journal, new PhysicalActionRegistry(List.of(
                    binding("default-unused", new EmptyProducer()), binding("custom-single-get", custom))),
                    (permit, request, deadline) -> {
                        submits.incrementAndGet();
                        issued.set(permit);
                        journal.trace.add("native-enter");
                        journal.consuming = true;
                        try { permit.consumeOnce(); } finally { journal.consuming = false; }
                        journal.trace.add("native-return");
                        return unknown(permit);
                    });
            ActionCommand original = command("diag-359-once-" + diagnosticFailure.getClass().getSimpleName());
            PrintStream previous = System.err;
            BrokenDiagnostics sink = new BrokenDiagnostics(previous, diagnosticFailure);
            try {
                System.setErr(sink);
                ActionReceipt first = actual.execute(original);
                assertEquals(ActionReceipt.Outcome.UNRESOLVED, first.outcome());
                assertEquals("software independent observer pending", assertInstanceOf(ActionState.Unknown.class, first.state()).reason());
                assertSame(first, actual.execute(original));
                assertEquals(1, submits.get());
                assertEquals(1, hooks.get());
                assertEquals(2, journal.hookWriterSessions);
                assertEquals(1, journal.hookSnapshots);
                assertEquals(List.of("native-enter", "hook-enter", "snapshot", "hook-exit", "native-return"), journal.trace);
                assertTrue(issued.get().consumed());
                assertThrows(IllegalStateException.class, issued.get()::consumeOnce);
                assertEquals(1, hooks.get());
                assertEquals(1, journal.hookSnapshots);
                assertTrue(sink.attempts > 0, "actual diagnostic calls reached the failing ordinary sink");
            } finally {
                System.setErr(previous);
            }
        }
    }

    @Test
    void submittingFailureAndProducerErrorRemainOriginalDespiteDiagnosticErrors() {
        Journal appendJournal = new Journal();
        IllegalStateException appendFailure = new IllegalStateException("original SUBMITTING append failed");
        appendJournal.failSubmitting = appendFailure;
        AtomicInteger nativeCalls = new AtomicInteger();
        var beforeAppend = coordinator(appendJournal, new PhysicalActionRegistry(List.of(binding("unused", new EmptyProducer()))),
                (permit, request, deadline) -> { nativeCalls.incrementAndGet(); throw new AssertionError("must not submit"); });
        ActionCommand appendCommand = command("diag-359-append-failure");
        PrintStream previous = System.err;
        BrokenDiagnostics sink = new BrokenDiagnostics(previous, new AssertionError("logger must not replace append failure"));
        try {
            System.setErr(sink);
            assertSame(appendFailure, assertThrows(IllegalStateException.class, () -> beforeAppend.execute(appendCommand)));
            assertEquals(0, appendFailure.getSuppressed().length);
            ActionReceipt intent = appendJournal.rows.get(appendCommand.actionId());
            assertInstanceOf(ActionState.IntentDurable.class, intent.state());
            assertSame(intent, beforeAppend.execute(appendCommand));
            assertEquals(0, nativeCalls.get());
            assertEquals(0, appendJournal.hookSnapshots);
            assertTrue(sink.attempts > 0);
        } finally {
            System.setErr(previous);
        }

        Journal producerJournal = new Journal();
        AssertionError producerFailure = new AssertionError("original producer Error is not optional RuntimeException");
        AtomicInteger producerCalls = new AtomicInteger();
        AtomicInteger submits = new AtomicInteger();
        AtomicReference<SubmissionPermit> issued = new AtomicReference<>();
        var producer = callback((same, command, guard, history, queue) -> {
            producerCalls.incrementAndGet(); throw producerFailure;
        });
        var actual = coordinator(producerJournal, new PhysicalActionRegistry(List.of(binding("failing-producer", producer))),
                (permit, request, deadline) -> {
                    submits.incrementAndGet(); issued.set(permit); producerJournal.consuming = true;
                    try { permit.consumeOnce(); } finally { producerJournal.consuming = false; }
                    throw new AssertionError("original producer Error must propagate");
                });
        ActionCommand original = command("diag-359-producer-error");
        sink = new BrokenDiagnostics(previous, new AssertionError("logger must not replace producer Error"));
        try {
            System.setErr(sink);
            assertSame(producerFailure, assertThrows(AssertionError.class, () -> actual.execute(original)));
            assertEquals(0, producerFailure.getSuppressed().length);
            ActionReceipt submitting = producerJournal.rows.get(original.actionId());
            assertInstanceOf(ActionState.Submitting.class, submitting.state());
            assertSame(submitting, actual.execute(original));
            assertTrue(issued.get().consumed());
            assertThrows(IllegalStateException.class, issued.get()::consumeOnce);
            assertEquals(1, submits.get());
            assertEquals(1, producerCalls.get());
            assertEquals(0, producerJournal.hookSnapshots);
            assertTrue(sink.attempts > 0);
        } finally {
            System.setErr(previous);
        }
    }

    @Test
    void nativeRuntimeAndInterruptionKeepUnknownAndNoReplayUnderBrokenDiagnostics() {
        boolean originallyInterrupted = Thread.currentThread().isInterrupted();
        PrintStream previous = System.err;
        try {
            Thread.interrupted();
            for (boolean interrupt : List.of(false, true)) {
                Journal journal = new Journal();
                AtomicInteger submits = new AtomicInteger();
                IllegalStateException originalRuntime = new IllegalStateException("original native runtime failure");
                var actual = coordinator(journal, new PhysicalActionRegistry(List.of(binding("default-unused", new EmptyProducer()))),
                        (permit, request, deadline) -> {
                            submits.incrementAndGet(); journal.consuming = true;
                            try { permit.consumeOnce(); } finally { journal.consuming = false; }
                            if (interrupt) throw new InterruptedException("original native interruption");
                            throw originalRuntime;
                        });
                ActionCommand original = command("diag-359-dispatch-failure-" + interrupt);
                BrokenDiagnostics sink = new BrokenDiagnostics(previous, new AssertionError("logging Error"));
                System.setErr(sink);
                ActionReceipt first = actual.execute(original);
                ActionState.Unknown unknown = assertInstanceOf(ActionState.Unknown.class, first.state());
                assertEquals(ActionReceipt.Outcome.UNRESOLVED, first.outcome());
                if (interrupt) {
                    assertEquals("interrupted after SUBMITTING; no replay", unknown.reason());
                    assertTrue(Thread.currentThread().isInterrupted());
                    Thread.interrupted();
                } else {
                    assertTrue(unknown.reason().startsWith("native dispatch result unknown:"));
                    assertTrue(unknown.reason().contains(originalRuntime.getMessage()));
                    assertFalse(Thread.currentThread().isInterrupted());
                }
                assertEquals(3, journal.appended.size());
                assertInstanceOf(ActionState.IntentDurable.class, journal.appended.get(0));
                assertInstanceOf(ActionState.Submitting.class, journal.appended.get(1));
                assertInstanceOf(ActionState.Unknown.class, journal.appended.get(2));
                assertSame(first, actual.execute(original));
                assertEquals(1, submits.get());
                assertEquals(0, journal.hookSnapshots);
                assertEquals(1, journal.hookWriterSessions);
                assertTrue(sink.attempts > 0);
                System.setErr(previous);
            }
        } finally {
            System.setErr(previous);
            Thread.interrupted();
            if (originallyInterrupted) Thread.currentThread().interrupt();
        }
    }

    /** Public, ordinary stderr interception, restricted to this candidate's diagnostic tag. */
    private static final class BrokenDiagnostics extends PrintStream {
        private final PrintStream previous;
        private final Throwable failure;
        private int attempts;
        BrokenDiagnostics(PrintStream previous, Throwable failure) {
            super(OutputStream.nullOutputStream(), true, StandardCharsets.UTF_8);
            this.previous = previous; this.failure = failure;
        }
        @Override public void println(String text) {
            if (text != null && text.startsWith("ACTION_SUBMISSION_PHASE")) {
                attempts++;
                if (failure instanceof RuntimeException runtime) throw runtime;
                if (failure instanceof Error error) throw error;
                throw new AssertionError("fixture requires an unchecked diagnostic failure");
            }
            previous.println(text);
        }
    }

    @FunctionalInterface private interface Hook {
        void run(ContinuityStorePort.Session same, ActionCommand command, GuardEvidence guard,
                Supplier<List<ActionReceipt>> history, PhysicalActionRegistry.Queue queue) throws IOException;
    }
    private static PhysicalActionRegistry.Producer callback(Hook hook) {
        return new EmptyProducer() {
            @Override public void beforeNative(ContinuityStorePort.Session same, ActionCommand command,
                    GuardEvidence guard, Supplier<List<ActionReceipt>> history, PhysicalActionRegistry.Queue queue) throws IOException {
                hook.run(same, command, guard, history, queue);
            }
        };
    }
    private static class EmptyProducer implements PhysicalActionRegistry.Producer {
        @Override public GuardEvidence guard(WriterContracts.Head head, ActionCommand command) { throw new AssertionError(); }
        @Override public PreparedAction prepare(ContinuityStorePort.Session same, ActionCommand command, String id) { throw new AssertionError(); }
        @Override public PhysicalOutcome post(PhysicalSubmission permit, PreparedAction request, Instant deadline) { throw new AssertionError(); }
        @Override public PhysicalActionRegistry.Observation observe(ContinuityStorePort.Session same, ActionCommand command,
                PhysicalActionState state, Instant deadline) { throw new AssertionError(); }
        @Override public void verifyArchived(WriterContracts.Head head, ActionReceipt receipt, ActionPorts.OutcomeArchive archive) { throw new AssertionError(); }
    }
    private static PhysicalActionRegistry.Binding binding(String name, PhysicalActionRegistry.Producer producer) {
        return new PhysicalActionRegistry.Binding(new OperationKey(name), TransportKind.PRESENTATION_MMAP,
                List.of(command("fixture-source").source().sourceRef()), producer);
    }
    private static NativeActionPort.Unknown unknown(SubmissionPermit permit) {
        return new NativeActionPort.Unknown(permit.requestId(), "software original wire outcome unknown", new byte[0], Optional.empty());
    }
    private static GuardEvidence guard(ActionCommand command) {
        return new GuardEvidence(command.before(), command.source(), command.sessionId(), BigInteger.ONE,
                command.operation(), command.source().sourceRef(), command.source().sourceRef(), "display-test-authority", NOW, command.deadline());
    }
    private static ActionCoordinator coordinator(Journal journal, PhysicalActionRegistry registry, NativeActionPort nativePort) {
        ActionPorts.PreparationPort preparation = new ActionPorts.PreparationPort() {
            @Override public void requireOutsideReadOnlyScope(ContinuityStorePort.Session same, ActionCommand command) { }
            @Override public NativeRequest prepare(ActionCommand command) {
                return new NativeRequest(command.operation().value(), "game.command." + command.operation().value(), new RawJson(new byte[] {'{', '}'}));
            }
            @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String requestId) { return prepare(command); }
        };
        var actual = new ActionCoordinator("display-test-authority", journal, (head, command) -> guard(command), preparation,
                nativePort, (command, attempt, outcome) -> new ActionPorts.Pending("software independent observer pending", List.of()),
                Clock.fixed(NOW, ZoneOffset.UTC));
        actual.bindPhysicalActions(registry); return actual;
    }
    /** Mechanical public DATA vector from original352; no actual source files/session are accessed. */
    private static ActionCommand command(String id) {
        var ref = new ExactRef("D:/display-software-vector/source.json", 1, "a".repeat(64));
        var source = new G2Source("display-software-vector", NOW.toString(), "1.20.0.4", ref);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(), game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        StrictJson.UINT64_MAX.subtract(BigInteger.ONE), BigInteger.valueOf(24000)),
                        "display-vector", StrictJson.UINT64_MAX, "episode-display"), 1);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "display-vector/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(id, before, source, "display-session", new OperationKey("resume-map"), new OpportunityJson.Obj(Map.of()),
                expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static final class Journal implements ActionJournal {
        private final LinkedHashMap<String, ActionReceipt> rows = new LinkedHashMap<>();
        private final List<ActionState> appended = new ArrayList<>();
        private final List<String> trace = new ArrayList<>();
        private long sequence;
        private boolean consuming;
        private int hookSnapshots, hookWriterSessions;
        private RuntimeException failSubmitting;
        private final WriterContracts.Head head = new WriterContracts.Head(ContinuityState.fromJson(StrictJson.object()
                .put("schema", "root.ck3.continuity-window/v1").put("machine_id", "display-software-vector")
                .put("sequence", 0).put("window_id", 1).put("status", "running").put("start_date_raw", 24000)
                .put("target_date_raw", 286992).put("target_days", 10958).put("last_settled_cycles", 0)
                .put("last_settled_date_raw", 24000).put("binding_lineage_count", 0), "display-software-vector"),
                List.of(), List.of(), List.of(), false);
        @Override public <T> T locked(Function<LockedJournal, T> operation) {
            return operation.apply(new LockedJournal() {
                @Override public ContinuityStorePort.Session writerSession() {
                    if (consuming) hookWriterSessions++;
                    return null;
                }
                @Override public WriterContracts.Head head() { return head; }
                @Override public Optional<ActionReceipt> find(String id) { return Optional.ofNullable(rows.get(id)); }
                @Override public List<ActionReceipt> unresolved() { return rows.values().stream().filter(row -> !row.settled()).toList(); }
                @Override public Snapshot snapshot() {
                    if (consuming) { hookSnapshots++; trace.add("snapshot"); }
                    return new Snapshot(sequence, head.digest(), List.copyOf(rows.values()), new MissingHistoryBasis());
                }
                @Override public ActionReceipt append(ActionCommand command, String digest, ActionState next) {
                    ActionTransitions.validate(find(command.actionId()), command, digest, next);
                    if (next instanceof ActionState.Submitting && failSubmitting != null) throw failSubmitting;
                    ActionReceipt receipt = new ActionReceipt(1, ++sequence, command, digest, next);
                    rows.put(command.actionId(), receipt); appended.add(next); return receipt;
                }
            });
        }
    }
}

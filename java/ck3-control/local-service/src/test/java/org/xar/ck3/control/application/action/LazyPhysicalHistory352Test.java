package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.math.BigInteger;
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
import java.util.function.Function;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
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
import org.xar.ck3.control.service.root.RootGuiPresentation;

/** Actual coordinator/once-hook plus Root binding entry on RAM ports; no Root/Native/file authority. */
class LazyPhysicalHistory352Test {
    private static final Instant NOW = Instant.parse("2026-10-26T19:00:00Z");

    @Test void defaultHookSkipsHistoryAndEachCustomInvocationSeesPriorCallbackMutationWithoutReplay() {
        var journal = new Journal();
        var hooks = new AtomicInteger();
        var nativeCalls = new AtomicInteger();
        var snapshots = new ArrayList<List<ActionReceipt>>();
        PhysicalActionRegistry.Producer custom = new EmptyProducer() {
            @Override public void beforeNative(ContinuityStorePort.Session same, ActionCommand command,
                    GuardEvidence guard, Supplier<List<ActionReceipt>> history, PhysicalActionRegistry.Queue queue) {
                List<ActionReceipt> actual = history.get();
                int prior = hooks.getAndIncrement();
                assertTrue(actual.stream().anyMatch(r -> r.command().equals(command)
                        && r.state() instanceof ActionState.Submitting));
                assertEquals(prior, actual.stream().filter(r -> r.command().actionId().startsWith("marker-")).count());
                snapshots.add(actual);
                journal.seedMarker("marker-" + prior);
            }
        };
        var registry = new PhysicalActionRegistry(List.of(binding("unused-default", new EmptyProducer()),
                binding("custom-a", custom), binding("custom-b", custom)));
        var coordinator = coordinator(journal, registry, (permit, request, deadline) -> {
            nativeCalls.incrementAndGet();
            journal.consuming = true;
            try { permit.consumeOnce(); } finally { journal.consuming = false; }
            assertEquals(3, journal.hookWriterSessions);
            assertEquals(2, journal.hookSnapshots);
            assertEquals(2, hooks.get());
            return unknown(permit);
        });
        var command = command("one-business", "resume-map");
        var first = coordinator.execute(command);
        assertEquals(ActionReceipt.Outcome.UNRESOLVED, first.outcome());
        assertEquals(RequestIds.forCommand(command), ActionTransitions.attempt(first.state()).orElseThrow().requestId());
        assertEquals(2, snapshots.size());
        assertNotSame(snapshots.get(0), snapshots.get(1));
        assertFalse(snapshots.get(0).stream().anyMatch(r -> r.command().actionId().equals("marker-0")));
        assertTrue(snapshots.get(1).stream().anyMatch(r -> r.command().actionId().equals("marker-0")));
        assertThrows(UnsupportedOperationException.class, () -> snapshots.get(0).clear());
        assertSame(first, coordinator.execute(command));
        assertEquals(1, nativeCalls.get());
        assertEquals(2, hooks.get());
        assertEquals(2, journal.hookSnapshots);
    }

    @Test void rootEntrySamplesBeforeOwnerAndOptionalFailureOrUnconsumedPermitCannotReplayBusiness() throws Exception {
        var command = command("root-entry", "resume-map");
        var events = new ArrayList<String>();
        var rootBinding = RootGuiPresentation.binding(List.of(command.source().sourceRef()),
                c -> { throw new AssertionError("no command owner should be requested"); },
                r -> { throw new AssertionError("no request owner should be requested"); },
                c -> { events.add("owner"); throw new IOException("no actual Root owner in this DATA test"); }, List::of);
        rootBinding.producer().beforeNative(null, command, guard(command), () -> {
            events.add("snapshot"); return List.of();
        }, ignored -> fail("no presentation should be queued"));
        assertEquals(List.of("snapshot", "owner"), events);
        events.clear();
        var marker = new UncheckedIOException(new IOException("original snapshot failure"));
        assertSame(marker, assertThrows(UncheckedIOException.class, () -> rootBinding.producer().beforeNative(
                null, command, guard(command), () -> { events.add("snapshot"); throw marker; }, ignored -> fail())));
        assertEquals(List.of("snapshot"), events);

        var rejectedJournal = new Journal();
        var rejectedHooks = new AtomicInteger();
        var rejected = coordinator(rejectedJournal,
                new PhysicalActionRegistry(List.of(binding("custom", callback((same, c, g, history, queue) -> {
                    history.get(); rejectedHooks.incrementAndGet();
                })))),
                (permit, request, deadline) -> new NativeActionPort.RejectedBeforeDispatch(permit.requestId(),
                        new NativeActionPort.ZeroDispatchProof(NativeActionPort.ZeroDispatchStage.BEFORE_WRITE,
                                0, "software guard rejected before permit consumption", Optional.empty())))
                .execute(command("no-consume", "resume-map"));
        assertEquals(ActionReceipt.Outcome.REJECTED_BEFORE_DISPATCH, rejected.outcome());
        assertEquals(0, rejectedHooks.get());
        assertEquals(0, rejectedJournal.hookSnapshots);

        for (boolean writerFails : List.of(false, true)) {
            var journal = new Journal();
            journal.failHookSnapshot = !writerFails;
            journal.failHookWriter = writerFails;
            var sideEffects = new AtomicInteger();
            var submits = new AtomicInteger();
            var actual = coordinator(journal,
                    new PhysicalActionRegistry(List.of(binding("custom", callback((same, c, g, history, queue) -> {
                        history.get(); sideEffects.incrementAndGet();
                    })))),
                    (permit, request, deadline) -> {
                        submits.incrementAndGet(); journal.consuming = true;
                        try { permit.consumeOnce(); } finally { journal.consuming = false; }
                        return unknown(permit);
                    });
            var original = command("optional-failure-" + writerFails, "resume-map");
            var first = actual.execute(original);
            assertEquals(ActionReceipt.Outcome.UNRESOLVED, first.outcome());
            assertEquals(0, sideEffects.get());
            assertEquals(1, journal.hookWriterSessions);
            assertEquals(writerFails ? 0 : 1, journal.hookSnapshots);
            assertSame(first, actual.execute(original));
            assertEquals(1, submits.get());
        }
    }

    private static NativeActionPort.Unknown unknown(SubmissionPermit permit) {
        return new NativeActionPort.Unknown(permit.requestId(), "software original wire outcome unknown",
                new byte[0], Optional.empty());
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
                List.of(command("source", "pause-map").source().sourceRef()), producer);
    }
    private static GuardEvidence guard(ActionCommand command) {
        return new GuardEvidence(command.before(), command.source(), command.sessionId(), BigInteger.ONE,
                command.operation(), command.source().sourceRef(), command.source().sourceRef(), "display-test-authority", NOW, command.deadline());
    }
    private static ActionCoordinator coordinator(Journal journal, PhysicalActionRegistry registry, NativeActionPort nativePort) {
        ActionPorts.PreparationPort preparation = new ActionPorts.PreparationPort() {
            @Override public void requireOutsideReadOnlyScope(ContinuityStorePort.Session same, ActionCommand command) { }
            @Override public NativeRequest prepare(ActionCommand command) {
                return new NativeRequest(command.operation().value(), "game.command." + command.operation().value(), new RawJson(new byte[]{'{', '}'}));
            }
            @Override public NativeRequest prepare(ContinuityStorePort.Session same, ActionCommand command, String id) { return prepare(command); }
        };
        var result = new ActionCoordinator("display-test-authority", journal, (head, command) -> guard(command), preparation,
                nativePort, (command, attempt, outcome) -> new ActionPorts.Pending("independent state unavailable", List.of()),
                Clock.fixed(NOW, ZoneOffset.UTC));
        result.bindPhysicalActions(registry); return result;
    }
    /** Existing DecisionDisplayTest public DATA vector, copied mechanically to keep this fixture self-contained. */
    private static ActionCommand command(String id, String operation) {
        var ref = new ExactRef("D:/display-software-vector/source.json", 1, "a".repeat(64));
        var source = new G2Source("display-software-vector", NOW.toString(), "1.20.0.4", ref);
        var game = new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("134000000000000001")));
        var before = new ProposalLifecycle.ObservationIdentity(source.machineId(), game,
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829),
                        StrictJson.UINT64_MAX.subtract(BigInteger.ONE), BigInteger.valueOf(24000)),
                        "display-vector", StrictJson.UINT64_MAX, "episode-display"), 1);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "display-vector/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        return new ActionCommand(id, before, source, "display-session", new OperationKey(operation), new OpportunityJson.Obj(Map.of()),
                expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
    }
    private static final class Journal implements ActionJournal {
        final LinkedHashMap<String, ActionReceipt> rows = new LinkedHashMap<>();
        long sequence;
        boolean consuming, failHookSnapshot, failHookWriter;
        int hookSnapshots, hookWriterSessions;
        final WriterContracts.Head head = new WriterContracts.Head(ContinuityState.fromJson(StrictJson.object()
                .put("schema", "root.ck3.continuity-window/v1").put("machine_id", "display-software-vector")
                .put("sequence", 0).put("window_id", 1).put("status", "running").put("start_date_raw", 24000)
                .put("target_date_raw", 286992).put("target_days", 10958).put("last_settled_cycles", 0)
                .put("last_settled_date_raw", 24000).put("binding_lineage_count", 0), "display-software-vector"),
                List.of(), List.of(), List.of(), false);
        void seedMarker(String id) {
            var command = command(id, "pause-map");
            rows.put(id, new ActionReceipt(1, ++sequence, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable()));
        }
        @Override public <T> T locked(Function<LockedJournal, T> work) {
            return work.apply(new LockedJournal() {
                @Override public ContinuityStorePort.Session writerSession() {
                    if (consuming) {
                        hookWriterSessions++;
                        if (failHookWriter) throw new UncheckedIOException(new IOException("software writer session unavailable"));
                    }
                    return null;
                }
                @Override public WriterContracts.Head head() { return head; }
                @Override public Optional<ActionReceipt> find(String id) { return Optional.ofNullable(rows.get(id)); }
                @Override public List<ActionReceipt> unresolved() { return rows.values().stream().filter(r -> !r.settled()).toList(); }
                @Override public Snapshot snapshot() {
                    if (consuming) {
                        hookSnapshots++;
                        if (failHookSnapshot) throw new UncheckedIOException(new IOException("software snapshot unavailable"));
                    }
                    return new Snapshot(sequence, head.digest(), List.copyOf(rows.values()), new MissingHistoryBasis());
                }
                @Override public ActionReceipt append(ActionCommand command, String digest, ActionState state) {
                    ActionTransitions.validate(find(command.actionId()), command, digest, state);
                    var receipt = new ActionReceipt(1, ++sequence, command, digest, state);
                    rows.put(command.actionId(), receipt); return receipt;
                }
            });
        }
    }
}

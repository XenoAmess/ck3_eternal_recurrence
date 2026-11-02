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
final class PostCommitJournal322Test {
    private static final String MACHINE = "postcommit322-software";
    private static final Instant DEADLINE = Instant.parse("2023-01-01T00:00:30Z");

    @Test void successfulReadbackServesOnlyTheSameViewAndStillReadsCurrentHead() {
        Memory memory = new Memory();
        var journal = new ContinuityActionJournal(memory, memory.archive);
        ActionCommand command = command("selected");
        journal.locked(memory, view -> {
            ActionReceipt intent = view.append(command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
            assertEquals(1, memory.loads, "append still performs its full fresh committed readback");
            int reads = memory.loads, heads = memory.heads;
            assertEquals(intent, view.find(command.actionId()).orElseThrow());
            assertEquals(heads + 1, memory.heads);
            assertEquals(reads, memory.loads, "the immediately following find reuses the successful readback");
            assertEquals(memory.expected(), view.snapshot().actions());
            assertEquals(List.of(intent), view.unresolved());
            assertEquals(reads, memory.loads);

            IOException original = new IOException("current head unavailable after successful memo");
            memory.headFailure = original;
            assertSame(original, assertThrows(UncheckedIOException.class, () -> view.find("selected")).getCause());
            memory.headFailure = null;
            long sequence = memory.current.state().sequence();
            memory.current = head(state(sequence, ContinuityActionJournal.recordHead(memory.current.state()), "different digest"));
            assertEquals(intent, view.find("selected").orElseThrow());
            assertEquals(reads + 1, memory.loads, "same sequence with a different state digest must read again");
            memory.current = head(state(sequence + 1, ContinuityActionJournal.recordHead(memory.current.state()), "new sequence"));
            assertEquals(intent, view.find("selected").orElseThrow());
            assertEquals(reads + 2, memory.loads);

            ActionReceipt unknown = view.append(command, ActionCodec.bodySha256(command),
                    new ActionState.Unknown(Optional.empty(), Optional.empty(), "original unresolved software DATA", List.of()));
            int afterAppend = memory.loads;
            assertEquals(unknown, view.find("selected").orElseThrow());
            assertEquals(memory.expected(), view.snapshot().actions());
            assertEquals(List.of(unknown), view.unresolved());
            assertEquals(afterAppend, memory.loads);
            assertFalse(unknown.settled());
            assertTrue(unknown.ack().isEmpty());
            assertEquals(DEADLINE, unknown.command().deadline());
            return null;
        });
        int reads = memory.loads;
        journal.locked(memory, view -> {
            assertEquals(memory.expected().getFirst(), view.find("selected").orElseThrow());
            return null;
        });
        assertEquals(reads + 2, memory.loads, "callback exit discards the old view memo");
    }

    @Test void firstFullReadbackFailureAndMissingTargetNeverSeedANewMemo() {
        Memory failed = new Memory();
        ExactRef tail = failed.add(new ActionReceipt(1, 1, command("other"),
                ActionCodec.bodySha256(command("other")), new ActionState.IntentDurable()), Optional.empty());
        failed.current = head(state(1, Optional.of(tail), "before"));
        failed.failAfterPreserve = tail;
        var journal = new ContinuityActionJournal(failed, failed.archive);
        journal.locked(failed, view -> {
            ActionCommand selected = command("selected");
            assertSame(failed.archiveFailure, assertThrows(UncheckedIOException.class,
                    () -> view.append(selected, ActionCodec.bodySha256(selected), new ActionState.IntentDurable())));
            assertEquals(3, failed.loads, "prior one-record read then both committed records, including the bad tail");
            failed.failAt = null;
            int before = failed.loads;
            assertEquals(failed.expected().stream().filter(r -> r.command().actionId().equals("selected")).findFirst(), view.find("selected"));
            assertEquals(before + 2, failed.loads, "caught first-read failure cannot publish the new memo");
            return null;
        });

        Memory missing = new Memory();
        ExactRef other = missing.add(new ActionReceipt(1, 1, command("other"),
                ActionCodec.bodySha256(command("other")), new ActionState.IntentDurable()), Optional.empty());
        // Deliberately adversarial software store: expose a different committed
        // action head. This is not a valid canonical reducer/physical write claim.
        missing.commitWrongHead = other;
        var wrong = new ContinuityActionJournal(missing, missing.archive);
        wrong.locked(missing, view -> {
            ActionCommand selected = command("selected");
            assertThrows(NoSuchElementException.class,
                    () -> view.append(selected, ActionCodec.bodySha256(selected), new ActionState.IntentDurable()));
            int before = missing.loads;
            assertEquals(missing.expected().getFirst(), view.find("other").orElseThrow());
            assertEquals(before + 1, missing.loads, "target search failure occurs before memo publication");
            assertTrue(view.find("selected").isEmpty());
            return null;
        });
        // Removing the redundant later walk intentionally removes some later IO
        // observations. No identical old second-walk failure trace is asserted.
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
        private Head current = PostCommitJournal322Test.head(state(0, Optional.empty(), "initial"));
        private int loads, heads, keys;
        private IOException headFailure;
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
            assertSame(current, prepared.predecessor()); current = PostCommitJournal322Test.head(prepared.reduced());
            return new Receipt(Disposition.COMMITTED, current.state(), prepared.request().identity(), 0, false);
        }
        @Override public <T> T locked(SessionWork<T> work) throws IOException { return work.run(this); }
        @Override public ExactRef persistedHead() { throw new AssertionError("no filesystem head"); }
        @Override public void requireWriter(Path lock) { throw new AssertionError("no physical writer authority"); }
        @Override public Pin capturePin(ExactRef reference, int maximum) { throw new AssertionError("no physical pin authority"); }
        @Override public void verifyPin(Pin pin) { throw new AssertionError("no physical pin authority"); }
    }
}

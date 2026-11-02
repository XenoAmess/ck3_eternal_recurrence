package org.xar.ck3.control.application.action;

import com.fasterxml.jackson.databind.node.ObjectNode;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedPostcondition;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ExpectedText;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.FieldKey;
import org.xar.ck3.control.g2.planning.ProposalLifecycle.ObservationIdentity;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Structural typed-DATA comparison with the unchanged public lookup oracle.
 * The archive proxy only supplies records: its synthetic keys do not qualify
 * encoded archive bytes, canonical writer membership, child effects or dispatch.
 */
public final class CompositeChildQualification319Test {
    private static final String MACHINE = "test-machine";
    private static final Instant DEADLINE = Instant.parse("2023-01-01T00:00:00Z");

    @Test
    void latestChildrenMatchPublicLookupsAndEachCallReadsAFreshCompleteChain() throws Exception {
        Chain chain = chain(MACHINE, 1);
        List<CompositeExecution.Child> children = children(chain);
        Memory single = new Memory(chain.records());
        ActionReceipt one = ContinuityActionJournal.lookup(chain.state(), "B", single.port).orElseThrow();
        int fullWalk = single.loads;
        assertEquals(chain.records().size(), fullWalk);
        assertEquals(chain.latestB(), one);

        Memory old = new Memory(chain.records());
        List<ActionReceipt> expected = publicLookups(chain, children, old);
        assertEquals(2 * fullWalk, old.loads);
        assertEquals(List.of(chain.latestB(), chain.latestA()), expected);
        assertNotEquals(chain.olderA(), expected.get(1));

        Memory fresh = new Memory(chain.records());
        List<ActionReceipt> actual = selected(chain.state(), children, fresh.port);
        assertEquals(expected, actual, "complete receipts and caller order must match lookup");
        assertEquals(fullWalk, fresh.loads, "two children use one complete fresh walk");
        assertEquals(expected, selected(chain.state(), children, fresh.port));
        assertEquals(2 * fullWalk, fresh.loads, "a new invocation must read the chain again");
        for (ActionReceipt receipt : actual) {
            assertInstanceOf(ActionState.Unknown.class, receipt.state());
            assertFalse(receipt.settled());
            assertEquals(ActionReceipt.Outcome.UNRESOLVED, receipt.outcome());
            assertTrue(receipt.ack().isEmpty());
            assertEquals(DEADLINE, receipt.command().deadline());
        }

        Memory empty = new Memory(chain.records());
        assertEquals(List.of(), selected(chain.state(), List.of(), empty.port));
        assertEquals(0, empty.loads);
        Memory singleton = new Memory(chain.records());
        assertEquals(List.of(chain.latestA()), selected(chain.state(), List.of(children.get(1)), singleton.port));
        assertEquals(fullWalk, singleton.loads, "the singleton still follows the public lookup route");
    }

    @Test
    void unrelatedTailMissingChildrenAndFirstWalkIoStillFailWithoutReplay() throws Exception {
        for (Chain invalid : List.of(chain("foreign-machine", 1), chain(MACHINE, 2))) {
            Memory old = new Memory(invalid.records());
            RuntimeException expected = assertThrows(RuntimeException.class,
                    () -> publicLookups(invalid, children(invalid), old));
            Memory fresh = new Memory(invalid.records());
            RuntimeException actual = assertThrows(RuntimeException.class,
                    () -> selected(invalid.state(), children(invalid), fresh.port));
            assertEquals(expected.getClass(), actual.getClass());
            assertEquals(expected.getMessage(), actual.getMessage());
            assertEquals(invalid.records().size(), fresh.loads,
                    "finding both children near the head must not skip the invalid unrelated tail");
            assertEquals(old.loads, fresh.loads);
            Memory one = new Memory(invalid.records());
            assertThrows(expected.getClass(),
                    () -> selected(invalid.state(), List.of(children(invalid).getFirst()), one.port));
            assertEquals(fresh.loads, one.loads);
        }

        Chain valid = chain(MACHINE, 1);
        List<CompositeExecution.Child> missing = List.of(children(valid).getFirst(),
                new CompositeExecution.Child("missing", "0".repeat(64)));
        Memory old = new Memory(valid.records());
        assertThrows(NoSuchElementException.class, () -> publicLookups(valid, missing, old));
        Memory fresh = new Memory(valid.records());
        assertThrows(NoSuchElementException.class, () -> selected(valid.state(), missing, fresh.port));
        assertEquals(valid.records().size(), fresh.loads);

        for (ExactRef failing : List.of(valid.head(), valid.tail())) {
            IOException original = new IOException("first complete walk original IO: " + failing.path());
            UncheckedIOException retained = new UncheckedIOException(original);
            Memory failNew = new Memory(valid.records(), failing, retained);
            UncheckedIOException failure = assertThrows(UncheckedIOException.class,
                    () -> selected(valid.state(), children(valid), failNew.port));
            assertSame(retained, failure);
            assertSame(original, failure.getCause());
            Memory failOld = new Memory(valid.records(), failing, retained);
            assertSame(retained, assertThrows(UncheckedIOException.class,
                    () -> publicLookups(valid, children(valid), failOld)));
            assertEquals(failOld.loads, failNew.loads);
        }
        // The eliminated second complete walk has fewer IO observations; this
        // test does not demand failures injected only into that removed repeat.
    }

    private static List<ActionReceipt> publicLookups(Chain chain, List<CompositeExecution.Child> children, Memory archive) {
        return children.stream().map(child -> ContinuityActionJournal.lookup(
                chain.state(), child.actionId(), archive.port).orElseThrow()).toList();
    }

    private static List<ActionReceipt> selected(ContinuityState state, List<CompositeExecution.Child> children,
            ActionPorts.OutcomeArchive archive) throws Exception {
        Method method = ContinuityActionJournal.class.getDeclaredMethod("compositeChildren",
                ContinuityState.class, List.class, ActionPorts.OutcomeArchive.class);
        method.setAccessible(true);
        try {
            return ((List<?>) method.invoke(null, state, children, archive)).stream()
                    .map(ActionReceipt.class::cast).toList();
        } catch (InvocationTargetException failure) {
            if (failure.getCause() instanceof Exception cause) throw cause;
            if (failure.getCause() instanceof Error cause) throw cause;
            throw new AssertionError(failure.getCause());
        }
    }

    private static List<CompositeExecution.Child> children(Chain chain) {
        return List.of(new CompositeExecution.Child("B", chain.latestB().bodySha256()),
                new CompositeExecution.Child("A", chain.latestA().bodySha256()));
    }

    private record Chain(ContinuityState state, Map<ExactRef, ActionRecord> records, ExactRef head,
            ExactRef tail, ActionReceipt olderA, ActionReceipt latestA, ActionReceipt latestB) { }

    private static Chain chain(String tailMachine, long tailSequence) {
        ActionCommand a = command("A", MACHINE), b = command("B", MACHINE);
        ActionReceipt tail = receipt(tailSequence, command("unrelated", tailMachine), false);
        ActionReceipt olderA = receipt(2, a, false), olderB = receipt(3, b, false);
        ActionReceipt latestA = receipt(4, a, true), latestB = receipt(5, b, true);
        Map<ExactRef, ActionRecord> records = new HashMap<>();
        ExactRef previous = null, tailRef = null;
        for (ActionReceipt receipt : List.of(tail, olderA, olderB, latestA, latestB)) {
            ExactRef key = new ExactRef("structural-record-" + records.size(), 1,
                    String.format("%064x", records.size() + 1));
            records.put(key, new ActionRecord(receipt, Optional.ofNullable(previous)));
            if (tailRef == null) tailRef = key;
            previous = key;
        }
        ObjectNode row = StrictJson.object();
        row.put("schema", "root.ck3.continuity-window/v1"); row.put("machine_id", MACHINE);
        row.put("sequence", 5); row.put("window_id", 1); row.put("start_date_raw", 0);
        row.put("target_date_raw", 24); row.put("target_days", 1); row.put("status", "running");
        row.put("last_settled_cycles", 0); row.put("last_settled_date_raw", 0);
        row.set(ContinuityActionJournal.STATE_FIELD, previous.toJson());
        return new Chain(ContinuityState.fromJson(row, MACHINE), Map.copyOf(records), previous,
                tailRef, olderA, latestA, latestB);
    }

    private static ActionReceipt receipt(long sequence, ActionCommand command, boolean unknown) {
        ActionState state = unknown ? new ActionState.Unknown(Optional.empty(), Optional.empty(),
                "retained original unresolved DATA", List.of()) : new ActionState.IntentDurable();
        return new ActionReceipt(1, sequence, command, ActionCodec.bodySha256(command), state);
    }

    private static ActionCommand command(String id, String machine) {
        ObservationIdentity before = new ObservationIdentity(machine,
                new GameGeneration(1, new PythonOnlyUInt64(BigInteger.ONE)),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(
                        BigInteger.ONE, BigInteger.ONE, BigInteger.ONE), "snap", BigInteger.ONE, "ep"), 1);
        G2Source source = new G2Source(machine, "2023-01-01T00:00:00Z", "structural-test",
                new ExactRef("structural-source", 1, "1".repeat(64)));
        ExpectedPostcondition expected = new ExpectedPostcondition(1, before, source, "obs",
                List.of(new ExpectedText(new FieldKey("k"), "v")));
        return new ActionCommand(id, before, source, "test-session", new OperationKey("op"),
                new OpportunityJson.Obj(Map.of()), expected,
                new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), DEADLINE);
    }

    private static final class Memory {
        private final ActionPorts.OutcomeArchive port;
        private int loads;
        private Memory(Map<ExactRef, ActionRecord> records) { this(records, null, null); }
        private Memory(Map<ExactRef, ActionRecord> records, ExactRef failing, UncheckedIOException original) {
            port = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[] {ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                        if (!method.getName().equals("loadRecord")) throw new AssertionError("unexpected archive call: " + method);
                        loads++;
                        ExactRef key = ExactRef.class.cast(args[0]);
                        if (key.equals(failing)) throw original;
                        ActionRecord record = records.get(key);
                        if (record == null) throw new NoSuchElementException("missing structural record");
                        return record;
                    });
        }
    }
}

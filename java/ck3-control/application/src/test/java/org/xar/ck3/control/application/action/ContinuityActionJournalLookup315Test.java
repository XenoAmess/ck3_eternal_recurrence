package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.time.Instant;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/** Bounded in-memory projection witnesses; no file, writer permission, Native or Game is exercised. */
final class ContinuityActionJournalLookup315Test {
    private static final String MACHINE = "journal315-software";
    private static final Instant NOW = Instant.parse("2030-01-01T00:00:00Z");
    private static ExactRef ref(int id) {
        return new ExactRef("D:/software-only/journal315/" + id, 1, String.format("%064x", id));
    }
    private static ActionReceipt receipt(String id, long sequence, String machine) {
        var source = new G2Source(machine, NOW.toString(), "1.20.0.4", ref(100));
        var before = new ProposalLifecycle.ObservationIdentity(machine,
                new GameGeneration(123, new PythonOnlyUInt64(new BigInteger("133700000000000001"))),
                new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(29829), BigInteger.ONE, BigInteger.valueOf(100)),
                        "native-1", BigInteger.ONE, "episode-1"), 1);
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "paused/v1",
                List.of(new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("paused"), true)));
        var command = new ActionCommand(id, before, source, "session-1", new OperationKey("pause-map"),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()), NOW.plusSeconds(30));
        return new ActionReceipt(1, sequence, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
    }
    private static ContinuityState state(Optional<ExactRef> head) {
        var row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE)
                .put("sequence", 8).put("window_id", 1).put("status", "running").put("target_days", 10)
                .put("start_date_raw", 53144328).put("target_date_raw", 53144568)
                .put("last_settled_date_raw", 53144328).put("last_settled_cycles", 0);
        row.putObject("UNKNOWN").put("kept", "full state");
        head.ifPresent(value -> row.set(ContinuityActionJournal.STATE_FIELD, value.toJson()));
        return ContinuityState.fromJson(row, MACHINE);
    }
    private static final class Archive {
        final Map<ExactRef, ActionRecord> records = new HashMap<>();
        final List<ExactRef> reads = new ArrayList<>();
        ExactRef failAt;
        final IllegalStateException failure = new IllegalStateException("fresh original unavailable");
        final ActionPorts.OutcomeArchive port = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(
                getClass().getClassLoader(), new Class<?>[]{ActionPorts.OutcomeArchive.class}, (proxy, method, args) -> {
                    if (!method.getName().equals("loadRecord")) throw new AssertionError("unexpected archive call " + method.getName());
                    var original = (ExactRef) args[0]; reads.add(original);
                    if (original.equals(failAt)) throw failure;
                    var value = records.get(original);
                    if (value == null) throw new IllegalStateException("missing original");
                    return value;
                });
        void add(int id, ActionReceipt value, Integer previous) {
            records.put(ref(id), new ActionRecord(value, previous == null ? Optional.empty() : Optional.of(ref(previous))));
        }
    }
    @Test void newestDuplicateWinsOnlyAfterWholeChainHasBeenReadInOrder() {
        var archive = new Archive();
        var newest = receipt("wanted", 3, MACHINE);
        archive.add(3, newest, 2); archive.add(2, receipt("other", 2, MACHINE), 1); archive.add(1, receipt("wanted", 1, MACHINE), null);
        assertSame(newest, ContinuityActionJournal.lookup(state(Optional.of(ref(3))), "wanted", archive.port).orElseThrow());
        assertEquals(List.of(ref(3), ref(2), ref(1)), archive.reads);
    }
    @Test void missingAndNullIdsDoNotSkipOrCacheOriginalReads() {
        var archive = new Archive(); archive.add(2, receipt("one", 2, MACHINE), 1); archive.add(1, receipt("two", 1, MACHINE), null);
        var state = state(Optional.of(ref(2)));
        assertTrue(ContinuityActionJournal.lookup(state, "absent", archive.port).isEmpty());
        assertTrue(ContinuityActionJournal.lookup(state, null, archive.port).isEmpty());
        assertEquals(List.of(ref(2), ref(1), ref(2), ref(1)), archive.reads);
    }
    @Test void aMatchCannotHideALaterCycle() {
        var archive = new Archive(); archive.add(2, receipt("wanted", 2, MACHINE), 1); archive.add(1, receipt("other", 1, MACHINE), 2);
        assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.lookup(state(Optional.of(ref(2))), "wanted", archive.port));
        assertEquals(List.of(ref(2), ref(1)), archive.reads);
    }
    @Test void aMatchCannotHideLaterSequenceOrMachineDrift() {
        for (boolean foreign : List.of(false, true)) {
            var archive = new Archive(); archive.add(2, receipt("wanted", 2, MACHINE), 1);
            archive.add(1, receipt("other", foreign ? 1 : 2, foreign ? "foreign-machine" : MACHINE), null);
            assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.lookup(state(Optional.of(ref(2))), "wanted", archive.port));
            assertEquals(List.of(ref(2), ref(1)), archive.reads);
        }
    }
    @Test void freshArchiveFailureAfterAnEarlierSuccessfulLookupStillEscapes() {
        var archive = new Archive(); archive.add(2, receipt("wanted", 2, MACHINE), 1); archive.add(1, receipt("other", 1, MACHINE), null);
        var state = state(Optional.of(ref(2)));
        assertTrue(ContinuityActionJournal.lookup(state, "wanted", archive.port).isPresent());
        archive.failAt = ref(1);
        assertSame(archive.failure, assertThrows(IllegalStateException.class, () -> ContinuityActionJournal.lookup(state, "wanted", archive.port)));
        assertEquals(List.of(ref(2), ref(1), ref(2), ref(1)), archive.reads);
    }
    @Test void absentAndExplicitNullHistoryHeadsRemainDistinct() {
        var archive = new Archive(); var missing = state(Optional.empty());
        assertTrue(ContinuityActionJournal.lookup(missing, "wanted", archive.port).isEmpty()); assertTrue(archive.reads.isEmpty());
        var row = missing.toJson(); row.putNull(ContinuityActionJournal.STATE_FIELD);
        var explicitNull = ContinuityState.fromJson(row, MACHINE);
        assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.lookup(explicitNull, "wanted", archive.port));
        assertTrue(archive.reads.isEmpty());
    }
    @Test void nonTargetNewerActionsCannotChangeWhichVersionIsReturned() {
        var archive = new Archive(); var target = receipt("wanted", 2, MACHINE);
        archive.add(4, receipt("other", 4, MACHINE), 3); archive.add(3, receipt("other", 3, MACHINE), 2);
        archive.add(2, target, 1); archive.add(1, receipt("wanted", 1, MACHINE), null);
        assertSame(target, ContinuityActionJournal.lookup(state(Optional.of(ref(4))), "wanted", archive.port).orElseThrow());
        assertEquals(List.of(ref(4), ref(3), ref(2), ref(1)), archive.reads);
    }
}

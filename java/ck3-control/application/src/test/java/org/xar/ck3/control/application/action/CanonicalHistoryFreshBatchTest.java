package org.xar.ck3.control.application.action;

import static org.junit.jupiter.api.Assertions.*;

import java.io.IOException;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.continuity.ContinuityState;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.GameGeneration;
import org.xar.ck3.control.contracts.PythonOnlyUInt64;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;
import org.xar.ck3.control.g2.common.G2Source;
import org.xar.ck3.control.g2.planning.ProposalLifecycle;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;

/**
 * Software action-record DATA only: actual command/record/receipt codecs, no Session, Root, Guard or ACK.
 * The archive denies publication/control and validates named byte/SHA material on all normal reads.
 * A typed cycle-only negative models an invalid OutcomeArchive, not an impossible content-hash fixed point.
 * Single-call read counts describe this real entry's traversal, never filesystem IO, Root authority or speed.
 */
final class CanonicalHistoryFreshBatchTest {
    private static final String MACHINE = "fresh-batch-software";
    private static final String HEADER = "historical receipt crossed actual writer machine/sequence";
    private static final String MISSING = "receipt is not in the surviving canonical action record chain";
    private static final String BODY = "historical action record has another complete original receipt body";

    @Test void oneSourceBatchReadsTheEntireChainOnceAndKeepsEachMembershipCheckAtItsQueryPoint() throws IOException {
        var f = new Fixture();
        var aRecord = f.records.get(0);
        var bRecord = f.records.get(1);
        var cRecord = f.records.get(2);
        var unknown = new ActionState.Unknown(Optional.empty(), Optional.empty(), "software unequal metadata", List.of());
        var changedBody = new ActionReceipt(1, f.a.sequence(), f.a.command(), f.a.bodySha256(), unknown);
        var missingWithWrongBody = new ActionReceipt(1, 11, f.a.command(), f.a.bodySha256(), unknown);
        var badHeaderWithWrongBody = new ActionReceipt(1, 31, f.a.command(), f.a.bodySha256(), unknown);
        var otherMachine = receipt("not-the-target", 11, "other-software-machine");
        ContinuityActionJournal.withCanonicalHistory(f.state(), f.archive, (lookup, membership) -> {
            assertEquals(List.of(cRecord, bRecord, aRecord), f.recordReads);
            assertEquals(3, f.receiptReads.size(), "non-target receipts are decoded before any query factory runs");
            return () -> {
                assertEquals(f.a, lookup.apply("target").orElseThrow());
                assertEquals(f.b, lookup.apply("unrelated").orElseThrow());
                assertTrue(lookup.apply("missing-action").isEmpty());
                assertEquals(aRecord, membership.apply(f.a));
                assertEquals(bRecord, membership.apply(f.b));
                // Complete receipt byte equality is the original contract; object identity is not required here.
                var equalReceipt = ActionReceiptCodec.decodeReceipt(ActionReceiptCodec.encodeReceipt(f.a, f.archive), f.archive);
                assertNotSame(f.a, equalReceipt);
                assertEquals(aRecord, membership.apply(equalReceipt));
                assertEquals(HEADER, assertThrows(IllegalArgumentException.class,
                        () -> membership.apply(badHeaderWithWrongBody)).getMessage());
                assertEquals(HEADER, assertThrows(IllegalArgumentException.class,
                        () -> membership.apply(otherMachine)).getMessage());
                assertEquals(MISSING, assertThrows(IllegalArgumentException.class,
                        () -> membership.apply(missingWithWrongBody)).getMessage());
                assertEquals(BODY, assertThrows(IllegalArgumentException.class,
                        () -> membership.apply(changedBody)).getMessage());
                assertThrows(NullPointerException.class, () -> membership.apply(null));
                assertEquals(cRecord, membership.apply(f.c));
                assertEquals(List.of(cRecord, bRecord, aRecord), f.recordReads,
                        "lookup/current/original queries consume the one source-produced full traversal");
                assertEquals(3, f.receiptReads.size());
                return null;
            };
        });
        assertEquals(0, f.deniedCalls, "no writer/publication/issuer callback was requested");
    }

    @Test void unrelatedCorruptionMachineSequenceAndCyclesFailBeforeTheQueryFactoryCanRun() {
        var damaged = new Fixture();
        damaged.corrupt(damaged.recordReceipts.get(damaged.records.get(1)));
        var calls = new AtomicInteger();
        var bytesFailure = assertThrows(IllegalArgumentException.class,
                () -> ContinuityActionJournal.withCanonicalHistory(damaged.state(), damaged.archive, (lookup, member) -> {
                    calls.incrementAndGet();
                    return () -> lookup.apply("other");
                }));
        assertEquals("software original bytes/SHA changed", bytesFailure.getMessage());
        assertEquals(0, calls.get(), "even a head target cannot bypass an unrelated receipt's complete validation");

        for (boolean machine : List.of(true, false)) {
            var f = new Fixture(machine ? "other-software-machine" : MACHINE, machine ? 20 : 31);
            var failure = assertThrows(IllegalArgumentException.class,
                    () -> ContinuityActionJournal.withCanonicalHistory(f.state(), f.archive, (lookup, member) -> {
                        calls.incrementAndGet();
                        return () -> lookup.apply("other");
                    }));
            assertEquals("action record chain sequence/machine drift", failure.getMessage());
            assertEquals(0, calls.get());
        }
        var cyclic = new Fixture();
        var head = cyclic.records.get(2);
        // Negative interface DATA only: a real strict CAS could not have this same-hash cyclic encoding.
        cyclic.malformedRecordShapes.put(head, new ActionRecord(cyclic.c, Optional.of(head)));
        var cycleFailure = assertThrows(IllegalArgumentException.class,
                () -> ContinuityActionJournal.withCanonicalHistory(cyclic.state(), cyclic.archive, (lookup, member) -> {
                    calls.incrementAndGet();
                    return () -> lookup.apply("other");
                }));
        assertEquals("action record chain is cyclic or exceeds explicit bounded read budget", cycleFailure.getMessage());
        assertEquals(0, calls.get());
        assertEquals(List.of(head), cyclic.recordReads, "repeat-reference failure precedes a second decode of that ref");
    }

    @Test void sourceQueriesCloseOnEveryExitRejectForeignThreadsAndEveryNewBatchReadsFreshOriginals() throws Exception {
        var f = new Fixture();
        var lookupRef = new AtomicReference<Function<String, Optional<ActionReceipt>>>();
        var memberRef = new AtomicReference<Function<ActionReceipt, ExactRef>>();
        ContinuityActionJournal.withCanonicalHistory(f.state(), f.archive, (lookup, membership) -> {
            lookupRef.set(lookup); memberRef.set(membership);
            return () -> {
                var failures = new AtomicReference<List<Throwable>>();
                Thread foreign = new Thread(() -> {
                    var actual = new ArrayList<Throwable>();
                    try { lookup.apply("target"); actual.add(new AssertionError("foreign lookup escaped")); }
                    catch (Throwable failure) { actual.add(failure); }
                    try { membership.apply(f.a); actual.add(new AssertionError("foreign membership escaped")); }
                    catch (Throwable failure) { actual.add(failure); }
                    failures.set(actual);
                }, "canonical-batch-software-foreign");
                foreign.setDaemon(true); foreign.start();
                try { foreign.join(5000); }
                catch (InterruptedException interrupted) { Thread.currentThread().interrupt(); throw new IOException(interrupted); }
                assertFalse(foreign.isAlive());
                assertEquals(2, failures.get().size());
                failures.get().forEach(failure -> assertInstanceOf(IllegalArgumentException.class, failure));
                assertEquals(f.a, lookup.apply("target").orElseThrow());
                assertEquals(f.records.get(0), membership.apply(f.a));
                return null;
            };
        });
        assertThrows(IllegalArgumentException.class, () -> lookupRef.get().apply("target"));
        assertThrows(IllegalArgumentException.class, () -> memberRef.get().apply(null),
                "closed ownership is checked before the supplied exact receipt");
        var original = new IOException("software original Callable failure");
        assertSame(original, assertThrows(IOException.class,
                () -> ContinuityActionJournal.withCanonicalHistory(f.state(), f.archive, (lookup, member) -> {
                    lookupRef.set(lookup); memberRef.set(member);
                    return () -> { throw original; };
                })));
        assertThrows(IllegalArgumentException.class, () -> lookupRef.get().apply("target"));
        assertThrows(IllegalArgumentException.class, () -> memberRef.get().apply(f.a));
        var factoryFailure = new IllegalStateException("software query factory original failure");
        assertSame(factoryFailure, assertThrows(IllegalStateException.class,
                () -> ContinuityActionJournal.withCanonicalHistory(f.state(), f.archive, (lookup, member) -> {
                    lookupRef.set(lookup); memberRef.set(member);
                    throw factoryFailure;
                })));
        assertThrows(IllegalArgumentException.class, () -> lookupRef.get().apply("target"));
        assertThrows(IllegalArgumentException.class, () -> memberRef.get().apply(f.a));

        var fresh = new Fixture();
        for (int invocation = 1; invocation <= 2; invocation++) {
            ContinuityActionJournal.withCanonicalHistory(fresh.state(), fresh.archive, (lookup, member) -> () -> {
                assertEquals(fresh.a, lookup.apply("target").orElseThrow());
                assertEquals(fresh.records.get(0), member.apply(fresh.a));
                return null;
            });
            assertEquals(invocation * 3, fresh.recordReads.size());
            assertEquals(invocation * 3, fresh.receiptReads.size());
        }
        fresh.corrupt(fresh.recordReceipts.get(fresh.records.get(0)));
        var callbacks = new AtomicInteger();
        var changed = assertThrows(IllegalArgumentException.class,
                () -> ContinuityActionJournal.withCanonicalHistory(fresh.state(), fresh.archive, (lookup, member) -> {
                    callbacks.incrementAndGet();
                    return () -> lookup.apply("other");
                }));
        assertEquals("software original bytes/SHA changed", changed.getMessage());
        assertEquals(0, callbacks.get());
        assertEquals(9, fresh.recordReads.size(), "a third independent invocation must traverse into the changed oldest original");
    }

    @Test void olderExactSuffixUsesOneFreshWalkAndRetainsItsOwnHeadAndBounds() {
        var f = new Fixture();
        var predecessor = at(f, f.records.get(1), 20);
        assertEquals(f.a, ContinuityActionJournal.lookupWithHistoricalMembership(f.state(), predecessor, "target", f.archive).orElseThrow());
        assertEquals(List.of(f.records.get(2), f.records.get(1), f.records.get(0)), f.recordReads);
        assertEquals(3, f.receiptReads.size());

        var latest = at(f, f.records.get(2), 40);
        assertEquals(MISSING, assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.lookupWithHistoricalMembership(
                latest, at(f, f.records.get(1), 35), "other", f.archive)).getMessage());
        assertEquals(HEADER, assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.lookupWithHistoricalMembership(
                latest, at(f, f.records.get(1), 9), "target", f.archive)).getMessage());
        assertEquals("action record chain sequence/machine drift", assertThrows(IllegalArgumentException.class,
                () -> ContinuityActionJournal.lookupWithHistoricalMembership(latest, at(f, f.records.get(1), 19), "target", f.archive)).getMessage());

        f.corrupt(f.recordReceipts.get(f.records.get(0)));
        assertEquals("software original bytes/SHA changed", assertThrows(IllegalArgumentException.class,
                () -> ContinuityActionJournal.lookupWithHistoricalMembership(latest, predecessor, "target", f.archive)).getMessage());
    }

    @Test void detachedCanonicalPredecessorStillReadsItsCompleteIndependentOriginals() {
        var f = new Fixture();
        f.add(receipt("past", 5, MACHINE), Optional.empty());
        var past = f.records.get(3);
        f.add(f.a, Optional.of(past));
        var detached = f.records.get(4);
        var predecessor = at(f, detached, 20);
        assertEquals(f.a, ContinuityActionJournal.lookupWithHistoricalMembership(f.state(), predecessor, "target", f.archive).orElseThrow());
        assertEquals(List.of(f.records.get(2), f.records.get(1), f.records.get(0), detached, past), f.recordReads);

        var unknown = new ActionState.Unknown(Optional.empty(), Optional.empty(), "different detached original", List.of());
        f.add(new ActionReceipt(1, f.a.sequence(), f.a.command(), f.a.bodySha256(), unknown), Optional.of(past));
        assertEquals(BODY, assertThrows(IllegalArgumentException.class, () -> ContinuityActionJournal.lookupWithHistoricalMembership(
                f.state(), at(f, f.records.get(5), 20), "target", f.archive)).getMessage());
        f.corrupt(f.recordReceipts.get(past));
        assertEquals("software original bytes/SHA changed", assertThrows(IllegalArgumentException.class,
                () -> ContinuityActionJournal.lookupWithHistoricalMembership(f.state(), predecessor, "target", f.archive)).getMessage());
    }

    private static ContinuityState at(Fixture fixture, ExactRef head, long sequence) {
        var state = fixture.state().toJson().put("sequence", sequence);
        state.set(ContinuityActionJournal.STATE_FIELD, head.toJson());
        return ContinuityState.fromJson(state, MACHINE);
    }

    private static ActionReceipt receipt(String id, long sequence, String machine) {
        var game = new GameGeneration(42, new PythonOnlyUInt64(new BigInteger("9007199254740993")));
        var frame = new JointBudgetSelector.ProposalFrame(new JointBudgetSelector.Frame(BigInteger.valueOf(73),
                BigInteger.valueOf(9), BigInteger.valueOf(53144328)), "software-snapshot", BigInteger.valueOf(2), "software-episode");
        var before = new ProposalLifecycle.ObservationIdentity(machine, game, frame, 1);
        var source = new G2Source(machine, "2026-10-23T16:00:00Z", "software-build", reference(bytes("software source")));
        var expected = new ProposalLifecycle.ExpectedPostcondition(1, before, source, "software-history/v1", List.of(
                new ProposalLifecycle.ExpectedBoolean(new ProposalLifecycle.FieldKey("native.gameplay_verified"), true)));
        var command = new ActionCommand(id, before, source, "software-session", new OperationKey("move-army"),
                new OpportunityJson.Obj(Map.of()), expected, new JointBudgetSelector.Claims(Set.of(), Set.of(), Set.of(), Set.of()),
                Instant.parse("2030-01-01T00:00:00Z"));
        return new ActionReceipt(1, sequence, command, ActionCodec.bodySha256(command), new ActionState.IntentDurable());
    }

    private static final class Fixture implements InvocationHandler {
        final Map<ExactRef, byte[]> originals = new LinkedHashMap<>();
        final Map<ExactRef, ActionRecord> malformedRecordShapes = new HashMap<>(); // cycle-only negative, never a positive.
        final Map<ExactRef, ExactRef> recordReceipts = new LinkedHashMap<>();
        final Map<String, ExactRef> receiptBySha = new HashMap<>();
        final List<ExactRef> records = new ArrayList<>(), recordReads = new ArrayList<>(), receiptReads = new ArrayList<>();
        final ActionPorts.OutcomeArchive archive;
        final ActionReceipt a, b, c;
        int deniedCalls;
        Fixture() { this(MACHINE, 20); }
        Fixture(String middleMachine, long middleSequence) {
            archive = (ActionPorts.OutcomeArchive) Proxy.newProxyInstance(ActionPorts.OutcomeArchive.class.getClassLoader(),
                    new Class<?>[]{ActionPorts.OutcomeArchive.class}, this);
            a = receipt("target", 10, MACHINE);
            b = receipt("unrelated", middleSequence, middleMachine);
            c = receipt("other", 30, MACHINE);
            add(a, Optional.empty()); add(b, Optional.of(records.get(0))); add(c, Optional.of(records.get(1)));
        }
        void add(ActionReceipt receipt, Optional<ExactRef> previous) {
            byte[] raw = ActionReceiptCodec.encodeReceipt(receipt, archive);
            ExactRef receiptRef = reference(raw); originals.put(receiptRef, raw); receiptBySha.put(receiptRef.sha256(), receiptRef);
            byte[] record = ActionRecordCodec.encode(new ActionRecord(receipt, previous), archive);
            ExactRef recordRef = reference(record); originals.put(recordRef, record); records.add(recordRef); recordReceipts.put(recordRef, receiptRef);
        }
        ContinuityState state() {
            var row = StrictJson.object().put("schema", "root.ck3.continuity-window/v1").put("machine_id", MACHINE)
                    .put("sequence", 30).put("window_id", 1).put("start_date_raw", 0).put("target_date_raw", 24)
                    .put("target_days", 1).put("status", "running").put("last_settled_cycles", 0).put("last_settled_date_raw", 0);
            row.set(ContinuityActionJournal.STATE_FIELD, records.get(2).toJson());
            return ContinuityState.fromJson(row, MACHINE);
        }
        byte[] read(ExactRef ref) {
            byte[] value = originals.get(ref);
            if (value == null) throw new AssertionError("unrecognized software original: " + ref);
            if (value.length != ref.bytes() || !ActionCodec.sha256(value).equals(ref.sha256()))
                throw new IllegalArgumentException("software original bytes/SHA changed");
            return value.clone();
        }
        void corrupt(ExactRef reference) { byte[] changed = read(reference); changed[0] ^= 1; originals.put(reference, changed); }
        @Override public Object invoke(Object proxy, Method method, Object[] args) {
            if (method.getDeclaringClass() == Object.class) return switch (method.getName()) {
                case "toString" -> "read-only software canonical original archive";
                case "hashCode" -> System.identityHashCode(proxy);
                case "equals" -> proxy == args[0];
                default -> throw new AssertionError(method);
            };
            return switch (method.getName()) {
                case "loadRecord" -> {
                    ExactRef ref = (ExactRef) args[0]; recordReads.add(ref);
                    yield malformedRecordShapes.containsKey(ref) ? malformedRecordShapes.get(ref) : ActionRecordCodec.decode(read(ref), archive);
                }
                case "loadReceipt" -> {
                    ExactRef ref = (ExactRef) args[0]; receiptReads.add(ref);
                    yield ActionReceiptCodec.decodeReceipt(read(ref), archive);
                }
                case "receiptReferenceOf" -> {
                    byte[] raw = ActionReceiptCodec.encodeReceipt((ActionReceipt) args[0], archive);
                    ExactRef ref = receiptBySha.get(ActionCodec.sha256(raw));
                    if (ref == null || !Arrays.equals(raw, read(ref))) throw new AssertionError("unrecognized software receipt lookup");
                    yield ref;
                }
                default -> { deniedCalls++; throw new AssertionError("no issuer/publication/control/default archive access: " + method.getName()); }
            };
        }
    }

    private static byte[] bytes(String text) { return text.getBytes(StandardCharsets.UTF_8); }
    private static ExactRef reference(byte[] raw) {
        // Value DATA only; no file is opened or published by this fixture.
        return new ExactRef(Path.of(System.getProperty("java.io.tmpdir"), "canonical-batch-data", ActionCodec.sha256(raw) + ".bin")
                .toAbsolutePath().toString(), raw.length, ActionCodec.sha256(raw));
    }
}

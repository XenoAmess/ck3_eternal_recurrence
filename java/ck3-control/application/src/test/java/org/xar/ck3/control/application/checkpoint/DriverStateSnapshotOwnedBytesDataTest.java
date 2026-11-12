package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.FullJsonTree;

/** Complete public DATA only; no private construction proof, issuer, authority or parser implementation is copied. */
final class DriverStateSnapshotOwnedBytesDataTest {
    private static final int MAX = DriverCheckpointStore.MAX_DRIVER_BYTES;

    @Test void completePublicConstructionPreservesEverySlotOriginalTokenAndOwnedBytes() {
        var expected = originalComplete();
        byte[] raw = expected.encode();
        byte[] before = raw.clone();
        String wire = text(raw);
        assertTrue(wire.contains("1.2300e+004"));
        assertTrue(wire.contains("-0.000e-02"));
        assertTrue(wire.contains("18446744073709551616000000000000000001"));
        var actual = DriverStateSnapshot.decodeComplete(raw);
        assertCompleteData(expected, actual);
        assertArrayEquals(before, raw);

        var historyInput = new ArrayList<>(expected.commandHistory());
        var publicCopy = withHistoryAndGoal(expected, historyInput, expected.campaignGoal());
        historyInput.clear();
        assertCompleteData(expected, publicCopy);
        assertThrows(UnsupportedOperationException.class, () -> actual.commandHistory().clear());

        byte[] originalValueBytes = bytes("{\"status\":\"owned\",\"raw\":1.00}");
        var publicValue = new DriverStateSnapshot.Value(originalValueBytes);
        byte[] valueBefore = publicValue.json();
        Arrays.fill(originalValueBytes, (byte) 0);
        assertArrayEquals(valueBefore, publicValue.json());
        byte[] returnedValue = publicValue.json(); Arrays.fill(returnedValue, (byte) 0);
        assertArrayEquals(valueBefore, publicValue.json());
        byte[] returnedRow = actual.commandHistory().getFirst().originalRow().json();
        Arrays.fill(returnedRow, (byte) 0);
        byte[] returnedSlot = ((DriverStateSnapshot.Value)actual.lastCheckpoint()).json();
        Arrays.fill(returnedSlot, (byte) 0);
        byte[] returnedWire = actual.encode(); Arrays.fill(returnedWire, (byte) 0);
        Arrays.fill(raw, (byte) 0);
        assertCompleteData(expected, actual);
    }

    @Test void unicodeAndEscapedDomainsMatchOriginalPublicValueAndHistoryConstruction() {
        String slash = Character.toString((char)92);
        String escaped = slash + "u";
        String supplementary = new String(Character.toChars(0x1f600));
        List<String> rawValues = List.of(
                "\"ASCII and 汉字\"",
                "\"" + supplementary + "\"",
                "\"" + escaped + "D83D" + escaped + "DE00\"",
                "\"" + escaped + "D83D\"",
                "\"" + escaped + "DE00\"",
                "{\"" + supplementary + "\":1,\"ascii\":2}",
                "{\"" + escaped + "D83D" + escaped + "DE00\":1,\"ascii\":2}",
                "{\"" + escaped + "D83D\":1,\"ascii\":2}",
                "\"" + slash + slash + "uD83D\"",
                "{\"literal\":\"" + slash + slash + "uDE00\",\"number\":-0.00e+03}",
                "[\"" + supplementary + "\",{\"nested\":\"" + escaped + "D83D\"},18446744073709551616000000000000000001]",
                "{\"escaped\":\"" + slash + "n" + slash + "t" + slash + Character.toString((char)34) + slash + slash + "\"}");
        var base = originalComplete();
        var templateRow = value("{\"index\":1,\"command\":\"variant\",\"result\":\"ROW_VARIANT\"}");
        var template = withHistoryAndGoal(base,
                List.of(new DriverStateSnapshot.HistoryEntry(1, templateRow), base.commandHistory().get(1), base.commandHistory().get(2)),
                value("\"SLOT_VARIANT\""));
        for (String rawValue : rawValues) {
            String rowJson = "{\"index\":1,\"command\":\"variant\",\"result\":" + rawValue + "}";
            byte[] raw = bytes(replaceOne(replaceOne(text(template.encode()), "\"ROW_VARIANT\"", rawValue),
                    "\"SLOT_VARIANT\"", rawValue));
            byte[] before = raw.clone();
            // This is the original public constructor oracle AFTER the original strict tree encoding.
            // It contains no proof scanner, surrogate predicate or bypass decision.
            var expectedRow = new DriverStateSnapshot.HistoryEntry(1, publicValueAfterTreeEncoding(rowJson));
            var expected = withHistoryAndGoal(base,
                    List.of(expectedRow, base.commandHistory().get(1), base.commandHistory().get(2)),
                    publicValueAfterTreeEncoding(rawValue));
            assertCompleteData(expected, DriverStateSnapshot.decodeComplete(raw));
            var calls = new AtomicInteger();
            var verified = DriverStateSnapshot.Complete.decodeAndVerify(raw, (complete, originalRow) -> {
                calls.incrementAndGet(); assertCompleteData(expected, complete);
                assertTrue(originalRow.has("command_history"));
            });
            assertEquals(1, calls.get()); assertCompleteData(expected, verified);
            assertArrayEquals(before, raw);
        }
        var optionalAbsent = new DriverStateSnapshot.Complete(base.session(), base.commandHistory(),
                base.lastCheckpoint(), new DriverStateSnapshot.NullValue(), base.managedRestoreTransaction(),
                base.successionExpectation(), new DriverStateSnapshot.Missing(), new DriverStateSnapshot.NullValue(),
                new DriverStateSnapshot.Missing());
        assertCompleteData(optionalAbsent, DriverStateSnapshot.decodeComplete(optionalAbsent.encode()));
    }

    @Test void verifierReceivesDetachedCompleteWhileNestedDecodeAndRowOrRawMutationRemainLocal() {
        var expected = originalComplete();
        byte[] raw = expected.encode();
        byte[] stableWire = raw.clone();
        var events = new ArrayList<String>();
        var escapedComplete = new AtomicReference<DriverStateSnapshot.Complete>();
        var escapedRow = new AtomicReference<ObjectNode>();
        var actual = DriverStateSnapshot.Complete.decodeAndVerify(raw, (complete, row) -> {
            events.add("outer"); escapedComplete.set(complete); escapedRow.set(row);
            assertCompleteData(expected, complete); assertArrayEquals(stableWire, raw);
            var inner = DriverStateSnapshot.Complete.decodeAndVerify(stableWire, (nested, nestedRow) -> {
                events.add("inner"); assertCompleteData(expected, nested);
                assertNotSame(row, nestedRow); nestedRow.removeAll(); nestedRow.put("changed", true);
                rejectPublicForgeries();
            });
            assertCompleteData(expected, inner); assertCompleteData(expected, complete);
            events.add("outer-after-inner");
            row.withArray("command_history").removeAll();
            row.removeAll(); row.put("not_a_driver", true);
            Arrays.fill(raw, (byte) 0);
            assertCompleteData(expected, complete); rejectPublicForgeries();
        });
        assertEquals(List.of("outer", "inner", "outer-after-inner"), events);
        assertSame(escapedComplete.get(), actual);
        assertCompleteData(expected, actual);
        escapedRow.get().put("later_mutation", 12);
        assertCompleteData(expected, actual);
        assertCompleteData(expected, DriverStateSnapshot.decodeComplete(stableWire));
        rejectPublicForgeries();
    }

    @Test void nullVerifierAndOriginalFailuresKeepTheirOrderAndDoNotRelaxPublicConstructors() {
        assertThrows(NullPointerException.class, () -> DriverStateSnapshot.Complete.decodeAndVerify(null, null));
        assertThrows(NullPointerException.class, () -> DriverStateSnapshot.Complete.decodeAndVerify(bytes("{"), null));
        var calls = new AtomicInteger();
        var directFailure = assertThrows(IllegalArgumentException.class,
                () -> DriverStateSnapshot.decodeComplete(bytes("{")));
        var verifiedFailure = assertThrows(IllegalArgumentException.class,
                () -> DriverStateSnapshot.Complete.decodeAndVerify(bytes("{"), (complete, row) -> calls.incrementAndGet()));
        assertEquals(0, calls.get());
        assertEquals(directFailure.getClass(), verifiedFailure.getClass());
        assertEquals(directFailure.getMessage(), verifiedFailure.getMessage());
        var expected = originalComplete(); byte[] raw = expected.encode(); byte[] before = raw.clone();
        var escaped = new AtomicReference<DriverStateSnapshot.Complete>();
        var sentinel = new IllegalStateException("original anchor verifier sentinel");
        assertSame(sentinel, assertThrows(IllegalStateException.class,
                () -> DriverStateSnapshot.Complete.decodeAndVerify(raw, (complete, row) -> {
                    calls.incrementAndGet(); escaped.set(complete); assertCompleteData(expected, complete);
                    row.removeAll(); rejectPublicForgeries(); throw sentinel;
                })));
        assertEquals(1, calls.get()); assertArrayEquals(before, raw);
        assertCompleteData(expected, escaped.get());
        rejectPublicForgeries();
        var next = DriverStateSnapshot.Complete.decodeAndVerify(raw, (complete, row) -> {
            calls.incrementAndGet(); assertCompleteData(expected, complete); rejectPublicForgeries();
        });
        assertEquals(2, calls.get()); assertCompleteData(expected, next);
        rejectPublicForgeries();
    }

    private static void rejectPublicForgeries() {
        assertThrows(IllegalArgumentException.class, () -> value("null"));
        assertThrows(IllegalArgumentException.class, () -> value("{"));
        var original = value("{\"index\":1,\"data\":\"original\"}");
        var wrongIndex = assertThrows(IllegalArgumentException.class,
                () -> new DriverStateSnapshot.HistoryEntry(2, original));
        assertEquals("history entry typed index equals original integer token", wrongIndex.getMessage());
        assertThrows(IllegalArgumentException.class,
                () -> new DriverStateSnapshot.HistoryEntry(1, value("{\"index\":1.0}")));
        assertThrows(IllegalArgumentException.class, () -> new DriverStateSnapshot.HistoryEntry(0, original));
    }

    private static DriverStateSnapshot.Complete originalComplete() {
        var session = new DriverStateSnapshot.Session("owned-proof-pipe", 42, BigInteger.valueOf(73), "episode-owned-proof");
        var history = List.of(
                new DriverStateSnapshot.HistoryEntry(1, value("{\"index\":1,\"command\":\"read\",\"ok\":true,\"result\":{\"ascii\":\"stable\",\"fraction\":1.2300e+004,\"huge\":18446744073709551616000000000000000001,\"negativeZero\":-0.000e-02}}")),
                new DriverStateSnapshot.HistoryEntry(2, value("{\"index\":2,\"command\":\"choose\",\"ok\":false,\"error\":\"汉字原件\"}")),
                new DriverStateSnapshot.HistoryEntry(3, value("{\"index\":3,\"command\":\"save\",\"result\":{\"enabled\":false,\"values\":[1,2,3]}}")));
        return new DriverStateSnapshot.Complete(session, history,
                value("{\"path\":\"checkpoint-original\",\"revision\":9007199254740993}"),
                new DriverStateSnapshot.NullValue(),
                value("{\"phase\":\"completed\",\"lineage\":[\"original-parent\"]}"),
                value("{\"character_id\":73,\"expected\":false}"),
                value("{\"current\":{\"episode\":\"episode-owned-proof\"}}"),
                value("{\"campaign_id\":\"original-campaign\",\"budget\":-123456789012345678901234567890}"),
                value("[{\"reason\":\"original advisory\"},{\"reason\":\"another advisory\"}]"));
    }

    private static DriverStateSnapshot.Complete withHistoryAndGoal(DriverStateSnapshot.Complete source,
            List<DriverStateSnapshot.HistoryEntry> history, DriverStateSnapshot.Slot goal) {
        return new DriverStateSnapshot.Complete(source.session(), history, source.lastCheckpoint(), source.rollbackWarFailure(),
                source.managedRestoreTransaction(), source.successionExpectation(), source.successionLifecycle(), goal, source.rollbackWarFailures());
    }

    private static DriverStateSnapshot.Value publicValueAfterTreeEncoding(String originalJson) {
        JsonNode originalTree = FullJsonTree.parse(bytes(originalJson), MAX);
        return new DriverStateSnapshot.Value(FullJsonTree.encode(originalTree, MAX));
    }
    private static DriverStateSnapshot.Value value(String raw) { return new DriverStateSnapshot.Value(bytes(raw)); }
    private static byte[] bytes(String raw) { return raw.getBytes(StandardCharsets.UTF_8); }
    private static String text(byte[] raw) { return new String(raw, StandardCharsets.UTF_8); }
    private static String replaceOne(String original, String target, String replacement) {
        int first = original.indexOf(target);
        assertTrue(first >= 0); assertEquals(first, original.lastIndexOf(target));
        return original.substring(0, first) + replacement + original.substring(first + target.length());
    }
    private static void assertCompleteData(DriverStateSnapshot.Complete expected, DriverStateSnapshot.Complete actual) {
        assertEquals(expected, actual);
        assertEquals(expected.session().pipeName(), actual.session().pipeName());
        assertEquals(expected.session().bridgePid(), actual.session().bridgePid());
        assertEquals(expected.session().actorId(), actual.session().actorId());
        assertEquals(expected.session().episodeRunId(), actual.session().episodeRunId());
        assertEquals(expected.commandHistory().size(), actual.commandHistory().size());
        for (int i = 0; i < expected.commandHistory().size(); i++) {
            assertEquals(expected.commandHistory().get(i).index(), actual.commandHistory().get(i).index());
            assertArrayEquals(expected.commandHistory().get(i).originalRow().json(), actual.commandHistory().get(i).originalRow().json());
        }
        List<DriverStateSnapshot.Slot> es = List.of(expected.lastCheckpoint(), expected.rollbackWarFailure(), expected.managedRestoreTransaction(),
                expected.successionExpectation(), expected.successionLifecycle(), expected.campaignGoal(), expected.rollbackWarFailures());
        List<DriverStateSnapshot.Slot> as = List.of(actual.lastCheckpoint(), actual.rollbackWarFailure(), actual.managedRestoreTransaction(),
                actual.successionExpectation(), actual.successionLifecycle(), actual.campaignGoal(), actual.rollbackWarFailures());
        for (int i = 0; i < es.size(); i++) {
            assertEquals(es.get(i).getClass(), as.get(i).getClass()); assertEquals(es.get(i), as.get(i));
            if (es.get(i) instanceof DriverStateSnapshot.Value ev)
                assertArrayEquals(ev.json(), ((DriverStateSnapshot.Value)as.get(i)).json());
        }
        assertArrayEquals(expected.encode(), actual.encode());
    }
}

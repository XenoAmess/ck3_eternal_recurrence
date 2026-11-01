package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.*;
import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.contracts.FullJsonTree;

public class DriverStateSnapshotImmutabilityTest {

    private static byte[] toBytes(String s) {
        return s.getBytes(StandardCharsets.UTF_8);
    }

    private static String historyJson(int index) {
        return "{\"index\":" + index + ",\"data\":{\"id\":123,\"val\":45.67}}";
    }

    private static String slotJson() {
        return "{\"status\":\"active\",\"count\":10}";
    }

    private static DriverStateSnapshot.Value makeValue(String json) {
        return new DriverStateSnapshot.Value(toBytes(json));
    }

    private static DriverStateSnapshot.HistoryEntry makeEntry(int index) {
        return new DriverStateSnapshot.HistoryEntry(index, makeValue(historyJson(index)));
    }

    private static DriverStateSnapshot.Session makeSession() {
        return new DriverStateSnapshot.Session("pipe-name", 100, BigInteger.valueOf(42), "run-id");
    }

    private static DriverStateSnapshot.Complete buildComplete() {
        List<DriverStateSnapshot.HistoryEntry> history = new ArrayList<>();
        for (int i = 1; i <= 3; i++) {
            history.add(makeEntry(i));
        }
        return new DriverStateSnapshot.Complete(
            makeSession(),
            history,
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue("[]")
        );
    }

    @Test
    public void testHistoryListMutationDoesNotAffectStoredSnapshot() {
        List<DriverStateSnapshot.HistoryEntry> history = new ArrayList<>();
        for (int i = 1; i <= 3; i++) {
            history.add(makeEntry(i));
        }

        DriverStateSnapshot.Complete snapshot = new DriverStateSnapshot.Complete(
            makeSession(),
            history,
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue(slotJson()),
            makeValue("[]")
        );

        byte[] originalEncoding = snapshot.encode();
        List<DriverStateSnapshot.HistoryEntry> originalHistory = snapshot.commandHistory();
        byte[] originalHistoryJson = originalHistory.get(0).originalRow().json();

        // Mutate the caller-owned list
        history.clear();
        history.add(makeEntry(99));

        // Verify snapshot is unaffected
        byte[] currentEncoding = snapshot.encode();
        assertArrayEquals(originalEncoding, currentEncoding, "Snapshot encoding must not change after caller list mutation");

        List<DriverStateSnapshot.HistoryEntry> currentHistory = snapshot.commandHistory();
        assertEquals(3, currentHistory.size(), "Snapshot history size must remain 3");
        assertEquals(1, currentHistory.get(0).index(), "First history entry index must remain 1");

        byte[] currentHistoryJson = currentHistory.get(0).originalRow().json();
        assertArrayEquals(originalHistoryJson, currentHistoryJson, "History entry JSON must not change");
    }

    @Test
    public void testValueJsonArrayMutationDoesNotAffectStoredSnapshot() {
        DriverStateSnapshot.Complete snapshot = buildComplete();

        // Get a reference to the internal Value's JSON array via accessor
        DriverStateSnapshot.Slot slot = snapshot.lastCheckpoint();
        assertTrue(slot instanceof DriverStateSnapshot.Value, "lastCheckpoint must be a Value");
        DriverStateSnapshot.Value value = (DriverStateSnapshot.Value) slot;
        byte[] jsonRef = value.json();

        // Capture original state
        byte[] originalEncoding = snapshot.encode();
        byte[] originalJson = Arrays.copyOf(jsonRef, jsonRef.length);

        // Mutate the returned array
        Arrays.fill(jsonRef, (byte) 0);

        // Verify snapshot is unaffected
        byte[] currentEncoding = snapshot.encode();
        assertArrayEquals(originalEncoding, currentEncoding, "Snapshot encoding must not change after Value.json array mutation");

        // Verify the Value itself still holds the original data
        byte[] currentJson = value.json();
        assertArrayEquals(originalJson, currentJson, "Value.json must return a defensive copy or immutable view");
    }

    @Test
    public void testHistoryEntryOriginalRowJsonMutationDoesNotAffectStoredSnapshot() {
        DriverStateSnapshot.Complete snapshot = buildComplete();

        DriverStateSnapshot.HistoryEntry entry = snapshot.commandHistory().get(0);
        DriverStateSnapshot.Value originalRow = entry.originalRow();
        byte[] jsonRef = originalRow.json();

        // Capture original state
        byte[] originalEncoding = snapshot.encode();
        byte[] originalJson = Arrays.copyOf(jsonRef, jsonRef.length);

        // Mutate the returned array
        Arrays.fill(jsonRef, (byte) 0);

        // Verify snapshot is unaffected
        byte[] currentEncoding = snapshot.encode();
        assertArrayEquals(originalEncoding, currentEncoding, "Snapshot encoding must not change after HistoryEntry.originalRow().json() mutation");

        // Verify the Value itself still holds the original data
        byte[] currentJson = originalRow.json();
        assertArrayEquals(originalJson, currentJson, "HistoryEntry.originalRow().json() must return a defensive copy");
    }

    @Test
    public void testEncodeArrayMutationDoesNotAffectSubsequentEncodes() {
        DriverStateSnapshot.Complete snapshot = buildComplete();

        byte[] encoding1 = snapshot.encode();
        byte[] originalEncoding = Arrays.copyOf(encoding1, encoding1.length);

        // Mutate the returned array
        Arrays.fill(encoding1, (byte) 0);

        byte[] encoding2 = snapshot.encode();
        assertArrayEquals(originalEncoding, encoding2, "Subsequent encode() must return identical bytes regardless of prior array mutation");
    }

    @Test
    public void testDecodeCompletePreservesImmutabilityOfInput() {
        DriverStateSnapshot.Complete original = buildComplete();
        byte[] encoded = original.encode();
        byte[] originalEncoded = Arrays.copyOf(encoded, encoded.length);

        // Decode first to ensure the snapshot is created from the input
        DriverStateSnapshot.Complete decoded = DriverStateSnapshot.decodeComplete(encoded);

        // Mutate the input array used for decoding
        Arrays.fill(encoded, (byte) 0);

        // Verify the decoded snapshot's encoding is still valid and unchanged
        byte[] currentEncoding = decoded.encode();
        assertArrayEquals(originalEncoded, currentEncoding, "Decoded snapshot must be unaffected by mutation of its own encode() output");
    }

    @Test
    public void originalConstructorInputsAndReturnedHistoryCannotMutateDriver() {
        byte[] historyInput = toBytes(historyJson(1));
        byte[] slotInput = toBytes(slotJson());
        var originalRow = new DriverStateSnapshot.Value(historyInput);
        var originalSlot = new DriverStateSnapshot.Value(slotInput);
        var history = new ArrayList<DriverStateSnapshot.HistoryEntry>();
        history.add(new DriverStateSnapshot.HistoryEntry(1, originalRow));
        var nil = new DriverStateSnapshot.NullValue();
        var snapshot = new DriverStateSnapshot.Complete(makeSession(), history,
                originalSlot, nil, nil, nil, nil, nil, makeValue("[]"));
        byte[] before = snapshot.encode();
        byte[] beforeRow = originalRow.json();
        byte[] beforeSlot = originalSlot.json();

        Arrays.fill(historyInput, (byte) 'x');
        Arrays.fill(slotInput, (byte) 'x');
        assertArrayEquals(beforeRow, originalRow.json());
        assertArrayEquals(beforeSlot, originalSlot.json());
        assertArrayEquals(before, snapshot.encode());

        assertThrows(UnsupportedOperationException.class,
                () -> snapshot.commandHistory().clear());
        assertThrows(UnsupportedOperationException.class,
                () -> snapshot.commandHistory().add(makeEntry(2)));
        assertEquals(1, snapshot.commandHistory().size());
        assertArrayEquals(before, snapshot.encode());
    }
}
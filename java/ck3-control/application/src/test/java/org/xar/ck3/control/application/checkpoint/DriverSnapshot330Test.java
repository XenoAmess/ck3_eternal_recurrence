package org.xar.ck3.control.application.checkpoint;

import static org.junit.jupiter.api.Assertions.assertArrayEquals;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertInstanceOf;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.math.BigInteger;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Complete;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.HistoryEntry;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Missing;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Session;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Slot;
import org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value;

/** Public immutable DATA contracts only; no reflection, archive, current source or writer authority. */
class DriverSnapshot330Test {
    private static final String ROW = "{\"index\":1,\"opaque\":-0.00e+2,\"integer\":18446744073709551615,\"text\":\"雪é\",\"nullable\":null}";
    private static final Session SESSION = new Session("snapshot-330-pipe", 123,
            new BigInteger("31254"), "snapshot-330-episode");

    private static byte[] utf8(String text) {
        return text.getBytes(StandardCharsets.UTF_8);
    }

    private static Complete snapshot(List<HistoryEntry> history, Slot shared, Slot optional) {
        return new Complete(SESSION, history, shared, new NullValue(), shared,
                shared, optional, shared, new Missing());
    }

    private static String expected() {
        return "{\"format_version\":2,\"pipe_name\":\"snapshot-330-pipe\",\"bridge_pid\":123,"
                + "\"episode_character_id\":31254,\"episode_run_id\":\"snapshot-330-episode\","
                + "\"command_history\":[" + ROW + "],\"last_checkpoint\":" + ROW
                + ",\"rollback_war_failure\":null,\"managed_restore_transaction\":" + ROW
                + ",\"succession_expectation\":" + ROW + ",\"campaign_goal\":" + ROW + "}";
    }

    @Test
    void constructorAccessorAndRepeatedEncodingKeepSharedValuesDetached() {
        byte[] callerRow = utf8(" \n" + ROW + " \t");
        Value shared = new Value(callerRow);
        Value equal = new Value(utf8(ROW));
        int originalHash = shared.hashCode();
        byte[] firstGetter = shared.json();
        byte[] secondGetter = shared.json();
        assertNotSame(firstGetter, secondGetter);
        assertArrayEquals(utf8(ROW), firstGetter);
        Arrays.fill(callerRow, (byte) '!');
        Arrays.fill(firstGetter, (byte) '!');
        assertArrayEquals(utf8(ROW), shared.json());
        assertEquals(equal, shared);
        assertEquals(originalHash, shared.hashCode());

        HistoryEntry entry = new HistoryEntry(1, shared);
        Complete complete = snapshot(List.of(entry), shared, new Missing());
        byte[] expectedBytes = utf8(expected());
        byte[] firstEncoding = complete.encode();
        assertArrayEquals(expectedBytes, firstEncoding);
        Arrays.fill(firstEncoding, (byte) '!');
        Arrays.fill(entry.originalRow().json(), (byte) '!');
        Arrays.fill(((Value) complete.lastCheckpoint()).json(), (byte) '!');
        assertArrayEquals(expectedBytes, complete.encode());
        assertArrayEquals(utf8(ROW), secondGetter);
        assertArrayEquals(utf8(ROW), shared.json());

        byte[] originalWire = expectedBytes.clone();
        Complete replayed = DriverStateSnapshot.decodeComplete(originalWire);
        Arrays.fill(originalWire, (byte) '!');
        assertArrayEquals(expectedBytes, replayed.encode());
        assertInstanceOf(Missing.class, replayed.successionLifecycle());
        assertInstanceOf(Missing.class, replayed.rollbackWarFailures());
        assertInstanceOf(NullValue.class, replayed.rollbackWarFailure());
        assertFalse(new String(replayed.encode(), StandardCharsets.UTF_8).contains("succession_lifecycle"));
        Arrays.fill(replayed.commandHistory().getFirst().originalRow().json(), (byte) '!');
        Arrays.fill(((Value) replayed.managedRestoreTransaction()).json(), (byte) '!');
        assertArrayEquals(expectedBytes, replayed.encode());

        Complete explicitNull = snapshot(List.of(entry), shared, new NullValue());
        assertInstanceOf(NullValue.class,
                DriverStateSnapshot.decodeComplete(explicitNull.encode()).successionLifecycle());
    }

    @Test
    void everyPublicIngressStillRejectsInvalidTokensIndicesAndMissingRequiredFields() {
        Value row = new Value(utf8(ROW));
        IllegalArgumentException mismatch = assertThrows(IllegalArgumentException.class,
                () -> new HistoryEntry(2, row));
        assertEquals("history entry typed index equals original integer token", mismatch.getMessage());
        assertThrows(IllegalArgumentException.class,
                () -> new HistoryEntry(1, new Value(utf8("{\"index\":1.0}"))));
        assertThrows(IllegalArgumentException.class,
                () -> new HistoryEntry(1, new Value(utf8("{\"index\":true}"))));
        assertThrows(IllegalArgumentException.class,
                () -> new HistoryEntry(1, new Value(utf8("[]"))));
        assertThrows(IllegalArgumentException.class, () -> new Value(utf8("null")));
        assertThrows(IllegalArgumentException.class, () -> new Value(utf8("{\"a\":1,\"a\":2}")));
        assertThrows(IllegalArgumentException.class, () -> new Value(utf8("{} {}")));
        assertThrows(IllegalArgumentException.class, () -> new Value(new byte[] {(byte) 0xc3, 0x28}));
        Value deepest = new Value(utf8("[".repeat(64) + "0" + "]".repeat(64)));
        assertArrayEquals(utf8("[".repeat(64) + "0" + "]".repeat(64)), deepest.json());
        assertThrows(IllegalArgumentException.class,
                () -> new Value(utf8("[".repeat(65) + "0" + "]".repeat(65))));

        HistoryEntry first = new HistoryEntry(1, row);
        HistoryEntry second = new HistoryEntry(2, new Value(utf8("{\"index\":2}")));
        assertThrows(IllegalArgumentException.class,
                () -> snapshot(List.of(second, first), row, new Missing()));
        assertThrows(IllegalArgumentException.class,
                () -> new Complete(SESSION, List.of(first), new Missing(), new NullValue(), row,
                        row, new Missing(), row, new Missing()));
        String wire = expected();
        assertThrows(IllegalArgumentException.class,
                () -> DriverStateSnapshot.decodeComplete(utf8(wire.replace("\"format_version\":2", "\"format_version\":3"))));
        assertThrows(IllegalArgumentException.class,
                () -> DriverStateSnapshot.decodeComplete(utf8(wire.replace("\"bridge_pid\":123", "\"bridge_pid\":true"))));
        assertThrows(IllegalArgumentException.class,
                () -> DriverStateSnapshot.decodeComplete(utf8(wire.substring(0, wire.length() - 1) + ",\"unknown\":null}")));
        assertThrows(IllegalArgumentException.class,
                () -> DriverStateSnapshot.decodeComplete(utf8(wire.replace("\"campaign_goal\":" + ROW, "\"campaign_goal_renamed\":" + ROW))));
        assertThrows(IllegalArgumentException.class, () -> DriverStateSnapshot.decodeComplete(utf8("[]")));
        assertArrayEquals(utf8(wire), DriverStateSnapshot.decodeComplete(utf8(wire)).encode());
    }
}

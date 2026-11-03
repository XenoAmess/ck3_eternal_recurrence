package org.xar.ck3.study.m6.activity265;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api;
import org.xar.ck3.control.g2.m2.nativecode.FullCopy437Api.Bits256;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;

/** Artificial shared storage for only the held four-instruction word/byte block. */
public final class ActivityWordBlock265IndependentTest {
    private static final long IMAGE = 0x1234_5678_0000_0000L;
    private static final long RBP = 0x1234_5678_0443_9546L;
    private static final long WORD_SOURCE = 0x1234_5678_0443_9524L;
    private static final long BYTE_SOURCE = 0x1234_5678_0443_9526L;
    private static final long WORD_DESTINATION = 0x1234_5678_0443_9526L;
    private static final long BYTE_DESTINATION = 0x1234_5678_0443_9528L;

    private ActivityWordBlock265IndependentTest() { }

    public static void main(String[] args) {
        check(args.length == 0, "this manual selects exactly its three new scenes");
        freshByteAlias();
        readWordBeforeError();
        writeWordAfterError();
        System.out.println("Three new activity word-block alias/error-prefix scenes passed");
    }

    private static void freshByteAlias() {
        OwnedMemory memory = new OwnedMemory(null, null);
        long result = ActivityWordBlock265.execute(IMAGE, RBP, memory);

        check(result == 0xB7L, "final EAX must contain the fresh unsigned aliased byte");
        check(memory.trace.equals(List.of(
                new Access("readUnsignedWord", WORD_SOURCE, 0),
                new Access("writeWord", WORD_DESTINATION, 0xE2B7),
                new Access("readUnsignedByte", BYTE_SOURCE, 0),
                new Access("writeByte", BYTE_DESTINATION, 0xB7))),
                "exact word/word/byte/byte port order and widths");
        check(memory.snapshot().equals(Map.ofEntries(
                Map.entry(0x1234_5678_0443_9523L, 0x5A),
                Map.entry(0x1234_5678_0443_9524L, 0xB7),
                Map.entry(0x1234_5678_0443_9525L, 0xE2),
                Map.entry(0x1234_5678_0443_9526L, 0xB7),
                Map.entry(0x1234_5678_0443_9527L, 0xE2),
                Map.entry(0x1234_5678_0443_9528L, 0xB7),
                Map.entry(0x1234_5678_0443_9529L, 0xF1))),
                "complete owned bytes: alias is fresh, word high byte and neighbors are exact");
    }

    private static void readWordBeforeError() {
        RuntimeException supplied = new IllegalStateException("owned read-word before operation");
        OwnedMemory memory = new OwnedMemory(supplied, null);

        expectSame(supplied, () -> ActivityWordBlock265.execute(IMAGE, RBP, memory));

        check(memory.trace.equals(List.of(new Access("readUnsignedWord", WORD_SOURCE, 0))),
                "word-read attempt fails before any subsequent port operation");
        check(memory.snapshot().equals(initialCells()), "before-read error has no cell effect");
    }

    private static void writeWordAfterError() {
        RuntimeException supplied = new IllegalArgumentException("owned word-write after commit");
        OwnedMemory memory = new OwnedMemory(null, supplied);

        expectSame(supplied, () -> ActivityWordBlock265.execute(IMAGE, RBP, memory));

        check(memory.trace.equals(List.of(
                new Access("readUnsignedWord", WORD_SOURCE, 0),
                new Access("writeWord", WORD_DESTINATION, 0xE2B7))),
                "committed word-write error must prevent the later byte read and byte write");
        check(memory.snapshot().equals(Map.ofEntries(
                Map.entry(0x1234_5678_0443_9523L, 0x5A),
                Map.entry(0x1234_5678_0443_9524L, 0xB7),
                Map.entry(0x1234_5678_0443_9525L, 0xE2),
                Map.entry(0x1234_5678_0443_9526L, 0xB7),
                Map.entry(0x1234_5678_0443_9527L, 0xE2),
                Map.entry(0x1234_5678_0443_9528L, 0xD8),
                Map.entry(0x1234_5678_0443_9529L, 0xF1))),
                "this fixture commits exactly two bytes before its ordinary error");
    }

    private static Map<Long, Integer> initialCells() {
        return Map.ofEntries(
                Map.entry(0x1234_5678_0443_9523L, 0x5A),
                Map.entry(0x1234_5678_0443_9524L, 0xB7),
                Map.entry(0x1234_5678_0443_9525L, 0xE2),
                Map.entry(0x1234_5678_0443_9526L, 0x19),
                Map.entry(0x1234_5678_0443_9527L, 0x6C),
                Map.entry(0x1234_5678_0443_9528L, 0xD8),
                Map.entry(0x1234_5678_0443_9529L, 0xF1));
    }

    private static void expectSame(RuntimeException supplied, Runnable action) {
        try {
            action.run();
        } catch (RuntimeException actual) {
            if (actual != supplied) {
                throw new AssertionError("ordinary Memory error was replaced or wrapped", actual);
            }
            return;
        }
        throw new AssertionError("ordinary Memory error was swallowed");
    }

    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    /** Values are normalized to the store width, as required by the existing ports. */
    private record Access(String operation, long address, int storeBits) { }

    private static final class OwnedMemory implements FullCopy437Api.Memory {
        private final Map<Long, Integer> cells = new HashMap<>(initialCells());
        private final List<Access> trace = new ArrayList<>();
        private final RuntimeException readWordBeforeError;
        private final RuntimeException writeWordAfterError;

        OwnedMemory(RuntimeException readWordBeforeError, RuntimeException writeWordAfterError) {
            this.readWordBeforeError = readWordBeforeError;
            this.writeWordAfterError = writeWordAfterError;
        }

        Map<Long, Integer> snapshot() { return Map.copyOf(cells); }

        private int cell(long address) {
            Integer value = cells.get(address);
            if (value == null) throw new AssertionError("unmapped owned byte " + Long.toHexString(address));
            return value;
        }

        private void store(long address, int value) {
            if (!cells.containsKey(address)) {
                throw new AssertionError("unmapped owned byte store " + Long.toHexString(address));
            }
            cells.put(address, value & 0xFF);
        }

        @Override public int readUnsignedWord(long address) {
            trace.add(new Access("readUnsignedWord", address, 0));
            // This supplied error is before the fixture reads either source cell.
            if (readWordBeforeError != null) throw readWordBeforeError;
            return cell(address) | (cell(address + 1) << 8);
        }

        @Override public void writeWord(long address, int value) {
            trace.add(new Access("writeWord", address, value & 0xFFFF));
            store(address, value);
            store(address + 1, value >>> 8);
            // This supplied error is after both commits; no general atomicity is assumed.
            if (writeWordAfterError != null) throw writeWordAfterError;
        }

        @Override public int readUnsignedByte(long address) {
            trace.add(new Access("readUnsignedByte", address, 0));
            return cell(address);
        }

        @Override public void writeByte(long address, int value) {
            trace.add(new Access("writeByte", address, value & 0xFF));
            store(address, value);
        }

        @Override public int readDword(long address) { throw unexpected("readDword"); }
        @Override public long readQword(long address) { throw unexpected("readQword"); }
        @Override public void writeDword(long address, int value) { throw unexpected("writeDword"); }
        @Override public int lockedXaddDword(long address, int value) { throw unexpected("lockedXaddDword"); }
        @Override public void writeQword(long address, long value) { throw unexpected("writeQword"); }
        @Override public Bits128 read128(long address) { throw unexpected("read128"); }
        @Override public void write128(long address, Bits128 value) { throw unexpected("write128"); }
        @Override public void write128NonTemporal(long address, Bits128 value) { throw unexpected("write128NonTemporal"); }
        @Override public void sfence() { throw unexpected("sfence"); }
        @Override public Bits256 read256(long address) { throw unexpected("read256"); }
        @Override public void write256(long address, Bits256 value) { throw unexpected("write256"); }
        @Override public void write256NonTemporal(long address, Bits256 value) { throw unexpected("write256NonTemporal"); }

        private AssertionError unexpected(String operation) {
            return new AssertionError("unexpected widened or extra Memory operation: " + operation);
        }
    }
}

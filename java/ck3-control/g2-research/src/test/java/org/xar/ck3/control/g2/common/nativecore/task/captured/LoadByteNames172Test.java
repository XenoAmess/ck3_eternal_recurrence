package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Unsigned byte order, fresh same-address reads and callback exception witnesses. */
public final class LoadByteNames172Test {
    private record ByteRead(long address, int value) { }
    private static ByteRead b(long address, int value) { return new ByteRead(address, value); }
    private static final class Memory implements LoadSearch4260af0.ReadMemory {
        private final ArrayDeque<ByteRead> expected;
        private Memory(ByteRead... rows) { expected = new ArrayDeque<>(Arrays.asList(rows)); }
        @Override public int readInt32(long address) { throw new AssertionError("unexpected DWORD"); }
        @Override public int readUnsigned8(long address) {
            ByteRead next = expected.remove();
            assertEquals(next.address(), address);
            return next.value();
        }
        private void done() { assertEquals(0, expected.size()); }
    }
    @Test public void unsignedDifferenceAndEqualNul() {
        Memory high = new Memory(b(0x1000L, 0x80), b(0x2000L, 0x7F));
        assertEquals(1, LoadByteNames4260b67.compare(0x1000L, 0x2000L, high));
        high.done();
        Memory equal = new Memory(b(0x3000L, 0x41), b(0x3000L, 0x41),
                b(0x3001L, 0), b(0x3001L, 0));
        assertEquals(0, LoadByteNames4260b67.compare(0x3000L, 0x3000L, equal));
        equal.done();
    }
    @Test public void sameAddressFreshReadsAndSameException() {
        Memory changing = new Memory(b(0x4000L, 0x41), b(0x4000L, 0x42));
        assertEquals(-1, LoadByteNames4260b67.compare(0x4000L, 0x4000L, changing));
        changing.done();
        RuntimeException sentinel = new IllegalStateException("owned byte failure");
        ArrayDeque<Long> trace = new ArrayDeque<>();
        LoadSearch4260af0.ReadMemory throwing = new LoadSearch4260af0.ReadMemory() {
            @Override public int readInt32(long address) { throw new AssertionError("unexpected DWORD"); }
            @Override public int readUnsigned8(long address) { trace.add(address); throw sentinel; }
        };
        assertSame(sentinel, assertThrows(IllegalStateException.class,
                () -> LoadByteNames4260b67.compare(0x5000L, 0x5000L, throwing)));
        assertEquals(Arrays.asList(0x5000L), Arrays.asList(trace.toArray(new Long[0])));
    }
}

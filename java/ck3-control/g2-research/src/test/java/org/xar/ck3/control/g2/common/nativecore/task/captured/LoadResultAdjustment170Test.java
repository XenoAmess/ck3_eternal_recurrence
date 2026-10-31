package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.Arrays;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** Signed displacements, fresh reads and full-width wrap with supplied memory. */
public final class LoadResultAdjustment170Test {
    private record Read(boolean qword, long address, long value) { }
    private static Read d(long address, int bits) { return new Read(false, address, bits); }
    private static Read q(long address, long bits) { return new Read(true, address, bits); }
    private static final class Memory implements NativeTaskMemory {
        private final ArrayDeque<Read> expected;
        private Memory(Read... reads) { expected = new ArrayDeque<>(Arrays.asList(reads)); }
        private long take(boolean qword, long address) {
            Read r = expected.remove();
            assertEquals(r.qword(), qword);
            assertEquals(r.address(), address);
            return r.value();
        }
        @Override public long readPointer(long address) { return take(true, address); }
        @Override public int readInt32(long address) { return (int) take(false, address); }
        @Override public void writeInt32(long address, int bits) { throw new AssertionError("write32"); }
        @Override public void writeInt64(long address, long bits) { throw new AssertionError("write64"); }
        private void done() { assertEquals(0, expected.size()); }
    }

    @Test public void signedNegativeSkipsNestedReadAndFullLongWraps() {
        Memory negative = new Memory(d(0x200CL, -1), d(0x2008L, -7));
        assertEquals(0xFF9L, LoadResultAdjustment4260f6b.adjust(0x1000L, 0x2000L, negative));
        negative.done();
        Memory wrap = new Memory(d(0x500CL, Integer.MIN_VALUE), d(0x5008L, 10));
        assertEquals(0x8000000000000008L,
                LoadResultAdjustment4260f6b.adjust(0x7FFFFFFFFFFFFFFEL, 0x5000L, wrap));
        wrap.done();
    }

    @Test public void nonnegativePathUsesSignedIndicesAndFreshRepeatedRead() {
        Memory signed = new Memory(d(0x200CL, 4), d(0x200CL, 4), d(0x2010L, -16),
                q(0x1004L, 0x3000L), d(0x2FF0L, -8), d(0x2008L, 12));
        assertEquals(0x1008L, LoadResultAdjustment4260f6b.adjust(0x1000L, 0x2000L, signed));
        signed.done();
        Memory changed = new Memory(d(0x200CL, 1), d(0x200CL, -4), d(0x2010L, -8),
                q(0xFFCL, 0x4000L), d(0x3FF8L, -9), d(0x2008L, 5));
        assertEquals(0xFF8L, LoadResultAdjustment4260f6b.adjust(0x1000L, 0x2000L, changed));
        changed.done();
    }
}

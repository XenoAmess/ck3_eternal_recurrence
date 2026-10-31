package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import static org.junit.jupiter.api.Assertions.assertEquals;

/** Exact addressed-read witnesses for pointer/name passes and runtime composition. */
public final class LoadSearch172Test {
    private static final long B = 0x100000000L;
    private record Read(int width, long address, long bits) { }
    private static Read d(long address, int bits) { return new Read(4, address, bits); }
    private static Read b(long address, int bits) { return new Read(1, address, bits); }
    private static Read q(long address, long bits) { return new Read(8, address, bits); }
    private static final class Memory implements LoadSearch4260af0.ReadMemory, NativeTaskMemory {
        private final ArrayDeque<Read> expected = new ArrayDeque<>();
        private Memory(Read... reads) { expected.addAll(Arrays.asList(reads)); }
        private long take(int width, long address) {
            Read r = expected.remove();
            assertEquals(r.width(), width);
            assertEquals(r.address(), address);
            return r.bits();
        }
        @Override public int readInt32(long address) { return (int) take(4, address); }
        @Override public int readUnsigned8(long address) { return (int) take(1, address); }
        @Override public long readPointer(long address) { return take(8, address); }
        @Override public void writeInt32(long address, int value) { throw new AssertionError("write32"); }
        @Override public void writeInt64(long address, long value) { throw new AssertionError("write64"); }
        private void done() { assertEquals(0, expected.size()); }
    }
    private static LoadRuntime4260e74.SearchCall call(long source, long target) {
        return new LoadRuntime4260e74.SearchCall(0x7000L, source, target, B,
                Long.MIN_VALUE, OptionalLong.empty(), OptionalLong.empty());
    }
    private static Memory fast(int count, int flags) {
        Memory m = new Memory(d(0x7010L, 0x100), d(B + 0x10CL, 0x200), d(B + 0x108L, count));
        if (count != 0) {
            m.expected.addAll(Arrays.asList(d(B + 0x200L, 0x300), d(B + 0x300L, 0x400),
                    d(B + 0x204L, 0x500), b(B + 0x514L, flags)));
            if ((flags & 4) == 0) { m.expected.add(d(B + 0x500L, 0x600)); }
        }
        return m;
    }
    private static Memory namesPrefix(int count) {
        Memory m = new Memory(d(0x7010L, 0x100), d(B + 0x10CL, 0x200), d(B + 0x108L, count),
                d(B + 0x200L, 0x300), d(B + 0x300L, 0x400));
        if (count == 2) { m.expected.addAll(Arrays.asList(d(B + 0x204L, 0x500), d(B + 0x500L, 0x600))); }
        m.expected.addAll(Arrays.asList(d(B + 0x200L, 0x300), d(B + 0x300L, 0x400)));
        return m;
    }

    @Test public void zeroFastMatchFlagStopAndUnsignedHighCount() {
        Memory zero = fast(0, 0);
        assertEquals(0L, LoadSearch4260af0.find(call(B + 0x600L, B + 0x400L), zero));
        zero.done();
        Memory match = fast(2, 0);
        assertEquals(B + 0x300L, LoadSearch4260af0.find(call(B + 0x600L, B + 0x400L), match));
        match.done();
        Memory blocked = fast(2, 4);
        assertEquals(0L, LoadSearch4260af0.find(call(B + 0x600L, B + 0x400L), blocked));
        blocked.done();
        Memory highCount = fast(Integer.MIN_VALUE, 0);
        assertEquals(B + 0x300L, LoadSearch4260af0.find(call(B + 0x600L, B + 0x400L), highCount));
        highCount.done();
    }

    @Test public void fallbackNamesRereadDescriptorsAndPreserveReturnedTarget() {
        Memory matched = namesPrefix(2);
        matched.expected.addAll(Arrays.asList(b(B + 0x410L, 0x41), b(B + 0x710L, 0x41),
                b(B + 0x411L, 0), b(B + 0x711L, 0), d(B + 0x204L, 0x500),
                b(B + 0x514L, 0), d(B + 0x500L, 0x600), b(B + 0x610L, 0x42),
                b(B + 0x810L, 0x42), b(B + 0x611L, 0), b(B + 0x811L, 0)));
        assertEquals(B + 0x300L, LoadSearch4260af0.find(call(B + 0x800L, B + 0x700L), matched));
        matched.done();
        Memory mismatch = namesPrefix(2);
        mismatch.expected.addAll(Arrays.asList(b(B + 0x410L, 0x41), b(B + 0x710L, 0x5A),
                d(B + 0x204L, 0x500), d(B + 0x500L, 0x600),
                b(B + 0x610L, 0x42), b(B + 0x710L, 0x5A)));
        assertEquals(0L, LoadSearch4260af0.find(call(B + 0x800L, B + 0x700L), mismatch));
        mismatch.done();
        Memory last = namesPrefix(1);
        last.expected.addAll(Arrays.asList(b(B + 0x410L, 0x41), b(B + 0x710L, 0x41),
                b(B + 0x411L, 0), b(B + 0x711L, 0)));
        assertEquals(0L, LoadSearch4260af0.find(call(B + 0x800L, B + 0x700L), last));
        last.done();
    }

    @Test public void actualRuntimeImportAndSearchConsumersUseTheNewMethod() {
        Memory m = new Memory(q(0x10000L, 0x12000L), q(0x11FF8L, 0x13000L),
                d(0x13004L, 0x100), d(0x13008L, 0), d(0x10000L, 0x12000), d(0x13000L, 1),
                d(0x13014L, 0x3000), d(0x13010L, 0x20), d(0x10024L, 0),
                d(0x13010L, 0x20), d(0x1002CL, 0x200), d(0x10028L, 2),
                d(0x10200L, 0x300), d(0x10300L, 0x400), d(0x10204L, 0x500),
                b(0x10514L, 0), d(0x10500L, 0x600), d(0x1030CL, -1), d(0x10308L, 0x44));
        LoadRuntimeImportBinding.SearchPorts remainder = new LoadRuntimeImportBinding.SearchPorts() {
            @Override public long call4260af0(LoadRuntime4260e74.SearchCall c) { throw new AssertionError("unbound af0"); }
            @Override public long call4260968(LoadRuntime4260e74.SearchCall c) { throw new AssertionError("unexpected968"); }
            @Override public long call4260c28(LoadRuntime4260e74.SearchCall c) { throw new AssertionError("unexpectedc28"); }
        };
        LoadRuntime4260e74.Ports ports = LoadRuntimeImportBinding.ports(
                (pc, slot) -> { throw new AssertionError("unexpected legacy API"); },
                LoadSearchRuntimeConsumer.ports(m, remainder));
        assertEquals(0xFF44L, LoadRuntime4260e74.execute(0x140000000L,
                0x10000L, -7, 0x10600L, 0x10400L, 0, m, ports));
        m.done();
    }
}

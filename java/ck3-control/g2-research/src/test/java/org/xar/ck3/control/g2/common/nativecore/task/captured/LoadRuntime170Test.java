package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayDeque;
import java.util.OptionalLong;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;

/** Finite normal-path and callback-boundary witnesses with supplied memory and ports. */
public final class LoadRuntime170Test {
    private static final long BASE = 0x140000000L;
    private record Read(boolean qword, long address, long value) { }
    private static Read d(long address, int value) { return new Read(false, address, value); }
    private static Read q(long address, long value) { return new Read(true, address, value); }

    private static final class Fixture implements NativeTaskMemory, LoadRuntime4260e74.Ports {
        private final ArrayDeque<Object> expected = new ArrayDeque<>();
        private final int flags;
        private final long result;
        private final boolean throwAtSearch;
        private final RuntimeException same = new IllegalStateException("owned callback failure");
        private LoadRuntime4260e74.LocalSlot64 legacySlot;
        private long source = 0x4444L;
        private long target = 0x5555L;
        private Fixture(int flags, boolean legacy, long result, boolean throwAtSearch) {
            this.flags = flags;
            this.result = result;
            this.throwAtSearch = throwAtSearch;
            expected.add(q(0x10000L, 0x12000L));
            expected.add(q(0x11FF8L, 0x13000L));
            expected.add(d(0x13004L, 0x100));
            expected.add(d(0x13008L, 0));
            expected.add(d(0x10000L, 0x12000));
            expected.add(d(0x13000L, legacy ? 0 : 1));
            expected.add(legacy ? "legacy" : d(0x13014L, 0x3000));
            expected.add(d(0x13010L, 0x20));
            expected.add(d(0x10024L, flags));
            expected.add((flags & 1) == 0 ? "af0" : (flags & 2) == 0 ? "968" : "c28");
            if (result != 0L && !throwAtSearch) {
                expected.add(d(result + 0xCL, -1));
                expected.add(d(result + 0x8L, 0x44));
            }
        }
        private long read(boolean qword, long address) {
            if (legacySlot != null) { assertEquals(OptionalLong.of(0x10000L), legacySlot.value()); }
            Object next = expected.remove();
            if (!(next instanceof Read r)) { throw new AssertionError("Expected callback before read: " + next); }
            assertEquals(r.qword(), qword);
            assertEquals(r.address(), address);
            return r.value();
        }
        @Override public long readPointer(long address) { return read(true, address); }
        @Override public int readInt32(long address) { return (int) read(false, address); }
        @Override public void writeInt32(long address, int value) { throw new AssertionError("write32"); }
        @Override public void writeInt64(long address, long value) { throw new AssertionError("write64"); }
        @Override public long call43da2d0(long rcx, LoadRuntime4260e74.LocalSlot64 slot,
                long r8, long r9, long rax) {
            assertEquals("legacy", expected.remove());
            assertEquals(0x13000L, rcx);
            assertEquals(source, r8);
            assertEquals(target, r9);
            assertEquals(0L, rax);
            assertEquals(OptionalLong.empty(), slot.value());
            slot.store(0xDEADBEEFL);
            legacySlot = slot;
            return 0x10000L;
        }
        private long search(String route, LoadRuntime4260e74.SearchCall call) {
            assertEquals(route, expected.remove());
            LoadRuntime4260e74.SearchCall wanted = (flags & 1) == 0
                    ? new LoadRuntime4260e74.SearchCall(0x13000L, source, target, 0x10000L,
                            0x20L, OptionalLong.empty(), OptionalLong.empty())
                    : new LoadRuntime4260e74.SearchCall(0xFF00L, 0x13000L, source, 0x107L,
                            0x20L, OptionalLong.of(target), OptionalLong.of(0x10000L));
            assertEquals(wanted, call);
            if (throwAtSearch) { throw same; }
            return result;
        }
        @Override public long call4260af0(LoadRuntime4260e74.SearchCall c) { return search("af0", c); }
        @Override public long call4260968(LoadRuntime4260e74.SearchCall c) { return search("968", c); }
        @Override public long call4260c28(LoadRuntime4260e74.SearchCall c) { return search("c28", c); }
        private long run(int mode) {
            return LoadRuntime4260e74.execute(BASE, 0x10000L, -7, source, target, mode, this, this);
        }
        private void done() { assertEquals(0, expected.size()); }
    }

    @Test public void nullAndAllThreeSelectedCallsRespectWidthsAndPackets() {
        Fixture empty = new Fixture(0, false, 0L, false);
        empty.expected.clear();
        assertEquals(0L, LoadRuntime4260e74.execute(BASE, 0L, -7, 1L, 2L, 99, empty, empty));
        empty.done();
        for (int flags : new int[] {0, 1, 3}) {
            Fixture f = new Fixture(flags, false, 0x15000L, false);
            assertEquals(0xFF44L, f.run(0));
            f.done();
        }
    }

    @Test public void legacySlotStoreAndActualGetterConsumerComposeWithoutFallback() {
        Fixture legacy = new Fixture(0, true, 0x15000L, false);
        assertEquals(0xFF44L, legacy.run(0));
        assertEquals(OptionalLong.of(0x10000L), legacy.legacySlot.value());
        legacy.done();
        Fixture composed = new Fixture(0, false, 0x15000L, false);
        composed.source = BASE + 0x5514438L;
        composed.target = BASE + 0x5514460L;
        composed.expected.addFirst(q(0x19010L, 0x10000L));
        composed.expected.addFirst(q(BASE + 0x5C6A520L, 0x19000L));
        composed.expected.addLast(q(0xFF6CL, 0x8000000000ABCDEFL));
        assertEquals(0x8000000000ABCDEFL, LoadSharedGetterC45df0.get(BASE, composed,
                LoadSharedRuntimeConsumer.ports(BASE, composed, composed)));
        composed.done();
    }

    @Test public void zeroAndUnsupportedFailureOrCallbackExceptionStopWithoutMoreReads() {
        Fixture zero = new Fixture(0, false, 0L, false);
        assertEquals(0L, zero.run(0));
        zero.done();
        Fixture rejected = new Fixture(1, false, 0L, false);
        LoadRuntime4260e74.SourceBoundary boundary = assertThrows(LoadRuntime4260e74.SourceBoundary.class,
                () -> rejected.run(Integer.MIN_VALUE));
        assertEquals(Integer.MIN_VALUE, boundary.failureModeBits());
        assertEquals(0xFF00L, boundary.completeObjectBits());
        assertEquals(0x4260FB6L, boundary.sourceTargetRva());
        assertEquals(0x4260FD9L, boundary.terminalRva());
        rejected.done();
        Fixture throwing = new Fixture(3, false, 0L, true);
        assertSame(throwing.same, assertThrows(IllegalStateException.class, () -> throwing.run(0)));
        throwing.done();
    }
}

package org.xar.ck3.control.g2.common.nativecore.task.captured;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

public final class StaticObjectB15000GrowthPortsTest {
    @Test
    public void repeatedGetterReadsAndOtherCallbacksPreserveSuppliedDependencies() {
        final Sparse177TestMemory memory = new Sparse177TestMemory();
        final Idler79eRegressionHost.Memory bytes = memory.bytes();
        final long moduleBase = 0x0000000100000000L;
        final long object = moduleBase + 0x5D1EAF0L;
        final long guard = moduleBase + 0x5D1EB08L;
        final long gsSlot1 = bytes.allocate(8);
        final long tls1 = bytes.allocate(20);
        final long gsSlot2 = bytes.allocate(8);
        final long tls2 = bytes.allocate(20);
        bytes.map(object, 16);
        bytes.map(guard, 4);
        bytes.seedInt64(gsSlot1, tls1);
        bytes.seedInt32(tls1 + 0x10L, 100);
        bytes.seedInt64(gsSlot2, tls2);
        bytes.seedInt32(tls2 + 0x10L, -7);
        bytes.seedInt32(guard, 50);
        for (int i = 0; i < 16; i++) bytes.seedByte(object + i, 0x60 + i);
        final List<Long> gsReads = new ArrayList<>();
        final List<String> staticCalls = new ArrayList<>();
        final StaticObjectB15000.Ports staticPorts = new StaticObjectB15000.Ports() {
            @Override public long readGs58() {
                final long slot = gsReads.isEmpty() ? gsSlot1 : gsSlot2;
                gsReads.add(slot);
                return slot;
            }
            @Override public void call4223a84(long rcx) {
                assertEquals(guard, rcx);
                staticCalls.add("guard");
                bytes.seedInt32(guard, -1);
            }
            @Override public void call4223a24(long rcx) {
                assertEquals(guard, rcx);
                assertEquals(0, bytes.peekUnsignedByte(object));
                assertEquals(255, bytes.peekUnsignedByte(object + 12L));
                staticCalls.add("commit");
                bytes.seedInt32(guard, 0x24681357);
            }
        };
        final List<SparseIntCells177Growth.KnownVirtual8> virtual8Calls = new ArrayList<>();
        final List<SparseIntCells177Growth.KnownVirtual16> virtual16Calls = new ArrayList<>();
        final List<SparseIntCells177Growth.Known17836d0> reinsertCalls = new ArrayList<>();
        final List<SparseIntCells177Growth.FrameAddress> frameCalls = new ArrayList<>();
        final List<Long> frameRdxCalls = new ArrayList<>();
        final List<String> otherCalls = new ArrayList<>();
        final long virtual8Return = 0xFEDCBA9876543210L;
        final IllegalStateException sentinel = new IllegalStateException("opaque reinsert failure");
        final SparseIntCells177Growth.Ports other = new SparseIntCells177Growth.Ports() {
            @Override public long callVirtual8(SparseIntCells177Growth.KnownVirtual8 known) {
                virtual8Calls.add(known);
                otherCalls.add("virtual8");
                return virtual8Return;
            }
            @Override public void callVirtual16(SparseIntCells177Growth.KnownVirtual16 known) {
                virtual16Calls.add(known);
                otherCalls.add("virtual16");
            }
            @Override public long callB15000() {
                throw new AssertionError("B15000 must use the supplied getter");
            }
            @Override public void call17836d0(SparseIntCells177Growth.Known17836d0 known) {
                reinsertCalls.add(known);
                otherCalls.add("reinsert");
                throw sentinel;
            }
            @Override public void call86f210(SparseIntCells177Growth.FrameAddress rcx, long rdx) {
                frameCalls.add(rcx);
                frameRdxCalls.add(rdx);
                otherCalls.add("frame");
            }
            @Override public void call4232cf4() {
                otherCalls.add("terminal");
            }
        };
        final StaticObjectB15000GrowthPorts adapter = new StaticObjectB15000GrowthPorts(
                moduleBase, memory, staticPorts, other);

        final long first = adapter.callB15000();
        final List<Idler79eRegressionHost.Access> firstTrace = bytes.trace();
        assertEquals(object, first);
        assertEquals(List.of(gsSlot1), gsReads);
        assertTrue(staticCalls.isEmpty());
        assertTrue(otherCalls.isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, gsSlot1, 8, tls1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, tls1 + 0x10L, 4, 100),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, 50)
        ), firstTrace);
        for (int i = 0; i < 16; i++) assertEquals(0x60 + i, bytes.peekUnsignedByte(object + i));
        bytes.clearTrace();
        bytes.seedInt32(guard, 0);

        final long second = adapter.callB15000();
        final List<Idler79eRegressionHost.Access> secondTrace = bytes.trace();
        assertEquals(object, second);
        assertEquals(List.of(gsSlot1, gsSlot2), gsReads);
        assertEquals(List.of("guard", "commit"), staticCalls);
        assertTrue(otherCalls.isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, gsSlot2, 8, tls2),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, tls2 + 0x10L, 4, -7),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, guard, 4, -1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, object, 1, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, object + 12L, 1, 255)
        ), secondTrace);
        assertEquals(0x24681357, bytes.peekInt32(guard));
        for (int i = 0; i < 16; i++) {
            final int expected = i == 0 ? 0 : i == 12 ? 255 : 0x60 + i;
            assertEquals(expected, bytes.peekUnsignedByte(object + i));
        }
        assertTrue(memory.effects().isEmpty());

        final SparseIntCells177Growth.KnownVirtual8 virtual8 = new SparseIntCells177Growth.KnownVirtual8(
                0x12345678L, gsSlot1, 0x8765432100000001L, 0xF1234567, tls2);
        assertEquals(virtual8Return, adapter.callVirtual8(virtual8));
        assertEquals(1, virtual8Calls.size());
        assertSame(virtual8, virtual8Calls.get(0));
        final SparseIntCells177Growth.KnownVirtual16 virtual16 = new SparseIntCells177Growth.KnownVirtual16(
                0x23456789L, gsSlot2, object, 0x81234567);
        adapter.callVirtual16(virtual16);
        assertEquals(1, virtual16Calls.size());
        assertSame(virtual16, virtual16Calls.get(0));
        final SparseIntCells177Growth.Known17836d0 reinsert = new SparseIntCells177Growth.Known17836d0(
                object, SparseIntCells177Growth.FrameAddress.LOCAL_OUTPUT_SP_PLUS30, 0x92345678, tls1);
        assertSame(sentinel, assertThrows(IllegalStateException.class, () -> adapter.call17836d0(reinsert)));
        assertEquals(1, reinsertCalls.size());
        assertSame(reinsert, reinsertCalls.get(0));
        adapter.call86f210(SparseIntCells177Growth.FrameAddress.LOCAL_OBJECT_SP_PLUS50, 0x8765432101234567L);
        assertEquals(List.of(SparseIntCells177Growth.FrameAddress.LOCAL_OBJECT_SP_PLUS50), frameCalls);
        assertEquals(List.of(0x8765432101234567L), frameRdxCalls);
        adapter.call4232cf4();
        assertEquals(List.of("virtual8", "virtual16", "reinsert", "frame", "terminal"), otherCalls);
    }
}

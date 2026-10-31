package org.xar.ck3.control.g2.common.nativecore.task.captured;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotSame;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

public final class Sparse177KnownCallsTest {
    @Test
    public void concreteExistingKeyRoutesAndLocalPairIdentitiesUseSuppliedDependencies() {
        final Sparse177TestMemory memory = new Sparse177TestMemory();
        final Idler79eRegressionHost.Memory bytes = memory.bytes();
        final long table = bytes.allocate(32);
        final long cells = bytes.allocate(48);
        final long separateOutput = bytes.allocate(16);
        final long pairOutput = bytes.allocate(16);
        final long keyAddress = bytes.allocate(4);
        final long pairAddress = bytes.allocate(8);
        final long carryTable = bytes.allocate(32);
        final long unmappedValueAddress = 0x7FFF12345678L;
        final long separateCell = cells + 12L;
        final long pairCell = cells + 24L;
        final int separateKey = 0x91ABCDEF;
        final int pairKey = 0x13579BDF;
        final int separateOldValue = 0x87654321;
        final int pairOldValue = 0x22334455;
        for (int i = 0; i < 48; i++) bytes.seedByte(cells + i, 0x50 + i);
        for (int i = 0; i < 16; i++) {
            bytes.seedByte(separateOutput + i, 0x90 + i);
            bytes.seedByte(pairOutput + i, 0xB0 + i);
        }
        bytes.seedInt64(table + 8L, cells);
        bytes.seedInt32(table + 0x10L, 9);
        bytes.seedInt32(table + 0x14L, 3);
        bytes.seedByte(table + 0x18L, 0);
        bytes.seedInt32(table + 0x1CL, 0x7FC01234);
        bytes.seedByte(separateCell, 3);
        bytes.seedInt32(separateCell + 4L, separateKey);
        bytes.seedInt32(separateCell + 8L, separateOldValue);
        bytes.seedByte(pairCell, 2);
        bytes.seedInt32(pairCell + 4L, pairKey);
        bytes.seedInt32(pairCell + 8L, pairOldValue);
        bytes.seedInt32(keyAddress, separateKey);
        bytes.seedInt32(pairAddress, pairKey);
        bytes.seedInt32(pairAddress + 4L, 0x9900BBCC);
        final SparseIntCells177Growth.Ports growthPorts = new SparseIntCells177Growth.Ports() {
            @Override public long callVirtual8(SparseIntCells177Growth.KnownVirtual8 known) {
                throw new AssertionError("Unexpected growth allocation");
            }
            @Override public void callVirtual16(SparseIntCells177Growth.KnownVirtual16 known) {
                throw new AssertionError("Unexpected growth release");
            }
            @Override public long callB15000() {
                throw new AssertionError("Unexpected growth sentinel");
            }
            @Override public void call17836d0(SparseIntCells177Growth.Known17836d0 known) {
                throw new AssertionError("Unexpected growth pair callback");
            }
            @Override public void call86f210(SparseIntCells177Growth.FrameAddress rcx, long rdx) {
                throw new AssertionError("Unexpected growth error object");
            }
            @Override public void call4232cf4() {
                throw new AssertionError("Unexpected growth error callback");
            }
        };
        final SparseIntCells177.Raw128 raw = new SparseIntCells177.Raw128(
                0xFEDCBA9876543210L, 0x0123456789ABCDEFL);
        final List<SparseIntCells177.Known17836d0> localCalls = new ArrayList<>();
        final Sparse177KnownCalls.LocalPairCalls localPairCalls = known -> {
            localCalls.add(known);
            return raw;
        };
        final Sparse177KnownCalls binder = new Sparse177KnownCalls(memory, growthPorts, localPairCalls);

        binder.call1783480(new SparseIntCells177.Known1783480(table, separateOutput,
                0x81234561, keyAddress, unmappedValueAddress));
        final List<Idler79eRegressionHost.Access> separateTrace = bytes.trace();
        assertEquals(separateCell, bytes.peekInt64(separateOutput));
        assertEquals(0, bytes.peekUnsignedByte(separateOutput + 8L));
        assertEquals(separateOldValue, bytes.peekInt32(separateCell + 8L));
        assertEquals(9, bytes.peekInt32(table + 0x10L));
        for (int i = 9; i < 16; i++) assertEquals(0x90 + i, bytes.peekUnsignedByte(separateOutput + i));
        assertTrue(localCalls.isEmpty());
        assertTrue(memory.effects().isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, table + 0x14L, 4, 3),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, table + 8L, 8, cells),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, separateCell, 1, 3),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, keyAddress, 4, separateKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, separateCell + 4L, 4, separateKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE64, separateOutput, 8, separateCell),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, separateOutput + 8L, 1, 0)
        ), separateTrace);
        bytes.clearTrace();

        binder.retry17836d0(table, pairOutput, 0x76543212, pairAddress);
        final List<Idler79eRegressionHost.Access> pairTrace = bytes.trace();
        assertEquals(pairCell, bytes.peekInt64(pairOutput));
        assertEquals(0, bytes.peekUnsignedByte(pairOutput + 8L));
        assertEquals(pairOldValue, bytes.peekInt32(pairCell + 8L));
        assertEquals(0x9900BBCC, bytes.peekInt32(pairAddress + 4L));
        assertEquals(9, bytes.peekInt32(table + 0x10L));
        for (int i = 9; i < 16; i++) assertEquals(0xB0 + i, bytes.peekUnsignedByte(pairOutput + i));
        assertTrue(localCalls.isEmpty());
        assertTrue(memory.effects().isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, table + 0x14L, 4, 3),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, table + 8L, 8, cells),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, pairCell, 1, 2),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, pairAddress, 4, pairKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, pairCell + 4L, 4, pairKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE64, pairOutput, 8, pairCell),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, pairOutput + 8L, 1, 0)
        ), pairTrace);

        final SparseIntCells177.Known17836d0 original = new SparseIntCells177.Known17836d0(
                table, SparseIntCells177.FrameAddress.LOCAL_OUTPUT_RBP_MINUS10, 0x82345678,
                SparseIntCells177.FrameAddress.LOCAL_PAIR_RBP_MINUS1C, 0x3579BDF1, 0x468ACE02);
        assertSame(raw, binder.call17836d0(original));
        assertEquals(1, localCalls.size());
        assertSame(original, localCalls.get(0));
        assertSame(raw, binder.carry17836d0(carryTable, 0xF1234567, 0x8ABCDE01, 0x7FEDCB02));
        assertEquals(2, localCalls.size());
        final SparseIntCells177.Known17836d0 carried = localCalls.get(1);
        assertNotSame(original, carried);
        assertEquals(carryTable, carried.rcx());
        assertEquals(0xF1234567, carried.r8d());
        assertEquals(0x8ABCDE01, carried.localPairKey());
        assertEquals(0x7FEDCB02, carried.localPairValue());
        assertSame(SparseIntCells177.FrameAddress.LOCAL_OUTPUT_RBP_MINUS10, carried.rdx());
        assertSame(SparseIntCells177.FrameAddress.LOCAL_PAIR_RBP_MINUS1C, carried.r9());
    }
}

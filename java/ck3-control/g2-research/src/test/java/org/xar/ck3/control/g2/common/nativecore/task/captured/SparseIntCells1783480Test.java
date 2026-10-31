package org.xar.ck3.control.g2.common.nativecore.task.captured;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

public final class SparseIntCells1783480Test {
    @Test
    public void existingKeyPreservesValueAndWritesOnlyNineOutputBytes() {
        final Sparse177TestMemory memory = new Sparse177TestMemory();
        final Idler79eRegressionHost.Memory bytes = memory.bytes();
        final long table = 0x1000L;
        final long output = 0x2000L;
        final long keyAddress = 0x3000L;
        final long cells = 0x5000L;
        final long unmappedValueAddress = 0x7FFF12345678L;
        final int key = 0x91ABCDEF;
        final int oldValue = 0x87654321;
        bytes.map(table, 32);
        bytes.map(output, 16);
        bytes.map(keyAddress, 4);
        bytes.map(cells, 12);
        for (int i = 0; i < 32; i++) bytes.seedByte(table + i, 0x51 + i);
        for (int i = 0; i < 12; i++) bytes.seedByte(cells + i, 0x72 + i);
        for (int i = 0; i < 16; i++) bytes.seedByte(output + i, 0xA0 + i);
        bytes.seedInt64(table + 8L, cells);
        bytes.seedInt32(table + 0x10L, 0x7FFFFFFF);
        bytes.seedInt32(table + 0x14L, 0);
        bytes.seedByte(table + 0x18L, 0);
        bytes.seedInt32(table + 0x1CL, 0x7FC01234);
        bytes.seedByte(cells, 3);
        bytes.seedInt32(cells + 4L, key);
        bytes.seedInt32(cells + 8L, oldValue);
        bytes.seedInt32(keyAddress, key);
        final int[] priorTable = new int[32];
        final int[] priorCell = new int[12];
        for (int i = 0; i < priorTable.length; i++) priorTable[i] = bytes.peekUnsignedByte(table + i);
        for (int i = 0; i < priorCell.length; i++) priorCell[i] = bytes.peekUnsignedByte(cells + i);
        final SparseIntCells1783480.Ports ports = new SparseIntCells1783480.Ports() {
            @Override public void call177fbd0(long t) {
                throw new AssertionError("Unexpected growth callback");
            }
            @Override public void retry1783480(long t, long o, int h, long k, long v) {
                throw new AssertionError("Unexpected retry callback");
            }
            @Override public SparseIntCells177.Raw128 carry17836d0(long t, int h, int k, int v) {
                throw new AssertionError("Unexpected carry callback");
            }
        };

        final long returned = SparseIntCells1783480.put(table, output, 0x8ACE1357,
                keyAddress, unmappedValueAddress, memory, ports);
        final List<Idler79eRegressionHost.Access> trace = bytes.trace();

        assertEquals(output, returned);
        assertEquals(cells, bytes.peekInt64(output));
        assertEquals(0, bytes.peekUnsignedByte(output + 8L));
        for (int i = 9; i < 16; i++) assertEquals(0xA0 + i, bytes.peekUnsignedByte(output + i));
        for (int i = 0; i < priorTable.length; i++) assertEquals(priorTable[i], bytes.peekUnsignedByte(table + i));
        for (int i = 0; i < priorCell.length; i++) assertEquals(priorCell[i], bytes.peekUnsignedByte(cells + i));
        assertTrue(memory.effects().isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, table + 0x14L, 4, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, table + 8L, 8, cells),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, cells, 1, 3),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, keyAddress, 4, key),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, cells + 4L, 4, key),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE64, output, 8, cells),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, output + 8L, 1, 0)
        ), trace);
    }

    @Test
    public void earlyGrowthForwardsOriginalArgumentsAndPreservesOpaqueRetryEffects() {
        final Sparse177TestMemory memory = new Sparse177TestMemory();
        final Idler79eRegressionHost.Memory bytes = memory.bytes();
        final long table = 0x11000L;
        final long output = 0x12000L;
        final long keyAddress = 0x13000L;
        final long valueAddress = 0x14000L;
        final long cells = 0x15000L;
        final int rawHash = 0x8ACE1357;
        final long grownPointer = 0x7FFF22223333L;
        final long growOutput = 0x1122334455667788L;
        final long retryOutput = 0x8877665544332211L;
        final int changedKey = 0xABCDEF01;
        final int changedValue = 0x76543210;
        bytes.map(table, 32);
        bytes.map(output, 16);
        bytes.map(keyAddress, 4);
        bytes.map(valueAddress, 4);
        bytes.map(cells, 12);
        for (int i = 0; i < 32; i++) bytes.seedByte(table + i, 0x31 + i);
        for (int i = 0; i < 12; i++) bytes.seedByte(cells + i, 0x62 + i);
        for (int i = 0; i < 16; i++) bytes.seedByte(output + i, 0x90 + i);
        bytes.seedInt64(table + 8L, cells);
        bytes.seedInt32(table + 0x10L, 0x10203040);
        bytes.seedInt32(table + 0x14L, 0);
        bytes.seedByte(table + 0x18L, 0);
        bytes.seedInt32(table + 0x1CL, 0x7FC01234);
        bytes.seedByte(cells, 0);
        bytes.seedInt32(keyAddress, 0x12345678);
        bytes.seedInt32(valueAddress, 0x23456789);
        final int[] priorCell = new int[12];
        for (int i = 0; i < priorCell.length; i++) priorCell[i] = bytes.peekUnsignedByte(cells + i);
        final List<String> callbacks = new ArrayList<>();
        final SparseIntCells1783480.Ports ports = new SparseIntCells1783480.Ports() {
            @Override public void call177fbd0(long t) {
                assertEquals(table, t);
                callbacks.add("grow");
                bytes.seedInt32(t + 0x14L, 7);
                bytes.seedInt64(t + 8L, grownPointer);
                bytes.seedInt32(keyAddress, changedKey);
                bytes.seedInt32(valueAddress, changedValue);
                bytes.seedInt64(output, growOutput);
                bytes.seedByte(output + 8L, 0x66);
            }
            @Override public void retry1783480(long t, long o, int h, long k, long v) {
                assertEquals(List.of("grow"), callbacks);
                assertEquals(table, t);
                assertEquals(output, o);
                assertEquals(rawHash, h);
                assertEquals(keyAddress, k);
                assertEquals(valueAddress, v);
                assertEquals(7, bytes.peekInt32(t + 0x14L));
                assertEquals(grownPointer, bytes.peekInt64(t + 8L));
                assertEquals(changedKey, bytes.peekInt32(k));
                assertEquals(changedValue, bytes.peekInt32(v));
                assertEquals(growOutput, bytes.peekInt64(o));
                assertEquals(0x66, bytes.peekUnsignedByte(o + 8L));
                callbacks.add("retry");
                bytes.seedInt64(o, retryOutput);
                bytes.seedByte(o + 8L, 0xA5);
            }
            @Override public SparseIntCells177.Raw128 carry17836d0(long t, int h, int k, int v) {
                throw new AssertionError("Unexpected carry callback");
            }
        };

        final long returned = SparseIntCells1783480.put(table, output, rawHash,
                keyAddress, valueAddress, memory, ports);
        final List<Idler79eRegressionHost.Access> trace = bytes.trace();

        assertEquals(output, returned);
        assertEquals(List.of("grow", "retry"), callbacks);
        assertEquals(retryOutput, bytes.peekInt64(output));
        assertEquals(0xA5, bytes.peekUnsignedByte(output + 8L));
        for (int i = 9; i < 16; i++) assertEquals(0x90 + i, bytes.peekUnsignedByte(output + i));
        assertEquals(grownPointer, bytes.peekInt64(table + 8L));
        assertEquals(7, bytes.peekInt32(table + 0x14L));
        assertEquals(0x10203040, bytes.peekInt32(table + 0x10L));
        assertEquals(changedKey, bytes.peekInt32(keyAddress));
        assertEquals(changedValue, bytes.peekInt32(valueAddress));
        for (int i = 0; i < priorCell.length; i++) assertEquals(priorCell[i], bytes.peekUnsignedByte(cells + i));
        assertTrue(memory.effects().isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, table + 0x14L, 4, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, table + 8L, 8, cells),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, cells, 1, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, table + 0x18L, 1, 0)
        ), trace);
    }
}

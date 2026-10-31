package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class SparseIntCells177BasicTest {
    private static final long TABLE = 0x1000L;
    private static final long BUCKETS = 0x2000L;
    private static final long OUTPUT = 0x3000L;
    private static final long KEY_ADDR = 0x4000L;
    private static final long VAL_ADDR = 0x5000L;

    private static void setup(Sparse177TestMemory memory, long table, long buckets,
                              long output, long keyAddress, long valueAddress) {
        memory.bytes().map(table, 0x20);
        memory.bytes().map(buckets, 0x100);
        memory.bytes().map(output, 16);
        memory.bytes().map(keyAddress, 4);
        memory.bytes().map(valueAddress, 4);
    }

    private static void seedTable(Sparse177TestMemory memory, long table, long buckets,
                                  int count, int mask, int maxDistance, float threshold) {
        memory.bytes().seedInt64(table + 0x08, buckets);
        memory.bytes().seedInt32(table + 0x10, count);
        memory.bytes().seedInt32(table + 0x14, mask);
        memory.bytes().seedByte(table + 0x18, maxDistance);
        memory.bytes().seedInt32(table + 0x1C, Float.floatToRawIntBits(threshold));
    }

    private static void seedCell(Sparse177TestMemory memory, long cell, int marker, int key, int value) {
        memory.bytes().seedByte(cell, marker);
        memory.bytes().seedInt32(cell + 4, key);
        memory.bytes().seedInt32(cell + 8, value);
    }

    private static void seedKV(Sparse177TestMemory memory, long keyAddress, long valueAddress,
                               int key, int value) {
        memory.bytes().seedInt32(keyAddress, key);
        memory.bytes().seedInt32(valueAddress, value);
    }

    private static final class Spy implements SparseIntCells177.Ports {
        final List<String> order = new ArrayList<>();
        final List<Long> calls177fbd0 = new ArrayList<>();
        final List<SparseIntCells177.Known1783480> calls1783480 = new ArrayList<>();
        final List<SparseIntCells177.Known17836d0> calls17836d0 = new ArrayList<>();
        Consumer<Long> on177;
        Consumer<SparseIntCells177.Known1783480> on3480;
        @Override public void call177fbd0(long rcx) {
            order.add("177FBD0");
            calls177fbd0.add(rcx);
            if (on177 != null) on177.accept(rcx);
        }
        @Override public void call1783480(SparseIntCells177.Known1783480 known) {
            order.add("1783480");
            calls1783480.add(known);
            if (on3480 != null) on3480.accept(known);
        }
        @Override public SparseIntCells177.Raw128 call17836d0(SparseIntCells177.Known17836d0 known) {
            order.add("17836D0");
            calls17836d0.add(known);
            throw new AssertionError("Unexpected carry helper on a basic witness");
        }
    }

    @Test
    public void testEmptyInsertion() {
        Sparse177TestMemory memory = new Sparse177TestMemory();
        Spy ports = new Spy();
        setup(memory, TABLE, BUCKETS, OUTPUT, KEY_ADDR, VAL_ADDR);
        seedTable(memory, TABLE, BUCKETS, 0, 1, 1, 1.0f);
        memory.bytes().seedInt32(BUCKETS, 0x12340000);
        memory.bytes().seedInt32(BUCKETS + 4, 0x55667788);
        for (int i = 0; i < 16; i++) memory.bytes().seedByte(OUTPUT + i, 0xA5);

        long returned = SparseIntCells177.put(TABLE, OUTPUT, 0, BUCKETS, BUCKETS + 4, memory, ports);

        int changedKey = 0x12340001;
        assertEquals(OUTPUT, returned);
        assertEquals(BUCKETS, memory.bytes().peekInt64(OUTPUT));
        assertEquals(1, memory.bytes().peekUnsignedByte(OUTPUT + 8));
        assertEquals(1, memory.bytes().peekUnsignedByte(BUCKETS));
        assertEquals(changedKey, memory.bytes().peekInt32(BUCKETS + 4));
        assertEquals(changedKey, memory.bytes().peekInt32(BUCKETS + 8));
        assertEquals(1, memory.bytes().peekInt32(TABLE + 0x10));
        for (int i = 9; i < 16; i++) assertEquals(0xA5, memory.bytes().peekUnsignedByte(OUTPUT + i));
        assertEquals(List.of(new Sparse177TestMemory.Effect(
                Sparse177TestMemory.Primitive.INC32, TABLE + 0x10, 1, 0)), memory.effects());
        assertTrue(ports.order.isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, TABLE + 0x14, 4, 1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, TABLE + 8, 8, BUCKETS),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, BUCKETS, 1, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, TABLE + 0x18, 1, 1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, TABLE + 0x10, 4, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, TABLE + 0x1C, 4, 0x3F800000),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, BUCKETS, 1, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, BUCKETS, 1, 1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, BUCKETS, 4, changedKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE32, BUCKETS + 4, 4, changedKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, BUCKETS + 4, 4, changedKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE32, BUCKETS + 8, 4, changedKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE64, OUTPUT, 8, BUCKETS),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, OUTPUT + 8, 1, 1)
        ), memory.bytes().trace());
    }

    @Test
    public void testDuplicateUpdate() {
        Sparse177TestMemory memory = new Sparse177TestMemory();
        Spy ports = new Spy();
        setup(memory, TABLE, BUCKETS, OUTPUT, KEY_ADDR, VAL_ADDR);
        seedTable(memory, TABLE, BUCKETS, 7, -1, 0, Float.NaN);
        long firstCell = BUCKETS - 12;
        memory.bytes().map(firstCell, 12);
        int originalKey = 0x778899AA;
        int freshValue = 0x80000007;
        seedKV(memory, KEY_ADDR, VAL_ADDR, originalKey, 11);
        seedCell(memory, firstCell, 1, 12, 13);
        seedCell(memory, BUCKETS, 2, originalKey, 14);
        memory.bytes().onAccess((backing, access) -> {
            if (access.op() == Idler79eRegressionHost.Op.READ32 && access.address() == KEY_ADDR) {
                backing.seedInt32(KEY_ADDR, 0x55);
            } else if (access.op() == Idler79eRegressionHost.Op.READ32 && access.address() == BUCKETS + 4) {
                backing.seedInt32(VAL_ADDR, freshValue);
            }
        });

        long returned = SparseIntCells177.put(TABLE, OUTPUT, -1, KEY_ADDR, VAL_ADDR, memory, ports);

        assertEquals(OUTPUT, returned);
        assertEquals(BUCKETS, memory.bytes().peekInt64(OUTPUT));
        assertEquals(0, memory.bytes().peekUnsignedByte(OUTPUT + 8));
        assertEquals(freshValue, memory.bytes().peekInt32(BUCKETS + 8));
        assertEquals(originalKey, memory.bytes().peekInt32(BUCKETS + 4));
        assertEquals(7, memory.bytes().peekInt32(TABLE + 0x10));
        assertEquals(0x55, memory.bytes().peekInt32(KEY_ADDR));
        assertTrue(memory.effects().isEmpty());
        assertTrue(ports.order.isEmpty());
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, TABLE + 0x14, 4, -1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, TABLE + 8, 8, BUCKETS),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, firstCell, 1, 1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, KEY_ADDR, 4, originalKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, firstCell + 4, 4, 12),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, BUCKETS, 1, 2),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, BUCKETS + 4, 4, originalKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, VAL_ADDR, 4, freshValue),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE32, BUCKETS + 8, 4, freshValue),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE64, OUTPUT, 8, BUCKETS),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, OUTPUT + 8, 1, 0)
        ), memory.bytes().trace());
    }

    @Test
    public void testGrowRoute() {
        Sparse177TestMemory memory = new Sparse177TestMemory();
        Spy ports = new Spy();
        setup(memory, TABLE, BUCKETS, OUTPUT, KEY_ADDR, VAL_ADDR);
        seedTable(memory, TABLE, BUCKETS, 4, 7, 0, 0.5f);
        seedKV(memory, KEY_ADDR, VAL_ADDR, 0x3333, 0x4444);
        int rawHash = -5;
        long selectedCell = BUCKETS + 36;
        for (int i = 0; i < 16; i++) memory.bytes().seedByte(OUTPUT + i, 0xA5);
        ports.on177 = rcx -> {
            memory.bytes().seedInt32(TABLE + 0x14, -99);
            memory.bytes().seedInt32(KEY_ADDR, 0x5555);
        };
        ports.on3480 = known -> {
            memory.bytes().seedInt64(OUTPUT, 0x0123456789ABCDEFL);
            memory.bytes().seedByte(OUTPUT + 8, 0x7F);
        };

        long returned = SparseIntCells177.put(TABLE, OUTPUT, rawHash, KEY_ADDR, VAL_ADDR, memory, ports);

        assertEquals(OUTPUT, returned);
        assertEquals(List.of("177FBD0", "1783480"), ports.order);
        assertEquals(List.of(TABLE), ports.calls177fbd0);
        assertEquals(List.of(new SparseIntCells177.Known1783480(
                TABLE, OUTPUT, rawHash, KEY_ADDR, VAL_ADDR)), ports.calls1783480);
        assertTrue(ports.calls17836d0.isEmpty());
        assertTrue(memory.effects().isEmpty());
        assertEquals(4, memory.bytes().peekInt32(TABLE + 0x10));
        assertEquals(0, memory.bytes().peekUnsignedByte(selectedCell));
        assertEquals(0x0123456789ABCDEFL, memory.bytes().peekInt64(OUTPUT));
        assertEquals(0x7F, memory.bytes().peekUnsignedByte(OUTPUT + 8));
        for (int i = 9; i < 16; i++) assertEquals(0xA5, memory.bytes().peekUnsignedByte(OUTPUT + i));
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, TABLE + 0x14, 4, 7),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, TABLE + 8, 8, BUCKETS),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, selectedCell, 1, 0),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, TABLE + 0x18, 1, 0)
        ), memory.bytes().trace());
    }

    @Test
    public void testNaNUnordered() {
        Sparse177TestMemory m = new Sparse177TestMemory();
        Spy p = new Spy();
        setup(m, TABLE, BUCKETS, OUTPUT, KEY_ADDR, VAL_ADDR);
        // Mask 1 -> 2 buckets. Count 0. MaxDist 1. Threshold NaN.
        seedTable(m, TABLE, BUCKETS, 0, 1, 1, Float.NaN);
        // Bucket 0 empty
        seedCell(m, BUCKETS, 0, 0, 0);
        // Key/Value
        seedKV(m, KEY_ADDR, VAL_ADDR, 0x1111, 0x2222);
        // Hash 0 -> Index 0. NaN comparison unordered -> JA false -> Insert
        long res = SparseIntCells177.put(TABLE, OUTPUT, 0, KEY_ADDR, VAL_ADDR, m, p);
        assertEquals(OUTPUT, res);
        // Verify INC32
        List<Sparse177TestMemory.Effect> effects = m.effects();
        boolean incFound = false;
        for (Sparse177TestMemory.Effect e : effects) {
            if (e.primitive() == Sparse177TestMemory.Primitive.INC32 && e.address() == TABLE + 0x10) incFound = true;
        }
        assertTrue(incFound, "INC32 expected");
        // Verify cell write
        assertEquals(1, m.bytes().peekUnsignedByte(BUCKETS));
        assertEquals(0x1111, m.bytes().peekInt32(BUCKETS + 4));
        assertEquals(0x2222, m.bytes().peekInt32(BUCKETS + 8));
        // Verify output flag 1
        assertEquals(1, m.bytes().peekUnsignedByte(OUTPUT + 8));
        // Verify no helper calls
        assertTrue(p.calls177fbd0.isEmpty());
        assertTrue(p.calls1783480.isEmpty());
        assertTrue(p.calls17836d0.isEmpty());
    }
}

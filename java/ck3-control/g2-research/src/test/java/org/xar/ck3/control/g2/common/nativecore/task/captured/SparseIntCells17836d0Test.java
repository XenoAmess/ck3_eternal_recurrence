package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public final class SparseIntCells17836d0Test {
    @Test
    public void existingKeyLeavesValueUntouched() {
        Fixture fixture = new Fixture(4, 0, Integer.MIN_VALUE);
        int key = 0x12345678;
        int originalValue = 0x87654321;
        fixture.cell(0, 1, key, originalValue);
        fixture.memory.bytes().seedInt32(fixture.pair, key);

        long returned = fixture.put();

        assertEquals(fixture.output, returned);
        fixture.assertCell(0, 1, key, originalValue);
        fixture.assertOutput(fixture.at(0), 0);
        assertTrue(fixture.memory.effects().isEmpty());
        assertTrue(fixture.ports.order.isEmpty());
        assertEquals(Integer.MIN_VALUE, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.table + 0x14, 4, 3),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ64, fixture.table + 8, 8, fixture.cells),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, fixture.at(0), 1, 1),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.pair, 4, key),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.at(0) + 4, 4, key),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE64, fixture.output, 8, fixture.at(0)),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE8, fixture.output + 8, 1, 0)
        ), fixture.memory.bytes().trace());
    }

    @Test
    public void neighborWritesKeyBeforeFreshPairValue() {
        Fixture fixture = new Fixture(8, 5, 2);
        fixture.cell(0, 1, 11, 12);
        fixture.cell(1, 1, 21, 22);
        fixture.cell(2, 0, 31, 32);
        fixture.input(101, 102);
        int freshValue = 0xCABA1E55;
        fixture.memory.bytes().onAccess((backing, access) -> {
            if (access.op() == Idler79eRegressionHost.Op.WRITE32
                    && access.address() == fixture.at(1) + 4 && access.value() == 101) {
                backing.seedInt32(fixture.pair + 4, freshValue);
            }
        });

        long returned = fixture.put();

        assertEquals(fixture.output, returned);
        fixture.assertCell(0, 1, 11, 12);
        fixture.assertCell(1, 2, 101, freshValue);
        fixture.assertCell(2, 2, 21, 22);
        fixture.assertOutput(fixture.at(1), 1);
        assertEquals(3, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
        assertEquals(List.of(new Sparse177TestMemory.Effect(
                Sparse177TestMemory.Primitive.INC32, fixture.table + 0x10, 3, 0)), fixture.memory.effects());
        assertTrue(fixture.ports.order.isEmpty());
        List<Idler79eRegressionHost.Access> sequence = fixture.memory.bytes().trace().stream()
                .filter(access -> (access.op() == Idler79eRegressionHost.Op.WRITE32
                        && (access.address() == fixture.at(1) + 4 || access.address() == fixture.at(1) + 8))
                        || (access.op() == Idler79eRegressionHost.Op.READ32 && access.address() == fixture.pair + 4))
                .toList();
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE32, fixture.at(1) + 4, 4, 101),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.pair + 4, 4, freshValue),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.WRITE32, fixture.at(1) + 8, 4, freshValue)
        ), sequence);
    }

    @Test
    public void carryWritesKeyBeforeFreshValueAndOpaqueContinuation() {
        Fixture fixture = new Fixture(8, 2, 3);
        fixture.cell(0, 1, 11, 12);
        fixture.cell(1, 1, 21, 22);
        fixture.cell(2, 2, 31, 32);
        fixture.input(101, 102);
        int freshValue = 0xA1B2C3D4;
        fixture.memory.bytes().onAccess((backing, access) -> {
            if (access.op() == Idler79eRegressionHost.Op.WRITE32
                    && access.address() == fixture.at(1) + 4 && access.value() == 101) {
                backing.seedInt32(fixture.pair + 4, freshValue);
            }
        });
        SparseIntCells177.Raw128 bits = new SparseIntCells177.Raw128(0x0123456789ABCDEFL, 0xFEDCBA9876543210L);
        fixture.ports.response = bits;
        fixture.ports.onGrow = table -> {
            assertEquals(fixture.table, table.longValue());
            fixture.assertCell(1, 3, 21, 22);
            fixture.assertCell(2, 2, 31, 32);
            assertEquals(0xA5A5A5A5A5A5A5A5L, fixture.memory.bytes().peekInt64(fixture.output));
            fixture.memory.bytes().seedInt32(fixture.pair, 999);
            fixture.memory.bytes().seedInt32(fixture.pair + 4, 888);
        };

        long returned = fixture.put();

        assertEquals(fixture.output, returned);
        assertEquals(List.of("177FBD0", "carry17836D0"), fixture.ports.order);
        assertEquals(List.of(fixture.table), fixture.ports.growCalls);
        assertTrue(fixture.ports.retryCalls.isEmpty());
        assertEquals(List.of(new Carry(fixture.table, Idler28eed20.prepare(0L, 0, 101).r8d(), 101, freshValue)),
                fixture.ports.carryCalls);
        fixture.assertCell(1, 3, 21, 22);
        fixture.assertCell(2, 2, 31, 32);
        assertEquals(3, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
        assertEquals(999, fixture.memory.bytes().peekInt32(fixture.pair));
        assertEquals(888, fixture.memory.bytes().peekInt32(fixture.pair + 4));
        assertEquals(List.of(new Sparse177TestMemory.Effect(
                Sparse177TestMemory.Primitive.WRITE128, fixture.output, bits.low(), bits.high())),
                fixture.memory.effects());
        for (int i = 0; i < 16; i++) {
            long half = i < 8 ? bits.low() : bits.high();
            assertEquals((int) ((half >>> ((i & 7) * 8)) & 255),
                    fixture.memory.bytes().peekUnsignedByte(fixture.output + i));
        }
        List<Idler79eRegressionHost.Access> reads = fixture.memory.bytes().trace().stream()
                .filter(access -> access.op() == Idler79eRegressionHost.Op.READ32
                        && access.address() == fixture.pair + 4).toList();
        assertEquals(List.of(new Idler79eRegressionHost.Access(
                Idler79eRegressionHost.Op.READ32, fixture.pair + 4, 4, freshValue)), reads);
        List<Idler79eRegressionHost.Access> trace = fixture.memory.bytes().trace();
        int keyWrite = trace.indexOf(new Idler79eRegressionHost.Access(
                Idler79eRegressionHost.Op.WRITE32, fixture.at(1) + 4, 4, 101));
        int valueRead = trace.indexOf(reads.getFirst());
        int valueWrite = trace.indexOf(new Idler79eRegressionHost.Access(
                Idler79eRegressionHost.Op.WRITE32, fixture.at(1) + 8, 4, freshValue));
        assertTrue(keyWrite >= 0 && keyWrite < valueRead && valueRead < valueWrite);
        assertTrue(trace.stream().noneMatch(access ->
                access.address() >= fixture.output && access.address() < fixture.output + 16));
    }

    private record Retry(long table, long output, int rawHash, long pair) { }
    private record Carry(long table, int rawHash, int key, int value) { }

    private static final class Fixture {
        final Sparse177TestMemory memory = new Sparse177TestMemory();
        final Spy ports = new Spy();
        final long table = memory.bytes().allocate(32);
        final long cells = memory.bytes().allocate(72);
        final long output = memory.bytes().allocate(16);
        final long pair;

        Fixture(int pairBytes, int limit, int count) {
            pair = memory.bytes().allocate(pairBytes);
            memory.bytes().seedInt64(table + 8, cells);
            memory.bytes().seedInt32(table + 0x10, count);
            memory.bytes().seedInt32(table + 0x14, 3);
            memory.bytes().seedByte(table + 0x18, limit);
            memory.bytes().seedInt32(table + 0x1C, Float.floatToRawIntBits(100.0f));
            for (int i = 0; i < 16; i++) memory.bytes().seedByte(output + i, 0xA5);
        }
        long at(int index) { return cells + index * 12L; }
        void cell(int index, int marker, int key, int value) {
            memory.bytes().seedByte(at(index), marker);
            memory.bytes().seedInt32(at(index) + 4, key);
            memory.bytes().seedInt32(at(index) + 8, value);
        }
        void input(int key, int value) {
            memory.bytes().seedInt32(pair, key);
            memory.bytes().seedInt32(pair + 4, value);
        }
        long put() { return SparseIntCells17836d0.put(table, output, 0, pair, memory, ports); }
        void assertCell(int index, int marker, int key, int value) {
            assertEquals(marker, memory.bytes().peekUnsignedByte(at(index)));
            assertEquals(key, memory.bytes().peekInt32(at(index) + 4));
            assertEquals(value, memory.bytes().peekInt32(at(index) + 8));
        }
        void assertOutput(long cell, int inserted) {
            assertEquals(cell, memory.bytes().peekInt64(output));
            assertEquals(inserted, memory.bytes().peekUnsignedByte(output + 8));
            for (int i = 9; i < 16; i++) assertEquals(0xA5, memory.bytes().peekUnsignedByte(output + i));
        }
    }

    private static final class Spy implements SparseIntCells17836d0.Ports {
        final List<String> order = new ArrayList<>();
        final List<Long> growCalls = new ArrayList<>();
        final List<Retry> retryCalls = new ArrayList<>();
        final List<Carry> carryCalls = new ArrayList<>();
        Consumer<Long> onGrow;
        SparseIntCells177.Raw128 response;
        @Override public void call177fbd0(long table) {
            order.add("177FBD0");
            growCalls.add(table);
            if (onGrow == null) throw new AssertionError("Unexpected grow callback");
            onGrow.accept(table);
        }
        @Override public void retry17836d0(long table, long output, int rawHash, long pairAddress) {
            order.add("retry17836D0");
            retryCalls.add(new Retry(table, output, rawHash, pairAddress));
            throw new AssertionError("Direct early retry is outside these three source witnesses");
        }
        @Override public SparseIntCells177.Raw128 carry17836d0(long table, int rawHash, int key, int value) {
            order.add("carry17836D0");
            carryCalls.add(new Carry(table, rawHash, key, value));
            if (response == null) throw new AssertionError("Unexpected carry callback");
            return response;
        }
    }
}

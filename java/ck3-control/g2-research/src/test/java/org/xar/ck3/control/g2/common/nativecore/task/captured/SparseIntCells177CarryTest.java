package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public final class SparseIntCells177CarryTest {
    @Test
    public void occupiedInsertionMovesOldPairToEmptyNeighbor() {
        Fixture fixture = new Fixture(5, 2);
        fixture.cell(0, 1, 11, 12);
        fixture.cell(1, 1, 21, 22);
        fixture.cell(2, 0, 31, 32);
        fixture.inputs(101, 102);
        for (int i = 1; i < 4; i++) fixture.memory.bytes().seedByte(fixture.at(2) + i, 0xA5);
        int freshValue = 0xDEADCAFE;
        fixture.memory.bytes().onAccess((backing, access) -> {
            if (access.op() == Idler79eRegressionHost.Op.READ32 && access.address() == fixture.key) {
                backing.seedInt32(fixture.key, 11);
            } else if (access.op() == Idler79eRegressionHost.Op.WRITE8 && access.address() == fixture.at(1)) {
                backing.seedInt32(fixture.value, freshValue);
            }
        });
        List<Sparse177TestMemory.Effect> observed = new ArrayList<>();
        fixture.memory.afterPrimitive(effect -> {
            assertEquals(3, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
            assertEquals(effect, fixture.memory.effects().getLast());
            observed.add(effect);
        });

        long returned = fixture.put();

        assertEquals(fixture.output, returned);
        fixture.assertCell(0, 1, 11, 12);
        fixture.assertCell(1, 2, 11, freshValue);
        fixture.assertCell(2, 2, 21, 22);
        fixture.assertOutput(fixture.at(1), 1);
        for (int i = 1; i < 4; i++) assertEquals(0xA5, fixture.memory.bytes().peekUnsignedByte(fixture.at(2) + i));
        assertEquals(3, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
        List<Sparse177TestMemory.Effect> expected = List.of(new Sparse177TestMemory.Effect(
                Sparse177TestMemory.Primitive.INC32, fixture.table + 0x10, 3, 0));
        assertEquals(expected, fixture.memory.effects());
        assertEquals(expected, observed);
        assertTrue(fixture.ports.order.isEmpty());
        List<Idler79eRegressionHost.Access> keyReads = fixture.memory.bytes().trace().stream()
                .filter(access -> access.op() == Idler79eRegressionHost.Op.READ32 && access.address() == fixture.key).toList();
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.key, 4, 101),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.key, 4, 11)), keyReads);
        assertEquals(freshValue, fixture.memory.bytes().trace().stream()
                .filter(access -> access.op() == Idler79eRegressionHost.Op.READ32 && access.address() == fixture.value)
                .findFirst().orElseThrow().value());
    }

    @Test
    public void carrySkipsUnsignedLargeMarkersAndKeepsOriginalOutputCell() {
        Fixture fixture = new Fixture(10, 4);
        fixture.cell(0, 1, 11, 12);
        fixture.cell(1, 1, 21, 22);
        fixture.cell(2, 2, 31, 32);
        fixture.cell(3, 0xFE, 41, 42);
        fixture.cell(4, 0, 51, 52);
        fixture.inputs(101, 102);

        long returned = fixture.put();

        assertEquals(fixture.output, returned);
        fixture.assertCell(0, 1, 11, 12);
        fixture.assertCell(1, 2, 101, 102);
        fixture.assertCell(2, 2, 31, 32);
        fixture.assertCell(3, 0xFE, 41, 42);
        fixture.assertCell(4, 4, 21, 22);
        fixture.assertOutput(fixture.at(1), 1);
        assertNotEquals(fixture.at(4), fixture.memory.bytes().peekInt64(fixture.output));
        assertEquals(5, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
        assertEquals(List.of(new Sparse177TestMemory.Effect(
                Sparse177TestMemory.Primitive.INC32, fixture.table + 0x10, 5, 0)), fixture.memory.effects());
        assertTrue(fixture.ports.order.isEmpty());
    }

    @Test
    public void carrySwapReadsNextPairAfterMarkerWrite() {
        Fixture fixture = new Fixture(10, 3);
        fixture.cell(0, 1, 11, 12);
        fixture.cell(1, 1, 21, 22);
        fixture.cell(2, 1, 31, 32);
        fixture.cell(3, 0, 41, 42);
        fixture.inputs(101, 102);
        int changedKey = 0xCCAA55AA;
        int changedValue = 0xDDEE33CC;
        fixture.memory.bytes().onAccess((backing, access) -> {
            if (access.op() == Idler79eRegressionHost.Op.WRITE8 && access.address() == fixture.at(2)) {
                backing.seedInt32(fixture.at(2) + 4, changedKey);
                backing.seedInt32(fixture.at(2) + 8, changedValue);
            }
        });

        long returned = fixture.put();

        assertEquals(fixture.output, returned);
        fixture.assertCell(0, 1, 11, 12);
        fixture.assertCell(1, 2, 101, 102);
        fixture.assertCell(2, 2, 21, 22);
        fixture.assertCell(3, 2, changedKey, changedValue);
        fixture.assertOutput(fixture.at(1), 1);
        assertEquals(4, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
        assertEquals(List.of(new Sparse177TestMemory.Effect(
                Sparse177TestMemory.Primitive.INC32, fixture.table + 0x10, 4, 0)), fixture.memory.effects());
        assertTrue(fixture.ports.order.isEmpty());
        List<Idler79eRegressionHost.Access> targetReads = fixture.memory.bytes().trace().stream()
                .filter(access -> access.op() == Idler79eRegressionHost.Op.READ32
                        && (access.address() == fixture.at(2) + 4 || access.address() == fixture.at(2) + 8)).toList();
        assertEquals(List.of(
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.at(2) + 4, 4, changedKey),
                new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ32, fixture.at(2) + 8, 4, changedValue)), targetReads);
    }

    @Test
    public void carryOverflowProjectsCapturedPairAndCopiesAllOpaqueBits() {
        Fixture fixture = new Fixture(2, 3);
        fixture.cell(0, 1, 11, 12);
        fixture.cell(1, 1, 21, 22);
        fixture.cell(2, 2, 31, 32);
        int incomingKey = 0x89ABCDEF;
        int incomingValue = 0xFEDCBA98;
        fixture.inputs(incomingKey, incomingValue);
        SparseIntCells177.Raw128 bits = new SparseIntCells177.Raw128(0x0123456789ABCDEFL, 0xFEDCBA9876543210L);
        fixture.ports.response = bits;
        fixture.ports.on177 = rcx -> {
            assertEquals(fixture.table, rcx.longValue());
            fixture.assertCell(1, 3, 21, 22);
            fixture.assertCell(2, 2, 31, 32);
            assertEquals(0xCCCCCCCCCCCCCCCCL, fixture.memory.bytes().peekInt64(fixture.output));
            fixture.memory.bytes().seedInt32(fixture.key, 77);
            fixture.memory.bytes().seedInt32(fixture.value, 88);
            fixture.cell(1, 9, 99, 100);
        };
        List<Sparse177TestMemory.Effect> observed = new ArrayList<>();
        fixture.memory.afterPrimitive(effect -> {
            assertEquals(Sparse177TestMemory.Primitive.WRITE128, effect.primitive());
            assertEquals(bits.low(), fixture.memory.bytes().peekInt64(fixture.output));
            assertEquals(bits.high(), fixture.memory.bytes().peekInt64(fixture.output + 8));
            assertEquals(effect, fixture.memory.effects().getLast());
            observed.add(effect);
        });

        long returned = fixture.put();

        assertEquals(fixture.output, returned);
        assertEquals(List.of("177FBD0", "17836D0"), fixture.ports.order);
        assertEquals(List.of(fixture.table), fixture.ports.calls177);
        assertTrue(fixture.ports.calls3480.isEmpty());
        SparseIntCells177.Known17836d0 expected = new SparseIntCells177.Known17836d0(
                fixture.table, SparseIntCells177.FrameAddress.LOCAL_OUTPUT_RBP_MINUS10,
                Idler28eed20.prepare(0L, 0, incomingKey).r8d(),
                SparseIntCells177.FrameAddress.LOCAL_PAIR_RBP_MINUS1C, incomingKey, incomingValue);
        assertEquals(List.of(expected), fixture.ports.calls36d0);
        Sparse177TestMemory.Effect expectedEffect = new Sparse177TestMemory.Effect(
                Sparse177TestMemory.Primitive.WRITE128, fixture.output, bits.low(), bits.high());
        assertEquals(List.of(expectedEffect), fixture.memory.effects());
        assertEquals(List.of(expectedEffect), observed);
        for (int i = 0; i < 16; i++) {
            long half = i < 8 ? bits.low() : bits.high();
            assertEquals((int) ((half >>> ((i & 7) * 8)) & 255), fixture.memory.bytes().peekUnsignedByte(fixture.output + i));
        }
        assertEquals(3, fixture.memory.bytes().peekInt32(fixture.table + 0x10));
        fixture.assertCell(1, 9, 99, 100);
        assertTrue(fixture.memory.bytes().trace().stream().noneMatch(access ->
                access.address() >= fixture.output && access.address() < fixture.output + 16));
    }

    private static final class Fixture {
        final Sparse177TestMemory memory = new Sparse177TestMemory();
        final Spy ports = new Spy();
        final long table = memory.bytes().allocate(32);
        final long output = memory.bytes().allocate(16);
        final long cells = memory.bytes().allocate(72);
        final long key = memory.bytes().allocate(4);
        final long value = memory.bytes().allocate(4);

        Fixture(int limit, int count) {
            memory.bytes().seedInt64(table + 8, cells);
            memory.bytes().seedInt32(table + 0x10, count);
            memory.bytes().seedInt32(table + 0x14, 3);
            memory.bytes().seedByte(table + 0x18, limit);
            memory.bytes().seedInt32(table + 0x1C, Float.floatToRawIntBits(100.0f));
            for (int i = 0; i < 16; i++) memory.bytes().seedByte(output + i, 0xCC);
        }
        long at(int index) { return cells + index * 12L; }
        void cell(int index, int marker, int rawKey, int rawValue) {
            memory.bytes().seedByte(at(index), marker);
            memory.bytes().seedInt32(at(index) + 4, rawKey);
            memory.bytes().seedInt32(at(index) + 8, rawValue);
        }
        void inputs(int rawKey, int rawValue) {
            memory.bytes().seedInt32(key, rawKey);
            memory.bytes().seedInt32(value, rawValue);
        }
        long put() { return SparseIntCells177.put(table, output, 0, key, value, memory, ports); }
        void assertCell(int index, int marker, int rawKey, int rawValue) {
            assertEquals(marker, memory.bytes().peekUnsignedByte(at(index)));
            assertEquals(rawKey, memory.bytes().peekInt32(at(index) + 4));
            assertEquals(rawValue, memory.bytes().peekInt32(at(index) + 8));
        }
        void assertOutput(long cell, int inserted) {
            assertEquals(cell, memory.bytes().peekInt64(output));
            assertEquals(inserted, memory.bytes().peekUnsignedByte(output + 8));
            for (int i = 9; i < 16; i++) assertEquals(0xCC, memory.bytes().peekUnsignedByte(output + i));
        }
    }

    private static final class Spy implements SparseIntCells177.Ports {
        final List<String> order = new ArrayList<>();
        final List<Long> calls177 = new ArrayList<>();
        final List<SparseIntCells177.Known1783480> calls3480 = new ArrayList<>();
        final List<SparseIntCells177.Known17836d0> calls36d0 = new ArrayList<>();
        Consumer<Long> on177;
        SparseIntCells177.Raw128 response;
        @Override public void call177fbd0(long rcx) {
            order.add("177FBD0");
            calls177.add(rcx);
            if (on177 == null) throw new AssertionError("Unexpected opaque helper");
            on177.accept(rcx);
        }
        @Override public void call1783480(SparseIntCells177.Known1783480 known) {
            order.add("1783480");
            calls3480.add(known);
            throw new AssertionError("Unexpected early-grow projection");
        }
        @Override public SparseIntCells177.Raw128 call17836d0(SparseIntCells177.Known17836d0 known) {
            order.add("17836D0");
            calls36d0.add(known);
            if (response == null) throw new AssertionError("Unexpected local-pair projection");
            return response;
        }
    }
}

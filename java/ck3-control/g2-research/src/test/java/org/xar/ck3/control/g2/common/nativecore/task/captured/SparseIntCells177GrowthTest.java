package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.List;
import java.util.ArrayList;
public final class SparseIntCells177GrowthTest {
@Test
public void testNormalGrowthFlow() {
    Sparse177TestMemory memory = new Sparse177TestMemory();
    Idler79eRegressionHost.Memory bytes = memory.bytes();
    long table = bytes.allocate(40);
    long oldCells = bytes.allocate(36);
    long newBuffer = bytes.allocate(168);
    long receiverA = bytes.allocate(8);
    long receiverB = bytes.allocate(8);
    long vtableA = bytes.allocate(24);
    long vtableB = bytes.allocate(24);
    long target8 = 0x1122334455667788L;
    long target16A = 0x1020304050607080L;
    long target16B = 0x8877665544332211L;
    int firstKey = 0x11223344;
    int secondKey = 0x89ABCDEF;
    bytes.seedInt32(table + 0x14, 2);
    bytes.seedInt32(table + 0x10, 2);
    bytes.seedByte(table + 0x18, 9);
    bytes.seedInt64(table + 8, oldCells);
    bytes.seedInt64(table + 0x20, receiverA);
    bytes.seedInt64(receiverA, vtableA);
    bytes.seedInt64(vtableA + 8, target8);
    bytes.seedInt64(vtableA + 16, target16A);
    bytes.seedInt64(receiverB, vtableB);
    bytes.seedInt64(vtableB + 16, 0x0102030405060708L);
    bytes.seedByte(oldCells, 1);
    bytes.seedInt32(oldCells + 4, firstKey);
    bytes.seedInt32(oldCells + 8, 101);
    bytes.seedByte(oldCells + 12, 0);
    bytes.seedInt32(oldCells + 16, 0x55667788);
    bytes.seedByte(oldCells + 24, 1);
    bytes.seedInt32(oldCells + 28, secondKey);
    bytes.seedInt32(oldCells + 32, 202);
    for (int offset = 0; offset < 168; offset++) bytes.seedByte(newBuffer + offset, 0xAA);
    List<String> order = new ArrayList<>();
    List<SparseIntCells177Growth.KnownVirtual8> allocations = new ArrayList<>();
    List<SparseIntCells177Growth.KnownVirtual16> releases = new ArrayList<>();
    List<SparseIntCells177Growth.Known17836d0> reinsertions = new ArrayList<>();
    int[] queries = {0};
    SparseIntCells177Growth.Ports ports = new SparseIntCells177Growth.Ports() {
        @Override
        public long callVirtual8(SparseIntCells177Growth.KnownVirtual8 known) {
            order.add("virtual8");
            allocations.add(known);
            assertEquals(new SparseIntCells177Growth.KnownVirtual8(target8, receiverA, 168L, 4, target8), known);
            assertEquals(7, bytes.peekInt32(table + 0x14));
            assertEquals(5, bytes.peekUnsignedByte(table + 0x18));
            assertEquals(0, bytes.peekInt32(table + 0x10));
            assertEquals(oldCells, bytes.peekInt64(table + 8));
            bytes.seedByte(table + 0x18, 1);
            return newBuffer;
        }
        @Override
        public void callVirtual16(SparseIntCells177Growth.KnownVirtual16 known) {
            order.add("virtual16");
            releases.add(known);
            assertEquals(new SparseIntCells177Growth.KnownVirtual16(target16B, receiverB, oldCells, 4), known);
        }
        @Override
        public long callB15000() {
            order.add("B15000");
            int occurrence = ++queries[0];
            if (occurrence == 1) {
                assertEquals(newBuffer, bytes.peekInt64(table + 8));
                assertEquals(0, bytes.peekUnsignedByte(newBuffer + 8 * 12L));
                assertEquals(0xFF, bytes.peekUnsignedByte(newBuffer + 9 * 12L));
                assertEquals(0xAA, bytes.peekUnsignedByte(newBuffer + 10 * 12L));
                assertTrue(reinsertions.isEmpty());
                return 0x33L;
            }
            assertEquals(2, occurrence);
            assertEquals(2, reinsertions.size());
            bytes.seedInt64(table + 0x20, receiverB);
            bytes.seedInt64(vtableB + 16, target16B);
            return 0x55L;
        }
        @Override
        public void call17836d0(SparseIntCells177Growth.Known17836d0 known) {
            order.add("17836D0");
            reinsertions.add(known);
            assertEquals(table, known.rcx());
            assertEquals(SparseIntCells177Growth.FrameAddress.LOCAL_OUTPUT_SP_PLUS30, known.rdx());
            assertEquals(0, bytes.peekInt32(table + 0x10));
        }
        @Override
        public void call86f210(SparseIntCells177Growth.FrameAddress rcx, long rdx) {
            throw new AssertionError("Unexpected abnormal constructor projection");
        }
        @Override
        public void call4232cf4() {
            throw new AssertionError("Unexpected abnormal callback");
        }
    };

    SparseIntCells177Growth.apply(table, memory, ports);

    assertEquals(List.of("virtual8", "B15000", "17836D0", "17836D0", "B15000", "virtual16"), order);
    assertEquals(2, queries[0]);
    assertEquals(1, allocations.size());
    assertEquals(1, releases.size());
    assertEquals(List.of(
            new SparseIntCells177Growth.Known17836d0(table,
                    SparseIntCells177Growth.FrameAddress.LOCAL_OUTPUT_SP_PLUS30,
                    Idler28eed20.prepare(0L, 0, firstKey).r8d(), oldCells + 4),
            new SparseIntCells177Growth.Known17836d0(table,
                    SparseIntCells177Growth.FrameAddress.LOCAL_OUTPUT_SP_PLUS30,
                    Idler28eed20.prepare(0L, 0, secondKey).r8d(), oldCells + 28)
    ), reinsertions);
    assertEquals(7, bytes.peekInt32(table + 0x14));
    assertEquals(1, bytes.peekUnsignedByte(table + 0x18));
    assertEquals(0, bytes.peekInt32(table + 0x10));
    assertEquals(newBuffer, bytes.peekInt64(table + 8));
    assertEquals(receiverB, bytes.peekInt64(table + 0x20));
    assertEquals(1, bytes.peekUnsignedByte(oldCells));
    assertEquals(0, bytes.peekUnsignedByte(oldCells + 12));
    assertEquals(1, bytes.peekUnsignedByte(oldCells + 24));
    for (int offset = 0; offset < 168; offset++) {
        int expected = offset == 108 ? 0xFF : offset < 108 && offset % 12 == 0 ? 0 : 0xAA;
        assertEquals(expected, bytes.peekUnsignedByte(newBuffer + offset), "new buffer offset " + offset);
    }
    List<Idler79eRegressionHost.Access> expectedMarkerWrites = new ArrayList<>();
    for (int index = 0; index < 9; index++) {
        expectedMarkerWrites.add(new Idler79eRegressionHost.Access(
                Idler79eRegressionHost.Op.WRITE8, newBuffer + index * 12L, 1, 0));
    }
    expectedMarkerWrites.add(new Idler79eRegressionHost.Access(
            Idler79eRegressionHost.Op.WRITE8, newBuffer + 108, 1, 0xFF));
    assertEquals(expectedMarkerWrites, bytes.trace().stream().filter(access ->
            access.op() == Idler79eRegressionHost.Op.WRITE8
                    && access.address() >= newBuffer && access.address() < newBuffer + 168).toList());
    assertEquals(List.of(
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 4, 1, 0x44),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 5, 1, 0x33),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 6, 1, 0x22),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 7, 1, 0x11),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 28, 1, 0xEF),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 29, 1, 0xCD),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 30, 1, 0xAB),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 31, 1, 0x89)
    ), bytes.trace().stream().filter(access -> access.op() == Idler79eRegressionHost.Op.READ8
            && ((access.address() >= oldCells + 4 && access.address() <= oldCells + 7)
                || (access.address() >= oldCells + 28 && access.address() <= oldCells + 31))).toList());
    assertEquals(List.of(
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells, 1, 1),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 12, 1, 0),
            new Idler79eRegressionHost.Access(Idler79eRegressionHost.Op.READ8, oldCells + 24, 1, 1)
    ), bytes.trace().stream().filter(access -> access.op() == Idler79eRegressionHost.Op.READ8
            && (access.address() == oldCells || access.address() == oldCells + 12
                || access.address() == oldCells + 24)).toList());
    assertTrue(memory.effects().isEmpty());
}

}

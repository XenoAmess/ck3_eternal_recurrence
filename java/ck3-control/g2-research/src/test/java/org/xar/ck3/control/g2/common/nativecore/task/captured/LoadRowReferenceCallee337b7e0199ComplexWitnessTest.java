package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.List;
import org.junit.jupiter.api.Test;
import org.xar.ck3.control.g2.common.nativecore.task.captured.LoadRowReferenceCallee337b7e0199WitnessTest.RowRef199Fixture;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.junit.jupiter.api.Assertions.*;

/** Bounded displacement, growth and actual thin-adapter cases from the same raw1019B source. */
public final class LoadRowReferenceCallee337b7e0199ComplexWitnessTest {
    private static final int NEW_HASH = 0x80000001;
    private static final long OLD_KEY = 0x2233445566778899L;
    private static final long NEW_KEY = 0x33445566778899AAL;
    private static final long THIRD_KEY = 0x445566778899AABBL;
    private static final long NEW_KEY_SLOT = 0x51000000L;
    private static final long NEW_DESCRIPTOR = 0x61000000L;
    private static final long NO_READ_RAX = 0xDEAD000000009999L;

    @Test
    void moveWalkRejectsBeforeLeaOrFindsFreeSlotOrSwapsThenCopiesWhole128() {
        for (int mode = 0; mode < 3; mode++) {
            RowRef199Fixture f = initializedMove(mode);
            long b = f.a + 0x50;
            long c = f.a + 0xA0;
            long d = f.a + 0xF0;
            f.budget.add(0x337BA40L, b, mode == 0);
            if (mode == 0) {
                assertThrows(UnsupportedOperationException.class, f::run);
                f.done();
                assertTrue(f.m.writesAt(f.out).isEmpty());
                assertEquals(NEW_HASH, f.m.rawD(b));
                assertEquals(2, f.m.rawB(b + 4));
            } else if (mode == 1) {
                f.calls.add(0x337BB4AL, TargetKind.DIRECT_RVA, 0x87C9B0L,
                        f.v(f.v2, OLD_KEY, c + 0x10, f.work + 0x40, f.v2.r8Bits(),
                                f.v2.r9Bits(), f.v2.r10Bits(), f.v2.r11Bits()),
                        f.local(c, 0, b + 0x10, b), f.v3, null);
                NormalReturn result = f.run();
                f.done();
                f.normal(result, f.v(f.v3, f.out, 0, f.v3.rdxBits(), f.v3.r8Bits(), f.v3.r9Bits(),
                        f.v3.r10Bits(), f.v3.r11Bits()), f.nv, f.ret);
                assertEquals(0x12345678, f.m.rawD(c));
                assertEquals(2, f.m.rawB(c + 4));
                assertEquals(OLD_KEY, f.m.rawQ(c + 8));
                assertEquals(b, f.m.rawQ(f.out));
                assertEquals(1, f.m.rawB(f.out + 8));
                assertEquals(1, f.m.rawD(f.table + 0x10));
                f.padding(f.out + 9, 7);
            } else {
                f.budget.add(0x337BA40L, c, false);
                NonvolatileBits atC = f.local(c, 0, b + 0x10, b);
                NonvolatileBits atD = f.local(d, 0, b + 0x10, b);
                f.calls.add(0x337BA8BL, TargetKind.DIRECT_RVA, 0xA636F0L,
                        f.v(f.v2, THIRD_KEY, f.work + 0x40, c + 0x10, f.v2.r8Bits(),
                                f.v2.r9Bits(), f.v2.r10Bits(), f.v2.r11Bits()), atC, f.v3, null);
                f.calls.add(0x337BAE2L, TargetKind.DIRECT_RVA, 0xA636F0L,
                        f.v(f.v3, NEW_KEY, f.work + 0x40, b + 0x10, f.v3.r8Bits(),
                                f.v3.r9Bits(), f.v3.r10Bits(), f.v3.r11Bits()), atD, f.v1, null);
                f.calls.add(0x337BAEAL, TargetKind.DIRECT_RVA, 0x337C040L,
                        f.v(f.v1, f.v1.raxBits(), f.table, f.v1.rdxBits(), f.v1.r8Bits(),
                                f.v1.r9Bits(), f.v1.r10Bits(), f.v1.r11Bits()), atD, f.v2, null);
                Bits128 whole = new Bits128(0xFEDCBA9876543210L, 0x8877665544332211L);
                f.calls.add(0x337BB00L, TargetKind.DIRECT_RVA, 0x337C5D0L,
                        f.v(f.v2, f.v2.raxBits(), f.table, f.bp - 1, Integer.toUnsignedLong(NEW_HASH),
                                f.work + 0x38, f.v2.r10Bits(), f.v2.r11Bits()), atD, f.v3, call -> {
                            assertEquals(NEW_KEY, f.m.rawQ(f.work + 0x38));
                            f.m.write128(f.bp - 1, whole);
                        });
                NormalReturn result = f.run();
                f.done();
                VolatileBits expected = new VolatileBits(f.out, 0, f.v3.rdxBits(), f.v3.r8Bits(),
                        f.v3.r9Bits(), f.v3.r10Bits(), f.v3.r11Bits(), whole, f.v3.xmm1(),
                        f.v3.xmm2(), f.v3.xmm3(), f.v3.xmm4(), f.v3.xmm5());
                f.normal(result, expected, f.nv, f.ret);
                assertEquals(whole.lowBits(), f.m.rawQ(f.out));
                assertEquals(whole.highBits(), f.m.rawQ(f.out + 8));
                assertEquals(List.of(new RowRef199Fixture.Op("w128", f.out, whole.lowBits())), f.m.writesAt(f.out));
                assertTrue(f.m.writesAt(f.out + 8).isEmpty());
                assertEquals(0x22334455, f.m.rawD(b));
                assertEquals(3, f.m.rawB(b + 4));
                assertEquals(THIRD_KEY, f.m.rawQ(b + 8));
                assertEquals(0x12345678, f.m.rawD(c));
                assertEquals(2, f.m.rawB(c + 4));
                assertEquals(OLD_KEY, f.m.rawQ(c + 8));
            }
            assertTrue(f.m.ops.stream().noneMatch(op -> op.kind().startsWith("r")
                    && op.address() == NO_READ_RAX), "NOP DWORD[RAX] owns no memory read");
        }
    }

    private static RowRef199Fixture initializedMove(int mode) {
        RowRef199Fixture f = new RowRef199Fixture();
        long b = f.a + 0x50;
        long c = f.a + 0xA0;
        long d = f.a + 0xF0;
        f.floating.enabled = true;
        f.m.putB(f.a + 4, 1);
        f.m.putQ(f.a + 8, f.key ^ 1);
        f.m.putD(b, 0x12345678);
        f.m.putB(b + 4, 1);
        f.m.putQ(b + 8, OLD_KEY);
        f.m.putD(c, 0x22334455);
        f.m.putB(c + 4, 1);
        f.m.putQ(c + 8, THIRD_KEY);
        f.m.putB(d + 4, 3);
        f.m.putQ(f.descriptor + 0x38, 0xDEAD1111L);
        f.m.putQ(NEW_DESCRIPTOR + 0x38, 0);
        f.m.putQ(NEW_KEY_SLOT, NEW_KEY);
        f.budget.add(0x337B831L, f.a, false);
        NonvolatileBits local = f.local(b, 0, b + 0x10, f.partialR14(2));
        f.calls.add(0x337B9CEL, TargetKind.DIRECT_RVA, 0x87C9B0L,
                f.v(f.fpBits(), OLD_KEY, f.work + 0x40, b + 0x10, f.in.r8Bits(), f.k,
                        f.in.r10Bits(), f.in.r11Bits()), local, f.v1, call -> {
                    f.m.writeDword(f.s + 0x18, NEW_HASH);
                    f.m.writeQword(f.s + 0x20, NEW_KEY_SLOT);
                    f.m.writeQword(f.s + 0x30, NEW_DESCRIPTOR);
                });
        VolatileBits moved = f.v(f.v2, NO_READ_RAX, f.v2.rcxBits(), f.v2.rdxBits(),
                f.v2.r8Bits(), f.v2.r9Bits(), f.v2.r10Bits(), f.v2.r11Bits());
        f.calls.add(0x337BA17L, TargetKind.DIRECT_RVA, 0xE23EA0L,
                f.v(f.v1, NEW_DESCRIPTOR, b + 8, f.bp - 0x49, Integer.toUnsignedLong(NEW_HASH),
                        f.v1.r9Bits(), f.v1.r10Bits(), f.v1.r11Bits()), local, moved, call -> {
                    assertEquals(NEW_KEY, f.m.rawQ(f.bp - 0x49));
                    // Controlled opaque move port's actual shared-memory effect.
                    f.m.writeQword(b + 8, NEW_KEY);
                    if (mode == 1) f.m.writeByte(c + 4, 0);
                    if (mode == 2) f.m.writeByte(f.table + 0x18, 2);
                });
        return f;
    }

    @Test
    void growthUsesSignedEaxAndFreshHomesOrExecutesBothFatalCallsThenTrap() {
        for (boolean fatal : new boolean[]{false, true}) {
            RowRef199Fixture f = new RowRef199Fixture();
            f.m.putB(f.a + 4, 0);
            f.m.putB(f.table + 0x18, 0); // distance1 is above0; no FP instructions are reached.
            NonvolatileBits local = f.local(f.a, f.k, f.nv.r13Bits(), f.partialR14(1));
            long rawResult = fatal ? 0x800000000000001FL : 0x12340000FFFFFFFFL;
            VolatileBits grow = f.v(f.v1, rawResult, f.v1.rcxBits(), f.v1.rdxBits(), f.v1.r8Bits(),
                    f.v1.r9Bits(), f.v1.r10Bits(), f.v1.r11Bits());
            f.calls.add(0x337BB7CL, TargetKind.DIRECT_RVA, 0x86E160L,
                    f.v(f.in, 0, 8, 1, f.in.r8Bits(), f.k, f.in.r10Bits(), f.in.r11Bits()),
                    local, grow, null);
            if (fatal) {
                f.calls.add(0x337BBD0L, TargetKind.DIRECT_RVA, 0x86F210L,
                        f.v(grow, grow.raxBits(), f.bp + 0x57, f.table, grow.r8Bits(), grow.r9Bits(),
                                grow.r10Bits(), grow.r11Bits()), local, f.v2, null);
                f.calls.add(0x337BBD5L, TargetKind.DIRECT_RVA, 0x4232CF4L,
                        f.v2, local, f.v3, null);
                assertThrows(UnsupportedOperationException.class, f::run);
                f.done();
                assertTrue(f.m.ops.stream().noneMatch(op -> op.kind().equals("rq") && op.address() == f.s));
            } else {
                f.calls.add(0x337BB8BL, TargetKind.DIRECT_RVA, 0x337C0C0L,
                        f.v(grow, grow.raxBits(), f.table, 0xFFFFFFFFL, grow.r8Bits(), grow.r9Bits(),
                                grow.r10Bits(), grow.r11Bits()), local, f.v2, call -> {
                            f.m.writeDword(f.s + 0x18, NEW_HASH);
                            f.m.writeQword(f.s + 0x20, 0xBADBADL);
                            f.m.writeQword(f.s + 0x30, NEW_DESCRIPTOR);
                        });
                f.calls.add(0x337BBA6L, TargetKind.DIRECT_RVA, 0x337C200L,
                        f.v(f.v2, NEW_DESCRIPTOR, f.table, f.out, Integer.toUnsignedLong(NEW_HASH), f.k,
                                f.v2.r10Bits(), f.v2.r11Bits()), local, f.v3,
                        call -> assertEquals(NEW_DESCRIPTOR, f.m.rawQ(f.work + 0x28)));
                NormalReturn result = f.run();
                f.done();
                f.normal(result, f.v(f.v3, f.out, f.v3.rcxBits(), f.v3.rdxBits(), f.v3.r8Bits(),
                        f.v3.r9Bits(), f.v3.r10Bits(), f.v3.r11Bits()), f.nv, f.ret);
            }
        }
    }

    @Test
    void actual195CallAdapterUsesCoreAndRejectsBadNvWhileUnmatchedObjectsKeepIdentity() {
        for (boolean malformedNv : new boolean[]{false, true}) {
            RowRef199Fixture f = new RowRef199Fixture();
            // Valid adapter case also distinguishes CDQE from unsigned index expansion.
            long bucket = malformedNv ? f.a : f.a - 0x2800000000L;
            VolatileBits input = malformedNv ? f.in : f.v(f.in, f.in.raxBits(), f.table, f.out,
                    0xABCD123480000000L, f.k, f.in.r10Bits(), f.in.r11Bits());
            if (!malformedNv) f.m.putD(f.table + 0x14, Integer.MIN_VALUE);
            f.m.putB(bucket + 4, 1);
            f.m.putQ(bucket + 8, f.key);
            f.m.putQ(f.s, f.image + 0x34EF8CAL);
            f.budget.add(0x337B831L, bucket, false);
            f.calls.add(0x337B8EDL, TargetKind.DIRECT_RVA, 0xA636F0L,
                    f.v(input, f.descriptor, f.bp - 0x49, bucket + 0x10, input.r8Bits(), f.k,
                            input.r10Bits(), input.r11Bits()),
                    f.local(bucket, 0, f.nv.r13Bits(), f.partialR14(1)), f.v1, call -> {
                        if (malformedNv) f.m.writeQword(f.s + 0x10, 0xBADBADL);
                    });
            Calls adapter = LoadRowReferenceCallee337b7e0199Calls.bind(f.image, f.m, f.calls, f.budget, f.floating);
            Call actual = new Call(0x34EF8C5L, TargetKind.DIRECT_RVA, 0x337B7E0L,
                    f.s + 8, input, f.nv);
            if (malformedNv) assertThrows(IllegalStateException.class, () -> adapter.invoke(actual));
            else assertEquals(f.v(f.v1, f.out, 0, f.v1.rdxBits(), f.v1.r8Bits(), f.v1.r9Bits(),
                    f.v1.r10Bits(), f.v1.r11Bits()), adapter.invoke(actual));
            f.done();
            assertEquals(bucket, f.m.rawQ(f.out));
            assertEquals(0, f.m.rawB(f.out + 8));
            assertTrue(f.m.writesAt(f.s).isEmpty(), "actual caller owns child return slot");
        }
        RowRef199Fixture f = new RowRef199Fixture();
        Passing pass = new Passing(f);
        Calls adapter = LoadRowReferenceCallee337b7e0199Calls.bind(f.image, f.m, pass, f.budget, f.floating);
        for (Call unmatched : List.of(
                new Call(0x34EF8C6L, TargetKind.DIRECT_RVA, 0x337B7E0L, f.s, f.in, f.nv),
                new Call(0x34EF8C5L, TargetKind.INDIRECT_ABSOLUTE, 0x337B7E0L, f.s, f.in, f.nv),
                new Call(0x34EF8C5L, TargetKind.DIRECT_RVA, 0x337B7E1L, f.s, f.in, f.nv))) {
            assertSame(f.v1, adapter.invoke(unmatched));
            assertSame(unmatched, pass.call);
        }
        Tail tail = new Tail(0x1234, TargetKind.DIRECT_RVA, 0x5678, f.entry);
        assertSame(pass.returnedTail, adapter.tail(tail));
        assertSame(tail, pass.tail);
        assertEquals(0x1234567890ABCDEFL, adapter.readGsQword58());
    }

    private static final class Passing implements Calls {
        final RowRef199Fixture f;
        final NormalReturn returnedTail;
        Call call;
        Tail tail;
        Passing(RowRef199Fixture fixture) { f = fixture; returnedTail = new NormalReturn(f.v1, f.ret, f.s + 8, f.nv); }
        @Override public VolatileBits invoke(Call value) { call = value; return f.v1; }
        @Override public NormalReturn tail(Tail value) { tail = value; return returnedTail; }
        @Override public long readGsQword58() { return 0x1234567890ABCDEFL; }
    }
}

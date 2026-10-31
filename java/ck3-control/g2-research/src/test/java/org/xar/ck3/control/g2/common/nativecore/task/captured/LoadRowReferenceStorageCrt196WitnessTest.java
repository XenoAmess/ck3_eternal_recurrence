package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.LoopBudget;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.junit.jupiter.api.Assertions.*;

/** New adapter bindings through mature185 cores; controlled opaque IAT and tail ports only. */
public final class LoadRowReferenceStorageCrt196WitnessTest {
    private static final long I = 0x100000000L;
    private static final long CALLER = 0x720000000100L;
    private static final long GUARD = 0x60000000L;
    private static final long GS = 0x61000000L;
    private static final long TLS = 0x62000000L;
    private static final long ENTER_TARGET = 0xDA00000000000011L;
    private static final long LEAVE_TARGET = 0xDB00000000000022L;
    private static final VolatileBits INPUT = sample(0x1000000000000000L);
    private static final VolatileBits ENTER_RESULT = sample(0x2000000000000000L);
    private static final VolatileBits LEAVE_RESULT = sample(0x3000000000000000L);
    private static final VolatileBits TAIL_RESULT = sample(0x4000000000000000L);
    private static final NonvolatileBits NV = new NonvolatileBits(0xA100000000000001L,
            0xA200000000000002L, 0xA300000000000003L, 0xA400000000000004L,
            0xA500000000000005L, 0xA600000000000006L, 0xA700000000000007L,
            0xA800000000000008L, new Bits128(0xA900000000000009L, 0xAA0000000000000AL));

    @Test
    void twoActualSitesEnterMatureCoresAndKeepCallerOwnedReturnSlot() {
        for (boolean a84 : new boolean[]{true, false}) {
            Fixture f = new Fixture(a84, 0);
            Calls bound = LoadRowReferenceStorageCrt196Calls.bind(I, f.m, f.ports, f.ports);
            assertEquals(TAIL_RESULT, bound.invoke(f.outer));
            f.done();
            assertTrue(f.m.writesAt(CALLER - 8).isEmpty(), "adapter must not push caller return a second time");
            assertEquals(I + f.site + 5, f.m.rawQ(CALLER - 8));
            assertEquals(a84 ? -1 : 8, f.m.rawD(GUARD));
            if (!a84) {
                assertEquals(8, f.m.rawD(I + 0x542F090L));
                assertEquals(8, f.m.rawD(TLS + 0x10));
            }
        }
        Pass pass = new Pass();
        Calls bound = LoadRowReferenceStorageCrt196Calls.bind(I, new Bytes(), pass,
                (site, address) -> { throw new AssertionError("unexpected loop budget"); });
        for (Call other : List.of(
                new Call(0x34F0504L, TargetKind.DIRECT_RVA, 0x4223A84L, CALLER, INPUT, NV),
                new Call(0x34F0526L, TargetKind.DIRECT_RVA, 0x4223A25L, CALLER, INPUT, NV))) {
            assertSame(TAIL_RESULT, bound.invoke(other));
            assertSame(other, pass.last);
        }
    }

    @Test
    void malformedTailNormalReturnsAreRejectedAfterActualCoreExecution() {
        // The external185 Tail port supplies malformed NR, not a fake execute implementation.
        Fixture wrongRip = new Fixture(true, 1);
        Calls first = LoadRowReferenceStorageCrt196Calls.bind(I, wrongRip.m, wrongRip.ports, wrongRip.ports);
        assertThrows(IllegalStateException.class, () -> first.invoke(wrongRip.outer));
        wrongRip.done();
        Fixture wrongNv = new Fixture(false, 2);
        Calls second = LoadRowReferenceStorageCrt196Calls.bind(I, wrongNv.m, wrongNv.ports, wrongNv.ports);
        assertThrows(IllegalStateException.class, () -> second.invoke(wrongNv.outer));
        wrongNv.done();
    }

    private static final class Fixture {
        final Bytes m = new Bytes();
        final boolean a84;
        final long site;
        final Call outer;
        final Ports ports;
        Fixture(boolean first, int corruption) {
            a84 = first;
            site = a84 ? 0x34F0503L : 0x34F0526L;
            VolatileBits input = bits(INPUT, INPUT.raxBits(), GUARD, INPUT.rdxBits(), INPUT.r8Bits(),
                    INPUT.r9Bits(), INPUT.r10Bits(), INPUT.r11Bits());
            outer = new Call(site, TargetKind.DIRECT_RVA, a84 ? 0x4223A84L : 0x4223A24L,
                    CALLER, input, NV);
            m.putQ(CALLER - 8, I + site + 5);
            m.putD(GUARD, 0);
            m.putQ(I + 0x43DA500L, ENTER_TARGET);
            m.putQ(I + 0x43DA4F0L, LEAVE_TARGET);
            m.putD(I + 0x542F090L, 7);
            m.putD(I + 0x5C5CBC4L, 2);
            m.putQ(GS + 2 * 8, TLS);
            ports = new Ports(this, corruption);
        }
        void done() {
            assertEquals(a84 ? 1 : 2, ports.calls);
            assertEquals(1, ports.tails);
            assertEquals(a84 ? 1 : 0, ports.budgets);
            assertEquals(a84 ? 0 : 1, ports.gsReads);
        }
    }

    private static final class Ports implements Calls, LoopBudget {
        final Fixture f;
        final int corruption;
        int calls;
        int tails;
        int budgets;
        int gsReads;
        Ports(Fixture fixture, int badField) { f = fixture; corruption = badField; }
        @Override public VolatileBits invoke(Call call) {
            int n = calls++;
            assertTrue(n < (f.a84 ? 1 : 2));
            long site = n == 0 ? (f.a84 ? 0x4223A94L : 0x4223A34L) : 0x4223A74L;
            assertEquals(site, call.callSiteRva());
            assertEquals(TargetKind.INDIRECT_ABSOLUTE, call.kind());
            assertEquals(n == 0 ? ENTER_TARGET : LEAVE_TARGET, call.targetBits());
            assertEquals(CALLER - 0x30, call.rspBits());
            assertEquals(I + site + 6, f.m.rawQ(CALLER - 0x38));
            assertEquals(calls, f.m.writesAt(CALLER - 0x38).size());
            NonvolatileBits local = new NonvolatileBits(GUARD, NV.rbpBits(), NV.rsiBits(), NV.rdiBits(),
                    NV.r12Bits(), NV.r13Bits(), NV.r14Bits(), NV.r15Bits(), NV.xmm6());
            assertEquals(local, call.nonvolatileBits());
            if (n == 0) {
                VolatileBits input = f.outer.volatileBits();
                assertEquals(bits(input, input.raxBits(), I + 0x5C5CB18L, input.rdxBits(), input.r8Bits(),
                        input.r9Bits(), input.r10Bits(), input.r11Bits()), call.volatileBits());
                return ENTER_RESULT;
            }
            assertEquals(bits(ENTER_RESULT, 8, I + 0x5C5CB18L, 2, TLS, 0x10,
                    ENTER_RESULT.r10Bits(), ENTER_RESULT.r11Bits()), call.volatileBits());
            return LEAVE_RESULT;
        }
        @Override public NormalReturn tail(Tail tail) {
            tails++;
            assertEquals(1, tails);
            assertEquals(f.a84 ? 0x4223AE4L : 0x4223A7FL, tail.jumpSiteRva());
            assertEquals(f.a84 ? TargetKind.INDIRECT_ABSOLUTE : TargetKind.DIRECT_RVA, tail.kind());
            assertEquals(f.a84 ? LEAVE_TARGET : 0x4223AECL, tail.targetBits());
            Entry entry = tail.entry();
            assertEquals(I, entry.imageBaseBits());
            assertEquals(CALLER - 8, entry.rspBits());
            assertEquals(NV, entry.nonvolatileBits());
            assertEquals(f.a84 ? bits(ENTER_RESULT, ENTER_RESULT.raxBits(), I + 0x5C5CB18L,
                    ENTER_RESULT.rdxBits(), ENTER_RESULT.r8Bits(), ENTER_RESULT.r9Bits(),
                    ENTER_RESULT.r10Bits(), ENTER_RESULT.r11Bits()) : LEAVE_RESULT, entry.volatileBits());
            // Tail is opaque and supplies NR in this protocol; read the actual caller-owned RIP.
            long rip = f.m.readQword(entry.rspBits());
            NonvolatileBits nv = entry.nonvolatileBits();
            if (corruption == 1) rip ^= 1;
            if (corruption == 2) nv = new NonvolatileBits(nv.rbxBits() ^ 1, nv.rbpBits(), nv.rsiBits(),
                    nv.rdiBits(), nv.r12Bits(), nv.r13Bits(), nv.r14Bits(), nv.r15Bits(), nv.xmm6());
            return new NormalReturn(TAIL_RESULT, rip, entry.rspBits() + 8, nv);
        }
        @Override public long readGsQword58() { gsReads++; return GS; }
        @Override public void beforeStep(long site, long address) {
            budgets++;
            assertTrue(f.a84);
            assertEquals(1, budgets, "fixture permits exactly one finite guard-zero step");
            assertEquals(0x4223A9AL, site);
            assertEquals(GUARD, address);
        }
    }

    private static final class Pass implements Calls {
        Call last;
        @Override public VolatileBits invoke(Call call) { last = call; return TAIL_RESULT; }
        @Override public NormalReturn tail(Tail tail) { throw new AssertionError("unexpected tail"); }
        @Override public long readGsQword58() { throw new AssertionError("unexpected GS"); }
    }

    private static VolatileBits bits(VolatileBits xmm, long a, long c, long d,
            long r8, long r9, long r10, long r11) {
        return new VolatileBits(a, c, d, r8, r9, r10, r11,
                xmm.xmm0(), xmm.xmm1(), xmm.xmm2(), xmm.xmm3(), xmm.xmm4(), xmm.xmm5());
    }
    private static VolatileBits sample(long n) {
        return new VolatileBits(n + 1, n + 2, n + 3, n + 4, n + 5, n + 6, n + 7,
                new Bits128(n + 0x10, n + 0x11), new Bits128(n + 0x20, n + 0x21),
                new Bits128(n + 0x30, n + 0x31), new Bits128(n + 0x40, n + 0x41),
                new Bits128(n + 0x50, n + 0x51), new Bits128(n + 0x60, n + 0x61));
    }
    private record Op(String kind, long address, long value) { }
    /** Same coherent physical-byte helper as this owner's195/196 source witnesses. */
    private static final class Bytes implements Memory {
        final Map<Long, Byte> data = new HashMap<>();
        final List<Op> ops = new ArrayList<>();
        int rawB(long a) { return Byte.toUnsignedInt(data.getOrDefault(a, (byte) 0xA5)); }
        long raw(long a, int length) {
            long value = 0;
            for (int k = 0; k < length; k++) value |= (long) rawB(a + k) << (8 * k);
            return value;
        }
        long rawQ(long a) { return raw(a, 8); }
        int rawD(long a) { return (int) raw(a, 4); }
        void put(long a, long value, int length) {
            for (int k = 0; k < length; k++) data.put(a + k, (byte) (value >>> (8 * k)));
        }
        void putQ(long a, long value) { put(a, value, 8); }
        void putD(long a, int value) { put(a, Integer.toUnsignedLong(value), 4); }
        List<Op> writesAt(long a) { return ops.stream().filter(op -> op.address() == a
                && op.kind().startsWith("w")).toList(); }
        @Override public int readDword(long a) { int v = rawD(a); ops.add(new Op("rd", a, Integer.toUnsignedLong(v))); return v; }
        @Override public long readQword(long a) { long v = rawQ(a); ops.add(new Op("rq", a, v)); return v; }
        @Override public int readUnsignedByte(long a) { int v = rawB(a); ops.add(new Op("rb", a, v)); return v; }
        @Override public void writeDword(long a, int v) { ops.add(new Op("wd", a, Integer.toUnsignedLong(v))); putD(a, v); }
        @Override public void writeQword(long a, long v) { ops.add(new Op("wq", a, v)); putQ(a, v); }
        @Override public void writeByte(long a, int v) { ops.add(new Op("wb", a, v & 0xFFL)); put(a, v, 1); }
        @Override public int lockedXaddDword(long a, int addend) {
            int old = rawD(a); ops.add(new Op("xa", a, addend)); putD(a, old + addend); return old;
        }
        @Override public Bits128 read128(long a) { ops.add(new Op("r128", a, 0)); return new Bits128(rawQ(a), rawQ(a + 8)); }
        @Override public void write128(long a, Bits128 v) {
            ops.add(new Op("w128", a, v.lowBits())); putQ(a, v.lowBits()); putQ(a + 8, v.highBits());
        }
    }
}

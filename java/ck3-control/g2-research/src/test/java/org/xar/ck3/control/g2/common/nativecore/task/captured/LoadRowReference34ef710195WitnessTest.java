package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Memory;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.junit.jupiter.api.Assertions.*;

/** Literal software witnesses from REFERENCE01.asm and the two BIND01 callsites. */
public final class LoadRowReference34ef710195WitnessTest {
    private static final long I = 0x100000000L;
    private static final long O = 0x20000000L;
    private static final long Q = 0x30000000L;
    private static final long S = 0x700000000108L;
    private static final long RET = 0x123456789ABCDEF0L;
    private static final long G = I + 0x5D75F40L;
    private static final VolatileBits V1 = sample(0x1100000000000000L);
    private static final VolatileBits V2 = sample(0x2200000000000000L);
    private static final VolatileBits V3 = sample(0x3300000000000000L);
    private static final VolatileBits V4 = sample(0x4400000000000000L);
    private static final VolatileBits V5 = sample(0x5500000000000000L);
    private static final VolatileBits V6 = sample(0x6600000000000000L);

    @Test
    void nullSourceHasExactHeaderMarkersPaddingAndFirstCallBits() {
        Fixture f = new Fixture(S, 0L, RET);
        f.first(null);
        NormalReturn r = f.run();
        f.done();
        normal(f, r, nullResult(V1), f.original, RET);
        assertEquals(0L, f.m.rawQ(Q));
        assertEquals(0L, f.m.rawQ(O + 0x10));
        assertEquals(I + 0x48F8928L, f.m.rawQ(O));
        assertEquals(0, f.m.rawD(O + 8));
        assertEquals(0, f.m.rawD(O + 0x18));
        assertEquals(0, f.m.rawD(O + 0x30));
        assertEquals(0x3F666666, f.m.rawD(O + 0x3C));
        assertEquals(O + 0x48, f.m.rawQ(O + 0x40));
        assertEquals(I + 0x48F8A18L, f.m.rawQ(O + 0x48));
        assertEquals(I + 0x54DE1E8L, f.m.rawQ(O + 0x4A0));
        assertEquals(O + 0x50, f.m.rawQ(O + 0x28));
        assertEquals(15, f.m.rawD(O + 0x34));
        assertEquals(6, f.m.rawB(O + 0x38));
        assertEquals(3, f.m.rawD(S + 0x18));
        assertEquals(3, f.m.rawD(S + 0x20));
        for (long p : new long[]{O + 0xC, O + 0x1C, O + 0x20, O + 0x50}) {
            assertEquals(0xA5A5A5A5, f.m.rawD(p), "unwritten DWORD " + Long.toHexString(p));
        }
        for (long p : new long[]{O + 0x39, O + 0x3A, O + 0x3B, O + 0x55, S + 0x1C, S + 0x24}) {
            assertEquals(0xA5, f.m.rawB(p));
        }
        List<Op> markers = new ArrayList<>();
        for (int k = 0; k < 22; k++) markers.add(new Op("wb", O + 0x54 + 0x30L * k, 0));
        markers.add(new Op("wb", O + 0x474, 0xFF));
        assertEquals(markers, f.m.ops.stream().filter(op -> op.kind().equals("wb")
                && op.address() >= O + 0x50 && op.address() <= O + 0x474).toList());
        assertEquals(List.of(new Op("wd", O + 8, 0)), f.m.writesAt(O + 8));
        assertEquals(List.of(new Op("wd", O + 0x18, 0)), f.m.writesAt(O + 0x18));
        assertEquals(List.of(new Op("wd", S + 0x18, 3)), f.m.writesAt(S + 0x18));
        assertEquals(List.of(new Op("wd", S + 0x20, 3)), f.m.writesAt(S + 0x20));
    }

    @Test
    void registrationUsesPhysicalHashAndFreshInlineOrExternalReceiver() {
        for (int variant = 0; variant < 2; variant++) {
            long p = variant == 0 ? 0x100000000L : 0x45670000L;
            // First variant: low32(P)=0 is still non-null. Second: first callback replaces O+10.
            Fixture f = new Fixture(S + 0x1000L * variant, variant == 0 ? p : 0L, RET);
            f.first(variant == 0 ? null : call -> f.m.writeQword(O + 0x10, p));
            long bp = f.s - 0x5F;
            long inline = bp - 0x11;
            long hashAddress = bp - 0x39;
            NonvolatileBits local = f.local(p + 0x18, G);
            // TEST EAX, not RAX: this full64 nonzero result has low32=0 and must succeed.
            VolatileBits guardReturn = rax(V2, 0x100000000L);
            f.script.add(0x34EF83CL, TargetKind.DIRECT_RVA, 0x42219E0L,
                    bits(V1, inline, G, O + 0x470, 28, 3, 15, V1.r11Bits()), local,
                    guardReturn, call -> {
                        int[] bytes = {0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF};
                        for (int k = 0; k < bytes.length; k++) f.m.writeByte(hashAddress + k, bytes[k]);
                    });
            // FNV-1a32 of the eight literal physical bytes above is F33F1185.
            f.script.add(0x34EF8C5L, TargetKind.DIRECT_RVA, 0x337B7E0L,
                    bits(guardReturn, inline, p + 0x18, bp - 0x21, 0xF33F1185L,
                            hashAddress, guardReturn.r10Bits(), guardReturn.r11Bits()), local,
                    V3, call -> {
                        assertEquals(inline, f.m.rawQ(call.rspBits() + 0x28));
                        assertEquals(1, f.m.rawB(bp - 0x29));
                    });
            long receiver = variant == 0 ? inline : 0x90005000L;
            long vt = 0xA0001000L + variant * 0x100L;
            long target = 0xFEDCBA9876543000L + variant;
            f.m.putQ(vt + 0x20, target);
            f.script.add(0x34EF8CEL, TargetKind.DIRECT_RVA, 0x4221A04L,
                    bits(V3, V3.raxBits(), G, V3.rdxBits(), V3.r8Bits(), V3.r9Bits(),
                            V3.r10Bits(), V3.r11Bits()), local, V4, call -> {
                        f.m.writeQword(bp + 0x27, receiver);
                        // Inline also changes its original scratch vptr: the later read must be fresh.
                        f.m.writeQword(receiver, vt);
                    });
            long setneRdx = (inline & ~0xFFL) | (variant == 0 ? 0L : 1L);
            f.script.add(0x34EF8EAL, TargetKind.INDIRECT_ABSOLUTE, target,
                    bits(V4, vt, receiver, setneRdx, V4.r8Bits(), V4.r9Bits(),
                            V4.r10Bits(), V4.r11Bits()), local, V5, null);
            NormalReturn r = f.run();
            f.done();
            normal(f, r, bits(V5, O, 0, V5.rdxBits(), V5.r8Bits(), V5.r9Bits(),
                    V5.r10Bits(), V5.r11Bits()), f.original, RET);
            assertEquals(p, f.m.rawQ(O + 0x10));
            List<Long> physicalReads = f.m.ops.stream().filter(op -> op.kind().equals("rb")
                    && op.address() >= hashAddress && op.address() < hashAddress + 8)
                    .map(Op::address).toList();
            assertEquals(List.of(hashAddress, hashAddress + 1, hashAddress + 2, hashAddress + 3,
                    hashAddress + 4, hashAddress + 5, hashAddress + 6, hashAddress + 7), physicalReads);
        }
    }

    @Test
    void tailReloadsSourceUsesAtomicOriginalCountAndPopsFreshStack() {
        for (int oldCount : new int[]{1, 2}) {
            Fixture f = new Fixture(S, 0L, RET);
            long p = 0x40000000L;
            long vt = 0x50000000L;
            long target = 0xC000000000004321L;
            long changedRip = 0x777788889999AAAAL;
            NonvolatileBits changed = new NonvolatileBits(0xB11L, 0xB22L, 0xB33L, 0xB44L,
                    f.original.r12Bits(), f.original.r13Bits(), 0xB55L, f.original.r15Bits(), f.original.xmm6());
            f.m.putQ(p + 8, vt);
            f.m.putQ(vt, target);
            f.m.putD(p + 0x10, oldCount);
            f.first(call -> {
                f.m.writeQword(Q, p);
                f.m.writeQword(f.s - 8, changed.rbpBits());
                f.m.writeQword(f.s - 0x10, changed.rbxBits());
                f.m.writeQword(f.s - 0x18, changed.rsiBits());
                f.m.writeQword(f.s - 0x20, changed.rdiBits());
                f.m.writeQword(f.s - 0x28, changed.r14Bits());
                f.m.writeQword(f.s, changedRip);
            });
            VolatileBits expected;
            if (oldCount == 1) {
                f.script.add(0x34EF916L, TargetKind.INDIRECT_ABSOLUTE, target,
                        bits(V1, vt, p + 8, 1, 28, 3, 15, V1.r11Bits()),
                        f.local(0, f.original.r14Bits()), V6, null);
                expected = bits(V6, O, V6.rcxBits(), V6.rdxBits(), V6.r8Bits(), V6.r9Bits(),
                        V6.r10Bits(), V6.r11Bits());
            } else {
                expected = bits(V1, O, p + 8, O + 0x470, 28, 3, 15, V1.r11Bits());
            }
            NormalReturn r = f.run();
            f.done();
            normal(f, r, expected, changed, changedRip);
            assertEquals(0L, f.m.rawQ(O + 0x10));
            assertEquals(oldCount - 1, f.m.rawD(p + 0x10));
            assertEquals(List.of(new Op("xa", p + 0x10, -1)),
                    f.m.ops.stream().filter(op -> op.kind().equals("xa")).toList());
            assertTrue(f.m.ops.stream().noneMatch(op -> op.kind().equals("wd") && op.address() == p + 0x10));
            List<Long> reads = f.m.ops.stream().filter(op -> op.kind().equals("rq")).map(Op::address).toList();
            assertEquals(List.of(f.s - 0x28, f.s - 0x20, f.s - 0x18, f.s - 0x10, f.s - 8, f.s),
                    reads.subList(reads.size() - 6, reads.size()));
        }
    }

    @Test
    void nonzeroGuardEaxCallsFatalWithZeroExtendedEcxThenTraps() {
        long p = 0x60000000L;
        Fixture f = new Fixture(S, p, RET);
        f.first(null);
        long bp = f.s - 0x5F;
        VolatileBits guardReturn = rax(V2, 0xABCD123480000001L);
        NonvolatileBits local = f.local(p + 0x18, G);
        f.script.add(0x34EF83CL, TargetKind.DIRECT_RVA, 0x42219E0L,
                bits(V1, bp - 0x11, G, O + 0x470, 28, 3, 15, V1.r11Bits()), local, guardReturn, null);
        f.script.add(0x34EF92BL, TargetKind.DIRECT_RVA, 0x4222120L,
                bits(guardReturn, guardReturn.raxBits(), 0x80000001L, guardReturn.rdxBits(),
                        guardReturn.r8Bits(), guardReturn.r9Bits(), guardReturn.r10Bits(), guardReturn.r11Bits()),
                local, V6, null);
        assertThrows(UnsupportedOperationException.class, f::run);
        f.done();
        assertEquals(0, f.m.rawB(bp - 0x29));
        assertTrue(f.m.ops.stream().noneMatch(op -> op.kind().equals("rb")
                && op.address() >= bp - 0x39 && op.address() < bp - 0x31));
        assertTrue(f.m.ops.stream().noneMatch(op -> op.kind().equals("rq") && op.address() == f.s));
    }

    @Test
    void twoRealConsumerSitesPreserveOwnedReturnSlotAndDelegateIdentity() {
        for (long site : new long[]{0xBD7DD2L, 0xBD7E5FL}) {
            long callerRsp = S + 8;
            Fixture f = new Fixture(callerRsp - 8, 0L, I + site + 5);
            f.first(null);
            Call call = new Call(site, TargetKind.DIRECT_RVA, 0x34EF710L, callerRsp,
                    f.entry.volatileBits(), f.original);
            Calls bound = LoadRowReference34ef710195Calls.bind(I, f.m, f.script);
            VolatileBits result = bound.invoke(call);
            f.done();
            assertEquals(nullResult(V1), result);
            assertEquals(I + site + 5, f.m.rawQ(callerRsp - 8));
            assertTrue(f.m.writesAt(callerRsp - 8).isEmpty(), "caller owns the existing return slot");
        }
        Fixture empty = new Fixture(S, 0L, RET);
        Delegate delegate = new Delegate(empty.entry);
        Calls bound = LoadRowReference34ef710195Calls.bind(I, empty.m, delegate);
        for (Call unmatched : List.of(
                new Call(0xBD7DD3L, TargetKind.DIRECT_RVA, 0x34EF710L, S, empty.entry.volatileBits(), empty.original),
                new Call(0xBD7DD2L, TargetKind.INDIRECT_ABSOLUTE, 0x34EF710L, S, empty.entry.volatileBits(), empty.original),
                new Call(0xBD7DD2L, TargetKind.DIRECT_RVA, 0x34EF711L, S, empty.entry.volatileBits(), empty.original))) {
            assertSame(V6, bound.invoke(unmatched));
            assertSame(unmatched, delegate.lastCall);
        }
        Tail tail = new Tail(0x1234, TargetKind.INDIRECT_ABSOLUTE, 0x87654321, empty.entry);
        assertSame(delegate.tailReturn, bound.tail(tail));
        assertSame(tail, delegate.lastTail);
        assertEquals(0x1234567890ABCDEFL, bound.readGsQword58());
        assertEquals(1, delegate.gsReads);

        // Use actual child execution to obtain an invalid NV return; no mocked target return.
        Fixture invalid = new Fixture(S, 0L, I + 0xBD7DD7L);
        invalid.first(call -> invalid.m.writeQword(S - 0x10, 0xBADBADL));
        Calls rejecting = LoadRowReference34ef710195Calls.bind(I, invalid.m, invalid.script);
        Call actual = new Call(0xBD7DD2L, TargetKind.DIRECT_RVA, 0x34EF710L, S + 8,
                invalid.entry.volatileBits(), invalid.original);
        assertThrows(IllegalStateException.class, () -> rejecting.invoke(actual));
        invalid.done();
    }

    private static void normal(Fixture f, NormalReturn actual, VolatileBits v,
            NonvolatileBits nv, long rip) {
        assertEquals(v, actual.volatileBits());
        assertEquals(nv, actual.nonvolatileBits());
        assertEquals(rip, actual.returnRipBits());
        assertEquals(f.s + 8, actual.callerRspBits());
    }

    private static VolatileBits nullResult(VolatileBits afterFirst) {
        return bits(afterFirst, O, 0, O + 0x470, 28, 3, 15, afterFirst.r11Bits());
    }

    private static VolatileBits bits(VolatileBits xmm, long a, long c, long d,
            long r8, long r9, long r10, long r11) {
        return new VolatileBits(a, c, d, r8, r9, r10, r11,
                xmm.xmm0(), xmm.xmm1(), xmm.xmm2(), xmm.xmm3(), xmm.xmm4(), xmm.xmm5());
    }

    private static VolatileBits rax(VolatileBits v, long a) {
        return bits(v, a, v.rcxBits(), v.rdxBits(), v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits());
    }

    private static VolatileBits sample(long n) {
        return new VolatileBits(n + 1, n + 2, n + 3, n + 4, n + 5, n + 6, n + 7,
                new Bits128(n + 0x10, n + 0x11), new Bits128(n + 0x20, n + 0x21),
                new Bits128(n + 0x30, n + 0x31), new Bits128(n + 0x40, n + 0x41),
                new Bits128(n + 0x50, n + 0x51), new Bits128(n + 0x60, n + 0x61));
    }

    private static final class Fixture {
        final long s;
        final Bytes m = new Bytes();
        final NonvolatileBits original = new NonvolatileBits(0xB100000000000001L, 0xB200000000000002L,
                0xB300000000000003L, 0xB400000000000004L, 0xB500000000000005L,
                0xB600000000000006L, 0xB700000000000007L, 0xB800000000000008L,
                new Bits128(0xB900000000000009L, 0xBA0000000000000AL));
        final Entry entry;
        final Script script;
        final long initialP;
        Fixture(long stack, long p, long ret) {
            s = stack;
            initialP = p;
            VolatileBits incoming = sample(0xA000000000000000L);
            entry = new Entry(I, s, bits(incoming, incoming.raxBits(), O, Q,
                    incoming.r8Bits(), incoming.r9Bits(), incoming.r10Bits(), incoming.r11Bits()), original);
            m.putQ(s, ret);
            m.putQ(Q, p);
            script = new Script(s, m);
        }
        NonvolatileBits local(long rdi, long r14) {
            return new NonvolatileBits(O, s - 0x5F, Q, rdi, original.r12Bits(), original.r13Bits(),
                    r14, original.r15Bits(), original.xmm6());
        }
        void first(Consumer<Call> after) {
            VolatileBits v = entry.volatileBits();
            script.add(0x34EF74EL, TargetKind.DIRECT_RVA, 0x34F04D0L,
                    bits(v, initialP, O, Q, v.r8Bits(), v.r9Bits(), v.r10Bits(), v.r11Bits()),
                    local(0, original.r14Bits()), V1, call -> {
                        assertEquals(0L, m.rawQ(Q));
                        assertEquals(initialP, m.rawQ(O + 0x10));
                        assertEquals(original.rbpBits(), m.rawQ(s - 8));
                        assertEquals(original.rbxBits(), m.rawQ(s - 0x10));
                        assertEquals(original.rsiBits(), m.rawQ(s - 0x18));
                        assertEquals(original.rdiBits(), m.rawQ(s - 0x20));
                        assertEquals(original.r14Bits(), m.rawQ(s - 0x28));
                        if (after != null) after.accept(call);
                    });
        }
        NormalReturn run() { return LoadRowReference34ef710195.execute(entry, m, script); }
        void done() { script.done(); }
    }

    private record Step(long site, TargetKind kind, long target, VolatileBits expected,
            NonvolatileBits nv, VolatileBits result, Consumer<Call> after) { }

    private static final class Script implements Calls {
        final long entryRsp;
        final Bytes memory;
        final List<Step> steps = new ArrayList<>();
        int index;
        Script(long rsp, Bytes m) { entryRsp = rsp; memory = m; }
        void add(long site, TargetKind kind, long target, VolatileBits expected,
                NonvolatileBits nv, VolatileBits result, Consumer<Call> after) {
            steps.add(new Step(site, kind, target, expected, nv, result, after));
        }
        @Override public VolatileBits invoke(Call call) {
            assertTrue(index < steps.size(), "unexpected call " + Long.toHexString(call.callSiteRva()));
            Step expected = steps.get(index++);
            assertEquals(expected.site(), call.callSiteRva());
            assertEquals(expected.kind(), call.kind());
            assertEquals(expected.target(), call.targetBits());
            assertEquals(entryRsp - 0xC8, call.rspBits());
            assertEquals(expected.expected(), call.volatileBits());
            assertEquals(expected.nv(), call.nonvolatileBits());
            long length = call.callSiteRva() == 0x34EF8EAL ? 3
                    : call.callSiteRva() == 0x34EF916L ? 2 : 5;
            assertEquals(I + call.callSiteRva() + length, memory.rawQ(call.rspBits() - 8));
            assertEquals(index, memory.writesAt(call.rspBits() - 8).size(), "exactly one owned push per CALL");
            if (expected.after() != null) expected.after().accept(call);
            return expected.result();
        }
        @Override public NormalReturn tail(Tail transfer) { throw new AssertionError("unexpected tail " + transfer); }
        @Override public long readGsQword58() { throw new AssertionError("unexpected GS"); }
        void done() { assertEquals(steps.size(), index, "missing opaque call"); }
    }

    private record Op(String kind, long address, long value) { }

    /** One physical byte map: all overlapping access widths share the same bytes. */
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
            int old = rawD(a);
            ops.add(new Op("xa", a, addend));
            putD(a, old + addend);
            return old;
        }
        @Override public Bits128 read128(long a) {
            ops.add(new Op("r128", a, 0));
            return new Bits128(rawQ(a), rawQ(a + 8));
        }
        @Override public void write128(long a, Bits128 v) {
            ops.add(new Op("w128", a, v.lowBits()));
            putQ(a, v.lowBits()); putQ(a + 8, v.highBits());
        }
    }

    private static final class Delegate implements Calls {
        Call lastCall;
        Tail lastTail;
        int gsReads;
        final NormalReturn tailReturn;
        Delegate(Entry entry) { tailReturn = new NormalReturn(V6, RET, entry.rspBits() + 8, entry.nonvolatileBits()); }
        @Override public VolatileBits invoke(Call call) { lastCall = call; return V6; }
        @Override public NormalReturn tail(Tail tail) { lastTail = tail; return tailReturn; }
        @Override public long readGsQword58() { gsReads++; return 0x1234567890ABCDEFL; }
    }
}

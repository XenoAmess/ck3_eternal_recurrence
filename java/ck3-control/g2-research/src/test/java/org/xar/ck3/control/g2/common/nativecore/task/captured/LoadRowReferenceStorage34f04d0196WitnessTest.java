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

/** Owner literal software witnesses from the complete93B ASM and frozen185 ports. */
public final class LoadRowReferenceStorage34f04d0196WitnessTest {
    private static final long I = 0x100000000L;
    private static final long S = 0x710000000108L;
    private static final long GS = 0x40000000L;
    private static final long TLS = 0x50000000L;
    private static final long GUARD = I + 0x5D75ED8L;
    private static final long STORAGE = I + 0x5D75EE0L;
    private static final long RET = 0x123456789ABCDEF0L;
    private static final VolatileBits V1 = sample(0x1100000000000000L);
    private static final VolatileBits V2 = sample(0x2200000000000000L);
    private static final NonvolatileBits NV = new NonvolatileBits(0xB100000000000001L,
            0xB200000000000002L, 0xB300000000000003L, 0xB400000000000004L,
            0xB500000000000005L, 0xB600000000000006L, 0xB700000000000007L,
            0xB800000000000008L, new Bits128(0xB900000000000009L, 0xBA0000000000000AL));

    @Test
    void signedDwordNotGreaterReadsModuleSlotZeroAndReturnsWithoutCallbacks() {
        int[][] input = {{-1, 0}, {Integer.MIN_VALUE, Integer.MAX_VALUE}, {7, 7}};
        for (int[] pair : input) {
            Fixture f = new Fixture(S, pair[0], pair[1]);
            NormalReturn actual = f.run();
            f.done();
            VolatileBits in = f.entry.volatileBits();
            assertReturn(f, actual, bits(in, STORAGE, TLS, 0x10, in.r8Bits(), in.r9Bits(),
                    in.r10Bits(), in.r11Bits()), RET);
            assertEquals(List.of(new Op("gs", 0x58, GS), new Op("rq", GS, TLS),
                    new Op("rd", TLS + 0x10, Integer.toUnsignedLong(pair[1])),
                    new Op("rd", GUARD, Integer.toUnsignedLong(pair[0])),
                    new Op("rq", S, RET)), f.m.ops);
        }
    }

    @Test
    void callbackFreshGuardTwoOrMinusOneControlsOnlyTwoFooterBytesAndAllVolatiles() {
        for (int postGuard : new int[]{2, -1}) {
            // Signed MAX > signed MIN, despite unsigned/full64 ordering being the opposite.
            Fixture f = new Fixture(S, Integer.MAX_VALUE, Integer.MIN_VALUE);
            VolatileBits in = f.entry.volatileBits();
            long changedRet = 0x9999888877776666L;
            f.script.add(0x34F0503L, 0x4223A84L,
                    bits(in, 0x80000000L, GUARD, 0x10, in.r8Bits(), in.r9Bits(),
                            in.r10Bits(), in.r11Bits()), V1, call -> {
                        f.m.writeDword(GUARD, postGuard);
                        f.m.writeQword(S, changedRet);
                    });
            VolatileBits after = V1;
            if (postGuard == -1) {
                f.script.add(0x34F0526L, 0x4223A24L,
                        bits(V1, V1.raxBits(), GUARD, V1.rdxBits(), V1.r8Bits(), V1.r9Bits(),
                                V1.r10Bits(), V1.r11Bits()), V2, call -> {
                            assertEquals(0, f.m.rawB(STORAGE + 4));
                            assertEquals(0xFF, f.m.rawB(STORAGE + 0x34));
                        });
                after = V2;
            }
            NormalReturn actual = f.run();
            f.done();
            assertReturn(f, actual, bits(after, STORAGE, after.rcxBits(), after.rdxBits(),
                    after.r8Bits(), after.r9Bits(), after.r10Bits(), after.r11Bits()), changedRet);
            List<Op> bytes = f.m.ops.stream().filter(op -> op.kind().equals("wb")).toList();
            assertEquals(postGuard == -1 ? List.of(new Op("wb", STORAGE + 4, 0),
                    new Op("wb", STORAGE + 0x34, 0xFF)) : List.of(), bytes);
            for (int offset = 0; offset < 0x40; offset++) {
                int expected = postGuard == -1 && offset == 4 ? 0
                        : postGuard == -1 && offset == 0x34 ? 0xFF : 0xA5;
                assertEquals(expected, f.m.rawB(STORAGE + offset), "footer byte " + offset);
            }
            assertEquals(List.of(new Op("rd", GUARD, Integer.MAX_VALUE),
                    new Op("rd", GUARD, Integer.toUnsignedLong(postGuard))),
                    f.m.ops.stream().filter(op -> op.kind().equals("rd") && op.address() == GUARD).toList());
            assertTrue(f.m.ops.stream().noneMatch(op -> op.kind().equals("xa")));
        }
    }

    @Test
    void actualParentCallUsesStorageAdapterAndOtherTransfersKeepIdentity() {
        long object = 0x20000000L;
        long sourceSlot = 0x30000000L;
        Bytes m = new Bytes();
        m.putQ(S, RET);
        m.putQ(sourceSlot, 0);
        m.putQ(GS, TLS);
        m.putD(TLS + 0x10, 7);
        m.putD(GUARD, 6);
        VolatileBits incoming = sample(0xA000000000000000L);
        VolatileBits parentV = bits(incoming, incoming.raxBits(), object, sourceSlot,
                incoming.r8Bits(), incoming.r9Bits(), incoming.r10Bits(), incoming.r11Bits());
        Entry parent = new Entry(I, S, parentV, NV);
        Delegate delegate = new Delegate(parent, m, false);
        Calls bound = LoadRowReferenceStorage34f04d0196Calls.bind(I, m, delegate);
        NormalReturn actual = LoadRowReference34ef710195.execute(parent, m, bound);
        assertEquals(bits(parentV, object, 0, object + 0x470, 28, 3, 15, parentV.r11Bits()), actual.volatileBits());
        assertEquals(NV, actual.nonvolatileBits());
        assertEquals(RET, actual.returnRipBits());
        assertEquals(S + 8, actual.callerRspBits());
        assertEquals(1, delegate.gsReads);
        assertNull(delegate.lastCall, "known34EF74E must execute196 rather than delegate");
        long callerOwnedSlot = S - 0xD0;
        assertEquals(List.of(new Op("wq", callerOwnedSlot, I + 0x34EF753L)), m.writesAt(callerOwnedSlot));
        assertEquals(0L, m.rawQ(object + 0x10));
        assertEquals(0L, m.rawQ(sourceSlot));
        assertTrue(m.ops.contains(new Op("rq", GS, TLS)));
        assertTrue(m.ops.contains(new Op("rd", TLS + 0x10, 7)));
        assertEquals(0xA5, m.rawB(STORAGE + 4));
        assertEquals(0xA5, m.rawB(STORAGE + 0x34));

        Delegate passthrough = new Delegate(parent, new Bytes(), true);
        Calls forwarding = LoadRowReferenceStorage34f04d0196Calls.bind(I, new Bytes(), passthrough);
        for (Call unmatched : List.of(
                new Call(0x34EF74FL, TargetKind.DIRECT_RVA, 0x34F04D0L, S, parentV, NV),
                new Call(0x34EF74EL, TargetKind.INDIRECT_ABSOLUTE, 0x34F04D0L, S, parentV, NV),
                new Call(0x34EF74EL, TargetKind.DIRECT_RVA, 0x34F04D1L, S, parentV, NV))) {
            assertSame(V2, forwarding.invoke(unmatched));
            assertSame(unmatched, passthrough.lastCall);
        }
        Tail tail = new Tail(0x1234, TargetKind.INDIRECT_ABSOLUTE, 0x987654321L, parent);
        assertSame(passthrough.tailReturn, forwarding.tail(tail));
        assertSame(tail, passthrough.lastTail);
        assertEquals(GS, forwarding.readGsQword58());
        assertEquals(1, passthrough.gsReads);
    }

    @Test
    void actualBd7CallerComposesBothBindersWithOneNewControlledInput() {
        long object = 0x20000000L;
        long sourceSlot = 0x30000000L;
        Bytes m = new Bytes();
        // The actual BD7DD2 caller owns its CALL return slot before either adapter runs.
        m.putQ(S, I + 0xBD7DD7L);
        m.putQ(sourceSlot, 0);
        m.putQ(GS, TLS);
        m.putD(TLS + 0x10, 7);
        m.putD(GUARD, 6);
        VolatileBits seed = sample(0xA000000000000000L);
        VolatileBits input = bits(seed, seed.raxBits(), object, sourceSlot,
                seed.r8Bits(), seed.r9Bits(), seed.r10Bits(), seed.r11Bits());
        Entry describedEntry = new Entry(I, S, input, NV);
        Delegate crtPorts = new Delegate(describedEntry, m, false);
        Calls storage = LoadRowReferenceStorage34f04d0196Calls.bind(I, m, crtPorts);
        Calls row = LoadRowReference34ef710195Calls.bind(I, m, storage);
        Call actual = new Call(0xBD7DD2L, TargetKind.DIRECT_RVA, 0x34EF710L, S + 8, input, NV);
        VolatileBits result = row.invoke(actual);
        assertEquals(bits(input, object, 0, object + 0x470, 28, 3, 15, input.r11Bits()), result);
        assertTrue(m.writesAt(S).isEmpty(), "both adapters consume the caller-owned slot");
        assertEquals(List.of(new Op("wq", S - 0xD0, I + 0x34EF753L)), m.writesAt(S - 0xD0));
        assertEquals(1, crtPorts.gsReads);
        assertNull(crtPorts.lastCall, "signed early return must not invoke opaque CRT calls");
        assertEquals(0L, m.rawQ(object + 0x10));
        assertEquals(0L, m.rawQ(sourceSlot));
        assertEquals(0xA5A5A5A5, m.rawD(object + 0x20));
        assertEquals(0xA5A5A5A5, m.rawD(object + 0x50));
        List<Op> expectedMarkers = new ArrayList<>();
        for (int k = 0; k < 22; k++) expectedMarkers.add(new Op("wb", object + 0x54 + 0x30L * k, 0));
        expectedMarkers.add(new Op("wb", object + 0x474, 0xFF));
        assertEquals(expectedMarkers, m.ops.stream().filter(op -> op.kind().equals("wb")
                && op.address() >= object + 0x50 && op.address() <= object + 0x474).toList());
    }

    private static void assertReturn(Fixture f, NormalReturn actual, VolatileBits expected, long rip) {
        assertEquals(expected, actual.volatileBits());
        assertEquals(NV, actual.nonvolatileBits());
        assertEquals(rip, actual.returnRipBits());
        assertEquals(f.entry.rspBits() + 8, actual.callerRspBits());
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

    private static final class Fixture {
        final Bytes m = new Bytes();
        final Entry entry;
        final Script script;
        Fixture(long stack, int guard, int tls) {
            entry = new Entry(I, stack, sample(0xA000000000000000L), NV);
            m.putQ(stack, RET);
            m.putQ(GS, TLS);
            m.putD(TLS + 0x10, tls);
            m.putD(GUARD, guard);
            script = new Script(entry, m);
        }
        NormalReturn run() { return LoadRowReferenceStorage34f04d0196.execute(entry, m, script); }
        void done() { script.done(); }
    }

    private record Step(long site, long target, VolatileBits expected,
            VolatileBits result, Consumer<Call> after) { }

    private static final class Script implements Calls {
        final Entry entry;
        final Bytes m;
        final List<Step> steps = new ArrayList<>();
        int index;
        int gsReads;
        Script(Entry e, Bytes memory) { entry = e; m = memory; }
        void add(long site, long target, VolatileBits expected, VolatileBits result, Consumer<Call> after) {
            steps.add(new Step(site, target, expected, result, after));
        }
        @Override public VolatileBits invoke(Call call) {
            assertTrue(index < steps.size(), "unexpected call " + Long.toHexString(call.callSiteRva()));
            Step step = steps.get(index++);
            assertEquals(step.site(), call.callSiteRva());
            assertEquals(TargetKind.DIRECT_RVA, call.kind());
            assertEquals(step.target(), call.targetBits());
            assertEquals(entry.rspBits() - 0x28, call.rspBits());
            assertEquals(step.expected(), call.volatileBits());
            assertEquals(NV, call.nonvolatileBits());
            assertEquals(I + call.callSiteRva() + 5, m.rawQ(call.rspBits() - 8));
            assertEquals(index, m.writesAt(call.rspBits() - 8).size());
            m.ops.add(new Op("call", call.callSiteRva(), call.targetBits()));
            if (step.after() != null) step.after().accept(call);
            return step.result();
        }
        @Override public long readGsQword58() { gsReads++; m.ops.add(new Op("gs", 0x58, GS)); return GS; }
        @Override public NormalReturn tail(Tail tail) { throw new AssertionError("unexpected tail " + tail); }
        void done() { assertEquals(steps.size(), index); assertEquals(1, gsReads); }
    }

    private static final class Delegate implements Calls {
        final Bytes m;
        final boolean allowCalls;
        final NormalReturn tailReturn;
        Call lastCall;
        Tail lastTail;
        int gsReads;
        Delegate(Entry entry, Bytes memory, boolean allow) {
            m = memory; allowCalls = allow;
            tailReturn = new NormalReturn(V2, RET, entry.rspBits() + 8, entry.nonvolatileBits());
        }
        @Override public VolatileBits invoke(Call call) {
            if (!allowCalls) throw new AssertionError("unexpected downstream call " + call);
            lastCall = call; return V2;
        }
        @Override public NormalReturn tail(Tail tail) { lastTail = tail; return tailReturn; }
        @Override public long readGsQword58() { gsReads++; m.ops.add(new Op("gs", 0x58, GS)); return GS; }
    }

    private record Op(String kind, long address, long value) { }

    /** Mechanically reused from the independent195 owner witness: one coherent physical byte map. */
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

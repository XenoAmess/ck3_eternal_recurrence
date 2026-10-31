package org.xar.ck3.control.g2.common.nativecore.task.captured;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.*;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.junit.jupiter.api.Assertions.*;

/** Independent literal cases; no target Java source was used to construct expected values. */
public final class LoadRowReferenceCallee337b7e0199WitnessTest {
    @Test
    void existingKeyHasNoFloatingAndRestoresFreshPhysicalStack() {
        RowRef199Fixture f = new RowRef199Fixture();
        f.m.putB(f.a + 4, 1);
        f.m.putQ(f.a + 8, f.key);
        f.budget.add(0x337B831L, f.a, false);
        long changedRip = 0x9988776655443322L;
        NonvolatileBits changed = new NonvolatileBits(0x7711L, 0x7722L, f.nv.rsiBits(), f.nv.rdiBits(),
                f.nv.r12Bits(), f.nv.r13Bits(), f.nv.r14Bits(), f.nv.r15Bits(), f.nv.xmm6());
        f.calls.add(0x337B8EDL, TargetKind.DIRECT_RVA, 0xA636F0L,
                f.v(f.in, f.descriptor, f.bp - 0x49, f.a + 0x10, f.in.r8Bits(), f.k,
                        f.in.r10Bits(), f.in.r11Bits()),
                f.local(f.a, 0, f.nv.r13Bits(), f.partialR14(1)), f.v1, call -> {
                    f.m.writeQword(f.s + 0x10, changed.rbxBits());
                    f.m.writeQword(f.s - 8, changed.rbpBits());
                    f.m.writeQword(f.s, changedRip);
                });
        NormalReturn result = f.run();
        f.done();
        f.normal(result, f.v(f.v1, f.out, 0, f.v1.rdxBits(), f.v1.r8Bits(), f.v1.r9Bits(),
                f.v1.r10Bits(), f.v1.r11Bits()), changed, changedRip);
        assertEquals(List.of(new RowRef199Fixture.Op("wq", f.out, f.a)), f.m.writesAt(f.out));
        assertEquals(List.of(new RowRef199Fixture.Op("wb", f.out + 8, 0)), f.m.writesAt(f.out + 8));
        f.padding(f.out + 9, 7);
    }

    @Test
    void emptyInsertionUsesInstructionFloatPortsPhysicalSixthAndExactWidths() {
        RowRef199Fixture f = new RowRef199Fixture();
        f.floating.enabled = true;
        long receiver = 0x70001000L;
        long vt = 0x70002000L;
        long target = 0xFE00000000000123L;
        f.m.putB(f.a + 4, 0);
        f.m.putQ(f.descriptor + 0x38, receiver);
        f.m.putQ(receiver, vt);
        f.m.putQ(vt, target);
        f.calls.add(0x337B8AFL, TargetKind.INDIRECT_ABSOLUTE, target,
                f.v(f.fpBits(), vt, receiver, f.a + 0x10, f.in.r8Bits(), f.k,
                        f.in.r10Bits(), f.in.r11Bits()),
                f.local(f.a, 0, f.a + 0x10, f.partialR14(1)), f.v1,
                call -> f.m.writeDword(f.table + 0x10, 8));
        NormalReturn result = f.run();
        f.done();
        f.normal(result, f.v(f.v1, f.out, f.v1.rcxBits(), f.v1.rdxBits(), f.v1.r8Bits(),
                f.v1.r9Bits(), f.v1.r10Bits(), f.v1.r11Bits()), f.nv, f.ret);
        assertEquals(9, f.m.rawD(f.table + 0x10));
        assertEquals(0, f.m.rawD(f.a));
        assertEquals(1, f.m.rawB(f.a + 4));
        assertEquals(f.key, f.m.rawQ(f.a + 8));
        assertEquals(f.v1.raxBits(), f.m.rawQ(f.a + 0x48));
        assertEquals(List.of(new RowRef199Fixture.Op("wd", f.a, 0)), f.m.writesAt(f.a));
        assertEquals(List.of(new RowRef199Fixture.Op("wb", f.a + 4, 1)), f.m.writesAt(f.a + 4));
        assertEquals(List.of(new RowRef199Fixture.Op("wq", f.out, f.a)), f.m.writesAt(f.out));
        assertEquals(List.of(new RowRef199Fixture.Op("wb", f.out + 8, 1)), f.m.writesAt(f.out + 8));
        f.padding(f.a + 5, 3);
        f.padding(f.out + 9, 7);
        assertTrue(f.m.ops.contains(new RowRef199Fixture.Op("rq", f.s + 0x30, f.descriptor)));
    }

    @Test
    void occupiedNextEmptyUsesTwoOpaqueCallsAndFreshParameterHomes() {
        RowRef199Fixture f = new RowRef199Fixture();
        long b = f.a + 0x50;
        long c = f.a + 0xA0;
        long oldKey = 0x2233445566778899L;
        long newKey = 0x33445566778899AAL;
        long newKeySlot = 0x51000000L;
        long newDescriptor = 0x61000000L;
        int newHash = 0x80000001;
        f.floating.enabled = true;
        f.m.putB(f.a + 4, 1);
        f.m.putQ(f.a + 8, f.key ^ 1);
        f.m.putD(b, 0x12345678);
        f.m.putB(b + 4, 1);
        f.m.putQ(b + 8, oldKey);
        f.m.putB(c + 4, 0);
        f.m.putQ(f.descriptor + 0x38, 0xDEAD0000L);
        f.m.putQ(newDescriptor + 0x38, 0);
        f.m.putQ(newKeySlot, newKey);
        f.budget.add(0x337B831L, f.a, false);
        NonvolatileBits local = f.local(b, 0, b + 0x10, f.partialR14(2));
        f.calls.add(0x337B93EL, TargetKind.DIRECT_RVA, 0x87C9B0L,
                f.v(f.fpBits(), oldKey, c + 0x10, b + 0x10, f.in.r8Bits(), f.k,
                        f.in.r10Bits(), f.in.r11Bits()), local, f.v1, call -> {
                    assertEquals(0x12345678, f.m.rawD(c));
                    assertEquals(2, f.m.rawB(c + 4));
                    assertEquals(oldKey, f.m.rawQ(c + 8));
                    f.m.writeDword(f.s + 0x18, newHash);
                    f.m.writeQword(f.s + 0x20, newKeySlot);
                    f.m.writeQword(f.s + 0x30, newDescriptor);
                });
        f.calls.add(0x337B987L, TargetKind.DIRECT_RVA, 0xE23EA0L,
                f.v(f.v1, newDescriptor, b + 8, f.bp - 0x49, Integer.toUnsignedLong(newHash),
                        f.v1.r9Bits(), f.v1.r10Bits(), f.v1.r11Bits()), local, f.v2,
                call -> assertEquals(newKey, f.m.rawQ(f.bp - 0x49)));
        NormalReturn result = f.run();
        f.done();
        f.normal(result, f.v(f.v2, f.out, 0, f.v2.rdxBits(), f.v2.r8Bits(), f.v2.r9Bits(),
                f.v2.r10Bits(), f.v2.r11Bits()), f.nv, f.ret);
        assertEquals(newHash, f.m.rawD(b));
        assertEquals(2, f.m.rawB(b + 4));
        assertEquals(1, f.m.rawD(f.table + 0x10));
        assertEquals(b, f.m.rawQ(f.out));
        assertEquals(1, f.m.rawB(f.out + 8));
        assertTrue(f.m.ops.contains(new RowRef199Fixture.Op("rq", f.s + 0x20, newKeySlot)));
        assertTrue(f.m.ops.contains(new RowRef199Fixture.Op("rq", f.s + 0x30, newDescriptor)));
        f.padding(c + 5, 3);
        f.padding(f.out + 9, 7);
    }

/** Test-only shared byte/trace fixtures, mechanically based on the owner's195/196 helpers. */
static final class RowRef199Fixture {
    final long image = 0x100000000L;
    final long s = 0x730000000108L;
    final long bp = s - 0x4F;
    final long work = s - 0x118;
    final long table = 0x20000000L;
    final long out = 0x30000000L;
    final long a = 0x40000000L;
    final long k = 0x50000000L;
    final long descriptor = 0x60000000L;
    final long key = 0x1122334455667788L;
    final long ret = 0x123456789ABCDEF0L;
    final Bytes m = new Bytes();
    final VolatileBits in;
    final VolatileBits v1 = sample(0x1100000000000000L);
    final VolatileBits v2 = sample(0x2200000000000000L);
    final VolatileBits v3 = sample(0x3300000000000000L);
    final NonvolatileBits nv = new NonvolatileBits(0xB100000000000001L, 0xB200000000000002L,
            0xB300000000000003L, 0xB400000000000004L, 0xB500000000000005L,
            0xB600000000000006L, 0xB70000000000127EL, 0xB800000000000008L,
            new Bits128(0xB900000000000009L, 0xBA0000000000000AL));
    final Entry entry;
    final Script calls = new Script();
    final Budgets budget = new Budgets();
    final Floating floating = new Floating();

    RowRef199Fixture() {
        VolatileBits seed = sample(0xA000000000000000L);
        in = v(seed, seed.raxBits(), table, out, 0xABCD123400000000L, k, seed.r10Bits(), seed.r11Bits());
        entry = new Entry(image, s, in, nv);
        m.putQ(s, ret);
        m.putQ(s + 0x30, descriptor);
        m.putD(table + 0x14, 7);
        m.putD(table + 0x10, 0);
        m.putB(table + 0x18, 8);
        m.putD(table + 0x1C, 0x3F000000);
        m.putQ(table + 8, a);
        m.putQ(k, key);
        m.putQ(descriptor + 0x38, 0);
    }
    NormalReturn run() { return LoadRowReferenceCallee337b7e0199.execute(entry, m, calls, budget, floating); }
    void done() { calls.done(); budget.done(); floating.done(); }
    long partialR14(int low) { return (nv.r14Bits() & ~0xFFL) | (low & 0xFFL); }
    NonvolatileBits local(long bucket, long r12, long r13, long r14) {
        return new NonvolatileBits(bucket, bp, table, out, r12, r13, r14, nv.r15Bits(), nv.xmm6());
    }
    void normal(NormalReturn actual, VolatileBits expected, NonvolatileBits restored, long rip) {
        assertEquals(expected, actual.volatileBits());
        assertEquals(restored, actual.nonvolatileBits());
        assertEquals(rip, actual.returnRipBits());
        assertEquals(s + 8, actual.callerRspBits());
    }
    void padding(long address, int count) { for (int j = 0; j < count; j++) assertEquals(0xA5, m.rawB(address + j)); }
    VolatileBits fpBits() {
        return new VolatileBits(in.raxBits(), in.rcxBits(), in.rdxBits(), in.r8Bits(), in.r9Bits(),
                in.r10Bits(), in.r11Bits(), new Bits128(0x40E00000L, 0), new Bits128(0x3E124925L, 0),
                in.xmm2(), in.xmm3(), in.xmm4(), in.xmm5());
    }
    VolatileBits v(VolatileBits xmm, long ax, long cx, long dx, long r8, long r9, long r10, long r11) {
        return new VolatileBits(ax, cx, dx, r8, r9, r10, r11,
                xmm.xmm0(), xmm.xmm1(), xmm.xmm2(), xmm.xmm3(), xmm.xmm4(), xmm.xmm5());
    }
    static VolatileBits sample(long n) {
        return new VolatileBits(n + 1, n + 2, n + 3, n + 4, n + 5, n + 6, n + 7,
                new Bits128(n + 0x10, n + 0x11), new Bits128(n + 0x20, n + 0x21),
                new Bits128(n + 0x30, n + 0x31), new Bits128(n + 0x40, n + 0x41),
                new Bits128(n + 0x50, n + 0x51), new Bits128(n + 0x60, n + 0x61));
    }
    record Expected(long site, TargetKind kind, long target, VolatileBits v, NonvolatileBits nv,
            VolatileBits result, Consumer<Call> action) { }
    final class Script implements Calls {
        final List<Expected> expected = new ArrayList<>();
        int index;
        void add(long site, TargetKind kind, long target, VolatileBits v, NonvolatileBits n,
                VolatileBits result, Consumer<Call> action) {
            expected.add(new Expected(site, kind, target, v, n, result, action));
        }
        @Override public VolatileBits invoke(Call call) {
            assertTrue(index < expected.size(), "unexpected call " + Long.toHexString(call.callSiteRva()));
            Expected e = expected.get(index++);
            assertEquals(e.site(), call.callSiteRva());
            assertEquals(e.kind(), call.kind());
            assertEquals(e.target(), call.targetBits());
            assertEquals(work, call.rspBits());
            assertEquals(e.v(), call.volatileBits());
            assertEquals(e.nv(), call.nonvolatileBits());
            long site = call.callSiteRva();
            long size = site == 0x337B8AFL || site == 0x337B8DFL || site == 0x337B979L || site == 0x337BA09L ? 2
                    : site == 0x337B908L || site == 0x337B9A2L || site == 0x337BA32L
                            || site == 0x337BB1CL || site == 0x337BB66L ? 3 : 5;
            assertEquals(image + site + size, m.rawQ(work - 8));
            assertEquals(index, m.writesAt(work - 8).size(), "one physical return push per owned CALL");
            if (e.action() != null) e.action().accept(call);
            return e.result();
        }
        @Override public NormalReturn tail(Tail transfer) { throw new AssertionError("unexpected tail " + transfer); }
        @Override public long readGsQword58() { throw new AssertionError("unexpected GS"); }
        void done() { assertEquals(expected.size(), index); }
    }
    record BudgetStep(long header, long bucket, boolean reject) { }
    final class Budgets implements LoopBudget {
        final List<BudgetStep> expected = new ArrayList<>();
        int index;
        void add(long header, long bucket, boolean reject) { expected.add(new BudgetStep(header, bucket, reject)); }
        @Override public void beforeStep(long header, long bucket) {
            assertTrue(index < expected.size(), "unexpected loop step");
            BudgetStep e = expected.get(index++);
            assertEquals(e.header(), header);
            assertEquals(e.bucket(), bucket);
            if (e.reject()) throw new UnsupportedOperationException("finite fixture budget");
        }
        void done() { assertEquals(expected.size(), index); }
    }
    final class Floating implements LoadRowReferenceCallee337b7e0199Api.Float32 {
        boolean enabled;
        boolean above;
        int nonzeroConversions;
        int divisions;
        int compares;
        @Override public int convertSignedDwordToFloatBits(int value) {
            assertTrue(enabled, "no floating instruction on this path");
            // Zero upper CVTDQ2PS lanes are exact+0 and may be materialized without port calls.
            if (value == 0) return 0;
            assertTrue(nonzeroConversions < 2);
            assertEquals(nonzeroConversions++ == 0 ? 1 : 7, value);
            return value == 1 ? 0x3F800000 : 0x40E00000;
        }
        @Override public int divideScalarFloatBits(int dividend, int divisor) {
            assertTrue(enabled); assertEquals(1, ++divisions);
            assertEquals(0x3F800000, dividend); assertEquals(0x40E00000, divisor);
            return 0x3E124925;
        }
        @Override public boolean orderedAbove(int left, int right) {
            assertTrue(enabled); assertEquals(1, ++compares);
            assertEquals(0x3E124925, left); assertEquals(0x3F000000, right);
            return above;
        }
        void done() {
            assertEquals(enabled ? 2 : 0, nonzeroConversions);
            assertEquals(enabled ? 1 : 0, divisions); assertEquals(enabled ? 1 : 0, compares);
        }
    }
    record Op(String kind, long address, long value) { }
    static final class Bytes implements Memory {
        final Map<Long, Byte> data = new HashMap<>();
        final List<Op> ops = new ArrayList<>();
        int rawB(long a) { return Byte.toUnsignedInt(data.getOrDefault(a, (byte) 0xA5)); }
        long raw(long a, int count) {
            long value = 0;
            for (int j = 0; j < count; j++) value |= (long) rawB(a + j) << (8 * j);
            return value;
        }
        long rawQ(long a) { return raw(a, 8); }
        int rawD(long a) { return (int) raw(a, 4); }
        void put(long a, long value, int count) { for (int j = 0; j < count; j++) data.put(a + j, (byte) (value >>> (8 * j))); }
        void putQ(long a, long value) { put(a, value, 8); }
        void putD(long a, int value) { put(a, Integer.toUnsignedLong(value), 4); }
        void putB(long a, int value) { put(a, value, 1); }
        List<Op> writesAt(long a) { return ops.stream().filter(op -> op.kind().startsWith("w") && op.address() == a).toList(); }
        @Override public int readDword(long a) { int v = rawD(a); ops.add(new Op("rd", a, Integer.toUnsignedLong(v))); return v; }
        @Override public long readQword(long a) { long v = rawQ(a); ops.add(new Op("rq", a, v)); return v; }
        @Override public int readUnsignedByte(long a) { int v = rawB(a); ops.add(new Op("rb", a, v)); return v; }
        @Override public void writeDword(long a, int v) { ops.add(new Op("wd", a, Integer.toUnsignedLong(v))); putD(a, v); }
        @Override public void writeQword(long a, long v) { ops.add(new Op("wq", a, v)); putQ(a, v); }
        @Override public void writeByte(long a, int v) { ops.add(new Op("wb", a, v & 0xFFL)); putB(a, v); }
        @Override public int lockedXaddDword(long a, int addend) { int old = rawD(a); ops.add(new Op("xa", a, addend)); putD(a, old + addend); return old; }
        @Override public Bits128 read128(long a) { ops.add(new Op("r128", a, 0)); return new Bits128(rawQ(a), rawQ(a + 8)); }
        @Override public void write128(long a, Bits128 v) { ops.add(new Op("w128", a, v.lowBits())); putQ(a, v.lowBits()); putQ(a + 8, v.highBits()); }
    }
}
}

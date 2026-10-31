package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.OptionalLong;
import java.util.ArrayList;

public final class WindowValueWitness178Test {
    @Test
    void independentLiteralSourceCases() {
        case1();
        case2();
        case3();
    }

    static void case1() {
        long base = 0x140000000L;
        long slot = base + 0x5C6A690L;
        Map<Long, Long> ptrs = new HashMap<>();
        Map<Long, Integer> reads = new HashMap<>();

        ptrs.put(slot, 0x1122334455667788L);
        LoadPdxWindowValue178.Memory getterMem = new LoadPdxWindowValue178.Memory() {
            @Override public long readPointer(long a) {
                reads.put(a, reads.getOrDefault(a, 0) + 1);
                if (!ptrs.containsKey(a)) throw new AssertionError("Missing readPointer at " + Long.toHexString(a));
                return ptrs.get(a);
            }
        };

        long v1 = LoadPdxWindowValue178.readRax(base, getterMem);
        if (v1 != 0x1122334455667788L) throw new AssertionError("C1 v1");

        ptrs.put(slot, 0xFEDCBA9876543210L);
        long v2 = LoadPdxWindowValue178.readRax(base, getterMem);
        if (v2 != 0xFEDCBA9876543210L) throw new AssertionError("C1 v2");

        if (reads.get(slot) != 2) throw new AssertionError("C1 read count");
        if (reads.size() != 1) throw new AssertionError("C1 extra reads");
    }

    static void case2() {
        long base = 0x140000000L;
        long g1 = 0x1000L;
        long obj = 0x2000L;
        long vptr = 0x3000L;
        long target = base + 0x3E098F0L;
        long getterSlot = base + 0x5C6A690L;

        Map<Long, Long> ptrs = new HashMap<>();
        Map<Long, Integer> bytes = new HashMap<>();
        Map<Long, Integer> reads = new HashMap<>();
        List<Long> writes = new ArrayList<>();

        ptrs.put(base + 0x5CB87F8L, g1);
        bytes.put(g1 + 0x161L, 1);
        ptrs.put(base + 0x5C6A688L, obj);
        ptrs.put(obj, vptr);
        ptrs.put(vptr + 0x10L, target);
        ptrs.put(getterSlot, 0L);

        LoadIdlerVirtualGate178.Memory mem = new LoadIdlerVirtualGate178.Memory() {
            @Override public long readPointer(long a) {
                reads.put(a, reads.getOrDefault(a, 0) + 1);
                if (!ptrs.containsKey(a)) throw new AssertionError("Missing readPointer at " + Long.toHexString(a));
                return ptrs.get(a);
            }
            @Override public int readUnsigned8(long a) {
                reads.put(a, reads.getOrDefault(a, 0) + 1);
                if (!bytes.containsKey(a)) throw new AssertionError("Missing readUnsigned8 at " + Long.toHexString(a));
                return bytes.get(a);
            }
            @Override public void writeInt64(long a, long v) {
                writes.add(a);
                ptrs.put(a, v);
            }
        };

        LoadIdlerVirtualGate178.Ports external = new LoadIdlerVirtualGate178.Ports() {
            @Override public long invoke(LoadIdlerRootPublication175.Invocation c) {
                throw new AssertionError("Unexpected external call at " + Long.toHexString(c.siteRva()));
            }
        };

        LoadIdlerVirtualGate178.Ports bound = LoadIdlerWindowValueConsumer178.bind(base, mem, external);
        LoadIdlerVirtualGate178.run3976ac0(base, mem, bound);

        if (reads.get(getterSlot) != 1) throw new AssertionError("C2 getter reads");
        if (writes.size() != 0) throw new AssertionError("C2 writes");
    }

    static void case3() {
        long base = 0x140000000L;
        long g1 = 0x1000L;
        long obj = 0x2000L;
        long vptr = 0x3000L;
        long target = base + 0x3E098F1L;
        long queryTarget = 0x1111222233334444L;
        long tailTarget = 0x5555666677778888L;

        Map<Long, Long> ptrs = new HashMap<>();
        Map<Long, Integer> bytes = new HashMap<>();
        Map<Long, Integer> reads = new HashMap<>();
        List<Long> writes = new ArrayList<>();
        List<LoadIdlerRootPublication175.Invocation> actualCalls = new ArrayList<>();

        ptrs.put(base + 0x5CB87F8L, g1);
        bytes.put(g1 + 0x161L, 1);
        ptrs.put(base + 0x5C6A688L, obj);
        ptrs.put(obj, vptr);
        ptrs.put(vptr + 0x10L, target);
        ptrs.put(base + 0x54D5040L, queryTarget);
        ptrs.put(base + 0x54D50E8L, tailTarget);

        LoadIdlerVirtualGate178.Memory mem = new LoadIdlerVirtualGate178.Memory() {
            @Override public long readPointer(long a) {
                reads.put(a, reads.getOrDefault(a, 0) + 1);
                if (!ptrs.containsKey(a)) throw new AssertionError("Missing readPointer at " + Long.toHexString(a));
                return ptrs.get(a);
            }
            @Override public int readUnsigned8(long a) {
                reads.put(a, reads.getOrDefault(a, 0) + 1);
                if (!bytes.containsKey(a)) throw new AssertionError("Missing readUnsigned8 at " + Long.toHexString(a));
                return bytes.get(a);
            }
            @Override public void writeInt64(long a, long v) {
                writes.add(a);
                ptrs.put(a, v);
            }
        };

        LoadIdlerVirtualGate178.Ports external = new LoadIdlerVirtualGate178.Ports() {
            @Override public long invoke(LoadIdlerRootPublication175.Invocation c) {
                actualCalls.add(c);
                if (c.siteRva() == 0x3976B0DL) return 0x1234567887654321L;
                if (c.siteRva() == 0x3976B1BL) return 1L;
                if (c.siteRva() == 0x3976B33L) return 0L;
                throw new AssertionError("Unknown site " + Long.toHexString(c.siteRva()));
            }
        };

        LoadIdlerVirtualGate178.Ports bound = LoadIdlerWindowValueConsumer178.bind(base, mem, external);
        LoadIdlerVirtualGate178.run3976ac0(base, mem, bound);

        List<LoadIdlerRootPublication175.Invocation> expected = List.of(
            new LoadIdlerRootPublication175.Invocation(0x3976B0DL, target, obj, OptionalLong.of(vptr), false),
            new LoadIdlerRootPublication175.Invocation(0x3976B1BL, queryTarget, 0x1234567887654321L, OptionalLong.empty(), false),
            new LoadIdlerRootPublication175.Invocation(0x3976B33L, tailTarget, 0x1234567887654321L, OptionalLong.of(0L), true)
        );

        if (!actualCalls.equals(expected)) throw new AssertionError("C3 calls mismatch");
        if (reads.get(base + 0x5C6A690L) != null) throw new AssertionError("C3 getter read");
        if (writes.size() != 0) throw new AssertionError("C3 writes");
    }
}
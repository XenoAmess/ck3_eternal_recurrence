package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Fixed normal software scenes; DF=0 and both unknown callees stay opaque. */
public final class GovernmentRegistryGrowth199Witness {
    private static final long B = 0x100000000L;
    private static final long S = 0xA0000008L;
    private static final long RET = 0x3333444455556666L;
    private static final long T = 0x60002000L;
    private static final long CALLBACK = 0x1122334455667788L;
    private static final long CALL_SP = 0x9FFFFFD0L;
    private static final long PUSH_SLOT = 0x9FFFFFC8L;
    private static final VolatileBits INPUT = bits(0x1000, 0xAAAA000011112222L,
            0x60001000L, 0xBBBB000033334444L);
    private static final NonvolatileBits N = new NonvolatileBits(
            0x1111000011110000L, 0x1111000011110001L, 0x1111000011110002L,
            0x1111000011110003L, 0x1111000011110004L, 0x1111000011110005L,
            0x1111000011110006L, 0x1111000011110007L, vector(0x1111000011110008L));
    private static final VolatileBits P1 = bits(0x2000, 0x62000000L,
            0xAAAA111122223333L, 0xBBBB222233334444L);
    private static final VolatileBits P1_ZERO = bits(0x2000, 0,
            0xAAAA111122223333L, 0xBBBB222233334444L);
    private static final VolatileBits P2 = bits(0x3000, 0xDEAD000055556666L,
            0xCCCC333344445555L, 0xDDDD444455556666L);
    private static final VolatileBits P3 = bits(0x4000, 0x63000000L,
            0xEEEE555566667777L, 0xFFFF666677778888L);
    private static final VolatileBits P3_ZERO = bits(0x4000, 0,
            0xEEEE555566667777L, 0xFFFF666677778888L);
    private static final VolatileBits P4 = bits(0x5000, 0xBEEF000077778888L,
            0xABCD777788889999L, 0xBCDE88889999AAAAL);
    private static final List<Long> GROW_SLOTS = List.of(
            0x62000000L, 0x62000008L, 0x62000010L, 0x62000018L,
            0x62000020L, 0x62000028L, 0x62000030L, 0x62000038L,
            0x62000040L, 0x62000048L, 0x62000050L, 0x62000058L,
            0x62000060L, 0x62000068L, 0x62000070L, 0x62000078L,
            0x62000080L, 0x62000088L, 0x62000090L, 0x62000098L,
            0x620000A0L, 0x620000A8L, 0x620000B0L, 0x620000B8L,
            0x620000C0L, 0x620000C8L, 0x620000D0L, 0x620000D8L,
            0x620000E0L, 0x620000E8L, 0x620000F0L, 0x620000F8L);
    private static final List<Long> FALLBACK_SLOTS = List.of(
            0x63000000L, 0x63000008L, 0x63000010L, 0x63000018L);
    private static int assertions;
    private GovernmentRegistryGrowth199Witness() { }

    private static void equal(Object expected, Object actual, String label) {
        assertions++;
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }
    // Mechanical construction of literal register records; no target-state execution here.
    private static VolatileBits v(long rax, long rcx, long rdx, long r8,
            long r9, long r10, long r11, VolatileBits xmm) {
        return new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11,
                xmm.xmm0(), xmm.xmm1(), xmm.xmm2(), xmm.xmm3(), xmm.xmm4(), xmm.xmm5());
    }
    private static NonvolatileBits callN(long capacity, long retainedR14) {
        return new NonvolatileBits(0, 0, 0x61000000L, capacity,
                N.r12Bits(), N.r13Bits(), retainedR14, 0x60001000L, N.xmm6());
    }
    private static TraceMemory seed(long descriptor, long current, long end, long returnRip) {
        TraceMemory m = new TraceMemory();
        m.backing.writeQword(S, returnRip);
        m.backing.writeQword(0x60001000L, 0x60001800L);
        m.backing.writeQword(0x60001800L, descriptor);
        m.backing.writeQword(0x60001008L, 0x60003000L);
        m.backing.writeQword(0x60003000L, CALLBACK);
        m.backing.writeQword(0x10542F0B8L, 0);
        if (descriptor != 0) {
            m.backing.writeQword(T, 0x61000000L);
            m.backing.writeQword(T + 8, current);
            m.backing.writeQword(T + 0x10, end);
        }
        return m;
    }
    private record Event(String operation, long address, long value) { }
    private static Event q(long address, long value) { return new Event("QWORD", address, value); }
    private static List<Event> savedStores() {
        return new ArrayList<>(List.of(q(0xA0000018L, N.rbxBits()),
                q(0xA0000020L, N.rbpBits()), q(0xA0000028L, N.rsiBits()),
                q(0xA0000000L, N.rdiBits()), q(0x9FFFFFF8L, N.r14Bits()),
                q(0x9FFFFFF0L, N.r15Bits())));
    }
    private static void repEvents(List<Event> expected, List<Long> slots) {
        for (long address : slots) {
            expected.add(new Event("BUDGET", address, 0x424DCACL));
            expected.add(q(address, 0));
        }
    }
    private static void descriptorStores(List<Event> expected, long begin, long current, long end) {
        expected.add(q(T, begin)); expected.add(q(T + 8, current)); expected.add(q(T + 0x10, end));
    }
    private static void expectCall(CallScript script, TraceMemory m, long site, long target,
            VolatileBits offered, NonvolatileBits offeredN, VolatileBits post, long pushedReturn) {
        script.expect(new OpaqueCall(site, target, CALL_SP, offered, offeredN), post,
                () -> equal(pushedReturn, m.backing.readQword(PUSH_SLOT),
                        "physical CALL push at " + Long.toHexString(site)));
    }
    private static void verify(String name, TraceMemory m, CallScript script,
            List<Long> slots, List<Event> events, VolatileBits expectedV, long returnRip, boolean consumer) {
        int[] steps = {0};
        GovernmentCrtBoundary185Api.LoopBudget budget = (header, address) -> {
            equal(0x424DCACL, header, name + " REP source header");
            if (steps[0] >= slots.size()) throw new AssertionError(name + " extra budget step");
            equal(slots.get(steps[0]++), address, name + " fixed budget address");
            m.events.add(new Event("BUDGET", address, header));
        };
        if (consumer) {
            var bound = GovernmentRegistryGrowth199Calls.bind(B, m, script, budget);
            VolatileBits actual = bound.invoke(new OpaqueCall(0x424DB58L, 0x424DBB0L,
                    0xA0000010L, INPUT, N));
            equal(expectedV, actual, name + " complete consumer post V/XMM");
        } else {
            GovernmentCallee164Api.NormalReturn actual = GovernmentRegistryGrowth199.execute(
                    new GovernmentCallee164Api.Entry(B, S, INPUT, N), m, script, budget);
            equal(new GovernmentCallee164Api.NormalReturn(expectedV, N, returnRip, 0xA0000010L),
                    actual, name + " complete V/N/XMM/RIP/SP");
        }
        equal(events, m.events, name + " all stores and before-store budget order");
        equal(slots.size(), steps[0], name + " exact REP count");
        script.done(0);
        equal(returnRip, m.backing.readQword(S), name + " actual return slot");
        equal(N.rbxBits(), m.backing.readQword(0xA0000018L), name + " saved RBX home");
        equal(N.rbpBits(), m.backing.readQword(0xA0000020L), name + " saved RBP home");
        equal(N.rsiBits(), m.backing.readQword(0xA0000028L), name + " saved RSI home");
        equal(N.rdiBits(), m.backing.readQword(0xA0000000L), name + " saved RDI");
        equal(N.r14Bits(), m.backing.readQword(0x9FFFFFF8L), name + " saved R14");
        equal(N.r15Bits(), m.backing.readQword(0x9FFFFFF0L), name + " saved R15");
        equal(0x60001800L, m.backing.readQword(0x60001000L), name + " original descriptor pointer cell");
        equal(0x60003000L, m.backing.readQword(0x60001008L), name + " original callback pointer cell");
        equal(CALLBACK, m.backing.readQword(0x60003000L), name + " callback source retained");
        equal(0L, m.backing.readQword(0x10542F0B8L), name + " cookie retained");
        equal(0, m.backing.atomicDwords.size(), name + " no atomic effects");
        equal(0, m.backing.atomicBytes.size(), name + " no atomic byte effects");
    }
    private static void descriptor(TraceMemory m, long begin, long current, long end, String name) {
        equal(T, m.backing.readQword(0x60001800L), name + " descriptor identity");
        equal(begin, m.backing.readQword(T), name + " begin");
        equal(current, m.backing.readQword(T + 8), name + " current");
        equal(end, m.backing.readQword(T + 0x10), name + " end");
    }
    private static void nullScene() {
        TraceMemory m = seed(0, 0, 0, RET);
        verify("NULL", m, new CallScript(0x9192939495969798L), List.of(), savedStores(),
                v(0xFFFFFFFFL, 0x60001000L, 0xBBBB000033334444L,
                        0x1008, 0x1009, 0x100A, 0x100B, INPUT), RET, false);
        equal(0L, m.backing.readQword(0x60001800L), "NULL remains null");
    }
    private static void capacityScene() {
        TraceMemory m = seed(T, 0x61000008L, 0x61000020L, RET);
        List<Event> events = savedStores();
        events.add(q(0x61000008L, CALLBACK));
        descriptorStores(events, 0x61000000L, 0x61000010L, 0x61000020L);
        verify("CAPACITY", m, new CallScript(0x9192939495969798L), List.of(), events,
                v(0, T, 0, 0x40, 0x61000008L, 0, 0x100B, INPUT), RET, false);
        descriptor(m, 0x61000000L, 0x61000010L, 0x61000020L, "CAPACITY");
        equal(CALLBACK, m.backing.readQword(0x61000008L), "CAPACITY appended callback");
    }
    private static void growScene(boolean consumer) {
        long returnRip = consumer ? 0x10424DB5DL : RET;
        TraceMemory m = seed(T, 0x61000000L, 0x61000000L, returnRip);
        CallScript script = new CallScript(0x9192939495969798L);
        expectCall(script, m, 0x424DC3EL, 0x425B804L,
                v(0x20, 0x61000000L, 0x20, 8, 0x61000000L, 0, 0x100B, INPUT),
                callN(0x20, 0x1111000011110006L), P1, 0x10424DC43L);
        expectCall(script, m, 0x424DC48L, 0x424E364L,
                v(0x62000000L, 0, 0xBBBB222233334444L, 0x2008, 0x2009, 0x200A, 0x200B, P1),
                callN(0x20, 0x62000000L), P2, 0x10424DC4DL);
        List<Event> events = savedStores();
        events.add(q(PUSH_SLOT, 0x10424DC43L)); events.add(q(PUSH_SLOT, 0x10424DC4DL));
        repEvents(events, GROW_SLOTS);
        events.add(q(0x62000000L, CALLBACK));
        descriptorStores(events, 0x62000000L, 0x62000008L, 0x62000100L);
        String name = consumer ? "CONSUMER_GROW" : "GROW";
        verify(name, m, script, GROW_SLOTS, events,
                v(0, T, 0, 0x40, 0x62000000L, 0, 0x300B, P2), returnRip, consumer);
        descriptor(m, 0x62000000L, 0x62000008L, 0x62000100L, name);
        for (int i = 0; i < GROW_SLOTS.size(); i++) {
            equal(i == 0 ? CALLBACK : 0L, m.backing.readQword(GROW_SLOTS.get(i)), name + " fixed slot " + i);
        }
    }
    private static void fallbackScene() {
        TraceMemory m = seed(T, 0x61000000L, 0x61000000L, RET);
        CallScript script = new CallScript(0x9192939495969798L);
        expectCall(script, m, 0x424DC3EL, 0x425B804L,
                v(0x20, 0x61000000L, 0x20, 8, 0x61000000L, 0, 0x100B, INPUT),
                callN(0x20, 0x1111000011110006L), P1_ZERO, 0x10424DC43L);
        expectCall(script, m, 0x424DC48L, 0x424E364L,
                v(0, 0, 0xBBBB222233334444L, 0x2008, 0x2009, 0x200A, 0x200B, P1_ZERO),
                callN(0x20, 0), P2, 0x10424DC4DL);
        expectCall(script, m, 0x424DC62L, 0x425B804L,
                v(0xDEAD000055556666L, 0x61000000L, 4, 8, 0x3009, 0x300A, 0x300B, P2),
                callN(4, 0), P3, 0x10424DC67L);
        expectCall(script, m, 0x424DC6CL, 0x424E364L,
                v(0x63000000L, 0, 0xFFFF666677778888L, 0x4008, 0x4009, 0x400A, 0x400B, P3),
                callN(4, 0x63000000L), P4, 0x10424DC71L);
        List<Event> events = savedStores();
        events.add(q(PUSH_SLOT, 0x10424DC43L)); events.add(q(PUSH_SLOT, 0x10424DC4DL));
        events.add(q(PUSH_SLOT, 0x10424DC67L)); events.add(q(PUSH_SLOT, 0x10424DC71L));
        repEvents(events, FALLBACK_SLOTS);
        events.add(q(0x63000000L, CALLBACK));
        descriptorStores(events, 0x63000000L, 0x63000008L, 0x63000020L);
        verify("FALLBACK", m, script, FALLBACK_SLOTS, events,
                v(0, T, 0, 0x40, 0x63000000L, 0, 0x500B, P4), RET, false);
        descriptor(m, 0x63000000L, 0x63000008L, 0x63000020L, "FALLBACK");
        for (int i = 0; i < FALLBACK_SLOTS.size(); i++) {
            equal(i == 0 ? CALLBACK : 0L, m.backing.readQword(FALLBACK_SLOTS.get(i)), "FALLBACK fixed slot " + i);
        }
    }
    private static void bothAllocationsFailScene() {
        TraceMemory m = seed(T, 0x61000000L, 0x61000000L, RET);
        CallScript script = new CallScript(0x9192939495969798L);
        expectCall(script, m, 0x424DC3EL, 0x425B804L,
                v(0x20, 0x61000000L, 0x20, 8, 0x61000000L, 0, 0x100B, INPUT),
                callN(0x20, 0x1111000011110006L), P1_ZERO, 0x10424DC43L);
        expectCall(script, m, 0x424DC48L, 0x424E364L,
                v(0, 0, 0xBBBB222233334444L, 0x2008, 0x2009, 0x200A, 0x200B, P1_ZERO),
                callN(0x20, 0), P2, 0x10424DC4DL);
        expectCall(script, m, 0x424DC62L, 0x425B804L,
                v(0xDEAD000055556666L, 0x61000000L, 4, 8, 0x3009, 0x300A, 0x300B, P2),
                callN(4, 0), P3_ZERO, 0x10424DC67L);
        expectCall(script, m, 0x424DC6CL, 0x424E364L,
                v(0, 0, 0xFFFF666677778888L, 0x4008, 0x4009, 0x400A, 0x400B, P3_ZERO),
                callN(4, 0), P4, 0x10424DC71L);
        List<Event> events = savedStores();
        events.add(q(PUSH_SLOT, 0x10424DC43L)); events.add(q(PUSH_SLOT, 0x10424DC4DL));
        events.add(q(PUSH_SLOT, 0x10424DC67L)); events.add(q(PUSH_SLOT, 0x10424DC71L));
        verify("FAIL_BOTH", m, script, List.of(), events,
                v(0xFFFFFFFFL, 0xABCD777788889999L, 0xBCDE88889999AAAAL,
                        0x5008, 0x5009, 0x500A, 0x500B, P4), RET, false);
        descriptor(m, 0x61000000L, 0x61000000L, 0x61000000L, "FAIL_BOTH");
    }
    public static void main(String[] args) {
        assertions = 0;
        if (args.length == 0) {
            nullScene(); capacityScene(); growScene(false); fallbackScene(); bothAllocationsFailScene();
            System.out.println("OK: 5 new literal normal growth scenes; " + assertions + " explicit assertions; DF0, two callees opaque");
        } else if (args.length == 1 && args[0].equals("consumer-grow")) {
            growScene(true);
            System.out.println("OK: 1 new already-pushed DB58 consumer GROW; " + assertions + " explicit assertions");
        } else {
            throw new IllegalArgumentException("no arguments, or consumer-grow");
        }
    }
    /** A small method-call observer over the existing fixture memory, not a CPU or target model. */
    private static final class TraceMemory implements GovernmentPrimaryTail155Api.Memory {
        final MemoryImage backing = new MemoryImage();
        final List<Event> events = new ArrayList<>();
        @Override public int readDword(long address) { return backing.readDword(address); }
        @Override public long readQword(long address) { return backing.readQword(address); }
        @Override public int readUnsignedByte(long address) { return backing.readUnsignedByte(address); }
        @Override public void writeDword(long address, int value) {
            events.add(new Event("DWORD", address, Integer.toUnsignedLong(value))); backing.writeDword(address, value);
        }
        @Override public int lockedXaddDword(long address, int addend) {
            events.add(new Event("XADD32", address, addend)); return backing.lockedXaddDword(address, addend);
        }
        @Override public void writeQword(long address, long value) {
            events.add(q(address, value)); backing.writeQword(address, value);
        }
        @Override public void writeByte(long address, int value) {
            events.add(new Event("BYTE", address, value & 255)); backing.writeByte(address, value);
        }
        @Override public Bits128 read128(long address) { return backing.read128(address); }
        @Override public void write128(long address, Bits128 value) {
            events.add(new Event("128LOW", address, value.lowBits()));
            events.add(new Event("128HIGH", address + 8, value.highBits())); backing.write128(address, value);
        }
    }
}

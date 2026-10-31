package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentCallee164Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.CallScript;
import org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.MemoryImage;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.bits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.vector;

/** Independent fixed normal inputs. All four deep callees remain full-V owned-memory ports. */
public final class GovernmentRegistryResize201Witness {
    private static final long B = 0x100000000L;
    private static final long S = 0xB0000008L;
    private static final long RET = 0x1234567876543210L;
    private static final long CALL_SP = 0xAFFFFFE0L;
    private static final long PUSH_SLOT = 0xAFFFFFD8L;
    private static final NonvolatileBits N = new NonvolatileBits(
            0x1111000011110000L, 0x1111000011110001L, 0x1111000011110002L,
            0x1111000011110003L, 0x1111000011110004L, 0x1111000011110005L,
            0x1111000011110006L, 0x1111000011110007L, vector(0x1111000011110008L));
    private static final VolatileBits INPUT_XMM = bits(0x1000, 0, 0, 0);
    private static final VolatileBits E = bits(0x2000, 0x60004000L,
            0xAAAA111122223333L, 0xBBBB222233334444L);
    private static final VolatileBits A = bits(0x3000, 0x70001000L,
            0xCCCC333344445555L, 0xDDDD444455556666L);
    private static final VolatileBits C = bits(0x4000, 0xDEAD000055556666L,
            0xEEEE555566667777L, 0xFFFF666677778888L);
    private static final VolatileBits OLD = bits(0x5000, 16,
            0xABCD777788889999L, 0xBCDE88889999AAAAL);
    private static final VolatileBits NEW = bits(0x6000, 0x70002000L,
            0xCDEF9999AAAABBBBL, 0xDEF0AAAABBBBCCCCL);
    private static final VolatileBits FAIL = bits(0x7000, 0,
            0xEFE1BBBBCCCCDDDDL, 0xF0F2CCCCDDDDEEEEL);
    private static final VolatileBits ODD_SIZE = bits(0x8000, 32,
            0x1020304050607080L, 0x2030405060708090L);
    private static final VolatileBits ODD_ALLOC = bits(0x9000, 0x70003000L,
            0x30405060708090A0L, 0x405060708090A0B0L);
    private static int assertions;
    private GovernmentRegistryResize201Witness() { }
    private static void equal(Object expected, Object actual, String label) {
        assertions++;
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(label + " expected=" + expected + " actual=" + actual);
        }
    }
    // Literal record assembly only; this helper performs no original instruction semantics.
    private static VolatileBits v(long rax, long rcx, long rdx, long r8,
            long r9, long r10, long r11, VolatileBits xmm) {
        return new VolatileBits(rax, rcx, rdx, r8, r9, r10, r11,
                xmm.xmm0(), xmm.xmm1(), xmm.xmm2(), xmm.xmm3(), xmm.xmm4(), xmm.xmm5());
    }
    private static VolatileBits input(long ptr, long count, long element) {
        return v(0xAAAA000011112222L, ptr, count, element, 0x9999AAAABBBBCCCCL,
                0xAAAABBBBCCCCDDDDL, 0xBBBBCCCCDDDDEEEEL, INPUT_XMM);
    }
    private static NonvolatileBits n(long rbx, long rbp, long rsi, long rdi) {
        return new NonvolatileBits(rbx, rbp, rsi, rdi, N.r12Bits(), N.r13Bits(),
                N.r14Bits(), N.r15Bits(), N.xmm6());
    }
    private record Event(String operation, long address, long value) { }
    private static Event q(long address, long value) { return new Event("QWORD", address, value); }
    private static TraceMemory seed(long returnRip) {
        TraceMemory m = new TraceMemory();
        m.backing.writeQword(S, returnRip);
        return m;
    }
    private static List<Event> savedStores() {
        return new ArrayList<>(List.of(q(0xB0000010L, N.rbxBits()),
                q(0xB0000018L, N.rbpBits()), q(0xB0000020L, N.rsiBits()),
                q(0xB0000000L, N.rdiBits())));
    }
    private static void expect(CallScript script, TraceMemory m, long site, long target,
            VolatileBits offered, NonvolatileBits offeredN, VolatileBits post,
            long physicalReturn, Runnable controlledMemoryInput) {
        script.expect(new OpaqueCall(site, target, CALL_SP, offered, offeredN), post, () -> {
            equal(physicalReturn, m.backing.readQword(PUSH_SLOT), "physical CALL at " + Long.toHexString(site));
            controlledMemoryInput.run();
        });
    }
    private static void verify(String name, TraceMemory m, VolatileBits entryV,
            CallScript script, List<Event> events, VolatileBits expectedV, long returnRip, boolean consumer) {
        if (consumer) {
            var bound = GovernmentRegistryResize201Calls.bind(B, m, script);
            VolatileBits actual = bound.invoke(new OpaqueCall(0x424DC3EL, 0x425B804L,
                    0xB0000010L, entryV, N));
            equal(expectedV, actual, name + " complete consumer V/XMM");
        } else {
            var actual = GovernmentRegistryResize201.execute(
                    new GovernmentCallee164Api.Entry(B, S, entryV, N), m, script);
            equal(new GovernmentCallee164Api.NormalReturn(expectedV, N, returnRip, 0xB0000010L),
                    actual, name + " complete V/N/XMM/RIP/SP");
        }
        equal(events, m.events, name + " exact source stores plus controlled port stores");
        equal(List.of(0xB0000010L, 0xB0000018L, 0xB0000020L, 0xB0000000L, S),
                m.qwordReads, name + " exact saved-register and actual RET reads");
        script.done(0);
        equal(returnRip, m.backing.readQword(S), name + " original return retained");
        equal(N.rbxBits(), m.backing.readQword(0xB0000010L), name + " saved RBX");
        equal(N.rbpBits(), m.backing.readQword(0xB0000018L), name + " saved RBP");
        equal(N.rsiBits(), m.backing.readQword(0xB0000020L), name + " saved RSI");
        equal(N.rdiBits(), m.backing.readQword(0xB0000000L), name + " saved RDI");
        equal(0, m.backing.atomicDwords.size(), name + " no atomic effects");
        equal(0, m.backing.atomicBytes.size(), name + " no byte atomics");
    }
    private static void overflow() {
        TraceMemory m = seed(RET);
        m.backing.writeQword(0x60004000L, 0xAABBCCDD11223344L);
        CallScript script = new CallScript(0x9192939495969798L);
        expect(script, m, 0x425B834L, 0x423B18CL,
                v(0x7FFFFFFFFFFFFFF0L, 0x60001000L, 0, 0x7FFFFFFFFFFFFFF1L,
                        0x9999AAAABBBBCCCCL, 0xAAAABBBBCCCCDDDDL, 0xBBBBCCCCDDDDEEEEL, INPUT_XMM),
                n(2, 0x7FFFFFFFFFFFFFF1L, 0x60001000L, N.rdiBits()), E, 0x10425B839L, () -> { });
        List<Event> events = savedStores();
        events.add(q(PUSH_SLOT, 0x10425B839L)); events.add(new Event("DWORD", 0x60004000L, 12));
        verify("OVERFLOW", m, input(0x60001000L, 2, 0x7FFFFFFFFFFFFFF1L), script, events,
                v(0, E.rcxBits(), E.rdxBits(), E.r8Bits(), E.r9Bits(), E.r10Bits(), E.r11Bits(), E), RET, false);
        equal(0xAABBCCDD0000000CL, m.backing.readQword(0x60004000L), "DWORD errno12 preserves high padding");
    }
    private static void nullGrow(boolean consumer) {
        long returnRip = consumer ? 0x10424DC43L : RET;
        TraceMemory m = seed(returnRip);
        for (int i = 0; i < 32; i++) m.backing.writeByte(0x70001000L + i, 0xA0 + i);
        m.backing.writeByte(0x70000FFFL, 0x5A); m.backing.writeByte(0x70001020L, 0x6B);
        CallScript script = new CallScript(0x9192939495969798L);
        expect(script, m, 0x425B85EL, 0x4251F4CL,
                v(0x3FFFFFFFFFFFFFF8L, 0, 0x20, 8, 0x9999AAAABBBBCCCCL,
                        0xAAAABBBBCCCCDDDDL, 0xBBBBCCCCDDDDEEEEL, INPUT_XMM),
                n(0x20, 8, 0, 0), A, 0x10425B863L, () -> { });
        expect(script, m, 0x425B87CL, 0x4226F10L,
                v(0x70001000L, 0x70001000L, 0, 0x20, 0x3009, 0x300A, 0x300B, A),
                n(0x20, 8, 0x70001000L, 0), C, 0x10425B881L, () -> {
                    // Frozen owned port input, not an implementation or native result of 4226F10.
                    for (int i = 0; i < 32; i++) m.writeByte(0x70001000L + i, 0);
                });
        List<Event> events = savedStores();
        events.add(q(PUSH_SLOT, 0x10425B863L)); events.add(q(PUSH_SLOT, 0x10425B881L));
        for (int i = 0; i < 32; i++) events.add(new Event("BYTE", 0x70001000L + i, 0));
        String name = consumer ? "CONSUMER_NULL_GROW" : "NULL_GROW";
        verify(name, m, input(0, 4, 8), script, events,
                v(0x70001000L, C.rcxBits(), C.rdxBits(), C.r8Bits(), C.r9Bits(), C.r10Bits(), C.r11Bits(), C),
                returnRip, consumer);
        for (int i = 0; i < 32; i++) equal(0, m.backing.readUnsignedByte(0x70001000L + i), name + " controlled byte " + i);
        equal(0x5A, m.backing.readUnsignedByte(0x70000FFFL), name + " preceding byte retained");
        equal(0x6B, m.backing.readUnsignedByte(0x70001020L), name + " following byte retained");
    }
    private static void shrink() {
        TraceMemory m = seed(RET);
        CallScript script = new CallScript(0x9192939495969798L);
        expect(script, m, 0x425B848L, 0x4259250L,
                v(0xFFFFFFFFFFFFFFE0L, 0x60002000L, 0, 8, 0x9999AAAABBBBCCCCL,
                        0xAAAABBBBCCCCDDDDL, 0xBBBBCCCCDDDDEEEEL, INPUT_XMM),
                n(1, 8, 0x60002000L, N.rdiBits()), OLD, 0x10425B84DL, () -> { });
        expect(script, m, 0x425B85EL, 0x4251F4CL,
                v(16, 0x60002000L, 8, 0x5008, 0x5009, 0x500A, 0x500B, OLD),
                n(8, 8, 0x60002000L, 16), NEW, 0x10425B863L, () -> { });
        List<Event> events = savedStores();
        events.add(q(PUSH_SLOT, 0x10425B84DL)); events.add(q(PUSH_SLOT, 0x10425B863L));
        verify("SHRINK", m, input(0x60002000L, 1, 8), script, events, NEW, RET, false);
    }
    private static void allocFail() {
        TraceMemory m = seed(RET);
        CallScript script = new CallScript(0x9192939495969798L);
        expect(script, m, 0x425B85EL, 0x4251F4CL,
                v(0xFFFFFFFFFFFFFFE0L, 0, 8, 8, 0x9999AAAABBBBCCCCL,
                        0xAAAABBBBCCCCDDDDL, 0xBBBBCCCCDDDDEEEEL, INPUT_XMM),
                n(8, 8, 0, 0), FAIL, 0x10425B863L, () -> { });
        List<Event> events = savedStores(); events.add(q(PUSH_SLOT, 0x10425B863L));
        verify("ALLOC_FAIL", m, input(0, 1, 8), script, events, FAIL, RET, false);
    }
    private static void oddShrink() {
        TraceMemory m = seed(RET);
        CallScript script = new CallScript(0x9192939495969798L);
        expect(script, m, 0x425B848L, 0x4259250L,
                v(0x555555555555554AL, 0x60003000L, 2, 8, 0x9999AAAABBBBCCCCL,
                        0xAAAABBBBCCCCDDDDL, 0xBBBBCCCCDDDDEEEEL, INPUT_XMM),
                n(3, 8, 0x60003000L, N.rdiBits()), ODD_SIZE, 0x10425B84DL, () -> { });
        expect(script, m, 0x425B85EL, 0x4251F4CL,
                v(32, 0x60003000L, 24, 0x8008, 0x8009, 0x800A, 0x800B, ODD_SIZE),
                n(24, 8, 0x60003000L, 32), ODD_ALLOC, 0x10425B863L, () -> { });
        List<Event> events = savedStores();
        events.add(q(PUSH_SLOT, 0x10425B84DL)); events.add(q(PUSH_SLOT, 0x10425B863L));
        verify("ODD_SHRINK", m, input(0x60003000L, 3, 8), script, events, ODD_ALLOC, RET, false);
    }
    public static void main(String[] args) {
        assertions = 0;
        if (args.length == 0) {
            overflow(); nullGrow(false); shrink(); allocFail(); oddShrink();
            System.out.println("OK: 5 independent literal resize normal scenes; " + assertions + " explicit assertions; four deep callees opaque");
        } else if (args.length == 1 && args[0].equals("consumer-null-grow")) {
            nullGrow(true);
            System.out.println("OK: 1 already-pushed DC3E consumer NULL_GROW; " + assertions + " explicit assertions");
        } else {
            throw new IllegalArgumentException("no arguments, or consumer-null-grow");
        }
    }
    /** Only observes methods on the pre-existing fixture memory; no CPU or callee algorithm. */
    private static final class TraceMemory implements GovernmentPrimaryTail155Api.Memory {
        final MemoryImage backing = new MemoryImage();
        final List<Event> events = new ArrayList<>();
        final List<Long> qwordReads = new ArrayList<>();
        @Override public int readDword(long address) { return backing.readDword(address); }
        @Override public long readQword(long address) { qwordReads.add(address); return backing.readQword(address); }
        @Override public int readUnsignedByte(long address) { return backing.readUnsignedByte(address); }
        @Override public void writeDword(long address, int value) {
            events.add(new Event("DWORD", address, Integer.toUnsignedLong(value))); backing.writeDword(address, value);
        }
        @Override public int lockedXaddDword(long address, int addend) {
            events.add(new Event("XADD32", address, addend)); return backing.lockedXaddDword(address, addend);
        }
        @Override public void writeQword(long address, long value) { events.add(q(address, value)); backing.writeQword(address, value); }
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

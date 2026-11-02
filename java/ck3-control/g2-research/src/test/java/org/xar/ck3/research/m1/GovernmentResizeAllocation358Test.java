package org.xar.ck3.research.m1;

import static org.junit.jupiter.api.Assertions.*;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import org.junit.jupiter.api.Test;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Call;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Calls;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Entry;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.NormalReturn;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.Tail;
import org.xar.ck3.research.m5.GovernmentCrtBoundary185Api.TargetKind;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import static org.xar.ck3.research.m1.GovernmentSharedComposition168Fixture.*;

/** New represented B85E->Base203->F64->FDA0 consumption; opaque heap port, never an OS/Game claim. */
class GovernmentResizeAllocation358Test {
    private static final long IMAGE = 0x180000000L;
    private static final long PRE = 0x100100L;
    private static final long HEAP_SLOT = IMAGE + 0x5C5DE30L;
    private static final long IAT_SLOT = IMAGE + 0x43DA768L;
    private static final NonvolatileBits N = new NonvolatileBits(0x711, 0x722, 0x733, 0x744,
            0x755, 0x766, 0x777, 0x788, new Bits128(0x12345678, 0x87654321));

    @Test void matchedParentConsumesAllocatorWithExactFramesFreshIatAndAllRepresentedVolatileBits() {
        var memory = new Memory();
        long firstHeap = 0xA100, secondHeap = 0xA200;
        long firstIat = 0x7FF00011L, secondIat = 0x7FF00022L;
        memory.writeQword(HEAP_SLOT, firstHeap); memory.writeQword(IAT_SLOT, firstIat);
        var calls = new ArrayList<Call>();
        var returns = List.of(bits(0xDD000, 0xC100, 0xC211, 0xC322), bits(0xEE000, 0xD100, 0xD211, 0xD322));
        Calls fallback = new NoCalls() {
            @Override public VolatileBits invoke(Call call) {
                int index = calls.size(); assertTrue(index < 2);
                long pre = PRE + index * 0x400L;
                long size = index == 0 ? 37 : 0;
                long effective = size == 0 ? 1 : size;
                VolatileBits incoming = bits(0x100 + index * 0x100, 0x1111, 0, size);
                var expected = fields(incoming, 1, index == 0 ? firstHeap : secondHeap, 0, effective, incoming.xmm0());
                assertEquals(new Call(0x424FDDEL, TargetKind.INDIRECT_ABSOLUTE, index == 0 ? firstIat : secondIat,
                        pre - 0x60, expected, workingN(effective)), call);
                assertEquals(IMAGE + 0x425B863L, memory.readQword(pre - 8));
                assertEquals(IMAGE + 0x4251F69L, memory.readQword(pre - 0x38));
                assertEquals(IMAGE + 0x424FDE4L, memory.readQword(pre - 0x68));
                assertEquals(size, memory.readQword(pre - 0x40));
                assertEquals(N.rbxBits(), memory.readQword(pre));
                assertEquals(N.rdiBits(), memory.readQword(pre - 0x10));
                calls.add(call);
                memory.writeQword(HEAP_SLOT, secondHeap); memory.writeQword(IAT_SLOT, secondIat);
                return returns.get(index);
            }
        };
        var bound = GovernmentResizeBase203Calls.bind(IMAGE, memory, fallback,
                (header, address) -> fail("successful new allocation has no retry budget step"));
        for (int index = 0; index < 2; index++) {
            long pre = PRE + index * 0x400L;
            memory.writeQword(pre - 8, IMAGE + 0x425B863L);
            VolatileBits input = bits(0x100 + index * 0x100, 0x1111, 0, index == 0 ? 37 : 0);
            var output = bound.invoke(new Call(0x425B85EL, TargetKind.DIRECT_RVA, 0x4251F4CL, pre, input, N));
            assertEquals(returns.get(index), output, "all7GPR+XMM0..5 survive the real nested epilogues");
            assertEquals(N.rbxBits(), memory.readQword(pre));
            assertEquals(N.rdiBits(), memory.readQword(pre - 0x10));
        }
        assertEquals(2, calls.size());
        assertTrue(calls.stream().noneMatch(call -> call.callSiteRva() == 0x4251F64L), "F64 itself is now consumed");
        assertEquals(secondHeap, memory.readQword(HEAP_SLOT));
        assertEquals(secondIat, memory.readQword(IAT_SLOT));
    }

    @Test void unmatchedOuterFramesDelegateIdenticallyAndOwnedReturnOrSavedNCorruptionStillRejects() {
        var memory = new Memory();
        var seen = new ArrayList<Call>();
        var transfers = new ArrayList<Tail>();
        var gs = new AtomicInteger();
        var post = bits(0x33000, 0xABCD, 0x123, 0x456);
        var returned = new NormalReturn(post, 0x444, 0x555, N);
        Calls fallback = new NoCalls() {
            @Override public VolatileBits invoke(Call call) { seen.add(call); return post; }
            @Override public NormalReturn tail(Tail transfer) { transfers.add(transfer); return returned; }
            @Override public long readGsQword58() { gs.incrementAndGet(); return 0x99887766; }
        };
        var bound = GovernmentResizeBase203Calls.bind(IMAGE, memory, fallback, (header, address) -> fail());
        var v = bits(0x1200, 0x11, 0, 37);
        var unmatched = List.of(
                new Call(0x425B85EL, TargetKind.DIRECT_RVA, 0x4251F4DL, PRE, v, N),
                new Call(0x425B85FL, TargetKind.DIRECT_RVA, 0x4251F4CL, PRE, v, N),
                new Call(0x425B85EL, TargetKind.INDIRECT_ABSOLUTE, 0x4251F4CL, PRE, v, N),
                new Call(0x4251F64L, TargetKind.DIRECT_RVA, 0x424FDA0L, PRE, v, N));
        int initialWrites = memory.writes;
        for (var call : unmatched) {
            assertSame(post, bound.invoke(call));
            assertSame(call, seen.get(seen.size() - 1));
        }
        assertEquals(unmatched.size(), seen.size());
        assertEquals(initialWrites, memory.writes, "unmatched callers never enter either prologue");
        assertEquals(0, memory.reads, "even a top-level exact inner F64 must remain opaque here");
        var transfer = new Tail(0xDEAD, TargetKind.INDIRECT_ABSOLUTE, 0xBEEF, new Entry(IMAGE, PRE, v, N));
        assertSame(returned, bound.tail(transfer)); assertSame(transfer, transfers.getFirst());
        assertEquals(0x99887766, bound.readGsQword58()); assertEquals(1, gs.get());

        // Literal owned slots from the two held prologues and CALL pushes, not an emulator of either body.
        for (long corruptedSlot : List.of(PRE - 8, PRE - 0x38, PRE - 0x40, PRE, PRE - 0x10)) {
            var owned = new Memory();
            owned.writeQword(PRE - 8, IMAGE + 0x425B863L);
            owned.writeQword(HEAP_SLOT, 0xA100); owned.writeQword(IAT_SLOT, 0x7FF00011L);
            var actualCalls = new AtomicInteger();
            Calls tamperingPort = new NoCalls() {
                @Override public VolatileBits invoke(Call call) {
                    assertEquals(0x424FDDEL, call.callSiteRva());
                    actualCalls.incrementAndGet();
                    owned.writeQword(corruptedSlot, 0xBAD0BAD0L);
                    return post;
                }
            };
            var checked = GovernmentResizeBase203Calls.bind(IMAGE, owned, tamperingPort, (header, address) -> fail());
            assertThrows(UnsupportedOperationException.class,
                    () -> checked.invoke(new Call(0x425B85EL, TargetKind.DIRECT_RVA, 0x4251F4CL, PRE, v, N)));
            assertEquals(1, actualCalls.get());
        }
    }

    private static NonvolatileBits workingN(long size) {
        return new NonvolatileBits(size, N.rbpBits(), N.rsiBits(), 0,
                N.r12Bits(), N.r13Bits(), N.r14Bits(), N.r15Bits(), N.xmm6());
    }
    private static class NoCalls implements Calls {
        @Override public VolatileBits invoke(Call call) { throw new AssertionError("unexpected opaque call " + call); }
        @Override public NormalReturn tail(Tail transfer) { throw new AssertionError("unexpected tail " + transfer); }
        @Override public long readGsQword58() { throw new AssertionError("unexpected GS read"); }
    }
    /** Mechanical shared owned-byte-memory fixture adapter, no target instructions/expected-state algorithm. */
    private static final class Memory implements GovernmentCrtBoundary185Api.Memory {
        final MemoryImage bytes = new MemoryImage();
        int writes, reads;
        @Override public int readDword(long address) { reads++; return bytes.readDword(address); }
        @Override public long readQword(long address) { reads++; return bytes.readQword(address); }
        @Override public int readUnsignedByte(long address) { reads++; return bytes.readUnsignedByte(address); }
        @Override public void writeDword(long address, int value) { writes++; bytes.writeDword(address, value); }
        @Override public int lockedXaddDword(long address, int value) { writes++; return bytes.lockedXaddDword(address, value); }
        @Override public void writeQword(long address, long value) { writes++; bytes.writeQword(address, value); }
        @Override public void writeByte(long address, int value) { writes++; bytes.writeByte(address, value); }
        @Override public Bits128 read128(long address) { reads++; return bytes.read128(address); }
        @Override public void write128(long address, Bits128 value) { writes++; bytes.write128(address, value); }
    }
}

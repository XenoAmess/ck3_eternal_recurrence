package org.xar.ck3.research.m1;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.Bits128;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.NonvolatileBits;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.OpaqueCall;
import org.xar.ck3.research.m5.GovernmentPrimaryTail155Api.VolatileBits;
import org.xar.ck3.research.m5.GovernmentSharedManager167Api;

/** One normal owned call, with fixed expectations from the 15B/72B originals. */
public final class GovernmentRegistryForward185Witness {
    private GovernmentRegistryForward185Witness() { }
    private static int assertions;
    private static void equal(Object expected, Object actual, String what) {
        assertions++;
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(what + " expected=" + expected + " actual=" + actual);
        }
    }
    public static void main(String[] args) {
        long base = 0x1_0000_0000L;
        long stack = 0x70000008L;
        long parentStack = stack + 8;
        long parentReturn = base + 0x4223F00L;
        long subject = 0x4455667788990011L;
        var memory = new ObservedMemory();
        memory.writeQword(stack, parentReturn);
        memory.writeQword(stack - 0x28, 0xAABBCCDD11223344L);
        memory.writeQword(stack + 0x20, 0x5566778811223344L);
        memory.reads.clear();
        memory.writes.clear();
        VolatileBits input = GovernmentSharedComposition168Fixture.bits(0x1000, 0x101, subject, 0x103);
        NonvolatileBits incoming = new NonvolatileBits(subject, 0x1234567887654321L,
                0x201, 0x202, 0xABCDEF0000000203L, 0x204, 0x205, 0x206,
                GovernmentSharedComposition168Fixture.vector(0x207));
        VolatileBits callbackEntry = new VolatileBits(2, stack + 0x18, stack - 0x28,
                stack - 0x20, stack + 0x20, input.r10Bits(), input.r11Bits(),
                input.xmm0(), input.xmm1(), input.xmm2(), input.xmm3(), input.xmm4(), input.xmm5());
        NonvolatileBits callbackN = new NonvolatileBits(subject, stack - 8,
                incoming.rsiBits(), incoming.rdiBits(), incoming.r12Bits(), incoming.r13Bits(),
                incoming.r14Bits(), incoming.r15Bits(), incoming.xmm6());
        VolatileBits post = GovernmentSharedComposition168Fixture.bits(0x9000, 0x901, 0x902, 0x903);
        var script = new GovernmentSharedComposition168Fixture.CallScript(0x8877665544332211L);
        script.expect(new OpaqueCall(0x424DF29L, 0x424DB38L, stack - 0x48,
                callbackEntry, callbackN), post, () -> {
            equal(List.of(), memory.reads, "no early RET or invented tail CALL read");
            equal(List.of(stack + 0x10, stack + 8, stack - 8, stack - 0x20,
                    stack - 0x18, stack - 0x50), memory.writes, "actual six qword stores");
            equal(base + 0x5C5D698L, memory.backing.readQword(stack + 8), "LEA static RCX home");
            equal(subject, memory.backing.readQword(stack + 0x10), "old full64 RCX becomes RDX home");
            equal(stack + 8, memory.backing.readQword(stack - 0x20), "first local pointer");
            equal(stack + 0x10, memory.backing.readQword(stack - 0x18), "second local pointer");
            equal(base + 0x424DF2EL, memory.backing.readQword(stack - 0x50), "physical DB38 return");
            equal(incoming.rbpBits(), memory.backing.readQword(stack - 8), "saved RBP");
            equal(0xAABBCCDD00000002L, memory.backing.readQword(stack - 0x28), "local DWORD count width");
            equal(0x5566778800000002L, memory.backing.readQword(stack + 0x20), "home DWORD count width");
            memory.writeQword(0x71000000L, 0x1020304050607080L);
        });
        var bound = GovernmentRegistryForward185Calls.bind(base, memory, script);
        VolatileBits actual = bound.invoke(new OpaqueCall(0x4223EFBL, 0x424DE78L,
                parentStack, input, incoming));
        equal(post, actual, "all actual post volatile bits");
        equal(List.of(stack - 8, stack), memory.reads, "actual POP RBP then RET reads");
        equal(parentReturn, memory.backing.readQword(stack), "existing parent return retained");
        equal(0x1020304050607080L, memory.backing.readQword(0x71000000L), "opaque memory effect retained");
        script.done(0);
        System.out.println("OK: 1 new owned 185 tail case, " + assertions + " assertions; DB38 opaque");
    }
    private static final class ObservedMemory implements GovernmentSharedManager167Api.Memory {
        final GovernmentSharedComposition168Fixture.MemoryImage backing =
                new GovernmentSharedComposition168Fixture.MemoryImage();
        final List<Long> reads = new ArrayList<>();
        final List<Long> writes = new ArrayList<>();
        @Override public int readUnsignedByte(long address) { return backing.readUnsignedByte(address); }
        @Override public int readDword(long address) { return backing.readDword(address); }
        @Override public long readQword(long address) { reads.add(address); return backing.readQword(address); }
        @Override public void writeByte(long address, int value) { backing.writeByte(address, value); }
        @Override public void writeDword(long address, int value) { backing.writeDword(address, value); }
        @Override public void writeQword(long address, long value) {
            writes.add(address); backing.writeQword(address, value);
        }
        @Override public Bits128 read128(long address) { return backing.read128(address); }
        @Override public void write128(long address, Bits128 value) { backing.write128(address, value); }
        @Override public int lockedXaddDword(long address, int addend) {
            return backing.lockedXaddDword(address, addend);
        }
        @Override public int lockedXaddByte(long address, int addend) {
            return backing.lockedXaddByte(address, addend);
        }
    }
}

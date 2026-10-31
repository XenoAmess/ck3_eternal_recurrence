package org.xar.ck3.control.g2.m2.nativecode;

/** Full262-byte 3076B60, with only actual unresolved named callees as ports. */
public final class PendingContextCopy3076B60 {
    private PendingContextCopy3076B60() { }
    public record Bits128(long low, long high) { }
    public interface Memory extends PendingComponentInit2756120.Memory {
        int read32(long address);
        long read64(long address);
        Bits128 read128(long address);
        void write128(long address, Bits128 value);
    }
    public interface Calls {
        void call373ACF0(Memory memory, long rcx, long rdx);
        void call105D2D0(Memory memory, long rcx);
        void callBCB7C0(Memory memory, long rcx, int edx, long r8, long r9);
        void call2503880(Memory memory, long rcx, long rdx);
    }
public static long copy(Memory memory, Calls calls, long destination, long source) {
    long r15 = destination;
    long r14 = source;
    long rcx = destination;
    long rdx = source;
    long rax = memory.read64(rdx);
    memory.write64(rcx, rax);
    rcx += 8;
    rdx += 8;
    calls.call373ACF0(memory, rcx, rdx);
    rcx = r15 + 0x170;
    rdx = r14 + 0x170;
    calls.call373ACF0(memory, rcx, rdx);
    int edx = memory.read32(r14 + 0x2d8);
    memory.write32(r15 + 0x2d8, edx);
    edx = memory.read32(r14 + 0x2dc);
    memory.write32(r15 + 0x2dc, edx);
    edx = memory.read32(r14 + 0x2e0);
    memory.write32(r15 + 0x2e0, edx);
    edx = memory.read32(r14 + 0x2e4);
    memory.write32(r15 + 0x2e4, edx);
    edx = memory.read32(r14 + 0x2e8);
    memory.write32(r15 + 0x2e8, edx);
    edx = memory.read32(r14 + 0x2ec);
    memory.write32(r15 + 0x2ec, edx);
    Bits128 xmm0 = memory.read128(r14 + 0x2f0);
    memory.write128(r15 + 0x2f0, xmm0);
    long rbx = (long) memory.read32(r14 + 0x30c);
    long rdi = memory.read64(r14 + 0x300);
    rcx = r15 + 0x300;
    calls.call105D2D0(memory, rcx);
    long r9 = rdi + rbx;
    long r8 = rdi;
    edx = memory.read32(r15 + 0x30c);
    rcx = r15 + 0x300;
    calls.callBCB7C0(memory, rcx, edx, r8, r9);
    rcx = r15 + 0x330;
    rdx = r14;
    calls.call2503880(memory, rcx, rdx);
    return r15;
}
}

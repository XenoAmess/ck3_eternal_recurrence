package org.xar.ck3.control.g2.m2.nativecode;

import org.xar.ck3.control.g2.m2.nativecode.PendingContextCopy3076B60.Bits128;

/** Full233-byte373ACF0 called twice by actual3076B60. */
public final class PendingEmbeddedCopy373ACF0 {
    private PendingEmbeddedCopy373ACF0() { }
    public interface Memory extends PendingContextCopy3076B60.Memory {
        void write16(long address, int value);
    }
    public interface Calls {
        void call8895D0(Memory memory, long rcx, long rdx);
        void call37282B0(Memory memory, long rcx, long rdx);
        void call260E040(Memory memory, long rcx, long rdx);
        void call3727180(Memory memory, long rcx, long rdx);
    }
    public static long copy(Memory memory, Calls calls, long destination, long source, long moduleBase) {
        long r14 = destination;
        long rsi = source;
        long rcx = destination;
        long rdx = source;
        long rbp = 0L;
        long rbx = 0L;
        long rax = 0L;

        memory.write32(rcx, (int) rbp);
        memory.write64(rcx + 0x8L, rbp);
        memory.write32(rcx + 0x10L, -1);
        rcx += 0x18L;

        calls.call8895D0(memory, rcx, rdx);

        rcx = r14 + 0x100L;
        memory.write64(rcx, rbp);
        memory.write64(rcx + 0x8L, rbp);
        rdx = moduleBase + 0x54DE270L;
        memory.write64(rcx + 0x10L, rdx);

        rbx = r14 + 0x118L;
        rax = moduleBase + 0x448D1F8L;
        memory.write64(rbx, rax);
        rax = moduleBase + 0x448D268L;
        memory.write64(rbx + 0x8L, rax);
        memory.write64(rbx + 0x10L, rbp);
        memory.write64(rbx + 0x18L, rbp);
        rax = moduleBase + 0x54DE278L;
        memory.write64(rbx + 0x20L, rax);
        memory.write32(rbx + 0x28L, (int) rbp);
        memory.write64(rbx + 0x30L, rbp);
        memory.write64(rbx + 0x38L, rbp);
        memory.write64(rbx + 0x40L, rdx);
        memory.write32(rbx + 0x48L, -1);
        memory.write16(rbx + 0x4CL, (int) rbp);
        memory.write8(rbx + 0x4EL, (int) rbp);

        Bits128 bits = memory.read128(rsi);
        memory.write128(r14, bits);
        memory.write32(r14 + 0x10L, memory.read32(rsi + 0x10L));

        rdx = rsi + 0x100L;
        calls.call37282B0(memory, rcx, rdx);

        rdx = rsi + 0x18L;
        rcx = r14 + 0x18L;
        calls.call260E040(memory, rcx, rdx);

        rdx = rsi + 0x118L;
        rcx = rbx;
        calls.call3727180(memory, rcx, rdx);

        rax = r14;
        return rax;
    }
}

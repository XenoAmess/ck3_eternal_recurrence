package org.xar.ck3.control.g2.m2.nativecode;

/** Complete normal129B2503880, actual caller3076C49. No native-type inventory claim. */
public final class PendingContextTailCopy2503880 {
    private PendingContextTailCopy2503880() { }
    public interface Memory {
        int read8(long address);
        long read64(long address);
        void write64(long address, long value);
    }
    public interface Calls {
        long call25037E0(Memory memory, long rcx, long rdx);
        void virtual10(Memory memory, long target, long rcx, long rdx, long r8);
    }
    public static long copy(Memory memory, Calls calls, long destination, long source) {
        long rax = memory.read64(source);
        if (rax == 0) {
            memory.write64(destination, 0);
            return destination;
        }
        int edi = memory.read8(rax + 0x26f8) & 0xFF;
        if (edi == 0x27) {
            memory.write64(destination, 0);
            return destination;
        }
        long rsi = memory.read64(source + 0x330);
        if (rsi == 0) {
            memory.write64(destination, 0);
            return destination;
        }
        long tableBasis = calls.call25037E0(memory, destination, source);
        long rcx = memory.read64(tableBasis + (edi << 6) + 0x38);
        if (rcx == 0) {
            memory.write64(destination, 0);
            return destination;
        }
        long rax2 = memory.read64(rcx);
        long target = memory.read64(rax2 + 0x10);
        calls.virtual10(memory, target, rcx, destination, rsi);
        return destination;
    }
}
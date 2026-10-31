package org.xar.ck3.control.g2.m2.nativecode;

public final class PendingCopyRep4226840 {
    private PendingCopyRep4226840() { }

    public static void copy(Copy4226860Api.Memory memory, long destination, long source, long bytes) {
        long rdi = destination;
        long rsi = source;
        long rcx = bytes;

        while (rcx != 0) {
            int value = (memory.read8(rsi) & 0xFF);
            memory.write8(rdi, value);
            rdi = rdi + 1;
            rsi = rsi + 1;
            rcx = rcx - 1;
        }
    }
}
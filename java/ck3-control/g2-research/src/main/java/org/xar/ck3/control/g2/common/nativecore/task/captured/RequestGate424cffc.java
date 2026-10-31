package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Source424CFFC known register roles, not a complete native calling convention. */
public final class RequestGate424cffc {
    private RequestGate424cffc() { }
    public interface Ports {
        long call424d02c(long knownRcx);
        int callIndirect43dbba8(long knownRcx, long liveRax);
    }

    public static int execute(long sizeBits, Ports ports) {
        long rbx = sizeBits;
        long rax = ports.call424d02c(rbx);
        if (rax == 0L) {
            return 0;
        }
        long rcx = rbx;
        int eax = ports.callIndirect43dbba8(rcx, rax);
        if (eax == 0) {
            return 0;
        }
        return 1;
    }
}

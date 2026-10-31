package org.xar.ck3.research.m3;

public final class GlobalReleaseWrapper168 {
    private GlobalReleaseWrapper168() {}
    public static long apply(GlobalReleaseApi168.Ports ports, long rcx, long rdx, long r8, long r9, long incomingRax) {
        if (rdx == 0) {
            return incomingRax;
        }
        return ports.tail40ec530(rdx, rdx, r8, r9, incomingRax);
    }
}

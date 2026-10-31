package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Two source-established linear entries ending in indirect tails;not full native ABI. */
public final class RequestIndexedTails4247ffc {
    private RequestIndexedTails4247ffc() { }
    public interface Ports {
        void jump43da500(long knownRcx, long liveRax);
        void jump43da4f0(long knownRcx, long liveRax, long liveRbx);
    }

    public static void call4247ffc(long moduleBase, int entryEcx, Ports ports) {
        // 1. MOVSXD RAX, ECX (signed32to64)
        long rax = (long) entryEcx;

        // 2. LEA RCX, [RAX + RAX*4]
        // This is an address calculation, not a memory read. The result is stored in RCX.
        long rcx = rax + (rax * 4L);

        // 3. LEA RAX, [moduleBase + 0x5c5d330]
        // Address calculation only, no memory read. The result is stored in RAX.
        rax = moduleBase + 0x5c5d330L;

        // 4. LEA RCX, [RAX + RCX*8]
        // Address calculation only, no memory read. The result is stored in RCX.
        rcx = rax + (rcx * 8L);

        // 5. JMP QWORD PTR [0x43da500]
        // The tail receives computedRCX and fullknownRAX.
        ports.jump43da500(rcx, rax);
    }

    public static void call4248050(long moduleBase, int entryEcx, long liveRbx, Ports ports) {
        // 1. MOVSXD RAX, ECX (signed32to64)
        long rax = (long) entryEcx;

        // 2. LEA RCX, [RAX + RAX*4]
        long rcx = rax + (rax * 4L);

        // 3. LEA RAX, [moduleBase + 0x5c5d330]
        rax = moduleBase + 0x5c5d330L;

        // 4. LEA RCX, [RAX + RCX*8]
        rcx = rax + (rcx * 8L);

        // 5. JMP QWORD PTR [0x43da4f0]
        // The tail receives computedRCX, fullknownRAX, and the supplied liveRBX.
        ports.jump43da4f0(rcx, rax, liveRbx);
    }
}

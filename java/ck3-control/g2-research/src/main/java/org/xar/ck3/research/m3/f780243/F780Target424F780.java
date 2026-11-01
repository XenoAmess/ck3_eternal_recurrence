package org.xar.ck3.research.m3.f780243;

import org.xar.ck3.research.m3.f780243.F780Api243.Input;
import org.xar.ck3.research.m3.f780243.F780Api243.Memory;
import org.xar.ck3.research.m3.f780243.F780Api243.Ports;
import org.xar.ck3.research.m3.f780243.F780Api243.Scratch;

/** Explicit supplied-storage business projection; physical NV, CPU and EH excluded. */
public final class F780Target424F780 {
    private F780Target424F780() { }

    public static void execute(Memory memory, Ports ports, Input input) {
        long entryRsp = input.scratch().entryRsp();
        long rdxAddress = input.rdxAddress();
        long r8Address = input.r8Address();
        long r9Address = input.r9Address();

        // F785 W64[actual entryE+0x20]=entryR9 raw64 FIRST, before all modeled reads.
        // entryE is the post-CALL entry RSP (input.scratch().entryRsp()).
        // The write is to entryE + 0x20.
        memory.writeInt64(entryRsp + 0x20L, r9Address);

        // F795 fresh R32[entryRDX] -> ECX bits.
        int ecx1 = memory.readInt32(rdxAddress);

        // F797 opaque call4247ffc with these bits.
        ports.call4247ffc(memory, 0x424F797L, ecx1);

        // F79D fresh R64[saved entryR8] -> p0;
        long p0 = memory.readPointer(r8Address);

        // F7A0 fresh R64[p0] -> p1;
        long p1 = memory.readPointer(p0);

        // F7A3 fresh R64[p1+0x88] -> atomic address;
        long atomicAddress = memory.readPointer(p1 + 0x88L);

        // F7AA one atomicIncrementInt32(address).
        memory.atomicIncrementInt32(atomicAddress);

        // F7AD fresh R32[saved entryR9] -> ECX bits.
        int ecx2 = memory.readInt32(r9Address);

        // F7AF call4248050 with those bits and liveRBX=entryR9.
        ports.call4248050(memory, 0x424F7AFL, ecx2, r9Address);
    }
}
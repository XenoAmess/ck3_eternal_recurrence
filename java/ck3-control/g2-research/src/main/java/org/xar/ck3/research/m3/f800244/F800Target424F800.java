package org.xar.ck3.research.m3.f800244;

import org.xar.ck3.research.m3.f8a8242.F8a8Api242.Memory;
import org.xar.ck3.research.m3.f800244.F800Api244.Input;
import org.xar.ck3.research.m3.f800244.F800Api244.Ports;

/** Explicit normal205B storage operations; opaque calls retain their own behavior. */
public final class F800Target424F800 {
    private F800Target424F800() { }

    public static void execute(Memory memory, Ports ports, Input input) {
        long entryRsp = input.scratch().entryRsp();
        long rdxAddress = input.rdxAddress();
        long r8Address = input.r8Address();
        long r9Address = input.r9Address();

        // F805 W64[E+0x20]=entryR9 raw64 FIRST.
        memory.writeInt64(entryRsp + 0x20L, r9Address);

        // F815 fresh R32[entryRDX] -> ECX bits.
        int ecx1 = memory.readInt32(rdxAddress);

        // F817 opaque call4247ffc with these bits.
        ports.call4247ffc(memory, 0x424F817L, ecx1);

        // F81D fresh R64[saved entryR8+8] -> a/liveRAX;
        long a = memory.readPointer(r8Address + 8L);

        // F821 fresh R64[a] -> rightIntermediate;
        long rightIntermediate = memory.readPointer(a);

        // F824 fresh R64[saved entryR8] -> leftIntermediate;
        long leftIntermediate = memory.readPointer(r8Address);

        // F827 fresh R64[rightIntermediate] -> knownRDX;
        long knownRDX = memory.readPointer(rightIntermediate);

        // F82A fresh R64[leftIntermediate] -> knownRCX;
        long knownRCX = memory.readPointer(leftIntermediate);

        // F82D call424fa90 with knownRCX, knownRDX, and liveRAX=a.
        ports.call424fa90(memory, 0x424F82DL, knownRCX, knownRDX, a);

        // F833 fresh R32[saved entryR9] -> ECX bits.
        int ecx2 = memory.readInt32(r9Address);

        // F835 call4248050 with those bits and liveRBX=entryR9.
        ports.call4248050(memory, 0x424F835L, ecx2, r9Address);
    }
}
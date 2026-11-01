package org.xar.ck3.research.m3.fa90245;

import java.util.OptionalLong;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242.Memory;
import org.xar.ck3.research.m3.fa90245.Fa90Api245.Input;
import org.xar.ck3.research.m3.fa90245.Fa90Api245.Ports;

/** Exact-width address operations for supplied storage; no process attachment. */
public final class Fa90Target424FA90 {
    private Fa90Target424FA90() { }

    public static void execute(Memory memory, Ports ports, Input input) {
        long base = input.moduleBase();
        long entryRcx = input.entryRcx();
        long entryRdx = input.entryRdx();
        long entryRax = input.entryRax();

        // FAA0: first fresh QWORD[entryRCX+0x90]
        long firstCurrent = memory.readPointer(entryRcx + 0x90L);

        // Track knownness of RDX and RAX for the final cleanup call
        OptionalLong knownRdx;
        OptionalLong knownRax;

        if (firstCurrent == 0) {
            // Source jumps directly to FAD8: no firstcall, no reload, no globalread, no LEA.
            // Later call still has knownRDX=originalEntryRDX and knownRAX=entryRAX.
            knownRdx = OptionalLong.of(entryRdx);
            knownRax = OptionalLong.of(entryRax);
        } else {
            // FAAC: call42568fc with firstCurrent, originalEntryRDX, entryRAX
            ports.call42568fc(memory, 0x424FAACL, firstCurrent, entryRdx, entryRax);

            // After opaque returns, RDX and RAX are unknown at this projection boundary.
            knownRdx = OptionalLong.empty();
            knownRax = OptionalLong.empty();

            // FAB1: fresh QWORD[entryRCX+0x90] -> current
            long current = memory.readPointer(entryRcx + 0x90L);

            // FAB8: fresh QWORD[base+0x5C5DCD8] -> globalValue
            long globalValue = memory.readPointer(base + 0x5C5DCD8L);

            if (current == globalValue) {
                // Exact raw64 equality skips to FAD8, without reachedLEA/count/secondcall.
                // Later RDX/RAX remain unknown from firstopaque.
                // knownRdx and knownRax are already empty.
            } else {
                // FAC1: LEA writes RAX=base+0x542F330. Address calculation, NO memory read.
                long sentinelAddress = base + 0x542F330L;
                // Now RAX knownsentinel again; RDX still unknown.
                knownRax = OptionalLong.of(sentinelAddress);
                // knownRdx remains empty.

                if (current == sentinelAddress) {
                    // Skip count/secondcall to FAD8 and keep knownsentinelRAX.
                    // knownRax is already set to sentinelAddress.
                } else {
                    // FACD: fresh DWORD[current+0x10] compared exactly to 0.
                    int dwordVal = memory.readInt32(current + 0x10L);

                    if (dwordVal != 0) {
                        // Nonzero skips secondcall, retaining knownsentinelRAX.
                        // knownRax is already set to sentinelAddress.
                    } else {
                        // Zero calls Ports.call42566fc(memory, 0x424FAD3, current, sentinelAddress) once.
                        // RDX here is always unknown after firstopaque and omitted from this specific knownargPort.
                        ports.call42566fc(memory, 0x424FAD3L, current, sentinelAddress);

                        // After secondopaque normal return, RAX is unknown again; RDX remains unknown.
                        knownRax = OptionalLong.empty();
                        // knownRdx remains empty.
                    }
                }
            }
        }

        // FAD8: ALWAYS W64[entryRCX+0x90] = originalEntryRDX after the reached cleanup path completes normally.
        memory.writeInt64(entryRcx + 0x90L, entryRdx);

        // Only if originalEntryRDX != 0, FAE7 calls Ports.call4256670(memory, 0x424FAE7, originalEntryRDX, knownRdx, knownRax) once.
        if (entryRdx != 0) {
            ports.call4256670(memory, 0x424FAE7L, entryRdx, knownRdx, knownRax);
        }
    }
}
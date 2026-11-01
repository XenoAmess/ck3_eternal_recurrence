package org.xar.ck3.research.m3.f780243;

import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f780243.F780Api243;

/**
 * Binding for the actual F8A8 consumer to the new F780 producer.
 * Legacy old6 methods delegate exactly to fallback.
 * Only new7 activates after sameMemory/site guards using actual receivedE.
 */
public final class F780FromF8Binding243 {
    private F780FromF8Binding243() { }

    public static F8a8Api242.Ports bind(F780Api243.Memory capturedMemory,
            F780Api243.Ports child, F8a8Api242.Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (child == null) {
            throw new RuntimeException("child");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
        }

        return new F8a8Api242.Ports() {
            @Override
            public void call424f780(F8a8Api242.Memory memory, long siteRva, long rcx, long rdx, long r8, long r9) {
                fallback.call424f780(memory, siteRva, rcx, rdx, r8, r9);
            }

            @Override
            public void call424f800(F8a8Api242.Memory memory, long siteRva, long rcx, long rdx, long r8, long r9) {
                fallback.call424f800(memory, siteRva, rcx, rdx, r8, r9);
            }

            @Override
            public void call424f780(F8a8Api242.Memory memory, long siteRva, long rcx, long rdx, long r8, long r9, long calleeEntryRsp) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424F955L) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                F780Api243.Input input = new F780Api243.Input(
                        rdx,
                        r8,
                        r9,
                        new F780Api243.Scratch(calleeEntryRsp));
                F780Target424F780.execute(capturedMemory, child, input);
            }

            @Override
            public void call424f800(F8a8Api242.Memory memory, long siteRva, long rcx, long rdx, long r8, long r9, long calleeEntryRsp) {
                fallback.call424f800(memory, siteRva, rcx, rdx, r8, r9, calleeEntryRsp);
            }
        };
    }
}
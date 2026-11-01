package org.xar.ck3.research.m3.f800244;

import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f800244.F800Api244;
import org.xar.ck3.research.m3.f800244.F800Target424F800;

/**
 * Binding for the actual F8A8 consumer to the new F800 producer.
 * Legacy old6 methods delegate exactly to fallback.
 * Only new7 activates after sameMemory/site guards using actual receivedE.
 */
public final class F800FromF8Binding244 {
    private F800FromF8Binding244() { }

    public static F8a8Api242.Ports bind(F8a8Api242.Memory capturedMemory,
            F800Api244.Ports child, F8a8Api242.Ports fallback) {
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
                fallback.call424f780(memory, siteRva, rcx, rdx, r8, r9, calleeEntryRsp);
            }

            @Override
            public void call424f800(F8a8Api242.Memory memory, long siteRva, long rcx, long rdx, long r8, long r9, long calleeEntryRsp) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424F96AL) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                F800Api244.Input input = new F800Api244.Input(
                        rdx,
                        r8,
                        r9,
                        new F800Api244.Scratch(calleeEntryRsp));
                F800Target424F800.execute(capturedMemory, child, input);
            }
        };
    }
}
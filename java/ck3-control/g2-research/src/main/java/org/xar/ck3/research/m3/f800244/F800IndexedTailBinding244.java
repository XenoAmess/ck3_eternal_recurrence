package org.xar.ck3.research.m3.f800244;

import org.xar.ck3.research.m3.f800244.F800Api244;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;

/**
 * Binding for the actual 244 consumer to the mature RequestIndexedTails4247ffc capability.
 * Captures moduleBase, identical Memory, and child Ports.
 * Owned call4247ffc and call4248050 check identity and site before invoking the mature static methods.
 * Middle call424fa90 is passive and forwards to fallback exactly once.
 */
public final class F800IndexedTailBinding244 {
    private F800IndexedTailBinding244() { }

    public static F800Api244.Ports bind(long moduleBase, F8a8Api242.Memory capturedMemory, RequestIndexedTails4247ffc.Ports tails, F800Api244.Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (tails == null) {
            throw new RuntimeException("tails");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
        }

        return new F800Api244.Ports() {
            @Override
            public void call4247ffc(F8a8Api242.Memory memory, long siteRva, int ecxBits) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424F817L) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                RequestIndexedTails4247ffc.call4247ffc(moduleBase, ecxBits, tails);
            }

            @Override
            public void call4248050(F8a8Api242.Memory memory, long siteRva, int ecxBits, long liveRbx) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424F835L) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                RequestIndexedTails4247ffc.call4248050(moduleBase, ecxBits, liveRbx, tails);
            }

            @Override
            public void call424fa90(F8a8Api242.Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax) {
                fallback.call424fa90(memory, siteRva, knownRcx, knownRdx, liveRax);
            }
        };
    }
}
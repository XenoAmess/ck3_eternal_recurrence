package org.xar.ck3.research.m3.f780243;

import org.xar.ck3.research.m3.f780243.F780Api243;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestIndexedTails4247ffc;

/**
 * Binding for the actual 243 consumer to the mature RequestIndexedTails4247ffc capability.
 * Captures moduleBase, identical Memory, and child Ports.
 * Owned call4247ffc and call4248050 check identity and site before invoking the mature static methods.
 * All other 243 Ports methods are not present in this interface, so no fallback is required.
 */
public final class F780IndexedTailBinding243 {
    private F780IndexedTailBinding243() { }

    public static F780Api243.Ports bind(long moduleBase, F780Api243.Memory capturedMemory, RequestIndexedTails4247ffc.Ports tails) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (tails == null) {
            throw new RuntimeException("tails");
        }

        return new F780Api243.Ports() {
            @Override
            public void call4247ffc(F780Api243.Memory memory, long siteRva, int ecxBits) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424F797L) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                RequestIndexedTails4247ffc.call4247ffc(moduleBase, ecxBits, tails);
            }

            @Override
            public void call4248050(F780Api243.Memory memory, long siteRva, int ecxBits, long liveRbx) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424F7AFL) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                RequestIndexedTails4247ffc.call4248050(moduleBase, ecxBits, liveRbx, tails);
            }
        };
    }
}
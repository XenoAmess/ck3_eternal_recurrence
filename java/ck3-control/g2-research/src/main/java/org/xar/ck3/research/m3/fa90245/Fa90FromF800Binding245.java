package org.xar.ck3.research.m3.fa90245;

import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.f800244.F800Api244;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.fa90245.Fa90Target424FA90;

/** Binding for the actual F800 consumer to the new FA90 producer. */
public final class Fa90FromF800Binding245 {
    private Fa90FromF800Binding245() { }

    public static F800Api244.Ports bind(long moduleBase, F8a8Api242.Memory capturedMemory, Fa90Api245.Ports child, F800Api244.Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (child == null) {
            throw new RuntimeException("child");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
        }

        return new F800Api244.Ports() {
            @Override
            public void call4247ffc(F8a8Api242.Memory memory, long siteRva, int ecxBits) {
                fallback.call4247ffc(memory, siteRva, ecxBits);
            }

            @Override
            public void call4248050(F8a8Api242.Memory memory, long siteRva, int ecxBits, long liveRbx) {
                fallback.call4248050(memory, siteRva, ecxBits, liveRbx);
            }

            @Override
            public void call424fa90(F8a8Api242.Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424F82DL) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                Fa90Api245.Input input = new Fa90Api245.Input(moduleBase, knownRcx, knownRdx, liveRax);
                Fa90Target424FA90.execute(capturedMemory, child, input);
            }
        };
    }
}
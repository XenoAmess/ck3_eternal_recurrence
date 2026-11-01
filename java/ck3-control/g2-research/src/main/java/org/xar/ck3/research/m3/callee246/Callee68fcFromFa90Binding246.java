package org.xar.ck3.research.m3.callee246;

import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;

/** Binding for the actual F800 consumer to the new 42568FC producer. */
public final class Callee68fcFromFa90Binding246 {
    private Callee68fcFromFa90Binding246() { }

    public static Fa90Api245.Ports bind(long moduleBase, Callee68fcApi246.Memory capturedMemory, Callee68fcApi246.Ports child, Fa90Api245.Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (child == null) {
            throw new RuntimeException("child");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
        }

        return new Fa90Api245.Ports() {
            @Override
            public void call42568fc(F8a8Api242.Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x424FAACL) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                Callee68fcApi246.Input input = new Callee68fcApi246.Input(moduleBase, knownRcx);
                Callee42568FC246.execute(capturedMemory, child, input);
            }

            @Override
            public void call42566fc(F8a8Api242.Memory memory, long siteRva, long knownRcx, long liveRax) {
                fallback.call42566fc(memory, siteRva, knownRcx, liveRax);
            }

            @Override
            public void call4256670(F8a8Api242.Memory memory, long siteRva, long knownRcx, java.util.OptionalLong knownRdx, java.util.OptionalLong knownRax) {
                fallback.call4256670(memory, siteRva, knownRcx, knownRdx, knownRax);
            }
        };
    }
}
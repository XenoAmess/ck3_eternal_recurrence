package org.xar.ck3.research.m3.callee246;

import org.xar.ck3.research.m3.callee246.Callee68fcApi246;

/** Binding for the actual 42568FC consumer to the new 42568D4 producer. */
public final class Callee68d4From68fcBinding247 {
    private Callee68d4From68fcBinding247() { }

    public static Callee68fcApi246.Ports bind(long moduleBase, Callee68d4Memory246 capturedMemory) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }

        return new Callee68fcApi246.Ports() {
            @Override
            public void call42568d4(Callee68fcApi246.Memory memory, long siteRva, long knownRcx, long knownRdx,
                    long liveRax, long knownR8, long knownR9) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("Mismatched capturedMemory");
                }
                if (siteRva != 0x425699AL) {
                    throw new RuntimeException("Invalid concrete source callsite");
                }
                Callee42568D4247.execute(capturedMemory, moduleBase, knownRcx);
            }
        };
    }
}
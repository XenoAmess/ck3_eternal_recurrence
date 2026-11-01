package org.xar.ck3.research.m3.tail250;

import org.xar.ck3.research.m3.callee246.Callee68d4Memory246;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m3.tail249.Tail6670Api249;

public final class Tail6874From6670Binding250 {
    private Tail6874From6670Binding250() { }

    public static Tail6670Api249.Ports bind(long moduleBase, Callee68d4Memory246 capturedMemory, Tail6670Api249.Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
        }

        return new Tail6670Api249.Ports() {
            @Override
            public void tail4256874(Callee68fcApi246.Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax, long knownR8) {
                if (memory == capturedMemory && siteRva == 0x42566F6L) {
                    Tail4256874250.execute(capturedMemory, moduleBase, knownRcx);
                } else {
                    fallback.tail4256874(memory, siteRva, knownRcx, knownRdx, liveRax, knownR8);
                }
            }
        };
    }
}
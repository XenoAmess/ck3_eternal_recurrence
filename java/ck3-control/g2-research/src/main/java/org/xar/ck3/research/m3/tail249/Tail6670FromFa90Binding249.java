package org.xar.ck3.research.m3.tail249;

import java.util.OptionalLong;
import org.xar.ck3.research.m3.callee246.Callee68fcApi246;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242;
import org.xar.ck3.research.m3.fa90245.Fa90Api245;
import org.xar.ck3.research.m3.tail249.Tail6670Api249;

/** Exact factory for binding 4256670 tail logic to Fa90 API; no process attachment. */
public final class Tail6670FromFa90Binding249 {
    private Tail6670FromFa90Binding249() { }

    public static Fa90Api245.Ports bind(
            long moduleBase,
            Callee68fcApi246.Memory capturedMemory,
            Tail6670Api249.Ports childTailPorts,
            Fa90Api245.Ports fallback) {
        if (capturedMemory == null) {
            throw new RuntimeException("capturedMemory");
        }
        if (childTailPorts == null) {
            throw new RuntimeException("childTailPorts");
        }
        if (fallback == null) {
            throw new RuntimeException("fallback");
        }

        return new Fa90Api245.Ports() {
            @Override
            public void call42568fc(F8a8Api242.Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax) {
                fallback.call42568fc(memory, siteRva, knownRcx, knownRdx, liveRax);
            }

            @Override
            public void call42566fc(F8a8Api242.Memory memory, long siteRva, long knownRcx, long liveRax) {
                fallback.call42566fc(memory, siteRva, knownRcx, liveRax);
            }

            @Override
            public void call4256670(F8a8Api242.Memory memory, long siteRva, long knownRcx,
                    OptionalLong knownRdx, OptionalLong knownRax) {
                if (memory != capturedMemory) {
                    throw new RuntimeException("memory identity mismatch");
                }
                if (siteRva != 0x424FAE7L) {
                    throw new RuntimeException("siteRva mismatch");
                }

                Tail6670Api249.Input input = new Tail6670Api249.Input(moduleBase, knownRcx);
                Tail4256670249.execute(capturedMemory, childTailPorts, input);
            }
        };
    }
}
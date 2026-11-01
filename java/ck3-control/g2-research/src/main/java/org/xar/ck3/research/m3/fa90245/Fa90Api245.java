package org.xar.ck3.research.m3.fa90245;

import java.util.OptionalLong;
import org.xar.ck3.research.m3.f8a8242.F8a8Api242.Memory;

/** Normal supplied-storage effects; physical NV, CPU and EH excluded. */
public final class Fa90Api245 {
    private Fa90Api245() { }

    public record Input(long moduleBase, long entryRcx, long entryRdx, long entryRax) { }

    public interface Ports {
        /** First call has all three source-known register values. */
        void call42568fc(Memory memory, long siteRva, long knownRcx, long knownRdx, long liveRax);

        /** RDX is unknown after the first opaque call; RAX is the reached LEA address. */
        void call42566fc(Memory memory, long siteRva, long knownRcx, long liveRax);

        /** Empty denotes unknown, never zero; both OptionalLong arguments are nonnull. */
        void call4256670(Memory memory, long siteRva, long knownRcx,
                OptionalLong knownRdx, OptionalLong knownRax);
    }
}

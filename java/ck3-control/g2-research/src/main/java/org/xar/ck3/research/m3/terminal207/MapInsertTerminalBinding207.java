package org.xar.ck3.research.m3.terminal207;

import org.xar.ck3.research.m3.map191.MapInsert191Api;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import java.util.Objects;

/**
 * Supplied-storage business CFG binding for MapInsert191Api.Ports.
 * Only terminal4232cf4 at site 0xC3BC88 is bound to Terminal4232CF4.trace.
 * All other callbacks are exact delegates to the fallback ports.
 */
public final class MapInsertTerminalBinding207 {
    private MapInsertTerminalBinding207() { }

    public interface SharedMemory extends MapInsert191Api.Memory, Terminal207Api.Memory { }

    public static MapInsert191Api.Ports bind(
            SharedMemory capturedMemory,
            long moduleBase,
            Terminal207Api.Ports terminalPorts,
            MapInsert191Api.Ports fallback) {
        Objects.requireNonNull(capturedMemory, "capturedMemory");
        Objects.requireNonNull(terminalPorts, "terminalPorts");
        Objects.requireNonNull(fallback, "fallback");

        return new MapInsert191Api.Ports() {
            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
                return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx);
            }

            @Override
            public int equal3f6d2b0(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx, long sourceEntryRsp) {
                return fallback.equal3f6d2b0(memory, siteRva, rcx, rdx, sourceEntryRsp);
            }

            @Override
            public void insertSlotC3cf10(MapInsert191Api.Memory memory, long siteRva, long bucket, int probe, int hash, long descriptor) {
                fallback.insertSlotC3cf10(memory, siteRva, bucket, probe, hash, descriptor);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map) {
                fallback.rehashC3a400(memory, siteRva, map);
            }

            @Override
            public void rehashC3a400(MapInsert191Api.Memory memory, long siteRva, long map, long sourceEntryRsp) {
                fallback.rehashC3a400(memory, siteRva, map, sourceEntryRsp);
            }

            @Override
            public void insertC3a5f0(MapInsert191Api.Memory memory, long siteRva, long map, long result, int hash, long descriptor) {
                fallback.insertC3a5f0(memory, siteRva, map, result, hash, descriptor);
            }

            @Override
            public void destroy856050(MapInsert191Api.Memory memory, long siteRva, long descriptor) {
                fallback.destroy856050(memory, siteRva, descriptor);
            }

            @Override
            public int capacity86e160(MapInsert191Api.Memory memory, long siteRva, int ecx, int edx) {
                return fallback.capacity86e160(memory, siteRva, ecx, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx) {
                fallback.reserveC3b700(memory, siteRva, map, edx);
            }

            @Override
            public void reserveC3b700(MapInsert191Api.Memory memory, long siteRva, long map, int edx, long sourceEntryRsp) {
                fallback.reserveC3b700(memory, siteRva, map, edx, sourceEntryRsp);
            }

            @Override
            public void overflow86f210(MapInsert191Api.Memory memory, long siteRva, long rcx, long rdx) {
                fallback.overflow86f210(memory, siteRva, rcx, rdx);
            }

            @Override
            public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0xC3BC88L) {
                    throw new IllegalArgumentException("Unexpected site RVA: " + Long.toHexString(siteRva));
                }
                Terminal207Api.Stop stop = Terminal4232CF4.trace(capturedMemory, terminalPorts, moduleBase);
                throw new UnsupportedOperationException("Terminal4232CF4 returned Stop: " + stop);
            }

            @Override
            public void terminal4232cf4(MapInsert191Api.Memory memory, long siteRva, long terminalEntryRsp) {
                if (memory != capturedMemory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                if (siteRva != 0xC3BC88L) {
                    throw new IllegalArgumentException("Unexpected site RVA: " + Long.toHexString(siteRva));
                }
                Terminal207Api.Stop stop = Terminal4232CF4.trace(capturedMemory, terminalPorts, moduleBase, terminalEntryRsp);
                throw new UnsupportedOperationException("Terminal4232CF4 returned Stop: " + stop);
            }
        };
    }
}
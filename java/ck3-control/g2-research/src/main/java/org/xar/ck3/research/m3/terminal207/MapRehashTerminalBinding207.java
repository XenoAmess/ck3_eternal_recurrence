package org.xar.ck3.research.m3.terminal207;

import org.xar.ck3.research.m3.MapRehashApi190;
import org.xar.ck3.research.m3.C3e150Api180;
import org.xar.ck3.research.m3.RegistryConsumerApi176;
import org.xar.ck3.research.m3.terminal207.Terminal207Api;
import java.util.Objects;

/**
 * Source-bound binding of MapRehashApi190.Ports to Terminal207Api for the exact C3A436 call site.
 * Only call4232cf4 is intercepted; all other ports delegate exactly to the fallback.
 */
public final class MapRehashTerminalBinding207 {
    private MapRehashTerminalBinding207() { }

    public interface SharedMemory extends MapRehashApi190.Memory, Terminal207Api.Memory { }

    public static MapRehashApi190.Ports bind(
            SharedMemory memory,
            long moduleBase,
            Terminal207Api.Ports terminalPorts,
            MapRehashApi190.Ports fallback) {
        Objects.requireNonNull(memory);
        Objects.requireNonNull(terminalPorts);
        Objects.requireNonNull(fallback);

        return new MapRehashApi190.Ports() {
            @Override
            public long allocatorSlot08(MapRehashApi190.Memory mem, long code, long allocator, long bytes, int alignment) {
                return fallback.allocatorSlot08(mem, code, allocator, bytes, alignment);
            }

            @Override
            public void allocatorSlot10(MapRehashApi190.Memory mem, long code, long allocator, long block, int alignment) {
                fallback.allocatorSlot10(mem, code, allocator, block, alignment);
            }

            @Override
            public void callc3b960(MapRehashApi190.Memory mem, long map, long output, int hash, long descriptor, long flagAddress) {
                fallback.callc3b960(mem, map, output, hash, descriptor, flagAddress);
            }

            @Override
            public void call856050(MapRehashApi190.Memory mem, long descriptor) {
                fallback.call856050(mem, descriptor);
            }

            @Override
            public void call86f210(MapRehashApi190.Memory mem, long output, long map) {
                fallback.call86f210(mem, output, map);
            }

            @Override
            public void call4232cf4(MapRehashApi190.Memory mem) {
                if (mem != memory) {
                    throw new IllegalArgumentException("Memory identity mismatch");
                }
                Terminal207Api.Stop stop = Terminal4232CF4.trace(memory, terminalPorts, moduleBase);
                throw new UnsupportedOperationException(
                    "Terminal4232CF4 returned Stop: " + stop.name());
            }

            @Override
            public long gs58(C3e150Api180.Memory mem) {
                return fallback.gs58(mem);
            }

            @Override
            public void call4223a84(C3e150Api180.Memory mem, long guard) {
                fallback.call4223a84(mem, guard);
            }

            @Override
            public void call4223a24(C3e150Api180.Memory mem, long guard) {
                fallback.call4223a24(mem, guard);
            }
        };
    }
}

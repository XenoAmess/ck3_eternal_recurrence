package org.xar.ck3.research.m3;

/** Explicit observations for the directly reachable normal entry of held 314B3793900. */
public final class GroupLookupApi182 {
    private GroupLookupApi182() { }
    public interface Memory extends RegistryConsumerApi176.Memory { }
    public interface Ports {
        /** Atomic DWORD add: returns old int32 bits and applies wrapping delta once. */
        int atomicXadd32(Memory memory, long address, int delta);
        /** One source PAUSE observation; the port may change supplied memory or throw. */
        void pause(Memory memory);
    }
}

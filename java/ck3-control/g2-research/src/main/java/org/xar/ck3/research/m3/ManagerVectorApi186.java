package org.xar.ck3.research.m3;

/** Explicit supplied observations for held416B normal producer; no native execution. */
public final class ManagerVectorApi186 {
    private ManagerVectorApi186() { }
    public interface Memory extends RegistryConsumerApi176.Memory {
        /** One source unlocked DWORD increment, modulo32; no cross-thread atomicity claim. */
        void incrementInt32(long address);
    }
    public interface Ports {
        /** Actual consumed receiver/code and supplied RAX observation; no other volatile arguments guessed. */
        long objectSlot08(Memory memory, long code, long receiver);
        /** Observed lowlane CVTDQ2PS(capacity), MULSS(multiplierBits), CVTTSS2SI result. */
        int growthCvtt32(Memory memory, int capacityBits, int multiplierBits);
        long allocatorSlot08(Memory memory, long code, long allocator, long bytes, int alignment);
        void objectSlot00(Memory memory, long code, long receiver, int flag);
        void allocatorSlot10(Memory memory, long code, long allocator, long block, int alignment);
    }
}

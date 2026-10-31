package org.xar.ck3.control.g2.m2.nativecode;

/** Frozen new adapter API. Physical stack stays explicit. */
public final class PendingQueueUpdateWithKnownCopy3727EC0 {
    private PendingQueueUpdateWithKnownCopy3727EC0() { }

    public interface Memory extends PendingQueueUpdateWithKnownHelpers3727EC0.Memory, Copy4226860Api.Memory { }

    public interface Calls {
        void pause(Memory memory);
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
    }

    public static void update(Memory memory, Calls calls, long receiver, long moduleBase, long stackSlotAddress) {
        final Memory outerMemory = memory;
        final long outerModuleBase = moduleBase;

        PendingQueueUpdateWithKnownHelpers3727EC0.Calls adapter = new PendingQueueUpdateWithKnownHelpers3727EC0.Calls() {
            @Override
            public void pause(PendingQueueUpdateWithKnownHelpers3727EC0.Memory m) {
                calls.pause(outerMemory);
            }

            @Override
            public long allocate(PendingQueueUpdateWithKnownHelpers3727EC0.Memory m, long target, long rcx, long rdx, int r8d) {
                return calls.allocate(outerMemory, target, rcx, rdx, r8d);
            }

            @Override
            public void release(PendingQueueUpdateWithKnownHelpers3727EC0.Memory m, long target, long rcx, long rdx, int r8d) {
                calls.release(outerMemory, target, rcx, rdx, r8d);
            }

            @Override
            public void copy4226860(PendingQueueUpdateWithKnownHelpers3727EC0.Memory m, long rcx, long rdx, long r8) {
                PendingMemoryCopy4226860.copy(outerMemory, rcx, rdx, r8, outerModuleBase);
            }
        };

        PendingQueueUpdateWithKnownHelpers3727EC0.update(outerMemory, adapter, receiver, moduleBase, stackSlotAddress);
    }
}
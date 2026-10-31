package org.xar.ck3.control.g2.m2.nativecode;

/** New real known-COPY adapter. SET remains explicit. */
public final class PendingSlotCapacityWithKnownCopy1ACDFB0 {
    private PendingSlotCapacityWithKnownCopy1ACDFB0() { }

    public interface Memory extends PendingSlotCapacityWithArray1ACDFB0.Memory, Copy4226860Api.Memory { }

    public interface Calls {
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
        void call4226F10(Memory memory, long rcx, int edx, long r8);
    }

    public static boolean grow(Memory memory, Calls calls, long tableAddress, int requestedCapacity, long moduleBase) {
        PendingSlotCapacityWithArray1ACDFB0.Calls arrayCalls = new PendingSlotCapacityWithArray1ACDFB0.Calls() {
            @Override
            public long allocate(PendingSlotCapacityWithArray1ACDFB0.Memory m, long target, long rcx, long rdx, int r8d) {
                return calls.allocate(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void release(PendingSlotCapacityWithArray1ACDFB0.Memory m, long target, long rcx, long rdx, int r8d) {
                calls.release(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void call4226860(PendingSlotCapacityWithArray1ACDFB0.Memory m, long rcx, long rdx, long r8) {
                PendingMemoryCopy4226860.copy(memory, rcx, rdx, r8, moduleBase);
            }
            @Override
            public void call4226F10(PendingSlotCapacityWithArray1ACDFB0.Memory m, long rcx, int edx, long r8) {
                calls.call4226F10(memory, rcx, edx, r8);
            }
        };

        return PendingSlotCapacityWithArray1ACDFB0.grow(memory, arrayCalls, tableAddress, requestedCapacity);
    }
}
package org.xar.ck3.control.g2.m2.nativecode;

public final class PendingSlotCapacityWithArray1ACDFB0 {
    private PendingSlotCapacityWithArray1ACDFB0() { }

    public interface Memory extends PendingSlotCapacity1ACDFB0.Memory, PendingSlotArrayReserve1ACE4B0.Memory { }

    public interface Calls {
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
        void call4226860(Memory memory, long rcx, long rdx, long r8);
        void call4226F10(Memory memory, long rcx, int edx, long r8);
    }

    public static boolean grow(Memory memory, Calls calls, long tableAddress, int requestedCapacity) {
        PendingSlotArrayReserve1ACE4B0.Calls reserveCalls = new PendingSlotArrayReserve1ACE4B0.Calls() {
            @Override
            public long allocate(PendingSlotArrayReserve1ACE4B0.Memory m, long target, long rcx, long rdx, int r8d) {
                return calls.allocate(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void release(PendingSlotArrayReserve1ACE4B0.Memory m, long target, long rcx, long rdx, int r8d) {
                calls.release(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void call4226860(PendingSlotArrayReserve1ACE4B0.Memory m, long rcx, long rdx, long r8) {
                calls.call4226860(memory, rcx, rdx, r8);
            }
        };

        PendingSlotCapacity1ACDFB0.Calls capacityCalls = new PendingSlotCapacity1ACDFB0.Calls() {
            @Override
            public void call1ACE4B0(PendingSlotCapacity1ACDFB0.Memory m, long rcx, int edx) {
                PendingSlotArrayReserve1ACE4B0.reserve(memory, reserveCalls, rcx, edx);
            }
            @Override
            public void call4226F10(PendingSlotCapacity1ACDFB0.Memory m, long rcx, int edx, long r8) {
                calls.call4226F10(memory, rcx, edx, r8);
            }
        };

        return PendingSlotCapacity1ACDFB0.grow(memory, capacityCalls, tableAddress, requestedCapacity);
    }
}
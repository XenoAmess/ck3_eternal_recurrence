package org.xar.ck3.control.g2.m2.nativecode;

/** Actual470 caller: known GROW/array and COPY/four children, PAGE remains explicit. */
public final class PendingSlotWithKnownHelpers2A32770 {
    private PendingSlotWithKnownHelpers2A32770() { }
    public interface Memory extends PendingSlotProducer2A32770.Memory,
            PendingSlotCapacityWithArray1ACDFB0.Memory,
            PendingContextWithKnownHelpers3076B60.Memory { }
    public interface Calls extends PendingContextWithKnownHelpers3076B60.Calls {
        boolean call2A321F0(Memory memory, long rcx, int edx);
        long slotAllocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void slotRelease(Memory memory, long target, long rcx, long rdx, int r8d);
        void call4226F10(Memory memory, long rcx, int edx, long r8);
    }
    public static long produce(Memory memory, Calls calls, PendingSlotProducer2A32770.Input input) {
        PendingSlotCapacityWithArray1ACDFB0.Calls growthAdapter = new PendingSlotCapacityWithArray1ACDFB0.Calls() {
            @Override
            public long allocate(PendingSlotCapacityWithArray1ACDFB0.Memory m, long target, long rcx, long rdx, int r8d) {
                return calls.slotAllocate(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void release(PendingSlotCapacityWithArray1ACDFB0.Memory m, long target, long rcx, long rdx, int r8d) {
                calls.slotRelease(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void call4226860(PendingSlotCapacityWithArray1ACDFB0.Memory m, long rcx, long rdx, long r8) {
                PendingMemoryCopy4226860.copy(Copy4226860SharedAdapter395.bind(memory), rcx, rdx, r8, input.moduleBase());
            }
            @Override
            public void call4226F10(PendingSlotCapacityWithArray1ACDFB0.Memory m, long rcx, int edx, long r8) {
                calls.call4226F10(memory, rcx, edx, r8);
            }
        };

        PendingSlotProducer2A32770.Calls producerAdapter = new PendingSlotProducer2A32770.Calls() {
            @Override
            public boolean call1ACDFB0(PendingSlotProducer2A32770.Memory m, long rcx, int edx) {
                return PendingSlotCapacityWithArray1ACDFB0.grow(memory, growthAdapter, rcx, edx);
            }
            @Override
            public boolean call2A321F0(PendingSlotProducer2A32770.Memory m, long rcx, int edx) {
                return calls.call2A321F0(memory, rcx, edx);
            }
            @Override
            public void call3076B60(PendingSlotProducer2A32770.Memory m, long rcx, long rdx) {
                PendingContextWithKnownHelpers3076B60.copy(memory, calls, rcx, rdx, input.moduleBase());
            }
        };

        return PendingSlotProducer2A32770.produce(memory, producerAdapter, input);
    }
}
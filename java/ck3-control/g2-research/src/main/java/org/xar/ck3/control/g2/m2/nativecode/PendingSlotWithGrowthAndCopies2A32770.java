package org.xar.ck3.control.g2.m2.nativecode;

/** Actual470 producer with knownCOPY and GROW/array call edges composed. */
public final class PendingSlotWithGrowthAndCopies2A32770 {
    private PendingSlotWithGrowthAndCopies2A32770() { }
    public interface Memory extends PendingSlotWithContextCopies2A32770.Memory,
            PendingSlotCapacityWithArray1ACDFB0.Memory { }
    public interface Calls extends PendingEmbeddedCopy373ACF0.Calls {
        boolean call2A321F0(PendingSlotProducer2A32770.Memory memory, long rcx, int edx);
        void call105D2D0(PendingContextCopy3076B60.Memory memory, long rcx);
        void callBCB7C0(PendingContextCopy3076B60.Memory memory, long rcx, int edx, long r8, long r9);
        void call2503880(PendingContextCopy3076B60.Memory memory, long rcx, long rdx);
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
        void call4226860(Memory memory, long rcx, long rdx, long r8);
        void call4226F10(Memory memory, long rcx, int edx, long r8);
    }
    public static long produce(Memory memory, Calls calls, PendingSlotProducer2A32770.Input input) {
        PendingSlotCapacityWithArray1ACDFB0.Calls growthCalls = new PendingSlotCapacityWithArray1ACDFB0.Calls() {
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
                calls.call4226860(memory, rcx, rdx, r8);
            }
            @Override
            public void call4226F10(PendingSlotCapacityWithArray1ACDFB0.Memory m, long rcx, int edx, long r8) {
                calls.call4226F10(memory, rcx, edx, r8);
            }
        };

        PendingSlotWithContextCopies2A32770.Calls copyCalls = new PendingSlotWithContextCopies2A32770.Calls() {
            @Override
            public boolean call1ACDFB0(PendingSlotProducer2A32770.Memory m, long rcx, int edx) {
                return PendingSlotCapacityWithArray1ACDFB0.grow(memory, growthCalls, rcx, edx);
            }
            @Override
            public boolean call2A321F0(PendingSlotProducer2A32770.Memory m, long rcx, int edx) {
                return calls.call2A321F0(m, rcx, edx);
            }
            @Override
            public void call105D2D0(PendingContextCopy3076B60.Memory m, long rcx) {
                calls.call105D2D0(m, rcx);
            }
            @Override
            public void callBCB7C0(PendingContextCopy3076B60.Memory m, long rcx, int edx, long r8, long r9) {
                calls.callBCB7C0(m, rcx, edx, r8, r9);
            }
            @Override
            public void call2503880(PendingContextCopy3076B60.Memory m, long rcx, long rdx) {
                calls.call2503880(m, rcx, rdx);
            }
            @Override
            public void call8895D0(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                calls.call8895D0(m, rcx, rdx);
            }
            @Override
            public void call37282B0(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                calls.call37282B0(m, rcx, rdx);
            }
            @Override
            public void call260E040(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                calls.call260E040(m, rcx, rdx);
            }
            @Override
            public void call3727180(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                calls.call3727180(m, rcx, rdx);
            }
        };

        return PendingSlotWithContextCopies2A32770.produce(memory, copyCalls, input);
    }
}
package org.xar.ck3.control.g2.m2.nativecode;

public final class PendingContextRangeWithKnownOrderBCB7C0 {
    private PendingContextRangeWithKnownOrderBCB7C0() { }

    public interface Memory extends PendingContextRangeInsertBCB7C0.Memory, RangeOrder410Api.Memory, Copy4226860Api.Memory { }

    public interface Calls {
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
    }

    public static void insert(Memory memory, Calls calls, RangeOrder410Api.LoopBudget budget, PendingContextRangeInsertBCB7C0.Input input) {

        PendingContextRangeInsertBCB7C0.Calls actualCalls = new PendingContextRangeInsertBCB7C0.Calls() {
            @Override
            public long allocate(PendingContextRangeInsertBCB7C0.Memory m, long target, long rcx, long rdx, int r8d) {
                return calls.allocate(memory, target, rcx, rdx, r8d);
            }

            @Override
            public void release(PendingContextRangeInsertBCB7C0.Memory m, long target, long rcx, long rdx, int r8d) {
                calls.release(memory, target, rcx, rdx, r8d);
            }

            @Override
            public void call4226860(PendingContextRangeInsertBCB7C0.Memory m, long rcx, long rdx, long r8) {
                PendingMemoryCopy4226860.copy(memory, rcx, rdx, r8, input.moduleBase());
            }

            @Override
            public void call9CF240(PendingContextRangeInsertBCB7C0.Memory m, long rcx, long rdx, long r8) {
                RangeOrder410Api.Input rangeInput = new RangeOrder410Api.Input(rcx, rdx, r8, input.moduleBase());
                PendingRangeOrder9CF240.apply(memory, budget, rangeInput);
            }
        };

        PendingContextRangeInsertBCB7C0.insert(memory, actualCalls, input);
    }
}
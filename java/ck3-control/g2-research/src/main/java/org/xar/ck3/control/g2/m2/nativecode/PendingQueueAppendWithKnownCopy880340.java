package org.xar.ck3.control.g2.m2.nativecode;

public final class PendingQueueAppendWithKnownCopy880340 {
    private PendingQueueAppendWithKnownCopy880340() { }

    public interface Memory extends PendingQueueAppend880340.Memory, Copy4226860Api.Memory { }

    public interface Calls {
        long allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void release(Memory memory, long target, long rcx, long rdx, int r8d);
    }

    public static long append(Memory memory, Calls calls, long container, long elementPointer, long moduleBase) {
        final Memory outerMemory = memory;
        final long outerModuleBase = moduleBase;

        PendingQueueAppend880340.Calls adapter = new PendingQueueAppend880340.Calls() {
            @Override
            public long allocate(PendingQueueAppend880340.Memory m, long target, long rcx, long rdx, int r8d) {
                return calls.allocate(outerMemory, target, rcx, rdx, r8d);
            }

            @Override
            public void release(PendingQueueAppend880340.Memory m, long target, long rcx, long rdx, int r8d) {
                calls.release(outerMemory, target, rcx, rdx, r8d);
            }

            @Override
            public void copy4226860(PendingQueueAppend880340.Memory m, long rcx, long rdx, long r8) {
                PendingMemoryCopy4226860.copy(outerMemory, rcx, rdx, r8, outerModuleBase);
            }
        };

        return PendingQueueAppend880340.append(outerMemory, adapter, container, elementPointer, moduleBase);
    }
}
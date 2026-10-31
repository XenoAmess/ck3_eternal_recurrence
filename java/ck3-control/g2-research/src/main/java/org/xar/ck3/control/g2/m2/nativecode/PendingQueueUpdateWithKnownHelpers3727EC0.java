package org.xar.ck3.control.g2.m2.nativecode;

/** Actual103 with known81 classification and known227 append, explicitphysicalstack ABI. */
public final class PendingQueueUpdateWithKnownHelpers3727EC0 {
    private PendingQueueUpdateWithKnownHelpers3727EC0() { }
    public interface Memory extends PendingEmbeddedQueueUpdate3727EC0.Memory,
            PendingQueueAppend880340.Memory, PendingEmbeddedClassify3727580.Memory { }
    public interface Calls {
        void pause(Memory memory);
        long allocate(Memory memory,long target,long rcx,long rdx,int r8d);
        void release(Memory memory,long target,long rcx,long rdx,int r8d);
        void copy4226860(Memory memory,long rcx,long rdx,long r8);
    }
    public static void update(Memory memory,Calls calls,long receiver,long moduleBase,long stackSlotAddress) {
        PendingQueueAppend880340.Calls appendCalls = new PendingQueueAppend880340.Calls() {
            @Override
            public long allocate(PendingQueueAppend880340.Memory m, long target, long rcx, long rdx, int r8d) {
                return calls.allocate(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void release(PendingQueueAppend880340.Memory m, long target, long rcx, long rdx, int r8d) {
                calls.release(memory, target, rcx, rdx, r8d);
            }
            @Override
            public void copy4226860(PendingQueueAppend880340.Memory m, long rcx, long rdx, long r8) {
                calls.copy4226860(memory, rcx, rdx, r8);
            }
        };
        PendingEmbeddedQueueUpdate3727EC0.Calls updateCalls = new PendingEmbeddedQueueUpdate3727EC0.Calls() {
            @Override
            public int classify3727580(PendingEmbeddedQueueUpdate3727EC0.Memory m, long rcx) {
                return PendingEmbeddedClassify3727580.classify(memory, rcx);
            }
            @Override
            public void pause(PendingEmbeddedQueueUpdate3727EC0.Memory m) {
                calls.pause(memory);
            }
            @Override
            public void enqueue880340(PendingEmbeddedQueueUpdate3727EC0.Memory m, long rcx, long rdx) {
                PendingQueueAppend880340.append(memory, appendCalls, rcx, rdx, moduleBase);
            }
        };
        PendingEmbeddedQueueUpdate3727EC0.update(memory, updateCalls, receiver, moduleBase, stackSlotAddress);
    }
}
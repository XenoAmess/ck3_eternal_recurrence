package org.xar.ck3.control.g2.m2.nativecode;

/** Real3076B60 composes the four held named callee implementations; no Game endpoint. */
public final class PendingContextWithKnownHelpers3076B60 {
    private PendingContextWithKnownHelpers3076B60() { }
    public interface Memory extends PendingEmbeddedCopy373ACF0.Memory,
            PendingContextChildInit105D2D0.Memory, PendingContextRangeInsertBCB7C0.Memory,
            PendingContextTailCopy2503880.Memory { }
    public interface Calls {
        void call8895D0(Memory memory, long rcx, long rdx);
        void call37282B0(Memory memory, long rcx, long rdx);
        void call260E040(Memory memory, long rcx, long rdx);
        void call3727180(Memory memory, long rcx, long rdx);
        void virtualInit10(Memory memory, long target, long rcx, long rdx, int r8d);
        void virtualInit20(Memory memory, long target, long rcx, long rdx, long r8);
        long rangeAllocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void rangeRelease(Memory memory, long target, long rcx, long rdx, int r8d);
        void call4226860(Memory memory, long rcx, long rdx, long r8);
        void call9CF240(Memory memory, long rcx, long rdx, long r8);
        long call25037E0(Memory memory, long rcx, long rdx);
        void virtualTail10(Memory memory, long target, long rcx, long rdx, long r8);
    }
    public static long copy(Memory memory, Calls calls, long destination, long source, long moduleBase) {
        PendingEmbeddedCopy373ACF0.Calls embeddedCalls = new PendingEmbeddedCopy373ACF0.Calls() {
            public void call8895D0(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) { calls.call8895D0(memory, rcx, rdx); }
            public void call37282B0(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) { calls.call37282B0(memory, rcx, rdx); }
            public void call260E040(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) { calls.call260E040(memory, rcx, rdx); }
            public void call3727180(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) { calls.call3727180(memory, rcx, rdx); }
        };
        PendingContextChildInit105D2D0.Calls initCalls = new PendingContextChildInit105D2D0.Calls() {
            public void virtual10(PendingContextChildInit105D2D0.Memory m, long target, long rcx, long rdx, int r8d) { calls.virtualInit10(memory, target, rcx, rdx, r8d); }
            public void virtual20(PendingContextChildInit105D2D0.Memory m, long target, long rcx, long rdx, long r8) { calls.virtualInit20(memory, target, rcx, rdx, r8); }
        };
        PendingContextRangeInsertBCB7C0.Calls rangeCalls = new PendingContextRangeInsertBCB7C0.Calls() {
            public long allocate(PendingContextRangeInsertBCB7C0.Memory m, long target, long rcx, long rdx, int r8d) { return calls.rangeAllocate(memory, target, rcx, rdx, r8d); }
            public void release(PendingContextRangeInsertBCB7C0.Memory m, long target, long rcx, long rdx, int r8d) { calls.rangeRelease(memory, target, rcx, rdx, r8d); }
            public void call4226860(PendingContextRangeInsertBCB7C0.Memory m, long rcx, long rdx, long r8) { calls.call4226860(memory, rcx, rdx, r8); }
            public void call9CF240(PendingContextRangeInsertBCB7C0.Memory m, long rcx, long rdx, long r8) { calls.call9CF240(memory, rcx, rdx, r8); }
        };
        PendingContextTailCopy2503880.Calls tailCalls = new PendingContextTailCopy2503880.Calls() {
            public long call25037E0(PendingContextTailCopy2503880.Memory m, long rcx, long rdx) { return calls.call25037E0(memory, rcx, rdx); }
            public void virtual10(PendingContextTailCopy2503880.Memory m, long target, long rcx, long rdx, long r8) { calls.virtualTail10(memory, target, rcx, rdx, r8); }
        };
        PendingContextCopy3076B60.Calls outerCalls = new PendingContextCopy3076B60.Calls() {
            public void call373ACF0(PendingContextCopy3076B60.Memory m, long rcx, long rdx) {
                PendingEmbeddedCopy373ACF0.copy(memory, embeddedCalls, rcx, rdx, moduleBase);
            }
            public void call105D2D0(PendingContextCopy3076B60.Memory m, long rcx) {
                PendingContextChildInit105D2D0.initialize(memory, initCalls, rcx, moduleBase);
            }
            public void callBCB7C0(PendingContextCopy3076B60.Memory m, long rcx, int edx, long r8, long r9) {
                PendingContextRangeInsertBCB7C0.insert(memory, rangeCalls, new PendingContextRangeInsertBCB7C0.Input(rcx, edx, r8, r9, moduleBase));
            }
            public void call2503880(PendingContextCopy3076B60.Memory m, long rcx, long rdx) {
                PendingContextTailCopy2503880.copy(memory, tailCalls, rcx, rdx);
            }
        };
        return PendingContextCopy3076B60.copy(memory, outerCalls, destination, source);
    }
}
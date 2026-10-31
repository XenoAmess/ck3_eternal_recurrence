package org.xar.ck3.control.g2.m2.nativecode;

/** Real3076B60 composes the four held named callee implementations; no Game endpoint. */
public final class PendingContextWithKnownHelpers3076B60 {
    private PendingContextWithKnownHelpers3076B60() { }
    public interface Memory extends PendingEmbeddedCopy373ACF0.Memory,
            PendingContextChildInit105D2D0.Memory, PendingContextRangeInsertBCB7C0.Memory,
            PendingContextTailCopy2503880.Memory, PendingEmbeddedInit8895D0.Memory,
            PendingEmbeddedElements37282B0.Memory, PendingEmbedded24Copy260E040.Memory, PendingEmbedded32Copy3727180.Memory, Copy4226860SharedAdapter395.Memory { }
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
        void call889780(Memory memory, long rcx, long rdx);
        long elementAllocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void callDBDB80(Memory memory, long rcx, long rdx, int r8d, int r9d);
        void virtualElementDestroy(Memory memory, long target, long rcx, long rdx);
        void copy16_21A5050(Memory memory, long destinationHeader, long sourceHeader);
        void copy4_B2EEE0(Memory memory, long destinationHeader, long sourceHeader);
        void copy16_8C70B0(Memory memory, long destinationHeader, long rdxZero, long begin, long end);
        void copy4_ADD0D0(Memory memory, long destinationHeader, long rdxZero, long begin, long end);
        long range16Virtual8(Memory memory,long target,long rcx,long rdx,long r8,long r9);
        void range16Virtual16(Memory memory,long target,long rcx,long rdx,long r8,long r9);
        void range16Direct8F8550(Memory memory,long rcx,long rdx,long r8,long r9);
        long copy24Allocate(Memory memory, long target, long rcx, long rdx, int r8d);
        void copy24Release(Memory memory, long target, long rcx, long rdx, int r8d);
        void prepare32_889660(Memory memory,long rcx);
        long copy32Allocate(Memory memory,long target,long rcx,long rdx,int r8d);
        void replace32_8874D0(Memory memory,long rcx,long rdx,int r8d,int r9d);
        void virtual32Destroy(Memory memory,long target,long rcx,long rdx);
        void finalize32_3727EC0(Memory memory,long rcx);
    }
    public static long copy(Memory memory,Calls calls,long destination,long source,long moduleBase) {
        PendingEmbeddedInit8895D0.Calls init8895D0Calls = new PendingEmbeddedInit8895D0.Calls() {
            public void virtual10(PendingEmbeddedInit8895D0.Memory m, long target, long rcx, long rdx, int r8d) { calls.virtualInit10(memory, target, rcx, rdx, r8d); }
            public void virtual20(PendingEmbeddedInit8895D0.Memory m, long target, long rcx, long rdx, long r8) { calls.virtualInit20(memory, target, rcx, rdx, r8); }
        };
        PendingEmbeddedElements37282B0.Calls elementsCalls = new PendingEmbeddedElements37282B0.Calls() {
            public void call889780(PendingEmbeddedElements37282B0.Memory m, long rcx, long rdx) { calls.call889780(memory, rcx, rdx); }
            public long allocate(PendingEmbeddedElements37282B0.Memory m, long target, long rcx, long rdx, int r8d) { return calls.elementAllocate(memory, target, rcx, rdx, r8d); }
            public void callDBDB80(PendingEmbeddedElements37282B0.Memory m, long rcx, long rdx, int r8d, int r9d) { calls.callDBDB80(memory, rcx, rdx, r8d, r9d); }
            public void virtualDestroy(PendingEmbeddedElements37282B0.Memory m, long target, long rcx, long rdx) { calls.virtualElementDestroy(memory, target, rcx, rdx); }
            public void copy16_21A5050(PendingEmbeddedElements37282B0.Memory m, long destinationHeader, long sourceHeader) { calls.copy16_21A5050(memory, destinationHeader, sourceHeader); }
            public void copy4_B2EEE0(PendingEmbeddedElements37282B0.Memory m, long destinationHeader, long sourceHeader) { calls.copy4_B2EEE0(memory, destinationHeader, sourceHeader); }
            public void copy16_8C70B0(PendingEmbeddedElements37282B0.Memory m, long destinationHeader, long rdxZero, long begin, long end) { calls.copy16_8C70B0(memory, destinationHeader, rdxZero, begin, end); }
            public void copy4_ADD0D0(PendingEmbeddedElements37282B0.Memory m, long destinationHeader, long rdxZero, long begin, long end) { calls.copy4_ADD0D0(memory, destinationHeader, rdxZero, begin, end); }
            public long range16Virtual8(PendingEmbeddedElements37282B0.Memory m, long target, long rcx, long rdx, long r8, long r9) { return calls.range16Virtual8(memory, target, rcx, rdx, r8, r9); }
            public void range16Virtual16(PendingEmbeddedElements37282B0.Memory m, long target, long rcx, long rdx, long r8, long r9) { calls.range16Virtual16(memory, target, rcx, rdx, r8, r9); }
            public void range16Direct8F8550(PendingEmbeddedElements37282B0.Memory m, long rcx, long rdx, long r8, long r9) { calls.range16Direct8F8550(memory, rcx, rdx, r8, r9); }
        };
        PendingEmbedded24Copy260E040.Calls copy24Calls = new PendingEmbedded24Copy260E040.Calls() {
            public long allocate(PendingEmbedded24Copy260E040.Memory m, long target, long rcx, long rdx, int r8d) { return calls.copy24Allocate(memory, target, rcx, rdx, r8d); }
            public void release(PendingEmbedded24Copy260E040.Memory m, long target, long rcx, long rdx, int r8d) { calls.copy24Release(memory, target, rcx, rdx, r8d); }
        };
        PendingEmbedded32Copy3727180.Calls copy32Calls = new PendingEmbedded32Copy3727180.Calls() {
            public void prepare889660(PendingEmbedded32Copy3727180.Memory m, long rcx) { calls.prepare32_889660(memory, rcx); }
            public long allocate(PendingEmbedded32Copy3727180.Memory m, long target, long rcx, long rdx, int r8d) { return calls.copy32Allocate(memory, target, rcx, rdx, r8d); }
            public void replace8874D0(PendingEmbedded32Copy3727180.Memory m, long rcx, long rdx, int r8d, int r9d) { calls.replace32_8874D0(memory, rcx, rdx, r8d, r9d); }
            public void virtualDestroy(PendingEmbedded32Copy3727180.Memory m, long target, long rcx, long rdx) { calls.virtual32Destroy(memory, target, rcx, rdx); }
            public void copy37282B0(PendingEmbedded32Copy3727180.Memory m, long rcx, long rdx) { PendingEmbeddedElements37282B0.copy(memory, elementsCalls, rcx, rdx, moduleBase); }
            public void finalize3727EC0(PendingEmbedded32Copy3727180.Memory m, long rcx) { calls.finalize32_3727EC0(memory, rcx); }
        };
        PendingEmbeddedCopy373ACF0.Calls embeddedCalls = new PendingEmbeddedCopy373ACF0.Calls() {
            public void call8895D0(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                PendingEmbeddedInit8895D0.initialize(memory, init8895D0Calls, rcx, moduleBase);
            }
            public void call37282B0(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                PendingEmbeddedElements37282B0.copy(memory, elementsCalls, rcx, rdx, moduleBase);
            }
            public void call260E040(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                PendingEmbedded24Copy260E040.copy(memory, copy24Calls, rcx, rdx);
            }
            public void call3727180(PendingEmbeddedCopy373ACF0.Memory m, long rcx, long rdx) {
                PendingEmbedded32Copy3727180.copy(memory, copy32Calls, rcx, rdx, moduleBase);
            }
        };
        PendingContextChildInit105D2D0.Calls initCalls = new PendingContextChildInit105D2D0.Calls() {
            public void virtual10(PendingContextChildInit105D2D0.Memory m, long target, long rcx, long rdx, int r8d) { calls.virtualInit10(memory, target, rcx, rdx, r8d); }
            public void virtual20(PendingContextChildInit105D2D0.Memory m, long target, long rcx, long rdx, long r8) { calls.virtualInit20(memory, target, rcx, rdx, r8); }
        };
        PendingContextRangeInsertBCB7C0.Calls rangeCalls = new PendingContextRangeInsertBCB7C0.Calls() {
            public long allocate(PendingContextRangeInsertBCB7C0.Memory m, long target, long rcx, long rdx, int r8d) { return calls.rangeAllocate(memory, target, rcx, rdx, r8d); }
            public void release(PendingContextRangeInsertBCB7C0.Memory m, long target, long rcx, long rdx, int r8d) { calls.rangeRelease(memory, target, rcx, rdx, r8d); }
            public void call4226860(PendingContextRangeInsertBCB7C0.Memory m, long rcx, long rdx, long r8) { PendingMemoryCopy4226860.copy(Copy4226860SharedAdapter395.bind(memory), rcx, rdx, r8, moduleBase); }
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
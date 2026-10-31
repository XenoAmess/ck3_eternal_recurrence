package org.xar.ck3.research.m3;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Calls;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Candidate;

public final class SelectedFreeEffects170 {
    private SelectedFreeEffects170() {}

    public static FreeEffectsApi170.Outcome release(
            NativeTaskMemory memory, long moduleBase, long receiver, long rows, long alignment,
            FreeEffectsApi170.Targets targets, Calls calls) {

        // 1. Preserve 855830's inline-skip branch before object/heap access.
        //    Address arithmetic wraps 64 bits.
        long inlineRows = receiver + 8;
        if (rows == inlineRows) {
            return new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.SKIPPED_INLINE, 0L);
        }

        // 2. On the noninline branch, actual first slot38 code is read from receiver's vptr+38.
        long entryVptr = memory.readPointer(receiver);
        long firstTarget = memory.readPointer(entryVptr + 0x38);

        // 3. If it differs from targets.selectorCode, return UNSUPPORTED_SELECTOR with exactly that observed code.
        if (firstTarget != targets.selectorCode()) {
            return new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.UNSUPPORTED_SELECTOR, firstTarget);
        }

        // 4. For the selected actual getter 86E140, reuse existing AllocatorSelector165.select.
        long returnedReceiver = AllocatorSelector165.select(memory, receiver);

        // 5. Fresh read returned object vptr and code at vptr+10 as actual 855830 does.
        long returnedVptr = memory.readPointer(returnedReceiver);
        long releaseTarget = memory.readPointer(returnedVptr + 0x10);

        // 6. If the code differs from targets.globalReleaseCode, return UNSUPPORTED_RELEASE with observed code.
        if (releaseTarget != targets.globalReleaseCode()) {
            return new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.UNSUPPORTED_RELEASE, releaseTarget);
        }

        // 7. For selected global 14B8571C0, source-null rows makes no lower callee or heap read.
        //    Return SKIPPED_NULL/observedCode0.
        if (rows == 0L) {
            return new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.SKIPPED_NULL, 0L);
        }

        // 8. For selected nonzero branch, use the actual current QWORD[moduleBase+5C5DE30] at the source 424E373 point.
        long heapHandleRaw = memory.readPointer(moduleBase + 0x5C5DE30L);

        // 9. Call existing M4 Free83Candidate.release once.
        //    Alignment is captured input bits but normal14/Crtfree overwrites/does not consume it.
        //    It does not become flags or a block address. HeapFree gets flags32=0 in M4 code.
        //    M4 Free83Candidate must retain its own polarity and effects.
        //    A zero bit heap handle is not a license to skip/throw an invented validity guard.
        Free83Candidate.release(rows, heapHandleRaw, calls);

        // 10. Return CALLEE_RETURNED/observedCode0 only if it returned normally.
        //     No catch/finally and no claim heapfree succeeded, GameAPPLIED or native callee executed.
        return new FreeEffectsApi170.Outcome(FreeEffectsApi170.Kind.CALLEE_RETURNED, 0L);
    }
}

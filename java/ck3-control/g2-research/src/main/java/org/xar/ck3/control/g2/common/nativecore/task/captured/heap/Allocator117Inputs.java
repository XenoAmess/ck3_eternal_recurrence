package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import java.util.List;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;

/** Literal normal-call roles of complete RF [424E2EC,424E361); no imported identity inferred. */
public final class Allocator117Inputs {
    private Allocator117Inputs() { }

    /** Exact mutable QWORD role of RIP5C5DE30; values are raw64, including zero. */
    public static final class HeapCell64 {
        public long value;
        public HeapCell64(long value) { this.value = value; }
    }

    public interface Calls {
        long allocateImported(long heapRaw, int flagsRaw32, long byteCountRaw);
        /** CALL424E250, with no argument registers explicitly prepared here. Unknown volatile inputs are not qualified. */
        int retryGate();
        /** CALL424CFFC, only incoming RCX=byteCountRaw and returned EAX32 are exposed. */
        int retryCall(long byteCountRaw);
        /** CALL423B18C; returned nonnull actual DWORD view, not an integer address/id. */
        Cell32 failureCell();
    }

    /** Input/callback scripts only, never expected target results or branch traces. */
    public record CaseSpec(String id, long countRaw, long elementBytesRaw, long initialHeapRaw,
            List<Long> allocationResults, List<Long> heapAfterAllocation,
            List<Integer> gateResults, List<Integer> retryResults,
            int selectedCell, int initialA, int initialB) {
        public CaseSpec {
            allocationResults = List.copyOf(allocationResults);
            heapAfterAllocation = List.copyOf(heapAfterAllocation);
            gateResults = List.copyOf(gateResults);
            retryResults = List.copyOf(retryResults);
            if (allocationResults.size() != heapAfterAllocation.size()
                    || allocationResults.size() > 4 || gateResults.size() > 4 || retryResults.size() > 4) {
                throw new IllegalArgumentException("Parallel allocation scripts; maximum four per list");
            }
            if (selectedCell < 0 || selectedCell > 1) {
                throw new IllegalArgumentException("Cell ordinal must be zero or one; both are nonnull");
            }
        }
    }
    public enum Kind { ALLOCATE, GATE, RETRY, FAILURE_CELL }
    /** Unused fields are zero. EAX results are zero-extended32; failure-cell result is an ordinal, never a pointer. */
    public record Event(Kind kind, long arg0, long arg1, long arg2, long result) { }
    public record Observation(long returnedRaw, int finalA, int finalB, List<Event> events) {
        public Observation { events = List.copyOf(events); }
    }
}

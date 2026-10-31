package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.HeapGlobalInit176Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.RequestAllocate424fda0;

/** Owned software sequence: call HeapGlobalInit176Candidate.init then RequestAllocate424fda0.allocate with SAME moduleBase/Memory exactly once each. */
public final class HeapGlobalInitRequestAllocate176Consumer {
    private HeapGlobalInitRequestAllocate176Consumer() { }

    public record Outcome(long initializationRaxBits, long allocationRaxBits) { }

    public static Outcome run(long moduleBase, long sizeBits, NativeTaskMemory memory,
            HeapGlobalInit176Inputs.Calls initialization, RequestAllocate424fda0.Ports allocation) {
        long initRax = HeapGlobalInit176Candidate.init(moduleBase, memory, initialization);
        long allocRax = RequestAllocate424fda0.allocate(moduleBase, sizeBits, memory, allocation);
        return new Outcome(initRax, allocRax);
    }
}
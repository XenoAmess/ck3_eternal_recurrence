package org.xar.ck3.control.g2.common.nativecore.task.captured.heap;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.HeapGlobalInit176Inputs.Calls;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs.HeapCell64;

public final class HeapGlobalInitAllocator117Consumer {
    public record Outcome(long initializationRaxBits, long allocationRaxBits) { }

    public static Outcome run(long moduleBase, long countRaw, long elementBytesRaw, HeapCell64 heap, Calls initialization, Allocator117Inputs.Calls allocation) {
        HeapCellMemory176 memory = new HeapCellMemory176(moduleBase, heap);
        long initializationRaxBits = HeapGlobalInit176Candidate.init(moduleBase, memory, initialization);
        long allocationRaxBits = Allocator117Candidate.allocate(countRaw, elementBytesRaw, heap, allocation);
        return new Outcome(initializationRaxBits, allocationRaxBits);
    }
}
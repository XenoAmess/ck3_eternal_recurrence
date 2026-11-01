package org.xar.ck3.research.m3.allocator241;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Candidate;
import org.xar.ck3.control.g2.common.nativecore.task.captured.heap.Allocator117Inputs;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs;
import org.xar.ck3.research.m3.allocator241.Allocator241Api;

public final class AllocatorReuse424E2EC241 {
    private AllocatorReuse424E2EC241() { }

    public static long execute(NativeTaskMemory memory, Allocator241Api.Ports ports, Allocator241Api.Input input) {
        long moduleBase = input.moduleBase();
        long countRaw = input.countRaw();
        long elementBytesRaw = input.elementBytesRaw();

        long heapGlobal = moduleBase + 0x5C5DE30L;
        long importSlot = moduleBase + 0x43DA768L;

        // Per-invocation mutable state holder to satisfy Java capture rules
        final Object[] state = new Object[3];
        state[0] = null; // recordedFailureAddress (Long)
        state[1] = null; // failureCellCreated (Boolean)
        state[2] = null; // privateCell (Cell32)

        Allocator117Inputs.Calls calls = new Allocator117Inputs.Calls() {
            @Override
            public long allocateImported(long heapRaw, int flagsRaw32, long byteCountRaw) {
                // Ignore heapRaw (private carrier value). Perform fresh reads as per protocol.
                long actualHeap = memory.readPointer(heapGlobal);
                long actualTarget = memory.readPointer(importSlot);

                // Forward to external port with observed values
                return ports.allocateImported(memory, 0x424E341L, actualTarget, actualHeap, flagsRaw32, byteCountRaw);
            }

            @Override
            public int retryGate() {
                return ports.retryGate(memory, 0x424E31DL);
            }

            @Override
            public int retryCall(long byteCountRaw) {
                return ports.retryCall(memory, 0x424E329L, byteCountRaw);
            }

            @Override
            public Free83Inputs.Cell32 failureCell() {
                // Call new address port first
                long addr = ports.failureCellAddress(memory, 0x424E34EL);

                // Record address and create private cell
                state[0] = Long.valueOf(addr);
                state[1] = Boolean.TRUE;
                Free83Inputs.Cell32 cell = new Free83Inputs.Cell32(0);
                state[2] = cell;

                return cell;
            }
        };

        // Create private heap carrier (value is ignored by adapter logic, used only as arg to allocateImported)
        Allocator117Inputs.HeapCell64 heapCarrier = new Allocator117Inputs.HeapCell64(0L);

        // Invoke mature algorithm exactly once
        long result = Allocator117Candidate.allocate(countRaw, elementBytesRaw, heapCarrier, calls);

        // Flush logic: only if failureCell was created and helper returned normally
        if (state[1] != null && (Boolean) state[1]) {
            long recordedFailureAddress = (Long) state[0];
            Free83Inputs.Cell32 privateCell = (Free83Inputs.Cell32) state[2];
            // WriteInt32 to the recorded address using the value from the private cell
            // The private cell's value was set to 0xC by Allocator117Candidate.fail
            memory.writeInt32(recordedFailureAddress, privateCell.value);
        }

        return result;
    }
}
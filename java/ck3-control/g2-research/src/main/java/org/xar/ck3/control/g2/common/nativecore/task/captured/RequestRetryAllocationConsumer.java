package org.xar.ck3.control.g2.common.nativecore.task.captured;

import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;
import org.xar.ck3.control.g2.common.nativecore.task.captured.cleanup.Free83Inputs.Cell32;

public final class RequestRetryAllocationConsumer {
    private RequestRetryAllocationConsumer() { }

    public interface Remainder {
        int call424e250();
        long heapAlloc(long heapHandleBits, int flagsBits, long bytesBits);
        Cell32 call423b18c();
    }

    public static RequestRetry4223b94.Ports ports(long moduleBase, NativeTaskMemory memory,
            Remainder remainder, RequestGate424cffc.Ports gate) {

        // Build allocation Ports for RequestAllocate424fda0
        RequestAllocate424fda0.Ports allocationPorts = new RequestAllocate424fda0.Ports() {
            @Override
            public int call424e250() {
                return remainder.call424e250();
            }

            @Override
            public int call424cffc(long knownRcx) {
                return RequestGate424cffc.execute(knownRcx, gate);
            }

            @Override
            public long heapAlloc(long heapHandleBits, int flagsBits, long bytesBits) {
                return remainder.heapAlloc(heapHandleBits, flagsBits, bytesBits);
            }

            @Override
            public Cell32 call423b18c() {
                return remainder.call423b18c();
            }
        };

        // Build Retry Ports for RequestRetry4223b94
        return new RequestRetry4223b94.Ports() {
            @Override
            public long call42420b8(long rcx) {
                return RequestAllocate424fda0.allocate(moduleBase, rcx, memory, allocationPorts);
            }

            @Override
            public int call424cffc(long rcx) {
                return RequestGate424cffc.execute(rcx, gate);
            }
        };
    }
}

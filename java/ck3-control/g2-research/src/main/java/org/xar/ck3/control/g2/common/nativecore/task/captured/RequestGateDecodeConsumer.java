package org.xar.ck3.control.g2.common.nativecore.task.captured;
import org.xar.ck3.control.g2.common.nativecore.task.NativeTaskMemory;

public final class RequestGateDecodeConsumer {
    private RequestGateDecodeConsumer() { }

    public static RequestGate424cffc.Ports gatePorts(long moduleBase, NativeTaskMemory memory,
            RequestDecode424d02c.Ports decoder, RequestGate424cffc.Ports remainder) {
        return new RequestGate424cffc.Ports() {
            @Override
            public long call424d02c(long knownRcx) {
                return RequestDecode424d02c.execute(moduleBase, memory, decoder);
            }

            @Override
            public int callIndirect43dbba8(long knownRcx, long liveRax) {
                return remainder.callIndirect43dbba8(knownRcx, liveRax);
            }
        };
    }
}

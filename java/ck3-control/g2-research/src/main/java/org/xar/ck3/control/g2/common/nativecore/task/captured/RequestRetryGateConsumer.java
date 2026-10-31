package org.xar.ck3.control.g2.common.nativecore.task.captured;

/** Consumer wiring for RequestRetry4223b94 and RequestGate424cffc. */
public final class RequestRetryGateConsumer {
    private RequestRetryGateConsumer() { }

    public static RequestRetry4223b94.Ports retryPorts(
            RequestRetry4223b94.Ports remainder,
            RequestGate424cffc.Ports gate) {
        return new RequestRetry4223b94.Ports() {
            @Override
            public long call42420b8(long rcx) {
                return remainder.call42420b8(rcx);
            }

            @Override
            public int call424cffc(long rcx) {
                return RequestGate424cffc.execute(rcx, gate);
            }
        };
    }
}

package org.xar.ck3.control.g2.common.nativecore.task.captured;

public final class RequestBlockRetryConsumer {
    private RequestBlockRetryConsumer() { }

    public static RequestBlock856db0.Ports ports(RequestRetry4223b94.Ports retryPorts) {
        return new RequestBlock856db0.Ports() {
            @Override
            public long call4223b94(long rcx) {
                return RequestRetry4223b94.execute(rcx, retryPorts);
            }
        };
    }
}

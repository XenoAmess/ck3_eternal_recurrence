package org.xar.ck3.control.nativebridge;

/** Local-service test constructor bridge; supplies no Root issuer or action authority. */
public final class PostAckReadTransportTestSupport {
    private PostAckReadTransportTestSupport() { }

    public static NativeGameTransport create(NativePacketPort endpoint, NativePipeEndpoint.Config config,
            int maximumFramesPerOperation, int maximumSubmissions) {
        return new NativeGameTransport(endpoint, config, maximumFramesPerOperation, maximumSubmissions);
    }
}

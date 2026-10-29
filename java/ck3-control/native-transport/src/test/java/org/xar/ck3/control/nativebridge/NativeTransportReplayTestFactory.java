package org.xar.ck3.control.nativebridge;

/** Shares the real packet replay constructor with offline tests in other packages. */
public final class NativeTransportReplayTestFactory {
    private NativeTransportReplayTestFactory() { }

    public static NativeGameTransport create(NativePacketPort endpoint, NativePipeEndpoint.Config config,
            int maximumFramesPerOperation, int maximumSubmissions) {
        return new NativeGameTransport(endpoint, config, maximumFramesPerOperation, maximumSubmissions);
    }
}

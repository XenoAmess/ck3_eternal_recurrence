package org.xar.ck3.control.nativebridge;

/** Test-source-only packet replay into the original transport state machine. */
public final class NativeGoalObservationFixture {
    private NativeGoalObservationFixture() { }

    public static NativeGameTransport receive(NativePacketPort packets,
            NativePipeEndpoint.Config configuration) {
        return new NativeGameTransport(packets, configuration, 16, 16);
    }

    public static NativeGameTransport receive(NativePacketPort packets,
            NativePipeEndpoint.Config configuration, int maximumFramesPerOperation,
            int maximumSubmissions) {
        return new NativeGameTransport(packets, configuration, maximumFramesPerOperation, maximumSubmissions);
    }
}

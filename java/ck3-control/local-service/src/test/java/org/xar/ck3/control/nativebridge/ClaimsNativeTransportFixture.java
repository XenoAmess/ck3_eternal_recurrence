package org.xar.ck3.control.nativebridge;

/** Test-only access to the actual transport constructor; no physical endpoint is created. */
public final class ClaimsNativeTransportFixture {
    private ClaimsNativeTransportFixture() { }
    public static NativeGameTransport create(NativePacketPort packets,NativePipeEndpoint.Config config) {
        return new NativeGameTransport(packets,config,16,16);
    }
}

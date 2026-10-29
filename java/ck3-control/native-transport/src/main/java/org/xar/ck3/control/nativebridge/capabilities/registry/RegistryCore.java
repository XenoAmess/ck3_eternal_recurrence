package org.xar.ck3.control.nativebridge.capabilities.registry;

import java.time.Instant;
import java.util.List;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.action.NativeActionPort;
import org.xar.ck3.control.nativebridge.NativeGameTransport;
import org.xar.ck3.control.nativebridge.NativeWire;

/** Actual standalone core/diagnostic producer on the single held transport. No reconstructed default diagnostics. */
public final class RegistryCore {
    public record CoreRequest(Instant deadline) { public CoreRequest { Objects.requireNonNull(deadline); } }
    public sealed interface CoreResult permits CoreKnown, CoreUnavailable { }
    public record CoreKnown(CoreFrame frame, NativeActionPort.AckReceived original) implements CoreResult {
        public CoreKnown { Objects.requireNonNull(frame); Objects.requireNonNull(original); }
    }
    public record CoreUnavailable(String reason, NativeActionPort.DispatchOutcome original) implements CoreResult {
        public CoreUnavailable { RegistryJson.require(reason != null && !reason.isEmpty(), "actual core refusal required"); Objects.requireNonNull(original); }
    }
    public record Capabilities(int formatVersion, String backendId, String mode, String source, String latency,
            boolean headless, boolean minimizedOperation, boolean visualFallback, boolean fallbackEnabled,
            NativeGameTransport.TransportDiagnostics diagnostics, Optional<List<String>> bridgeCapabilities,
            List<PublicRoutes.Info> publicMethods) {
        public Capabilities { Objects.requireNonNull(diagnostics); bridgeCapabilities = bridgeCapabilities.map(List::copyOf); publicMethods = List.copyOf(publicMethods); }
    }
    private final NativeGameTransport held;
    private final PublicRoutes routes;
    public RegistryCore(NativeGameTransport held, PublicRoutes routes) {
        this.held = Objects.requireNonNull(held, "sole held Native transport required"); this.routes = Objects.requireNonNull(routes);
    }
    public CoreResult query_core_frame_v1(CoreRequest request) throws InterruptedException {
        NativeActionPort.DispatchOutcome original = held.readCoreFrame(Objects.requireNonNull(request).deadline());
        if (!(original instanceof NativeActionPort.AckReceived ack) || !ack.nativeOk() || ack.originalResultToken().isEmpty())
            return new CoreUnavailable("original standalone core result is absent, rejected or UNKNOWN; no replay", original);
        try { return new CoreKnown(CoreFrame.decode(ack.originalResultToken().orElseThrow()),ack); }
        catch (IllegalArgumentException invalid) { return new CoreUnavailable("malformed original core prefix: " + invalid.getMessage(), original); }
    }
    public NativeGameTransport.TransportDiagnostics bridge_diagnostics() { return held.diagnostics(); }
    /** Raw hello advertisements and installed Java routes remain distinct; neither grants execution. */
    public Capabilities capabilities() {
        NativeGameTransport.TransportDiagnostics diagnostics = held.diagnostics();
        Optional<List<String>> actual = diagnostics.originalHello().map(value -> value.original().capabilities());
        return new Capabilities(1,"native-headless","native-headless","injected-dll-named-pipe","realtime",
                true,true,false,false,diagnostics,actual,routes.inventory());
    }
}


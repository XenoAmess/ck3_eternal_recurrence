package org.xar.ck3.control.wave2.governance.projection;

import java.util.List;
import java.util.Objects;
import java.util.function.Function;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.governance.focusscope.EducationFocusScopeProjectionPort;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext;
import org.xar.ck3.control.wave2.governance.government.GovernmentContextCodec;

/** One module service catalog; no native I/O, actions, writer or fallback. */
public final class GovernanceWave2ProjectionCatalog implements ProjectionPortCatalog {
    public GovernanceWave2ProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_GOVERNMENT_CONTEXT,
                        GovernmentContextCodec::decodeRequest, GovernmentContext::build, GovernmentContextCodec::encode)),
                RegisteredProjection.of(new TypedPort<>(ProjectionOperation.GOVERNANCE_GOVERNMENT_ADAPTER_NORMALIZE,
                        GovernmentContextCodec::decodeNormalizedAdapter, (GovernmentContext.Observation input) -> input, GovernmentContextCodec::encodeAdapter)),
                RegisteredProjection.of(new EducationFocusScopeProjectionPort()));
    }
    private record TypedPort<I, O>(ProjectionOperation operation, Function<byte[], I> decoder,
            Function<I, O> application, Function<O, byte[]> encoder) implements ProjectionPort<I, O> {
        private TypedPort {
            Objects.requireNonNull(operation); Objects.requireNonNull(decoder);
            Objects.requireNonNull(application); Objects.requireNonNull(encoder);
        }
        @Override public I decode(byte[] rawPayload) { return decoder.apply(rawPayload); }
        @Override public O project(I input) { return application.apply(input); }
        @Override public byte[] encode(O output) { return encoder.apply(output); }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }
}

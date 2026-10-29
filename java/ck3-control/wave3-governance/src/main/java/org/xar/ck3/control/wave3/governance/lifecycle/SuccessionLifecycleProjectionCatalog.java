package org.xar.ck3.control.wave3.governance.lifecycle;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;

/** Existing lifecycle leaves hosted by the one shared process; no lifecycle service or writer. */
public final class SuccessionLifecycleProjectionCatalog implements ProjectionPortCatalog {
    public SuccessionLifecycleProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new NormalizePort()), RegisteredProjection.of(new ConstructPort()), RegisteredProjection.of(new ConsumerPort()), RegisteredProjection.of(new AnchorPort()));
    }
    private abstract static class BoundedPort<I, O> implements ProjectionPort<I, O> {
        @Override public final int inputMaximumBytes() { return SuccessionLifecycleCodec.MAX_BYTES; }
        @Override public final int outputMaximumBytes() { return SuccessionLifecycleCodec.MAX_BYTES; }
    }
    public static final class NormalizePort extends BoundedPort<SuccessionLifecycleBinding, SuccessionLifecycleBinding> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.LIFECYCLE_NORMALIZE; }
        @Override public SuccessionLifecycleBinding decode(byte[] rawPayload) { return SuccessionLifecycleConsumerPort.decodeNormalizeRequest(rawPayload); }
        @Override public SuccessionLifecycleBinding project(SuccessionLifecycleBinding input) { return input; }
        @Override public byte[] encode(SuccessionLifecycleBinding output) { return SuccessionLifecycleCodec.encode(output); }
    }
    public static final class ConstructPort extends BoundedPort<SuccessionLifecycleConsumerPort.Constructor, SuccessionLifecycleBinding> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.LIFECYCLE_CONSTRUCT; }
        @Override public SuccessionLifecycleConsumerPort.Constructor decode(byte[] rawPayload) { return SuccessionLifecycleConsumerPort.decodeConstructorRequest(rawPayload); }
        @Override public SuccessionLifecycleBinding project(SuccessionLifecycleConsumerPort.Constructor input) { return SuccessionLifecycleConsumerPort.construct(input); }
        @Override public byte[] encode(SuccessionLifecycleBinding output) { return SuccessionLifecycleCodec.encode(output); }
    }
    public static final class ConsumerPort extends BoundedPort<SuccessionLifecycleConsumerPort.BindingRequest, SuccessionLifecycleBinding> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.LIFECYCLE_CONSUMER; }
        @Override public SuccessionLifecycleConsumerPort.BindingRequest decode(byte[] rawPayload) { return SuccessionLifecycleConsumerPort.decodeConsumerRequest(rawPayload); }
        @Override public SuccessionLifecycleBinding project(SuccessionLifecycleConsumerPort.BindingRequest input) { return SuccessionLifecycleConsumerPort.consume(input); }
        @Override public byte[] encode(SuccessionLifecycleBinding output) { return SuccessionLifecycleCodec.encode(output); }
    }
    public static final class AnchorPort extends BoundedPort<SuccessionLifecycleConsumerPort.AnchorRequest, SuccessionLifecycleBinding> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.LIFECYCLE_THREE_ANCHOR; }
        @Override public SuccessionLifecycleConsumerPort.AnchorRequest decode(byte[] rawPayload) { return SuccessionLifecycleConsumerPort.decodeAnchorRequest(rawPayload); }
        @Override public SuccessionLifecycleBinding project(SuccessionLifecycleConsumerPort.AnchorRequest input) { return SuccessionLifecycleConsumerPort.consume(input); }
        @Override public byte[] encode(SuccessionLifecycleBinding output) { return SuccessionLifecycleCodec.encode(output); }
    }
}

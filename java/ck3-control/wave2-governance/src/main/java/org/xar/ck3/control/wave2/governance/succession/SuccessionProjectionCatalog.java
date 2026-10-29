package org.xar.ck3.control.wave2.governance.succession;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import static org.xar.ck3.control.wave2.governance.succession.SuccessionModel.*;

/** Existing governance domain ports registered into the single shared Quarkus host. */
public final class SuccessionProjectionCatalog implements ProjectionPortCatalog {
    public SuccessionProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new FreezePort()), RegisteredProjection.of(new NormalizePort()), RegisteredProjection.of(new ReconcilePort()));
    }
    private abstract static class BoundedPort<I, O> implements ProjectionPort<I, O> {
        @Override public final int inputMaximumBytes() { return SuccessionCodec.MAX_BYTES; }
        @Override public final int outputMaximumBytes() { return SuccessionCodec.MAX_BYTES; }
    }
    public static final class FreezePort extends BoundedPort<SuccessionConsumerPort.FreezeRequest, Expectation> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.SUCCESSION_FREEZE; }
        @Override public SuccessionConsumerPort.FreezeRequest decode(byte[] rawPayload) { return SuccessionConsumerPort.decodeFreezeRequest(rawPayload); }
        @Override public Expectation project(SuccessionConsumerPort.FreezeRequest input) { return SuccessionConsumerPort.freeze(input); }
        @Override public byte[] encode(Expectation output) { return SuccessionCodec.encodeExpectation(output); }
    }
    public static final class NormalizePort extends BoundedPort<Expectation, Expectation> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.SUCCESSION_NORMALIZE; }
        @Override public Expectation decode(byte[] rawPayload) { return SuccessionConsumerPort.decodeNormalizeRequest(rawPayload); }
        @Override public Expectation project(Expectation input) { return input; }
        @Override public byte[] encode(Expectation output) { return SuccessionCodec.encodeExpectation(output); }
    }
    public static final class ReconcilePort extends BoundedPort<SuccessionConsumerPort.ReconcileRequest, Reconciliation> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.SUCCESSION_RECONCILE; }
        @Override public SuccessionConsumerPort.ReconcileRequest decode(byte[] rawPayload) { return SuccessionConsumerPort.decodeReconcileRequest(rawPayload); }
        @Override public Reconciliation project(SuccessionConsumerPort.ReconcileRequest input) { return SuccessionConsumerPort.reconcile(input); }
        @Override public byte[] encode(Reconciliation output) { return SuccessionCodec.encodeReconciliation(output); }
    }
}

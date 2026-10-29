package org.xar.ck3.control.wave2.events.projection;

import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionHostContext;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.events.interactionfallback.InteractionFallback;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence;
import org.xar.ck3.control.wave2.events.interactionreceipt.InteractionReceipt;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistry;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryCodec;
import org.xar.ck3.control.wave2.events.interactionregistry.InteractionRegistryReader;
import org.xar.ck3.control.wave2.events.unhandledevent.InteractionHostJson;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Existing interaction leaves share one host; only response assessment is independent of configured roots. */
public final class InteractionProjectionPortCatalog implements ProjectionPortCatalog {
    public InteractionProjectionPortCatalog() { }
    @Override public List<RegisteredProjection> registrations() { return List.of(RegisteredProjection.of(new ReceiptPort())); }
    @Override public List<RegisteredProjection> registrations(ProjectionHostContext context) {
        return context.eventSources().map(source -> List.of(RegisteredProjection.of(new LookupPort(source)), RegisteredProjection.of(new BeforePort(source)),
                RegisteredProjection.of(new ReceiptPort()), RegisteredProjection.of(new PlanPort(source)))).orElseGet(this::registrations);
    }
    private static ProjectionProtocolException unavailable() {
        return new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "configured interaction source context unavailable");
    }
    private record LookupPort(EventSourceReadContext configured) implements ProjectionPort<InteractionRegistry.Lookup, InteractionRegistry.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_INTERACTION_REGISTRY_LOOKUP; }
        @Override public int inputMaximumBytes() { return 4096; }
        @Override public int outputMaximumBytes() { return InteractionHostJson.WIRE_MAXIMUM; }
        @Override public InteractionRegistry.Lookup decode(byte[] raw) { return InteractionRegistryCodec.parseLookup(raw); }
        @Override public InteractionRegistry.Result project(InteractionRegistry.Lookup input) {
            try {
                TrustedEventSourceContext trusted = TrustedEventSourceContext.openEvidence(configured);
                SourceReviewedInteractionContinuation.verifyGui(trusted);
                if (!InteractionFallback.GUI_SHA256.equals(input.guiSha256())) throw new IllegalArgumentException("expected GUI assertion differs from actual stock source");
                return new InteractionRegistryReader(trusted.machineId()).load(trusted, input);
            } catch (TrustedEventSourceContext.UnavailableException unavailable) { throw unavailable(); }
        }
        @Override public byte[] encode(InteractionRegistry.Result result) { return InteractionHostJson.encodeRegistry(result); }
    }
    private record BeforePort(EventSourceReadContext configured) implements ProjectionPort<InteractionHostJson.BeforeInput, InteractionBeforeEvidence.Result> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_INTERACTION_BEFORE; }
        @Override public int inputMaximumBytes() { return InteractionHostJson.WIRE_MAXIMUM; }
        @Override public int outputMaximumBytes() { return InteractionHostJson.ORIGINAL_MAXIMUM; }
        @Override public InteractionHostJson.BeforeInput decode(byte[] raw) { return InteractionHostJson.decodeBefore(raw); }
        @Override public InteractionBeforeEvidence.Result project(InteractionHostJson.BeforeInput input) {
            try { return InteractionHostJson.before(input, TrustedEventSourceContext.openEvidence(configured)); }
            catch (TrustedEventSourceContext.UnavailableException unavailable) { throw unavailable(); }
        }
        @Override public byte[] encode(InteractionBeforeEvidence.Result result) { return InteractionHostJson.encodeBefore(result); }
    }
    private record ReceiptPort() implements ProjectionPort<InteractionHostJson.ReceiptRequest, InteractionHostJson.ReceiptOutput> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_INTERACTION_RECEIPT; }
        @Override public int inputMaximumBytes() { return InteractionHostJson.WIRE_MAXIMUM; }
        @Override public int outputMaximumBytes() { return 65_536; }
        @Override public InteractionHostJson.ReceiptRequest decode(byte[] raw) { return InteractionHostJson.decodeReceipt(raw); }
        @Override public InteractionHostJson.ReceiptOutput project(InteractionHostJson.ReceiptRequest input) { return InteractionHostJson.projectReceipt(input); }
        @Override public byte[] encode(InteractionHostJson.ReceiptOutput result) { return InteractionHostJson.encodeReceipt(result); }
    }
    private record PlanPort(EventSourceReadContext configured) implements ProjectionPort<SourceReviewedInteractionContinuation.Input, Optional<ObjectValue>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_INTERACTION_LEFT_PLAN; }
        @Override public int inputMaximumBytes() { return SourceReviewedInteractionContinuation.MAX_BYTES; }
        @Override public int outputMaximumBytes() { return SourceReviewedInteractionContinuation.MAX_BYTES; }
        @Override public SourceReviewedInteractionContinuation.Input decode(byte[] raw) { return SourceReviewedInteractionContinuation.decode(raw); }
        @Override public Optional<ObjectValue> project(SourceReviewedInteractionContinuation.Input input) {
            try { return SourceReviewedInteractionContinuation.plan(input, TrustedEventSourceContext.openEvidence(configured)); }
            catch (TrustedEventSourceContext.UnavailableException unavailable) { throw unavailable(); }
        }
        @Override public byte[] encode(Optional<ObjectValue> result) { return SourceReviewedInteractionContinuation.encode(result); }
    }
}

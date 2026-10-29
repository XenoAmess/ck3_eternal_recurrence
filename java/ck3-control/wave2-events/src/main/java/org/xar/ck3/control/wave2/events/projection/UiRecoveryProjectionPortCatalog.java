package org.xar.ck3.control.wave2.events.projection;

import java.util.List;
import org.xar.ck3.control.contracts.projection.EventSourceReadContext;
import org.xar.ck3.control.contracts.projection.ProjectionError;
import org.xar.ck3.control.contracts.projection.ProjectionHostContext;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.ProjectionProtocolException;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryOfflineJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;

/** Existing UI analyzer and known-evidence reader share the source-qualified host. */
public final class UiRecoveryProjectionPortCatalog implements ProjectionPortCatalog {
    public UiRecoveryProjectionPortCatalog() { }
    @Override public List<RegisteredProjection> registrations() { return List.of(); }
    @Override public List<RegisteredProjection> registrations(ProjectionHostContext context) {
        return context.eventSources().map(source -> List.of(RegisteredProjection.of(new Analyze(source)),
                RegisteredProjection.of(new Lookup(source)))).orElseGet(List::of);
    }
    private static ProjectionProtocolException unavailable() {
        return new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "configured UI recovery source context unavailable");
    }
    private record Analyze(EventSourceReadContext configured) implements ProjectionPort<UiRecoveryOfflineJson.AnalysisRequest, EvidenceDocument> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UI_RECOVERY_ANALYZE; }
        @Override public int inputMaximumBytes() { return UiRecoveryOfflineJson.ANALYSIS_MAX_BYTES; }
        @Override public int outputMaximumBytes() { return UiRecoveryOfflineJson.ANALYSIS_MAX_BYTES; }
        @Override public UiRecoveryOfflineJson.AnalysisRequest decode(byte[] raw) { return UiRecoveryOfflineJson.decodeAnalysis(raw); }
        @Override public EvidenceDocument project(UiRecoveryOfflineJson.AnalysisRequest input) {
            try { return UiRecoveryOfflineJson.analyze(input, configured); }
            catch (TrustedEventSourceContext.UnavailableException missing) { throw unavailable(); }
        }
        @Override public byte[] encode(EvidenceDocument output) { return UiRecoveryOfflineJson.encode(output); }
    }
    private record Lookup(EventSourceReadContext configured) implements ProjectionPort<UiRecoveryOfflineJson.LookupRequest, EvidenceDocument> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UI_RECOVERY_KNOWN_LOOKUP; }
        @Override public int inputMaximumBytes() { return UiRecoveryOfflineJson.LOOKUP_MAX_BYTES; }
        @Override public int outputMaximumBytes() { return UiRecoveryOfflineJson.LOOKUP_MAX_BYTES; }
        @Override public UiRecoveryOfflineJson.LookupRequest decode(byte[] raw) { return UiRecoveryOfflineJson.decodeLookup(raw); }
        @Override public EvidenceDocument project(UiRecoveryOfflineJson.LookupRequest input) {
            try { return UiRecoveryOfflineJson.lookup(input, configured); }
            catch (TrustedEventSourceContext.UnavailableException missing) { throw unavailable(); }
        }
        @Override public byte[] encode(EvidenceDocument output) { return UiRecoveryOfflineJson.encode(output); }
    }
}

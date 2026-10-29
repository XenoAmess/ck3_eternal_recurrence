package org.xar.ck3.control.wave2.events.projection;

import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.ObjectValue;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventEvidenceJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedPopulistReceipt;

/** Incident body composition only; output does not persist evidence or grant gameplay authority. */
public final class EventEvidenceProjectionCatalog implements ProjectionPortCatalog {
    public EventEvidenceProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() {
        return List.of(RegisteredProjection.of(new BeforePort()), RegisteredProjection.of(new AfterPort()), RegisteredProjection.of(new SourceReviewedReceiptPort()));
    }
    private record BeforePort() implements ProjectionPort<UnhandledEventEvidenceJson.BeforeInput, Optional<ObjectValue>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UNHANDLED_BEFORE; }
        @Override public int inputMaximumBytes() { return 1_048_576; }
        @Override public int outputMaximumBytes() { return 1_048_576; }
        @Override public UnhandledEventEvidenceJson.BeforeInput decode(byte[] raw) { return UnhandledEventEvidenceJson.decodeBefore(raw); }
        @Override public Optional<ObjectValue> project(UnhandledEventEvidenceJson.BeforeInput input) { return UnhandledEventEvidenceJson.before(input); }
        @Override public byte[] encode(Optional<ObjectValue> result) { return UnhandledEventEvidenceJson.encodeBody(result); }
    }
    private record AfterPort() implements ProjectionPort<UnhandledEventEvidenceJson.AfterInput, Optional<ObjectValue>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UNHANDLED_AFTER_BODY; }
        @Override public int inputMaximumBytes() { return 1_048_576; }
        @Override public int outputMaximumBytes() { return 1_048_576; }
        @Override public UnhandledEventEvidenceJson.AfterInput decode(byte[] raw) { return UnhandledEventEvidenceJson.decodeAfter(raw); }
        @Override public Optional<ObjectValue> project(UnhandledEventEvidenceJson.AfterInput input) { return UnhandledEventEvidenceJson.after(input); }
        @Override public byte[] encode(Optional<ObjectValue> result) { return UnhandledEventEvidenceJson.encodeBody(result); }
    }
    private record SourceReviewedReceiptPort() implements ProjectionPort<SourceReviewedPopulistReceipt.Input, Optional<ObjectValue>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UNHANDLED_RECEIPT_SOURCE_REVIEWED; }
        @Override public int inputMaximumBytes() { return 1_048_576; }
        @Override public int outputMaximumBytes() { return 16_384; }
        @Override public SourceReviewedPopulistReceipt.Input decode(byte[] raw) { return SourceReviewedPopulistReceipt.decode(raw); }
        @Override public Optional<ObjectValue> project(SourceReviewedPopulistReceipt.Input input) { return SourceReviewedPopulistReceipt.verify(input); }
        @Override public byte[] encode(Optional<ObjectValue> result) { return SourceReviewedPopulistReceipt.encodeResult(result); }
    }

}

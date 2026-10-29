package org.xar.ck3.control.wave2.events.projection;

import java.util.List;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.events.eventoutcome.EventOptionSubmissionClaim;

/** Pure document production. This port cannot create a claim, submit an event, or grant replay. */
public final class EventOptionClaimProjectionCatalog implements ProjectionPortCatalog {
    public EventOptionClaimProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() { return List.of(RegisteredProjection.of(new ClaimPort())); }
    private record ClaimPort() implements ProjectionPort<EventOptionSubmissionClaim.Request, EventOptionSubmissionClaim.Document> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_EVENT_OPTION_CLAIM_DOCUMENT; }
        @Override public int inputMaximumBytes() { return EventOptionSubmissionClaim.MAXIMUM_BYTES; }
        @Override public int outputMaximumBytes() { return EventOptionSubmissionClaim.MAXIMUM_BYTES; }
        @Override public EventOptionSubmissionClaim.Request decode(byte[] raw) { return EventOptionSubmissionClaim.decode(raw); }
        @Override public EventOptionSubmissionClaim.Document project(EventOptionSubmissionClaim.Request request) {
            return EventOptionSubmissionClaim.prepare(request);
        }
        @Override public byte[] encode(EventOptionSubmissionClaim.Document result) { return EventOptionSubmissionClaim.encode(result); }
    }
}

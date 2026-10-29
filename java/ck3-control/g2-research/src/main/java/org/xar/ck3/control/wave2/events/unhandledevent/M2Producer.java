package org.xar.ck3.control.wave2.events.unhandledevent;

import static org.xar.ck3.control.wave2.events.unhandledevent.RetainedJson.*;
import static org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewJson.*;

import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.wave2.events.interactionbefore.InteractionBeforeEvidence;
import org.xar.ck3.control.wave2.events.unhandledevent.InteractionHostJson;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedInteractionContinuation;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventEvidenceJson;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback;

/** Mechanical research entry into the existing producers; it owns no artifact or action writer. */
public final class M2Producer {
    private M2Producer() { }

    public record CaptureIdentity(String incidentId, String capturedAtUtc) {
        public CaptureIdentity {
            StrictJson.require(incidentId != null && incidentId.matches("[0-9a-f]{32}"), "original incident identity required");
            StrictJson.utc(capturedAtUtc);
        }
    }

    public record EventProduction(Optional<UnhandledEventFallback.Plan> proposal,
            ProjectionJson plan, ProjectionJson before) {
        public EventProduction {
            Objects.requireNonNull(proposal); Objects.requireNonNull(plan); Objects.requireNonNull(before);
        }
        public boolean actionAuthorized() { return false; }
        public boolean replayAllowed() { return false; }
    }

    public record InteractionProduction(Optional<ObjectValue> proposal,
            ProjectionJson plan, ProjectionJson before) {
        public InteractionProduction {
            Objects.requireNonNull(proposal); Objects.requireNonNull(plan); Objects.requireNonNull(before);
        }
        public boolean actionAuthorized() { return false; }
        public boolean replayAllowed() { return false; }
    }

    /** Raw JSON first reaches the original typed decoder; dedicated and already captured plans retain priority. */
    public static EventProduction event(ProjectionJson originalRequest,
            UnhandledEventFallback.ExistingPlan existing, CaptureIdentity identity) {
        Objects.requireNonNull(originalRequest); Objects.requireNonNull(existing); Objects.requireNonNull(identity);
        UnhandledEventFallback.Request request = UnhandledEventCodec.decodePlan(originalRequest.bytes());
        Optional<UnhandledEventFallback.Plan> proposal = UnhandledEventFallback.proposeForUnhandledPhase(existing, request);
        byte[] plan = UnhandledEventCodec.encode(proposal);
        if (proposal.isEmpty()) return new EventProduction(proposal, json(plan), json(encode(NULL)));
        UnhandledEventFallback.Plan selected = proposal.orElseThrow();
        ObjectValue planned = obj(f("snapshot_id", value(selected.binding().snapshotId())),
                f("revision", value(selected.binding().revision())),
                f("plan", UnhandledEventCodec.legacyPlan(selected)));
        var before = UnhandledEventEvidenceJson.before(new UnhandledEventEvidenceJson.BeforeInput(
                Optional.of(planned), identity.incidentId(), identity.capturedAtUtc()));
        return new EventProduction(proposal, json(plan), json(UnhandledEventEvidenceJson.encodeBody(before)));
    }

    /** The original native window, both role identities and GUI source guards remain in the existing producer. */
    public static InteractionProduction interaction(ProjectionJson originalRequest,
            TrustedEventSourceContext trusted, CaptureIdentity identity) {
        Objects.requireNonNull(originalRequest); Objects.requireNonNull(trusted); Objects.requireNonNull(identity);
        var request = SourceReviewedInteractionContinuation.decode(originalRequest.bytes());
        // The existing strategy caller gives dedicated choices and captured UNKNOWN attempts priority.
        if (request.originalPlan() instanceof ObjectValue existing
                && (!(v(existing, "selected_step") instanceof NullValue)
                    || v(existing, "unhandled_interaction_fallback") instanceof ObjectValue))
            return new InteractionProduction(Optional.empty(), json(encode(NULL)), json(encode(NULL)));
        Optional<ObjectValue> proposal = SourceReviewedInteractionContinuation.plan(request, trusted);
        byte[] plan = SourceReviewedInteractionContinuation.encode(proposal);
        if (proposal.isEmpty()) return new InteractionProduction(proposal, json(plan), json(encode(NULL)));
        ObjectValue snapshot = request.snapshot().orElseThrow();
        byte[] planned = encode(obj(f("snapshot_id", v(snapshot, "snapshot_id")), f("revision", v(snapshot, "revision")),
                f("plan", proposal.orElseThrow())));
        InteractionBeforeEvidence.Result before = InteractionHostJson.before(new InteractionHostJson.BeforeInput(
                new InteractionHostJson.Original(planned, sha(planned)), identity.incidentId(), identity.capturedAtUtc()), trusted);
        return new InteractionProduction(proposal, json(plan), json(InteractionHostJson.encodeBefore(before)));
    }

    /** Response evidence never turns an ACK or unknown response into action custody or replay permission. */
    public static ProjectionJson eventAfter(ProjectionJson originalRequest) {
        Objects.requireNonNull(originalRequest);
        return json(UnhandledEventEvidenceJson.encodeBody(UnhandledEventEvidenceJson.after(
                UnhandledEventEvidenceJson.decodeAfter(originalRequest.bytes()))));
    }

    public static ProjectionJson interactionAfter(ProjectionJson originalRequest) {
        Objects.requireNonNull(originalRequest);
        return json(InteractionHostJson.encodeReceipt(InteractionHostJson.projectReceipt(
                InteractionHostJson.decodeReceipt(originalRequest.bytes()))));
    }

    private static ProjectionJson json(byte[] raw) { return ProjectionJson.value(raw, 1_048_576); }
}

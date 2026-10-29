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
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedEventConsumer;
import org.xar.ck3.control.wave2.events.unhandledevent.SourceReviewedPlanJson;
import org.xar.ck3.control.wave2.events.unhandledevent.TrustedEventSourceContext;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.SourceReviewedMandatoryPlanner;
import org.xar.ck3.control.events.mandatorychoice.MandatoryChoiceModel.EvidenceDocument;

/** The full source-reading continuation is registered only with server-owned machine and filesystem context. */
public final class FullEventSourceProjectionCatalog implements ProjectionPortCatalog {
    public FullEventSourceProjectionCatalog() { }
    @Override public List<RegisteredProjection> registrations() { return List.of(); }
    @Override public List<RegisteredProjection> registrations(ProjectionHostContext context) {
        return context.eventSources().map(source -> List.of(RegisteredProjection.of(new ContinuationPort(source)),
                RegisteredProjection.of(new MandatoryPlanPort(source)))).orElseGet(List::of);
    }

    private record ContinuationPort(EventSourceReadContext configured)
            implements ProjectionPort<SourceReviewedPlanJson.Input, SourceReviewedEventConsumer.ReviewedPlan> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UNHANDLED_PLAN_SOURCE_REVIEWED; }
        @Override public int inputMaximumBytes() { return 1_048_576; }
        @Override public int outputMaximumBytes() { return 1_048_576; }
        @Override public SourceReviewedPlanJson.Input decode(byte[] raw) { return SourceReviewedPlanJson.decode(raw); }
        @Override public SourceReviewedEventConsumer.ReviewedPlan project(SourceReviewedPlanJson.Input input) {
            try {
                TrustedEventSourceContext trusted = TrustedEventSourceContext.open(configured);
                return SourceReviewedEventConsumer.continueWithExistingPlan(input.plan(), input.snapshot(), input.actionSteps(), trusted);
            } catch (TrustedEventSourceContext.UnavailableException error) {
                throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "configured event source context unavailable");
            }
        }
        @Override public byte[] encode(SourceReviewedEventConsumer.ReviewedPlan result) { return SourceReviewedPlanJson.encode(result); }
    }

    private record MandatoryPlanPort(EventSourceReadContext configured)
            implements ProjectionPort<SourceReviewedMandatoryPlanner.Input, EvidenceDocument> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_MANDATORY_CHOICE_PLAN_SOURCE_REVIEWED; }
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
        @Override public SourceReviewedMandatoryPlanner.Input decode(byte[] raw) { return SourceReviewedMandatoryPlanner.decode(raw); }
        @Override public EvidenceDocument project(SourceReviewedMandatoryPlanner.Input input) {
            try { return new SourceReviewedMandatoryPlanner(configured).plan(input); }
            catch (TrustedEventSourceContext.UnavailableException error) {
                throw new ProjectionProtocolException(ProjectionError.Code.OPERATION_UNAVAILABLE, "configured mandatory evidence context unavailable");
            }
        }
        @Override public byte[] encode(EvidenceDocument result) { return SourceReviewedMandatoryPlanner.encode(result); }
    }
}

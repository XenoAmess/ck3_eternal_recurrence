package org.xar.ck3.control.wave2.events.projection;

import java.util.List;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionOperation;
import org.xar.ck3.control.contracts.projection.ProjectionPort;
import org.xar.ck3.control.contracts.projection.ProjectionPortCatalog;
import org.xar.ck3.control.contracts.projection.RegisteredProjection;
import org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningJson;
import org.xar.ck3.control.wave2.events.choiceplanning.ChoicePlanningModel;
import org.xar.ck3.control.wave2.events.choiceplanning.MandatoryChoicePlanner;
import org.xar.ck3.control.wave2.events.mandatorybefore.MandatoryBeforeJson;
import org.xar.ck3.control.wave2.events.mandatorybefore.MandatoryBeforeModel;
import org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptJson;
import org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptModel;
import org.xar.ck3.control.wave2.events.mandatoryreceipt.MandatoryReceiptProducer;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoveryIdentityJson;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoverySourceFingerprint;
import org.xar.ck3.control.wave2.events.uirecoveryidentity.UiRecoverySourceModel;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventCodec;
import org.xar.ck3.control.wave2.events.unhandledevent.UnhandledEventFallback;

/** Pure typed projections. The unhandled candidate carries no source-review, file, native or writer authority. */
public final class EventsProjectionPortCatalog implements ProjectionPortCatalog {
    private static final List<RegisteredProjection> PORTS = List.of(
            RegisteredProjection.of(new MandatoryChoicePort()),
            RegisteredProjection.of(new UiFingerprintPort()),
            RegisteredProjection.of(new MandatoryBeforeProjection()),
            RegisteredProjection.of(new MandatoryReceiptProjection()),
            RegisteredProjection.of(new UnhandledCandidatePort()));

    public EventsProjectionPortCatalog() { }

    @Override public List<RegisteredProjection> registrations() { return PORTS; }

    private abstract static class BoundedPort<I, O> implements ProjectionPort<I, O> {
        @Override public int inputMaximumBytes() { return 65_536; }
        @Override public int outputMaximumBytes() { return 65_536; }
    }

    private static final class MandatoryChoicePort
            extends BoundedPort<ChoicePlanningModel.PlanningInput, ChoicePlanningModel.PlanningResult> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_MANDATORY_CHOICE_PLAN; }
        @Override public ChoicePlanningModel.PlanningInput decode(byte[] raw) { return ChoicePlanningJson.decode(raw); }
        @Override public ChoicePlanningModel.PlanningResult project(ChoicePlanningModel.PlanningInput input) {
            return new MandatoryChoicePlanner().plan(input);
        }
        @Override public byte[] encode(ChoicePlanningModel.PlanningResult result) { return ChoicePlanningJson.encode(result); }
    }

    private static final class UiFingerprintPort
            extends BoundedPort<UiRecoverySourceModel.Projection, Optional<UiRecoverySourceModel.Fingerprint>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UI_RECOVERY_FINGERPRINT; }
        @Override public UiRecoverySourceModel.Projection decode(byte[] raw) { return UiRecoveryIdentityJson.decode(raw); }
        @Override public Optional<UiRecoverySourceModel.Fingerprint> project(UiRecoverySourceModel.Projection input) {
            return switch (input) {
                case UiRecoverySourceModel.Ready ready -> new UiRecoverySourceFingerprint().identify(ready.input());
                case UiRecoverySourceModel.Unavailable unavailable -> Optional.empty();
            };
        }
        @Override public byte[] encode(Optional<UiRecoverySourceModel.Fingerprint> result) { return UiRecoveryIdentityJson.encode(result); }
    }

    private static final class MandatoryBeforeProjection
            extends BoundedPort<MandatoryBeforeModel.Input, MandatoryBeforeModel.BeforeBody> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_MANDATORY_BEFORE; }
        @Override public MandatoryBeforeModel.Input decode(byte[] raw) { return MandatoryBeforeJson.decode(raw); }
        @Override public MandatoryBeforeModel.BeforeBody project(MandatoryBeforeModel.Input input) {
            return new MandatoryBeforeModel.BeforeBody(input);
        }
        @Override public byte[] encode(MandatoryBeforeModel.BeforeBody result) { return MandatoryBeforeJson.encode(result); }
    }

    private static final class MandatoryReceiptProjection
            extends BoundedPort<MandatoryReceiptModel.Input, MandatoryReceiptModel.AfterResponse> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_MANDATORY_RECEIPT; }
        @Override public MandatoryReceiptModel.Input decode(byte[] raw) { return MandatoryReceiptJson.decode(raw); }
        @Override public MandatoryReceiptModel.AfterResponse project(MandatoryReceiptModel.Input input) {
            return new MandatoryReceiptProducer().produce(input);
        }
        @Override public byte[] encode(MandatoryReceiptModel.AfterResponse result) { return MandatoryReceiptJson.encode(result); }
    }

    private static final class UnhandledCandidatePort
            extends BoundedPort<UnhandledEventFallback.Request, Optional<UnhandledEventFallback.Plan>> {
        @Override public ProjectionOperation operation() { return ProjectionOperation.EVENTS_UNHANDLED_PLAN_CANDIDATE; }
        @Override public int inputMaximumBytes() { return 1_048_576; }
        @Override public int outputMaximumBytes() { return 1_048_576; }
        @Override public UnhandledEventFallback.Request decode(byte[] raw) { return UnhandledEventCodec.decodePlan(raw); }
        @Override public Optional<UnhandledEventFallback.Plan> project(UnhandledEventFallback.Request input) {
            return UnhandledEventFallback.plan(input);
        }
        @Override public byte[] encode(Optional<UnhandledEventFallback.Plan> result) { return UnhandledEventCodec.encode(result); }
    }
}

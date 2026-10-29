package org.xar.ck3.control.application.planning.campaign;

import java.io.IOException;
import java.util.Arrays;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.application.driver.DriverObservationAssembler;
import org.xar.ck3.control.application.driver.DriverObservationFacts;
import org.xar.ck3.control.application.driver.DriverSnapshotFacts;
import org.xar.ck3.control.application.driver.DriverStateAssembler;
import org.xar.ck3.control.application.planning.PlanningRequest;
import org.xar.ck3.control.continuity.writer.ContinuityStorePort;
import org.xar.ck3.control.application.session.OrdinaryCycleTransitions.SessionAuthority;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.contracts.StrictJson;
import org.xar.ck3.control.g2.m7.GoalCodec;
import org.xar.ck3.control.g2.m7.NativeCalendarObservation;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.wave2.governance.government.GovernmentContext;

/**
 * Captures the actual held planning frame and complete published Driver once.
 * The resulting supplier never observes another frame while evaluating that request.
 * This is a kernel input producer; it grants no episode, action, cycle or SAVE authority.
 */
public final class M7KernelInputs implements M7CampaignPolicies.GoalObservationSource {
    private final ContinuityStorePort writer;
    private final SessionAuthority writerAuthority;
    private final DriverStateAssembler drivers;
    private volatile Captured latest;

    public M7KernelInputs(ContinuityStorePort soleWriter, SessionAuthority actualWriterAuthority, DriverStateAssembler actualDrivers) {
        writer = Objects.requireNonNull(soleWriter); writerAuthority = Objects.requireNonNull(actualWriterAuthority);
        drivers = Objects.requireNonNull(actualDrivers);
    }

    /** Root calls inside the actual readiness writer lease, using its qualified EXE/source epoch. */
    public synchronized Captured capture(ContinuityStorePort.Session borrowed, PlanningRequest request,
            DriverObservationAssembler.Complete assembled, String sourceEpoch, ExactRef executable,
            Optional<GovernmentContext.Context> government) throws IOException {
        return capture(borrowed, request, assembled, Optional.of(sourceEpoch), Optional.of(executable), government);
    }

    /** Root calls inside the actual readiness writer lease, using its qualified EXE/source epoch. */
    public synchronized Captured capture(ContinuityStorePort.Session borrowed, PlanningRequest request,
            DriverObservationAssembler.Complete assembled, Optional<String> sourceEpoch, Optional<ExactRef> executable,
            Optional<GovernmentContext.Context> government) throws IOException {
        Objects.requireNonNull(borrowed); Objects.requireNonNull(request); Objects.requireNonNull(assembled);
        Objects.requireNonNull(sourceEpoch); Objects.requireNonNull(executable); Objects.requireNonNull(government);
        latest = null;
        writerAuthority.require(borrowed);
        String head = borrowed.head().digest();
        Captured result = drivers.withFrozenFacts(borrowed, frozen -> {
            StrictJson.require(frozen.state() instanceof DriverSnapshotFacts.Known,
                    "actual complete published Driver is required for M7 input capture");
            DriverSnapshotFacts.Known known = (DriverSnapshotFacts.Known) frozen.state();
            validateJoin(request, assembled, known);
            StrictJson.require(frozen.actions().headSha256().equals(head),
                    "M7 input capture crossed the original action/writer head");
            return new Captured(request, known.stamp(), assembled.originalEvidence(), head,
                    M7CampaignPolicies.projectGoal(request, sourceEpoch, executable, government));
        });
        writerAuthority.require(borrowed);
        StrictJson.require(head.equals(borrowed.head().digest()), "writer changed during M7 input capture");
        latest = result;
        return result;
    }

    /** One bounded request slot, installed only by a successful actual readiness capture. */
    @Override public Optional<M7CampaignPolicies.GoalInput> current(PlanningRequest request) {
        Objects.requireNonNull(request);
        Captured captured = latest;
        return captured != null && captured.request == request ? captured.current(request) : Optional.empty();
    }

    /** Pure producer/consumer join, independently callable by full-frame regression fixtures. */
    static void validateJoin(PlanningRequest request, DriverObservationAssembler.Complete assembled,
            DriverSnapshotFacts.Known known) {
        Objects.requireNonNull(request); Objects.requireNonNull(assembled); Objects.requireNonNull(known);
        StrictJson.require(request.before().equals(assembled.identity()) && request.source().equals(assembled.source())
                && request.sessionId().equals(assembled.sessionId())
                && request.observations().snapshot().equals(assembled.semantic()),
                "M7 request differs from the actual complete readiness observation");
        DriverObservationFacts facts = known.observation().orElseThrow(
                () -> new IllegalArgumentException("M7 requires the original published Driver observation facts"));
        StrictJson.require(facts.transport().machineId().equals(request.before().machineId())
                && facts.transport().game().equals(request.before().game())
                && facts.transport().sessionId().equals(request.sessionId())
                && facts.transport().connectionGeneration().equals(assembled.connectionGeneration())
                && facts.snapshotId().equals(request.before().frame().snapshotId())
                && facts.publicRevision().equals(request.before().frame().revision())
                && facts.nativeRevision().equals(request.before().frame().identity().nativeRevision())
                && facts.observationVersion() == request.before().observationVersion()
                && facts.source().equals(request.source())
                && known.stamp().game().equals(request.before().game())
                && known.stamp().episodeRunId().equals(request.before().frame().episodeRunId())
                && known.driver().session().actorId().equals(request.before().frame().identity().player())
                && Arrays.equals(known.driver().encode(), facts.driver().encode()),
                "M7 input crossed actual Game birth, transport, full Driver version, episode or native frame");
        OpportunityJson.Value goal = request.observations().snapshot().get("campaign_goal");
        switch (known.driver().campaignGoal()) {
            case org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Missing ignored ->
                    StrictJson.require(goal == null && request.observations().campaignGoal().isEmpty(),
                            "missing original goal was replaced by an invented kernel goal");
            case org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.NullValue ignored ->
                    StrictJson.require(goal == OpportunityJson.Nil.INSTANCE && request.observations().campaignGoal().isEmpty(),
                            "explicit null original goal changed at the M7 boundary");
            case org.xar.ck3.control.application.checkpoint.DriverStateSnapshot.Value retained -> {
                StrictJson.require(goal != null && request.observations().campaignGoal().isPresent(),
                        "original complete campaign goal is required by both consumers");
                StrictJson.require(OpportunityJson.parse(retained.json()).equals(goal)
                        && GoalCodec.parseGoal(OpportunityJson.toNode(goal)).equals(
                                request.observations().campaignGoal().orElseThrow()),
                        "M7 retained goal bytes, semantic goal and typed ordinary goal disagree");
            }
        }
        NativeCalendarObservation.project(request.before(), request.source(), assembled.semantic());
    }

    /** Immutable observation data; a later request must obtain its own actual readiness capture. */
    public static final class Captured implements M7CampaignPolicies.GoalObservationSource {
        private final PlanningRequest request;
        private final DriverSnapshotFacts.Stamp driverStamp;
        private final ExactRef originalNative;
        private final String writerHeadDigest;
        private final Optional<M7CampaignPolicies.GoalInput> input;
        private Captured(PlanningRequest request, DriverSnapshotFacts.Stamp driverStamp, ExactRef originalNative,
                String writerHeadDigest, Optional<M7CampaignPolicies.GoalInput> input) {
            this.request = request; this.driverStamp = driverStamp; this.originalNative = originalNative;
            this.writerHeadDigest = writerHeadDigest; this.input = input;
        }
        @Override public Optional<M7CampaignPolicies.GoalInput> current(PlanningRequest actual) {
            StrictJson.require(actual == request,
                    "captured M7 input belongs to the original held PlanningRequest instance");
            return input;
        }
        public DriverSnapshotFacts.Stamp driverStamp() { return driverStamp; }
        public ExactRef originalNative() { return originalNative; }
        public String writerHeadDigest() { return writerHeadDigest; }
    }
}

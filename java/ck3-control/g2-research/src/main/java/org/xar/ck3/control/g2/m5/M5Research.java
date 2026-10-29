package org.xar.ck3.control.g2.m5;

import java.util.Objects;
import org.xar.ck3.control.contracts.projection.ProjectionJson;
import org.xar.ck3.control.g2.common.G2Domain;
import org.xar.ck3.control.g2.common.G2Request;
import org.xar.ck3.control.g2.common.G2Response;
import org.xar.ck3.control.g2.common.Milestone;
import org.xar.ck3.control.g2.planning.ProposalLifecycleCodec;
import org.xar.ck3.control.planning.opportunity.OpportunityJson;
import org.xar.ck3.control.planning.opportunity.OpportunityJson.Obj;
import org.xar.ck3.control.wave2.planning.jointintake.FormalProposalIntake;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreats;
import org.xar.ck3.control.wave3.planning.participatingwar.ParticipatingWarThreatsCodec;

/**
 * Same-frame M5 analytic composition. Existing domain policies keep candidate value,
 * legality, ordering, reservations, submissions, and independent result verification.
 */
public final class M5Research implements G2Domain {
    /** Missing and explicit null remain distinct when a caller has no ordinary war plan. */
    public sealed interface ExistingWarPlan permits MissingPlan, NullPlan, ObservedPlan { }
    public record MissingPlan() implements ExistingWarPlan { }
    public record NullPlan() implements ExistingWarPlan { }
    public record ObservedPlan(Obj plan) implements ExistingWarPlan {
        public ObservedPlan { Objects.requireNonNull(plan, "original observed plan"); }
    }

    /**
     * The intake analysis contains the unchanged selected identity, budget, original
     * benefit evidence, and unpriced obligations. The war observation covers only
     * published player-participant wars; it supplies no purchase or peace authority.
     */
    public record Result(Obj intakeAnalysis, ParticipatingWarThreats.Observation participatingWars,
                         ExistingWarPlan existingWarPlan) {
        public Result {
            Objects.requireNonNull(intakeAnalysis, "original intake analysis");
            Objects.requireNonNull(participatingWars, "participating-war observation");
            Objects.requireNonNull(existingWarPlan, "original war-plan presence");
        }
    }

    @Override public Milestone milestone() { return Milestone.M5; }

    @Override public G2Response evaluate(G2Request request) {
        Objects.requireNonNull(request, "G2 request");
        if (request.milestone() != milestone()) {
            throw new IllegalArgumentException("M5 domain requires the M5 milestone");
        }
        M5PayloadCodec.OperationRequest operation = M5PayloadCodec.decodeOperation(request.payload().bytes());
        byte[] result = switch (operation) {
            case M5PayloadCodec.ContextRequest context -> M5PayloadCodec.encodeResult(assess(context.context()));
            case M5PayloadCodec.LifecycleRequest lifecycle -> ProposalLifecycleCodec.evaluateG2Payload(
                    lifecycle.payload().bytes(), request.source());
        };
        return new G2Response(request.requestId(), milestone(), request.source(),
                ProjectionJson.object(result, M5PayloadCodec.MAXIMUM_BYTES));
    }

    /** Pure decision-context inner payload; the G2 entry requires the explicit operation envelope. */
    public static byte[] evaluatePayload(byte[] payload) {
        return M5PayloadCodec.encodeResult(assess(M5PayloadCodec.decodeRequest(payload)));
    }

    /**
     * Runs the original migrated collector once, then derives scope facts from that
     * exact immutable input snapshot. An unavailable threat observation stays unknown
     * and does not erase otherwise valid candidates or fabricate a safer war scope.
     */
    public static Result assess(M5PayloadCodec.Request request) {
        Objects.requireNonNull(request, "M5 payload");
        Obj intake = request.intakeRequest();
        byte[] analysis = FormalProposalIntake.collect(OpportunityJson.encode(intake));
        Obj snapshot = OpportunityJson.object(intake.get("snapshot"), "original intake snapshot");
        ParticipatingWarThreats.Observation threats = ParticipatingWarThreatsCodec.observeSnapshot(
                OpportunityJson.encode(snapshot));
        return new Result(M5PayloadCodec.decodeAnalysis(analysis),
                threats, request.existingWarPlan());
    }
}

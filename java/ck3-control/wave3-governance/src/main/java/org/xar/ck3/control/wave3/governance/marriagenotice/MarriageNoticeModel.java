package org.xar.ck3.control.wave3.governance.marriagenotice;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.ObjectValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.WireValue;

/** Source knowledge and ordinary-plan projection are distinct from notification action authority. */
public final class MarriageNoticeModel {
    private MarriageNoticeModel() { }
    public sealed interface SourceContext permits UnknownContext, ContextFacts { }
    public record UnknownContext(WireValue original) implements SourceContext { public UnknownContext { Objects.requireNonNull(original); } }
    public record ContextFacts(String version, String executableSha256, String canonicalKey,
                               BigInteger deterministicKeyHash, String backendId) implements SourceContext { }
    public record ReviewInput(SourceContext context, WireValue historicalEvidence) {
        public ReviewInput { Objects.requireNonNull(context); Objects.requireNonNull(historicalEvidence); }
    }
    public sealed interface ReviewResult permits UnchangedEvidence, ReviewedEvidence { }
    public record UnchangedEvidence(WireValue evidence) implements ReviewResult { public UnchangedEvidence { Objects.requireNonNull(evidence); } }
    /** An offline source annotation; loaded definition and material results remain unqualified. */
    public record ReviewedEvidence(ObjectValue historicalEvidence) implements ReviewResult { public ReviewedEvidence { Objects.requireNonNull(historicalEvidence); } }

    public enum Classification { KNOWN_MARRIAGE_SPECIAL, EVIDENCE_INVALID, OTHER }
    public record Decision(Classification classification, String interactionKey, List<String> marriageContractGaps,
                           String definitionKey, BigInteger pendingInteractionId) {
        public Decision {
            Objects.requireNonNull(classification);
            marriageContractGaps = marriageContractGaps == null ? null : List.copyOf(marriageContractGaps);
            signedInstance(pendingInteractionId);
        }
    }
    public record Plan(ObjectValue original, String selectedStep, String phase, Decision decision) {
        public Plan { Objects.requireNonNull(original); }
    }
    public record PendingInteraction(BigInteger instanceId, Boolean autoAcceptNotification) {
        public PendingInteraction { Objects.requireNonNull(instanceId); signedInstance(instanceId); }
    }
    public record SnapshotView(WireValue original, PendingInteraction pendingInteraction,
                               boolean exclusiveModalPresent, boolean activeEventPresent, boolean currentEventPresent) {
        public SnapshotView { Objects.requireNonNull(original); }
    }
    public record ContinueInput(Plan blockedPlan, SnapshotView snapshot, List<String> actionSteps) {
        public ContinueInput { Objects.requireNonNull(blockedPlan); Objects.requireNonNull(snapshot); actionSteps = List.copyOf(actionSteps); }
    }
    public enum ProjectionScope { PLANNING_ONLY }
    public record OrdinaryProjection(ObjectValue snapshot, List<String> actionSteps, ProjectionScope scope) {
        public OrdinaryProjection { Objects.requireNonNull(snapshot); actionSteps = List.copyOf(actionSteps); Objects.requireNonNull(scope); }
    }
    @FunctionalInterface
    public interface OrdinaryChooser { Plan choose(OrdinaryProjection projection); }
    public sealed interface ContinuationResult permits UnchangedPlan, ContinuedPlan { }
    public record UnchangedPlan(Plan plan) implements ContinuationResult { public UnchangedPlan { Objects.requireNonNull(plan); } }
    public record ContinuedPlan(Plan ordinaryPlan, Plan deferredDiagnosis, BigInteger pendingInteractionId,
                                OrdinaryProjection projection) implements ContinuationResult {
        public ContinuedPlan { Objects.requireNonNull(ordinaryPlan); Objects.requireNonNull(deferredDiagnosis); Objects.requireNonNull(pendingInteractionId); Objects.requireNonNull(projection); }
    }
    private static void signedInstance(BigInteger value) {
        if (value != null && (value.compareTo(BigInteger.ONE.shiftLeft(31).negate()) < 0
                || value.compareTo(BigInteger.ONE.shiftLeft(31).subtract(BigInteger.ONE)) > 0
                || BigInteger.valueOf(-1).equals(value))) {
            throw new IllegalArgumentException("pending native signed-int32 generation identity or invalid sentinel");
        }
    }
}

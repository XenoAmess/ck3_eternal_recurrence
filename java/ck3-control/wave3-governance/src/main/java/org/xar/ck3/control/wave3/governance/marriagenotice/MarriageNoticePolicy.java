package org.xar.ck3.control.wave3.governance.marriagenotice;

import static org.xar.ck3.control.wave3.governance.marriagenotice.MarriageNoticeModel.*;

import java.math.BigInteger;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.Set;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.NullValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.ObjectValue;
import org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.WireValue;

/** Exact existing source-review and blocked-notification continuation rules, with no submit channel. */
public final class MarriageNoticePolicy {
    public static final String KEY = "arrange_marriage_interaction";
    public static final BigInteger KEY_HASH = BigInteger.valueOf(1_298_930_137);
    public static final String VERSION = "1.20.0.4";
    public static final String EXECUTABLE_SHA256 = "98702F88A547CDE2EAF29A85F93B85F68EE4CF8148336A4F7AFAEB75319DD518";
    public static final String BACKEND_ID = "ck3-1.20.0.4-native-pending-character-interaction-context-v1";
    public static final String SOURCE_SHA256 = "9481FD44A078F2D06034DD4A2107FE183F231D2B49D8B90F106C1D54F7A501F0";
    public static final String SOURCE_POLICY = "ck3-1.20.0.4-explicit-marriage-special-reject-only-v1";
    public static final String BLOCKED_PHASE = "pending_character_interaction_degraded_blocked";
    private static final Set<String> PENDING_STEPS = Set.of("accept-pending-character-interaction", "reject-pending-character-interaction",
            "block-pending-character-interaction", "acknowledge-pending-character-interaction", "query-pending-character-interaction-context-v1");
    private MarriageNoticePolicy() { }

    public static ReviewResult reviewSource(ReviewInput input) {
        if (!(input.historicalEvidence() instanceof ObjectValue history) || !(input.context() instanceof ContextFacts facts)
                || !VERSION.equals(facts.version()) || !EXECUTABLE_SHA256.equals(facts.executableSha256())
                || !KEY.equals(facts.canonicalKey()) || !KEY_HASH.equals(facts.deterministicKeyHash()) || !BACKEND_ID.equals(facts.backendId())) {
            return new UnchangedEvidence(input.historicalEvidence());
        }
        return new ReviewedEvidence(history);
    }

    public static boolean isBlockedReply(Plan plan) {
        Decision decision = plan.decision();
        return plan.selectedStep() == null && BLOCKED_PHASE.equals(plan.phase()) && decision != null
                && (decision.classification() == Classification.KNOWN_MARRIAGE_SPECIAL
                    || decision.classification() == Classification.EVIDENCE_INVALID && KEY.equals(decision.interactionKey())
                    && decision.marriageContractGaps() != null && !decision.marriageContractGaps().isEmpty())
                && KEY.equals(decision.definitionKey());
    }

    /** One canonical eligibility/projection path, shared by the callback seam and staged host operation. */
    public static Optional<OrdinaryProjection> prepareOrdinaryProjection(ContinueInput input) {
        Objects.requireNonNull(input);
        Plan blocked = input.blockedPlan(); SnapshotView snapshot = input.snapshot(); PendingInteraction pending = snapshot.pendingInteraction();
        if (!isBlockedReply(blocked) || !(snapshot.original() instanceof ObjectValue original) || pending == null
                || !Boolean.FALSE.equals(pending.autoAcceptNotification()) || !Objects.equals(pending.instanceId(), blocked.decision().pendingInteractionId())
                || snapshot.exclusiveModalPresent() || snapshot.activeEventPresent() || snapshot.currentEventPresent()) {
            return Optional.empty();
        }
        List<String> steps = input.actionSteps().stream().filter(step -> !PENDING_STEPS.contains(step)).toList();
        Map<String, WireValue> projected = new HashMap<>(original.values()); projected.put("pending_character_interaction", NullValue.INSTANCE);
        return Optional.of(new OrdinaryProjection(new ObjectValue(projected), steps, ProjectionScope.PLANNING_ONLY));
    }

    public static ContinuationResult continueOrdinary(ContinueInput input, OrdinaryChooser chooser) {
        Objects.requireNonNull(chooser);
        Optional<OrdinaryProjection> prepared = prepareOrdinaryProjection(input);
        if (prepared.isEmpty()) { return new UnchangedPlan(input.blockedPlan()); }
        OrdinaryProjection projection = prepared.orElseThrow();
        Plan blocked = input.blockedPlan(); List<String> steps = projection.actionSteps();
        PendingInteraction pending = input.snapshot().pendingInteraction();
        Plan ordinary = Objects.requireNonNull(chooser.choose(projection), "ordinary chooser returned no plan");
        String selected = ordinary.selectedStep();
        if (selected == null || !steps.contains(selected) || PENDING_STEPS.contains(selected)
                || ordinary.phase() != null && ordinary.phase().startsWith("pending_")) { return new UnchangedPlan(blocked); }
        return new ContinuedPlan(ordinary, blocked, pending.instanceId(), projection);
    }
}


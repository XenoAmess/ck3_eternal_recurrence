package org.xar.ck3.control.wave2.governance.betrothal;

import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;
import static org.xar.ck3.control.wave2.governance.betrothal.BetrothalModel.*;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.TreeSet;

/** Pure resource projection and existing-M5 adaptation; no reservation or action is performed. */
public final class BetrothalProposals {
    public static final String MODE = "fulfill_existing_betrothal";
    public static final String SUBMIT_STEP = "submit-current-first-heir-betrothal-fulfillment-v1-private";
    public static final String SCHEMA = "xar.ck3.current-betrothal-fulfillment-resource-proposal.v1";
    private static final ObjectValue NO_EXTENSIONS = new ObjectValue(Map.of());
    private static final List<String> UNPRICED = List.of("child_dynasty_result", "alliance_result",
            "alliance_war_obligation", "betrothal_break_cost");
    private BetrothalProposals() { }

    /** Retains the owning formal policy's selected/held value without independently authorizing it. */
    public static ResourceProposal build(BuildInput input) {
        Relation relation = input.relation();
        Actionability value = relation.actionability();
        Roles roles = new Roles(input.frame().playedCharacterId(), relation.heirCharacterId(),
                relation.betrothedCharacterId(), value.roles().recipient(), value.roles().intermediary());
        TreeSet<BigInteger> claims = new TreeSet<>();
        addPositive(claims, roles.actor()); addPositive(claims, roles.heir()); addPositive(claims, roles.partner());
        addPositive(claims, roles.recipient()); addPositive(claims, roles.intermediary());
        String key = roles.heir() == null ? null : "first-heir-marriage:" + roles.heir();
        ExistingCommitment commitment = new ExistingCommitment("native_bilateral_betrothal",
                relation.bilateralVerified(), roles.heir(), roles.partner(), key, MODE, false, NO_EXTENSIONS);
        return new ResourceProposal(SCHEMA, MODE, SUBMIT_STEP, input.frame(), relation.nativeRevision(),
                input.selected(), input.selected(), input.reasons(), roles, new ArrayList<>(claims), value.costs(), commitment,
                Boolean.TRUE.equals(value.readyToMarryBetrothed()) ? "complete_existing_adult_betrothal" : null,
                value.predictedOutcomeIfAccepted(), value.matrilinealOptionSelected(), value.nativeChildHousePreview(),
                relation.descendants(), relation.descendantsSummary(), value.effectiveMatrilinealIfAccepted(),
                value.recipientAiAcceptRaw(), value.recipientAnswerStatusRaw(), NullValue.INSTANCE, "unknown", UNPRICED,
                false, NO_EXTENSIONS);
    }

    /** Applies the original same-frame, zero-cost and role-binding gates. It does not re-evaluate native legality. */
    public static Opportunity adapt(AdaptInput input) {
        Frame frame = input.frame();
        ResourceProposal resource = input.plan().resourceProposal();
        if (resource == null || !SCHEMA.equals(resource.schema()) || !MODE.equals(resource.mode())
                || !SUBMIT_STEP.equals(input.plan().selectedStep()) || !SUBMIT_STEP.equals(resource.typedStep())
                || !Boolean.TRUE.equals(resource.selected()) || !Boolean.TRUE.equals(resource.formalActionReady())
                || !frame.equals(resource.sourceFrame()) || !frame.nativeRevision().equals(resource.sourceNativeRevision())) {
            throw new ProjectionDomainRejection("selected same-frame current-betrothal resource proposal required");
        }
        GenericCosts costs = resource.immediateGenericCosts();
        if (costs == null || !BigInteger.valueOf(100_000).equals(costs.rawScale().value())
                || !"actor".equals(costs.payerRole().value()) || !"on_send".equals(costs.applicationTiming().value())) {
            throw new ProjectionDomainRejection("current-betrothal joint proposal requires observed zero on-send costs");
        }
        for (CostTerm term : CostTerm.values()) {
            if (!BigInteger.ZERO.equals(costs.amounts().getOrDefault(term, Field.missing()).value())) {
                throw new ProjectionDomainRejection("current-betrothal joint proposal requires observed zero on-send costs");
            }
        }
        Roles roles = resource.roles();
        ExistingCommitment commitment = resource.existingCommitment();
        List<BigInteger> claims = resource.characterClaims();
        String commitmentKey = "first-heir-marriage:" + roles.heir();
        if (!positive(roles.heir()) || !positive(roles.partner()) || !positive(roles.recipient())
                || !Objects.equals(roles.actor(), frame.playedCharacterId()) || commitment == null
                || !Boolean.TRUE.equals(commitment.bilateralVerified())
                || !Boolean.FALSE.equals(commitment.newBetrothalCommitment())
                || !commitmentKey.equals(commitment.commitmentKey()) || claims == null) {
            throw new ProjectionDomainRejection("current-betrothal resource role binding is incomplete");
        }
        TreeSet<BigInteger> normalized = new TreeSet<>();
        for (BigInteger id : claims) { addPositive(normalized, id); }
        Set<BigInteger> required = new HashSet<>();
        required.add(frame.playedCharacterId()); required.add(roles.heir()); required.add(roles.partner()); required.add(roles.recipient());
        if (!claims.equals(new ArrayList<>(normalized)) || !normalized.containsAll(required)) {
            throw new ProjectionDomainRejection("current-betrothal resource role binding is incomplete");
        }
        return new Opportunity(frame, "marriage:fulfill-betrothal:" + roles.heir() + ":" + roles.partner() + ":" + roles.recipient(),
                costs.amounts().get(CostTerm.GOLD).value(),
                claims.stream().filter(id -> !id.equals(frame.playedCharacterId())).toList(), List.of(commitment.commitmentKey()), resource);
    }

    private static boolean positive(BigInteger value) { return value != null && value.signum() > 0; }
    private static void addPositive(Set<BigInteger> claims, BigInteger value) { if (positive(value)) { claims.add(value); } }
}

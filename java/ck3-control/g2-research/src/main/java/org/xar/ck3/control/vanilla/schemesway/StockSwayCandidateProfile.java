package org.xar.ck3.control.vanilla.schemesway;

import java.math.BigDecimal;
import java.util.List;
import java.util.Objects;
import java.util.OptionalInt;
import org.xar.ck3.control.contracts.ExactRef;
import org.xar.ck3.control.g2.common.G2Source;

/** Authored source references, never a replacement script evaluator, score, candidate enumeration or action. */
public final class StockSwayCandidateProfile {
    public static final long SOURCE_BYTES = 78098;
    public static final String SOURCE_SHA256 = "850bb20cae67eece4f4d423f0d2f5cee0c22a0457224b9b4eedcf109ad41e1d5";
    private StockSwayCandidateProfile() { }
    public enum Evidence { AUTHORED_STATIC, UNKNOWN_CURRENT_NATIVE_CALLER }
    public enum Tier { BARONY, COUNTY, DUCHY, KINGDOM, EMPIRE, HEGEMONY }
    public enum Group { LIEGE_AND_NEIGHBORING_RULERS, VASSALS_AND_PEER_VASSALS, COUNCILLORS }
    public enum Operation { ADD, FACTOR }
    public enum PredicateRef {
        INTRIGUE_TEMPTATION_FOCUS, RECIPIENT_VASSAL,
        PROSPECTIVE_VASSAL_WITH_AUTHORED_FAITH_TIER_AND_THREAT_FILTERS,
        LIBERTY_FACTION_AT_PEACE, CLAIMANT_FACTION_AT_PEACE, INDEPENDENCE_FACTION_AT_PEACE,
        VASSAL_FACTION_LEADER, VASSAL_NEGATIVE_OPINION, POWERFUL_VASSAL_NEGATIVE_OPINION,
        DIFFERENT_FAITH, TIER_DIFFERENCE_ABOVE_TWO_AND_NON_THEOCRATIC_LESSEE,
        MALICIOUS_ACTOR, AUTHORED_DIPLOMATIC_TRAIT_OR_BRANCH, RECIPIENT_CHILD_OF_ACTOR,
        ACTOR_CHILD_OF_RECIPIENT, RECIPIENT_CLAIM_ON_ACTOR_PRIMARY_TITLE,
        THEOCRATIC_LESSEE_OPINION_AT_MOST_FIFTY, CLAN_TAX_COLLECTOR_OPINION_AT_MOST_FIFTY
    }
    public record TargetGroup(Group group, OptionalInt maximum) {
        public TargetGroup { Objects.requireNonNull(group); Objects.requireNonNull(maximum); }
    }
    public record Cadence(Tier tier, int months) {
        public Cadence { Objects.requireNonNull(tier); if (months < 0) { throw new IllegalArgumentException("nonnegative authored cadence"); } }
    }
    /** Conditions remain referenced to the entire exact authored block; predicates are not reevaluated here. */
    public record ModifierReference(PredicateRef predicate, Operation operation, BigDecimal authoredOperand) {
        public ModifierReference { Objects.requireNonNull(predicate); Objects.requireNonNull(operation); Objects.requireNonNull(authoredOperand); }
    }
    public record Profile(G2Source source, List<TargetGroup> targetGroups, List<Cadence> cadence,
            BigDecimal authoredBase, List<ModifierReference> orderedModifierReferences,
            Evidence authoredEvidence, Evidence candidateEnumeratorEvidence, Evidence senderRankingEvidence) {
        public Profile {
            Objects.requireNonNull(source); targetGroups = List.copyOf(targetGroups); cadence = List.copyOf(cadence);
            Objects.requireNonNull(authoredBase); orderedModifierReferences = List.copyOf(orderedModifierReferences);
            Objects.requireNonNull(authoredEvidence); Objects.requireNonNull(candidateEnumeratorEvidence); Objects.requireNonNull(senderRankingEvidence);
        }
        public boolean computesScore() { return false; }
        public boolean completeNativeCandidatesClaimed() { return false; }
        public boolean submissionAuthorized() { return false; }
        public String currentEarlyGateKey() { return "is_available"; }
        public String authoredModifierBlockKey() { return "sway_interaction.ai_will_do"; }
        public int authoredModifierBlockFirstLine() { return 2401; }
        public int authoredModifierBlockLastLine() { return 2592; }
        public boolean authoredVisibilityOpinionCheckLast() { return true; }
    }

    public static Profile sourceBound(G2Source actualStockSource) {
        Objects.requireNonNull(actualStockSource); ExactRef ref = actualStockSource.sourceRef();
        if (!actualStockSource.exactBuild().equals("1.20.0.4") || ref.bytes() != SOURCE_BYTES || !ref.sha256().equals(SOURCE_SHA256)) {
            throw new IllegalArgumentException("exact .4 whole stock interaction source required; old build/source cannot be relabeled");
        }
        return new Profile(actualStockSource,
                List.of(new TargetGroup(Group.LIEGE_AND_NEIGHBORING_RULERS, OptionalInt.of(10)),
                        new TargetGroup(Group.VASSALS_AND_PEER_VASSALS, OptionalInt.of(10)),
                        new TargetGroup(Group.COUNCILLORS, OptionalInt.empty())),
                List.of(new Cadence(Tier.BARONY, 0), new Cadence(Tier.COUNTY, 120), new Cadence(Tier.DUCHY, 24),
                        new Cadence(Tier.KINGDOM, 6), new Cadence(Tier.EMPIRE, 6), new Cadence(Tier.HEGEMONY, 6)),
                new BigDecimal("10"), List.of(
                        modifier(PredicateRef.INTRIGUE_TEMPTATION_FOCUS, Operation.ADD, "-20"),
                        modifier(PredicateRef.RECIPIENT_VASSAL, Operation.ADD, "10"),
                        modifier(PredicateRef.PROSPECTIVE_VASSAL_WITH_AUTHORED_FAITH_TIER_AND_THREAT_FILTERS, Operation.ADD, "30"),
                        modifier(PredicateRef.LIBERTY_FACTION_AT_PEACE, Operation.ADD, "10"),
                        modifier(PredicateRef.CLAIMANT_FACTION_AT_PEACE, Operation.ADD, "20"),
                        modifier(PredicateRef.INDEPENDENCE_FACTION_AT_PEACE, Operation.ADD, "30"),
                        modifier(PredicateRef.VASSAL_FACTION_LEADER, Operation.FACTOR, "2"),
                        modifier(PredicateRef.VASSAL_NEGATIVE_OPINION, Operation.FACTOR, "3"),
                        modifier(PredicateRef.POWERFUL_VASSAL_NEGATIVE_OPINION, Operation.FACTOR, "4"),
                        modifier(PredicateRef.DIFFERENT_FAITH, Operation.FACTOR, "0.5"),
                        modifier(PredicateRef.TIER_DIFFERENCE_ABOVE_TWO_AND_NON_THEOCRATIC_LESSEE, Operation.FACTOR, "0.25"),
                        modifier(PredicateRef.MALICIOUS_ACTOR, Operation.FACTOR, "0.5"),
                        modifier(PredicateRef.AUTHORED_DIPLOMATIC_TRAIT_OR_BRANCH, Operation.FACTOR, "2"),
                        modifier(PredicateRef.RECIPIENT_CHILD_OF_ACTOR, Operation.FACTOR, "0.75"),
                        modifier(PredicateRef.ACTOR_CHILD_OF_RECIPIENT, Operation.FACTOR, "2"),
                        modifier(PredicateRef.RECIPIENT_CLAIM_ON_ACTOR_PRIMARY_TITLE, Operation.FACTOR, "0.25"),
                        modifier(PredicateRef.THEOCRATIC_LESSEE_OPINION_AT_MOST_FIFTY, Operation.FACTOR, "10"),
                        modifier(PredicateRef.CLAN_TAX_COLLECTOR_OPINION_AT_MOST_FIFTY, Operation.FACTOR, "10")),
                Evidence.AUTHORED_STATIC, Evidence.UNKNOWN_CURRENT_NATIVE_CALLER, Evidence.UNKNOWN_CURRENT_NATIVE_CALLER);
    }
    private static ModifierReference modifier(PredicateRef predicate, Operation operation, String operand) {
        return new ModifierReference(predicate, operation, new BigDecimal(operand));
    }
}

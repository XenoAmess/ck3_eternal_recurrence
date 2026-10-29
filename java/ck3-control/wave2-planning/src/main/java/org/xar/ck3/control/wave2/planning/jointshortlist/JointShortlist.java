package org.xar.ck3.control.wave2.planning.jointshortlist;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.NativeCharacterId;
import org.xar.ck3.control.finance.jointbudget.JointBudgetSelector;

/** Closed shortlist preparation. The existing dispatcher remains the only reservation authority. */
public final class JointShortlist {
    private JointShortlist() { }
    public enum Phase { fewer_than_five_priced_legal_candidates, assessed_comparison_prepared }
    public enum Domain { first_heir_marriage, marriage, war, council, building, diplomacy, lifestyle }
    public record Frame(BigInteger player, BigInteger nativeRevision, BigInteger dateRaw,
                        String snapshotId, BigInteger revision, String episodeRunId) {
        public Frame {
            NativeCharacterId.of(player); positive(nativeRevision); nonnegative(dateRaw); positive(revision);
            require(snapshotId != null && !snapshotId.isEmpty(), "snapshot identity required");
            require(episodeRunId != null && !episodeRunId.isEmpty(), "episode identity required");
        }
    }
    public record UnpricedCandidate(String candidateId, Domain domain, List<String> needed) {
        public UnpricedCandidate { Objects.requireNonNull(candidateId); Objects.requireNonNull(domain); needed = List.copyOf(needed); }
    }
    /** The original readback row is carried separately by the codec for lossless extension-field output. */
    public record RaisedSupply(BigInteger armyId, BigInteger currentSupplyRaw, BigInteger scale) {
        public RaisedSupply { Objects.requireNonNull(armyId); nonnegative(currentSupplyRaw); require(BigInteger.valueOf(100000).equals(scale), "supply scale"); }
    }
    public record CurrentWarResources(BigInteger treasuryRaw, List<BigInteger> activeWarIds,
                                      List<RaisedSupply> raisedSupply, boolean futureSupplyReady, boolean campaignCostReady) {
        public CurrentWarResources { Objects.requireNonNull(treasuryRaw); activeWarIds = List.copyOf(activeWarIds); raisedSupply = List.copyOf(raisedSupply); }
    }
    public record Prepared(Frame frame, int legalCandidateCount, int pricedCandidateCount,
                           List<UnpricedCandidate> unpricedCandidates, CurrentWarResources currentWarResources,
                           JointBudgetSelector.AssessedInput assessedInput) {
        public Prepared {
            Objects.requireNonNull(frame); unpricedCandidates = List.copyOf(unpricedCandidates);
            require(legalCandidateCount >= pricedCandidateCount && pricedCandidateCount >= 0, "candidate counts");
            require((pricedCandidateCount >= 5) == (assessedInput != null), "complete comparison requires typed selector input");
        }
        public Phase phase() { return assessedInput == null ? Phase.fewer_than_five_priced_legal_candidates : Phase.assessed_comparison_prepared; }
        public JointBudgetSelector.Result analyze() { return assessedInput == null ? null : JointBudgetSelector.select(assessedInput); }
        public boolean reservationCreated() { return false; }
        public boolean formalActionReady() { return false; }
    }
    public static List<String> missingInputs(Domain domain) {
        return switch (domain) {
            case first_heir_marriage -> List.of("marriage_or_betrothal_outcome", "alliance_value_and_long_term_obligation");
            case marriage -> List.of("marriage_outcome_and_long_term_obligation");
            case war -> List.of("declaration_bound_participants_and_allies", "future_route_supply_campaign_cost_and_exit_terms");
            case council -> List.of("common_policy_value");
            case building -> List.of("common_policy_value_and_payback");
            case diplomacy -> List.of("common_policy_value_and_faction_deadline");
            case lifestyle -> List.of("common_policy_value_and_perk_opportunity_cost");
        };
    }
    private static void positive(BigInteger value) { require(value != null && value.signum() > 0, "positive integer required"); }
    private static void nonnegative(BigInteger value) { require(value != null && value.signum() >= 0, "nonnegative integer required"); }
    static void require(boolean value, String message) { if (!value) { throw new IllegalArgumentException(message); } }
}

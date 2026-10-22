package org.xar.ck3.control.finance.jointbudget;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

/** Pure M5 analytic selector. It neither reserves resources nor emits an action. */
public final class JointBudgetSelector {
    private static final Set<String> OBSERVED_DOMAINS = Set.of("council", "building", "diplomacy", "lifestyle");
    private JointBudgetSelector() { }

    public enum Status { SELECTED, WAIT, MISSING_ASSESSMENTS }
    public enum Reason {
        ELIGIBLE, NONPOSITIVE_NET_VALUE, SHARED_GOLD_BUDGET, PROJECTED_SUPPLY_DEFICIT,
        ARMY_NOT_CONTROLLABLE, EXISTING_COMMITMENT_CONFLICT, WAR_SLOT_BUDGET
    }

    public record Frame(BigInteger player, BigInteger nativeRevision, BigInteger dateRaw) {
        public Frame { positive(player); positive(nativeRevision); nonnegative(dateRaw); }
    }

    /** Null means the old producer's explicit get()/missing projection, never a numeric zero. */
    public record ProposalFrame(Frame identity, String snapshotId, BigInteger revision, String episodeRunId) {
        public ProposalFrame { Objects.requireNonNull(identity); }
    }

    public record Claims(Set<BigInteger> armyIds, Set<BigInteger> allyCharacterIds,
                         Set<BigInteger> characterIds, Set<String> commitmentKeys) {
        public Claims {
            armyIds = Set.copyOf(armyIds); allyCharacterIds = Set.copyOf(allyCharacterIds);
            characterIds = Set.copyOf(characterIds); commitmentKeys = Set.copyOf(commitmentKeys);
            armyIds.forEach(JointBudgetSelector::nonnegative);
            allyCharacterIds.forEach(JointBudgetSelector::positive);
            characterIds.forEach(JointBudgetSelector::positive);
            commitmentKeys.forEach(value -> require(!value.isEmpty(), "empty commitment key"));
        }
        public boolean overlaps(Claims other) {
            return intersects(armyIds, other.armyIds) || intersects(allyCharacterIds, other.allyCharacterIds)
                    || intersects(characterIds, other.characterIds) || intersects(commitmentKeys, other.commitmentKeys);
        }
    }

    public record Values(BigInteger benefitUnits, BigInteger warCostUnits, BigInteger familyCostUnits,
                         BigInteger diplomacyCostUnits, BigInteger supplyCostUnits, BigInteger longTermCostUnits) {
        public Values {
            nonnegative(benefitUnits); nonnegative(warCostUnits); nonnegative(familyCostUnits);
            nonnegative(diplomacyCostUnits); nonnegative(supplyCostUnits); nonnegative(longTermCostUnits);
        }
        public BigInteger net() {
            return benefitUnits.subtract(warCostUnits).subtract(familyCostUnits).subtract(diplomacyCostUnits)
                    .subtract(supplyCostUnits).subtract(longTermCostUnits);
        }
    }

    public record Proposal(String candidateId, String domain, boolean domainPolicyReady, ProposalFrame frame,
                           BigInteger goldCostRaw, Claims claims, BigInteger projectedSupplyMarginRaw,
                           BigInteger warSlotClaim, BigInteger minimumGoldReserveRaw) {
        public Proposal {
            Objects.requireNonNull(candidateId); Objects.requireNonNull(domain); Objects.requireNonNull(frame);
            Objects.requireNonNull(claims); nonnegative(goldCostRaw); nonnegative(warSlotClaim);
            nonnegative(minimumGoldReserveRaw);
        }
    }

    public record Candidate(String candidateId, String domain, BigInteger subjectCharacterId,
                            BigInteger candidateCharacterId, Proposal proposal) {
        public Candidate { Objects.requireNonNull(candidateId); Objects.requireNonNull(domain); }
    }
    public record Intake(ProposalFrame frame, List<Candidate> candidates) {
        public Intake {
            Objects.requireNonNull(frame); candidates = List.copyOf(candidates);
            Set<String> seen = new HashSet<>();
            for (Candidate candidate : candidates) { require(seen.add(candidate.candidateId), "duplicate candidate identity"); }
        }
    }
    public record Army(BigInteger id, boolean controllable) {
        public Army { Objects.requireNonNull(id); }
    }
    public record Snapshot(Frame frame, BigInteger goldRaw, Set<BigInteger> activeWarIds, List<Army> armies) {
        public Snapshot {
            Objects.requireNonNull(frame); Objects.requireNonNull(goldRaw);
            activeWarIds = Set.copyOf(activeWarIds); armies = List.copyOf(armies);
            Set<BigInteger> seen = new HashSet<>();
            for (Army army : armies) { require(seen.add(army.id), "duplicate army identity"); }
        }
    }
    public record Commitments(BigInteger goldRaw, BigInteger pendingWarSlots, Claims claims) {
        public Commitments { nonnegative(goldRaw); nonnegative(pendingWarSlots); Objects.requireNonNull(claims); }
    }
    public record Assessment(String candidateId, Frame frame, Values values, BigInteger goldRaw,
                             BigInteger projectedSupplyMarginUnits, Claims claims) {
        public Assessment {
            Objects.requireNonNull(candidateId); Objects.requireNonNull(frame); Objects.requireNonNull(values);
            nonnegative(goldRaw); Objects.requireNonNull(projectedSupplyMarginUnits); Objects.requireNonNull(claims);
        }
    }
    public sealed interface Input permits MissingAssessments, AssessedInput { }
    /** The old producer returns before reading treasury, army, or budget amounts in this branch. */
    public record MissingAssessments(Intake intake) implements Input {
        public MissingAssessments { Objects.requireNonNull(intake); }
    }
    public record AssessedInput(Intake intake, Snapshot snapshot, List<Assessment> assessments,
                                Commitments commitments, BigInteger goldReserveRaw,
                                BigInteger maxActiveWars) implements Input {
        public AssessedInput {
            Objects.requireNonNull(intake); Objects.requireNonNull(snapshot); assessments = List.copyOf(assessments);
            Objects.requireNonNull(commitments); nonnegative(goldReserveRaw); nonnegative(maxActiveWars);
            require(assessments.size() >= 5, "at least five assessed legal rows required");
            require(intake.frame.identity.equals(snapshot.frame), "crossed the paused native frame");
        }
    }
    public record Evaluated(String candidateId, String domain, BigInteger netUnits, Reason reason,
                            Values valueComponents, BigInteger goldRaw, BigInteger warSlotClaim,
                            BigInteger minimumGoldReserveRaw, BigInteger projectedSupplyMarginUnits,
                            Claims claims) { }
    public record Result(Status status, Frame frame, int unassessedLegalCandidateCount,
                         List<Evaluated> evaluated, String selectedCandidateId) {
        public Result { evaluated = List.copyOf(evaluated); }
        public boolean formalActionReady() { return false; }
    }

    public static Result select(Input input) {
        Objects.requireNonNull(input);
        if (input instanceof MissingAssessments missing) {
            return new Result(Status.MISSING_ASSESSMENTS, missing.intake.frame.identity,
                    missing.intake.candidates.size(), List.of(), null);
        }
        AssessedInput request = (AssessedInput) input;
        List<Evaluated> evaluated = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        Map<String, Candidate> legal = new HashMap<>();
        request.intake.candidates.forEach(candidate -> legal.put(candidate.candidateId, candidate));
        Set<BigInteger> usableArmies = new HashSet<>();
        request.snapshot.armies.stream().filter(Army::controllable).forEach(army -> usableArmies.add(army.id));
        for (Assessment assessment : request.assessments) {
            require(seen.add(assessment.candidateId), "duplicate assessment candidate");
            Candidate candidate = legal.get(assessment.candidateId);
            require(candidate != null, "assessment candidate absent from intake");
            require(assessment.frame.equals(request.intake.frame.identity), "assessment crossed the paused native frame");
            Proposal proposal = candidate.proposal;
            if (candidate.domain.equals("first_heir_marriage")) {
                require(candidate.subjectCharacterId != null && candidate.candidateCharacterId != null
                        && assessment.claims.characterIds.contains(candidate.subjectCharacterId)
                        && assessment.claims.characterIds.contains(candidate.candidateCharacterId), "family must claim both marriage roles");
            } else if (OBSERVED_DOMAINS.contains(candidate.domain) || proposal != null) {
                require(proposal != null && proposal.candidateId.equals(candidate.candidateId)
                        && proposal.domain.equals(candidate.domain) && proposal.domainPolicyReady
                        && proposal.frame.equals(request.intake.frame), "observed proposal not bound to intake");
                require(assessment.goldRaw.equals(proposal.goldCostRaw) && assessment.claims.equals(proposal.claims),
                        "assessed resource claims differ from observation");
                require(candidate.domain.equals("war") ? assessment.projectedSupplyMarginUnits.equals(proposal.projectedSupplyMarginRaw)
                        : assessment.projectedSupplyMarginUnits.signum() == 0, "assessed route supply differs from observation");
            } else { require(candidate.domain.equals("war"), "unknown M5 candidate domain"); }
            BigInteger warSlots = proposal == null ? (candidate.domain.equals("war") ? BigInteger.ONE : BigInteger.ZERO) : proposal.warSlotClaim;
            BigInteger minimumReserve = proposal == null ? BigInteger.ZERO : proposal.minimumGoldReserveRaw;
            BigInteger net = assessment.values.net();
            Reason reason;
            if (net.signum() <= 0) { reason = Reason.NONPOSITIVE_NET_VALUE; }
            else if (assessment.goldRaw.add(request.commitments.goldRaw)
                    .add(request.goldReserveRaw.max(minimumReserve)).compareTo(request.snapshot.goldRaw) > 0) { reason = Reason.SHARED_GOLD_BUDGET; }
            else if (assessment.projectedSupplyMarginUnits.signum() < 0) { reason = Reason.PROJECTED_SUPPLY_DEFICIT; }
            else if (!usableArmies.containsAll(assessment.claims.armyIds)) { reason = Reason.ARMY_NOT_CONTROLLABLE; }
            else if (assessment.claims.overlaps(request.commitments.claims)) { reason = Reason.EXISTING_COMMITMENT_CONFLICT; }
            else if (warSlots.signum() != 0 && BigInteger.valueOf(request.snapshot.activeWarIds.size())
                    .add(request.commitments.pendingWarSlots).add(warSlots).compareTo(request.maxActiveWars) > 0) { reason = Reason.WAR_SLOT_BUDGET; }
            else { reason = Reason.ELIGIBLE; }
            evaluated.add(new Evaluated(candidate.candidateId, candidate.domain, net, reason, assessment.values,
                    assessment.goldRaw, warSlots, minimumReserve, assessment.projectedSupplyMarginUnits, assessment.claims));
        }
        Evaluated selected = evaluated.stream().filter(row -> row.reason == Reason.ELIGIBLE)
                .min(Comparator.comparing(Evaluated::netUnits).reversed()
                        .thenComparing(Evaluated::candidateId, JointBudgetSelector::comparePythonText)).orElse(null);
        return new Result(selected == null ? Status.WAIT : Status.SELECTED, request.intake.frame.identity,
                request.intake.candidates.size() - evaluated.size(), evaluated, selected == null ? null : selected.candidateId);
    }

    /** Python str ordering compares Unicode scalar values, not UTF-16 code units. */
    public static int comparePythonText(String first, String second) {
        int left = 0; int right = 0;
        while (left < first.length() && right < second.length()) {
            int a = first.codePointAt(left); int b = second.codePointAt(right);
            if (a != b) { return Integer.compare(a, b); }
            left += Character.charCount(a); right += Character.charCount(b);
        }
        return Integer.compare(first.length() - left, second.length() - right);
    }
    private static <T> boolean intersects(Set<T> first, Set<T> second) {
        return first.stream().anyMatch(second::contains);
    }
    private static void positive(BigInteger value) { require(value != null && value.signum() > 0, "positive integer required"); }
    private static void nonnegative(BigInteger value) { require(value != null && value.signum() >= 0, "nonnegative integer required"); }
    static void require(boolean condition, String message) { if (!condition) { throw new IllegalArgumentException(message); } }
}

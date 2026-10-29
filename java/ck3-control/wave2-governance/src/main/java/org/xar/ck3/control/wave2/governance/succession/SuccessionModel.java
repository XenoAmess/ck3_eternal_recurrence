package org.xar.ck3.control.wave2.governance.succession;

import java.math.BigInteger;
import java.util.List;
import java.util.Objects;
import org.xar.ck3.control.contracts.NativeCharacterId;

/** Immutable projections of the original succession wire contract; no authority or IO. */
public final class SuccessionModel {
    private SuccessionModel() { }
    public static final String EXPECTATION_SCHEMA = "xar.ck3.succession-expectation/v1";
    public static final String RECONCILIATION_SCHEMA = "xar.ck3.succession-reconciliation/v1";
    public static final String OPERATING_SCHEMA = "xar.ck3.ordinary-succession-operating-context/v1";
    private static final BigInteger UINT64_MAX = BigInteger.ONE.shiftLeft(64).subtract(BigInteger.ONE);

    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, int dateRaw) {
        public Frame { nonempty(snapshotId); uint64(revision); uint64(nativeRevision); }
    }
    public record Binding(Frame frame, String episodeRunId, int episodeCharacterId) {
        public Binding { Objects.requireNonNull(frame); nonempty(episodeRunId); character(episodeCharacterId); }
    }
    /** Exact original extensible title object bytes, alongside the fields this leaf consumes. */
    public record Title(int titleId, BigInteger integerTier, WireObject original) {
        public Title { positive(titleId); Objects.requireNonNull(original); }
    }
    public record WireObject(byte[] bytes) {
        public WireObject { Objects.requireNonNull(bytes); bytes = bytes.clone(); }
        @Override public byte[] bytes() { return bytes.clone(); }
    }
    public record TitleRow(Title title, Integer firstHeirCharacterId, boolean primary) {
        public TitleRow { Objects.requireNonNull(title); nullableCharacter(firstHeirCharacterId); }
    }
    public enum ExpectationState { SUCCESSOR_EXPECTED, NO_PRIMARY_HEIR }
    public enum RiskState { SINGLE_SUCCESSOR, SPLIT_SUCCESSORS, NO_PRIMARY_HEIR }
    public record Expectation(Binding binding, ExpectationState state, int predecessorCharacterId,
            Integer expectedSuccessorCharacterId, List<TitleRow> titleExpectations, RiskState riskState) {
        public Expectation {
            Objects.requireNonNull(binding); Objects.requireNonNull(state); character(predecessorCharacterId);
            nullableCharacter(expectedSuccessorCharacterId); titleExpectations = List.copyOf(titleExpectations);
            Objects.requireNonNull(riskState);
            check(binding.episodeCharacterId() == predecessorCharacterId, "predecessor binding disagrees");
            check((expectedSuccessorCharacterId == null) == (state == ExpectationState.NO_PRIMARY_HEIR), "expectation state disagrees");
            check((expectedSuccessorCharacterId == null) == (riskState == RiskState.NO_PRIMARY_HEIR), "risk and successor disagree");
            check(!Objects.equals(expectedSuccessorCharacterId, predecessorCharacterId), "expectation points to predecessor");
            int prior = 0, primaryCount = 0; Integer primaryHeir = null;
            for (TitleRow row : titleExpectations) {
                check(row.title().titleId() > prior, "title order is not canonical"); prior = row.title().titleId();
                check(!Objects.equals(row.firstHeirCharacterId(), predecessorCharacterId), "title points to predecessor");
                if (row.primary()) { primaryCount++; primaryHeir = row.firstHeirCharacterId(); }
            }
            check(primaryCount == 1 && Objects.equals(primaryHeir, expectedSuccessorCharacterId), "primary title disagrees");
        }
        public TitleRow primary() { return titleExpectations.stream().filter(TitleRow::primary).findFirst().orElseThrow(); }
    }
    public record Actor(int characterId, boolean alive) { public Actor { character(characterId); } }
    public enum Lifecycle { ORDINARY_CAMPAIGN_SUCCESSION, ROGUE_ONE_LIFE, UNKNOWN }
    public record Snapshot(Frame frame, String episodeRunId, Integer episodeCharacterId, Boolean paused,
            Boolean mapReady, Boolean terminal, String terminalReason, Actor actor,
            boolean activeEvent, boolean pendingInteraction, Lifecycle lifecycle) {
        public Snapshot { nullableCharacter(episodeCharacterId); }
    }
    /** Only available/partial original bundles reach this model. */
    public record TurnBundle(Frame frame, Actor ruler, List<TitleRow> titleRows,
            Integer primaryHeirCharacterId, RiskState riskState) {
        public TurnBundle {
            Objects.requireNonNull(frame); Objects.requireNonNull(ruler); titleRows = List.copyOf(titleRows);
            nullableCharacter(primaryHeirCharacterId); int primaries = 0; java.util.Set<Integer> ids = new java.util.HashSet<>();
            for (TitleRow row : titleRows) { check(ids.add(row.title().titleId()), "duplicate title"); if (row.primary()) { primaries++; } }
            check(primaries == 1, "exactly one primary required");
        }
    }
    public enum Verdict { MATCHED, UNEXPECTED_SUCCESSOR, TITLE_DISTRIBUTION_MISMATCH }
    public record Reconciliation(Binding predecessorBinding, Frame successorBinding, int predecessorCharacterId,
            Integer expectedSuccessorCharacterId, int actualSuccessorCharacterId, boolean successorMatch,
            List<Integer> expectedInheritedTitleIds, List<Integer> matchedInheritedTitleIds,
            List<Integer> missingExpectedInheritedTitleIds, List<Integer> unexpectedRetainedPredecessorTitleIds,
            List<Integer> expectedOtherHeirTitleIds, List<Integer> expectedWithoutHeirTitleIds,
            List<Integer> observedAdditionalSuccessorTitleIds, boolean titleDistributionMatch, Verdict verdict) {
        public Reconciliation {
            expectedInheritedTitleIds = List.copyOf(expectedInheritedTitleIds); matchedInheritedTitleIds = List.copyOf(matchedInheritedTitleIds);
            missingExpectedInheritedTitleIds = List.copyOf(missingExpectedInheritedTitleIds); unexpectedRetainedPredecessorTitleIds = List.copyOf(unexpectedRetainedPredecessorTitleIds);
            expectedOtherHeirTitleIds = List.copyOf(expectedOtherHeirTitleIds); expectedWithoutHeirTitleIds = List.copyOf(expectedWithoutHeirTitleIds);
            observedAdditionalSuccessorTitleIds = List.copyOf(observedAdditionalSuccessorTitleIds);
        }
    }
    public enum IssueKind { NO_OBSERVED_PRIMARY_TITLE_HEIR, PERSONAL_ESTATE_SPLIT_BETWEEN_OBSERVED_HEIRS,
        OTHER_HEIR_RECEIVES_EQUAL_OR_HIGHER_RANK_TITLE, HELD_TITLES_WITHOUT_OBSERVED_HEIR }
    public record Issue(IssueKind kind, List<Integer> titleIds) { public Issue { titleIds = List.copyOf(titleIds); } }
    public record Estate(int primaryTitleId, Integer primaryTitleHeirCharacterId, RiskState riskState,
            List<TitleRow> titleExpectations, List<Integer> primaryHeirTitles, List<Integer> otherHeirTitles,
            List<Integer> withoutHeirTitles, List<Integer> equalOrHigherOtherHeirTitles, List<Integer> unknownRankOtherHeirTitles) {
        public Estate { titleExpectations = List.copyOf(titleExpectations); primaryHeirTitles = List.copyOf(primaryHeirTitles);
            otherHeirTitles = List.copyOf(otherHeirTitles); withoutHeirTitles = List.copyOf(withoutHeirTitles);
            equalOrHigherOtherHeirTitles = List.copyOf(equalOrHigherOtherHeirTitles); unknownRankOtherHeirTitles = List.copyOf(unknownRankOtherHeirTitles); }
    }
    public record Changes(Binding sourceBinding, List<Integer> addedTitles, List<Integer> removedTitles,
            List<Integer> changedFirstHeirTitles, boolean primaryTitleChanged, boolean primaryTitleHeirChanged) {
        public Changes { addedTitles = List.copyOf(addedTitles); removedTitles = List.copyOf(removedTitles); changedFirstHeirTitles = List.copyOf(changedFirstHeirTitles); }
    }
    public sealed interface OperatingResult permits AvailableOperating, UnavailableOperating { }
    public record AvailableOperating(Binding sourceBinding, Estate estate, List<Issue> issues,
            Changes changes, String previousComparisonUnavailableReason) implements OperatingResult {
        public AvailableOperating { issues = List.copyOf(issues); }
    }
    public record UnavailableOperating(boolean playerDecisionPending, String reason) implements OperatingResult {
        public UnavailableOperating { nonempty(reason); }
    }
    static void character(int value) { NativeCharacterId.of(value); }
    static void nullableCharacter(Integer value) { if (value != null) { character(value); } }
    static void positive(int value) { check(value > 0, "positive int32 required"); }
    static void nullablePositive(Integer value) { if (value != null) { positive(value); } }
    static void nonempty(String value) { check(value != null && !value.isEmpty(), "nonempty string required"); }
    static void uint64(BigInteger value) { check(value != null && value.signum() >= 0 && value.compareTo(UINT64_MAX) <= 0, "uint64 required"); }
    static void check(boolean condition, String reason) { if (!condition) { throw new IllegalArgumentException(reason); } }
}

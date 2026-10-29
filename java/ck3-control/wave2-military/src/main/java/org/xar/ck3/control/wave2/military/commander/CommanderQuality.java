package org.xar.ck3.control.wave2.military.commander;

import java.math.BigInteger;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.Set;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

/** Pure single-Army native-base-quality comparison and existing formal scan. No submission API. */
public final class CommanderQuality {
    public static final String QUERY_CAPABILITY = "game.command.query-army-commander-candidates-v1-for-army-N";
    public static final String ASSIGN_CAPABILITY = "game.command.assign-army-commander-v1-army-N-to-character-N";
    public static final String ASSIGN_PREFIX = "assign-army-commander-v1-army-";
    private CommanderQuality() { }

    public enum Presence { MISSING, NULL, VALUE }
    public record Field<T>(Presence presence, T value) {
        public Field { Objects.requireNonNull(presence); if ((presence == Presence.VALUE) != (value != null)) { throw new IllegalArgumentException("field presence/value mismatch"); } }
        public static <T> Field<T> missing() { return new Field<>(Presence.MISSING, null); }
        public static <T> Field<T> nullValue() { return new Field<>(Presence.NULL, null); }
        public static <T> Field<T> of(T value) { return new Field<>(Presence.VALUE, Objects.requireNonNull(value)); }
    }
    public record NativeId(int value) {
        public NativeId { if (value < 0) { throw new IllegalArgumentException("nonnegative full native int32 ID required"); } }
    }
    public record Frame(String snapshotId, BigInteger revision, BigInteger nativeRevision, BigInteger dateRaw, BigInteger querySequence) {
        public Frame {
            Objects.requireNonNull(snapshotId); Objects.requireNonNull(revision); Objects.requireNonNull(nativeRevision); Objects.requireNonNull(dateRaw); Objects.requireNonNull(querySequence);
            if (snapshotId.isEmpty() || revision.signum() < 0 || nativeRevision.signum() <= 0 || querySequence.signum() <= 0) { throw new ProjectionDomainRejection("invalid commander query frame"); }
        }
    }
    public enum RoleStatus { AVAILABLE, ABSENT, UNAVAILABLE }
    public enum ObservationStatus { AVAILABLE, UNAVAILABLE }
    public record CurrentQuality(ObservationStatus status, NativeId sourceCharacterId, Integer value, String unavailableReason) {
        public CurrentQuality {
            Objects.requireNonNull(status);
            if (status == ObservationStatus.AVAILABLE && (sourceCharacterId == null || value == null || unavailableReason != null)
                    || status == ObservationStatus.UNAVAILABLE && (value != null || unavailableReason == null || unavailableReason.isBlank())) { throw new ProjectionDomainRejection("current native quality status/value mismatch"); }
        }
    }
    public record CurrentRole(RoleStatus status, NativeId characterId, Field<CurrentQuality> quality) {
        public CurrentRole {
            Objects.requireNonNull(status); Objects.requireNonNull(quality);
            if (status == RoleStatus.AVAILABLE && characterId == null || status == RoleStatus.ABSENT && characterId != null) { throw new ProjectionDomainRejection("current role identity/status mismatch"); }
            if (quality.presence() == Presence.VALUE) {
                CurrentQuality q = quality.value();
                if (!Objects.equals(characterId, q.sourceCharacterId()) || q.status() == ObservationStatus.AVAILABLE && status != RoleStatus.AVAILABLE) { throw new ProjectionDomainRejection("current quality is not bound to actual assigned role"); }
            }
        }
        public Integer observedQuality() { return status == RoleStatus.AVAILABLE && quality.presence() == Presence.VALUE && quality.value().status() == ObservationStatus.AVAILABLE ? quality.value().value() : null; }
    }
    public record Candidate(NativeId characterId, boolean available, boolean eligibilityObservable, Boolean canAssign,
                            boolean qualityObservable, Integer nativeQuality, Integer genericAdvantage) {
        public Candidate {
            if (eligibilityObservable != (canAssign != null) || qualityObservable != (nativeQuality != null) || qualityObservable != (genericAdvantage != null)) { throw new ProjectionDomainRejection("candidate independent observation status/value mismatch"); }
        }
        public boolean eligibleAlternative(NativeId currentId) { return available && eligibilityObservable && Boolean.TRUE.equals(canAssign) && qualityObservable && !Objects.equals(characterId, currentId); }
    }
    public record Candidates(NativeId armyId, NativeId nativeArmyId, NativeId ownerCharacterId, CurrentRole current,
                             boolean collectionComplete, BigInteger sourceCount, List<Candidate> candidates) {
        public Candidates { Objects.requireNonNull(armyId); Objects.requireNonNull(current); Objects.requireNonNull(sourceCount); if (sourceCount.signum() < 0) { throw new IllegalArgumentException("negative source count"); } candidates = List.copyOf(candidates); }
    }
    public enum ProposalStatus {
        KEEP_CURRENT("keep_current"), CURRENT_QUALITY_UNAVAILABLE("current_quality_unavailable"), NO_ELIGIBLE_CANDIDATE("no_eligible_candidate"),
        ASSIGN_EMPTY_ROLE("assign_candidate_for_empty_role"), ASSIGN_BETTER("assign_better_candidate");
        private final String wire;
        ProposalStatus(String wire) { this.wire = wire; }
        public String wire() { return wire; }
    }
    public record Proposal(ProposalStatus status, Candidates context, Frame frame, Integer currentQuality, Candidate bestCandidate,
                           Long qualityGain, NativeId proposedCharacterId, String selectedStep, String unavailableReason) {
        public Proposal { Objects.requireNonNull(status); Objects.requireNonNull(context); Objects.requireNonNull(frame); }
    }

    /** First row wins equal scores; assignment eligibility does not erase the current role. */
    public static Proposal propose(Candidates input, Frame frame) {
        Candidate best = null;
        for (Candidate row : input.candidates()) {
            if (row.eligibleAlternative(input.current().characterId()) && (best == null || row.nativeQuality() > best.nativeQuality())) { best = row; }
        }
        Integer current = input.current().observedQuality();
        ProposalStatus status = ProposalStatus.KEEP_CURRENT; Long gain = null; String reason = null;
        if (input.current().status() != RoleStatus.ABSENT && current == null) {
            status = ProposalStatus.CURRENT_QUALITY_UNAVAILABLE; reason = "current_native_ai_base_quality_unavailable";
        } else if (best == null) {
            if (input.current().status() == RoleStatus.ABSENT) { status = ProposalStatus.NO_ELIGIBLE_CANDIDATE; reason = "no_available_can_assign_candidate"; }
        } else if (input.current().status() == RoleStatus.ABSENT) { status = ProposalStatus.ASSIGN_EMPTY_ROLE;
        } else {
            gain = (long) best.nativeQuality() - current;
            if (gain > 0) { status = ProposalStatus.ASSIGN_BETTER; }
        }
        boolean action = status == ProposalStatus.ASSIGN_EMPTY_ROLE || status == ProposalStatus.ASSIGN_BETTER;
        NativeId proposed = action ? Objects.requireNonNull(best).characterId() : null;
        // The old canonical step constructor rejects an actionable null identity.
        String step = action ? assignmentStep(input.armyId(), Objects.requireNonNull(proposed, "actionable candidate lacks character identity")) : null;
        return new Proposal(status, input, frame, current, best, gain, proposed, step, reason);
    }
    public static String assignmentStep(NativeId army, NativeId character) { return ASSIGN_PREFIX + army.value() + "-to-character-" + character.value(); }

    public record Army(NativeId id, boolean controllable) { public Army { Objects.requireNonNull(id); } }
    public record PlanContext(boolean planPresent, String phase, Field<String> selectedStep, Field<NativeId> pursuitArmy,
                              BigInteger publicRevision, List<Army> armies, Set<String> capabilities) {
        public PlanContext { Objects.requireNonNull(selectedStep); Objects.requireNonNull(pursuitArmy); armies = List.copyOf(armies); capabilities = Set.copyOf(capabilities); }
    }
    public sealed interface QueryOutcome permits Queried, InputUnavailable { }
    public record Queried(Proposal proposal) implements QueryOutcome { public Queried { Objects.requireNonNull(proposal); } }
    public record InputUnavailable(String reason) implements QueryOutcome { public InputUnavailable { Objects.requireNonNull(reason); } }
    @FunctionalInterface public interface QueryPort { QueryOutcome query(NativeId armyId, BigInteger expectedPublicRevision); }
    public record UnavailableInput(NativeId armyId, String reason) { public UnavailableInput { Objects.requireNonNull(armyId); Objects.requireNonNull(reason); } }
    public record Selection(QueryOutcome outcome, List<UnavailableInput> unavailableInputs) {
        public Selection { Objects.requireNonNull(outcome); unavailableInputs = List.copyOf(unavailableInputs); }
        public String selectedStep() { return outcome instanceof Queried queried ? queried.proposal().selectedStep() : null; }
    }
    public record Decision(Selection selection) { public boolean actionable() { return selection != null && selection.selectedStep() != null; } }

    /** Actual consumer scan order, admitted phases and first-action semantics; only calls the supplied read port. */
    public static Decision plan(PlanContext input, QueryPort port) {
        Objects.requireNonNull(port);
        if (!input.planPresent() || input.phase() == null || !Set.of("native_war_reconnaissance", "native_war_pursuit", "native_war_pursuit_progress", "native_war_counterpolicy_hold").contains(input.phase())) { return new Decision(null); }
        String baseline = input.selectedStep().value();
        if ("native_war_counterpolicy_hold".equals(input.phase()) ? baseline != null : !"native_war_pursuit".equals(input.phase()) && !"life-advance".equals(baseline)) { return new Decision(null); }
        if (!input.capabilities().containsAll(Set.of(QUERY_CAPABILITY, ASSIGN_CAPABILITY))) { return new Decision(null); }
        boolean ordinaryScan = input.pursuitArmy().presence() == Presence.MISSING;
        List<NativeId> ids = ordinaryScan ? input.armies().stream().filter(Army::controllable).map(Army::id).toList()
                : input.pursuitArmy().presence() == Presence.VALUE ? List.of(input.pursuitArmy().value()) : List.of();
        Selection selection = null; List<UnavailableInput> unavailable = new ArrayList<>();
        for (NativeId armyId : ids) {
            QueryOutcome outcome = Objects.requireNonNull(port.query(armyId, Objects.requireNonNull(input.publicRevision(), "planned revision missing")));
            if (outcome instanceof InputUnavailable failed) {
                if (!ordinaryScan) { return new Decision(new Selection(failed, List.of())); }
                unavailable.add(new UnavailableInput(armyId, failed.reason()));
                if (selection == null) { selection = new Selection(failed, List.of()); }
                continue;
            }
            selection = new Selection(outcome, List.of());
            if (selection.selectedStep() != null) { return new Decision(new Selection(outcome, unavailable)); }
        }
        return new Decision(selection == null ? null : new Selection(selection.outcome(), unavailable));
    }
}

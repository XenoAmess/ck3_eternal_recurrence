package org.xar.ck3.control.planning.optionalcadence;

import java.math.BigInteger;
import java.util.Objects;
import java.util.Optional;
import org.xar.ck3.control.contracts.projection.ProjectionDomainRejection;

import static org.xar.ck3.control.planning.optionalcadence.CadenceModels.*;

/** Pure transitions only. The existing single writer retains file publication authority. */
public final class OptionalCheckCadence {
    private OptionalCheckCadence() { }

    public static State forEpisode(State state, String episodeRunId) {
        Objects.requireNonNull(state, "state");
        nonempty(episodeRunId, "episode_run_id");
        return state.episodeRunId().equals(episodeRunId) ? state : State.empty(episodeRunId);
    }

    public static Optional<Deferred> deferred(State state, Domain domain, Frame current) {
        Objects.requireNonNull(current, "current");
        Row row = forEpisode(state, current.episodeRunId()).row(domain);
        if (row.nextDueDateRaw().isEmpty()
                || current.dateRaw().compareTo(row.nextDueDateRaw().orElseThrow()) >= 0) {
            return Optional.empty();
        }
        BigInteger due = row.nextDueDateRaw().orElseThrow();
        BigInteger remaining = due.subtract(current.dateRaw()).add(RAW_PER_DAY.subtract(BigInteger.ONE))
                .divide(RAW_PER_DAY);
        return Optional.of(new Deferred(
                row.technicalDefer().isPresent() ? DeferStatus.TECHNICAL_READ_UNAVAILABLE : DeferStatus.COOLDOWN,
                row.technicalDefer().isPresent() ? row.consecutiveNoAction() : 0,
                due, row.technicalDefer(), remaining));
    }

    public static ReviewGate gate(State state, Domain domain, Optional<Frame> current, PendingState pending) {
        Objects.requireNonNull(current, "current");
        Objects.requireNonNull(pending, "pending");
        if (pending == PendingState.PENDING) { return new CheckRequired(CheckReason.PENDING_RECEIPT); }
        if (pending == PendingState.UNKNOWN) { return new CheckRequired(CheckReason.UNKNOWN_RECEIPT); }
        if (current.isEmpty()) { return new CheckRequired(CheckReason.FRAME_UNAVAILABLE); }
        return deferred(state, domain, current.orElseThrow()).<ReviewGate>map(CheckDeferred::new)
                .orElseGet(() -> new CheckRequired(CheckReason.DUE));
    }

    public static boolean actionRecorded(State state, Domain domain, Frame current) {
        Objects.requireNonNull(current, "current");
        return forEpisode(state, current.episodeRunId()).row(domain).lastActualActionFrame()
                .filter(current.marker()::equals).isPresent();
    }

    /** Mirrors the completed-read observer guard; incomplete/unknown reads never earn a no-op. */
    public static State observeRead(State state, Domain domain, Frame current, ReadCompletion completion) {
        Objects.requireNonNull(completion, "completion");
        State selected = forEpisode(state, current.episodeRunId());
        if (completion == ReadCompletion.INCOMPLETE_OR_UNKNOWN || actionRecorded(selected, domain, current)) {
            return selected;
        }
        return record(selected, domain, current, false);
    }

    /** Call only for an actual action or a completed no-action check; UNKNOWN is neither. */
    public static State record(State state, Domain domain, Frame current, boolean actualAction) {
        Objects.requireNonNull(current, "current");
        State selected = forEpisode(state, current.episodeRunId());
        Row row = selected.row(domain);
        if (actualAction) {
            if (row.lastActualActionFrame().filter(current.marker()::equals).isPresent()) { return selected; }
            return selected.with(domain, new Row(0, Optional.empty(), row.lastCheckFrame(),
                    Optional.of(current.marker()), row.nativeCatalogue(), Optional.empty()));
        }
        if (row.lastCheckFrame().filter(current.marker()::equals).isPresent()) { return selected; }
        if (row.nextDueDateRaw().filter(due -> current.dateRaw().compareTo(due) < 0).isPresent()) {
            throw new ProjectionDomainRejection("optional check recorded inside its cooldown");
        }
        int misses = row.consecutiveNoAction() + 1;
        return selected.with(domain, new Row(misses == 3 ? 0 : misses,
                misses == 3 ? Optional.of(current.dateRaw().add(COOLDOWN_RAW)) : Optional.empty(),
                Optional.of(current.marker()), row.lastActualActionFrame(), row.nativeCatalogue(), Optional.empty()));
    }

    /** The caller must first qualify an advertised native capability; this grants no action credit. */
    public static Requalification requalifyLifestyleFrontierOnce(State state, Frame current, String catalogue) {
        nonempty(catalogue, "native_catalogue");
        Objects.requireNonNull(current, "current");
        State selected = forEpisode(state, current.episodeRunId());
        Row row = selected.row(Domain.LIFESTYLE);
        if (row.nativeCatalogue().filter(catalogue::equals).isPresent()) {
            return new Requalification(selected, false);
        }
        return new Requalification(selected.with(Domain.LIFESTYLE,
                new Row(0, Optional.empty(), Optional.empty(), row.lastActualActionFrame(),
                        Optional.of(catalogue), Optional.empty())), true);
    }

    /** Caller must retain same-frame read-only diagnostics and establish that no action is pending. */
    public static State deferCouncilTechnicalRead(State state, Frame current, String evidencePath) {
        nonempty(evidencePath, "evidence_path");
        Objects.requireNonNull(current, "current");
        State selected = forEpisode(state, current.episodeRunId());
        Row row = selected.row(Domain.COUNCIL);
        if (row.technicalDefer().filter(previous -> previous.frame().equals(current.marker())).isPresent()
                && row.nextDueDateRaw().filter(due -> due.compareTo(current.dateRaw()) > 0).isPresent()) {
            return selected;
        }
        BigInteger due = current.dateRaw().add(COOLDOWN_RAW)
                .max(row.nextDueDateRaw().orElse(current.dateRaw()));
        return selected.with(Domain.COUNCIL, new Row(row.consecutiveNoAction(), Optional.of(due),
                Optional.of(current.marker()), row.lastActualActionFrame(), row.nativeCatalogue(),
                Optional.of(new TechnicalDefer(current.marker(), evidencePath))));
    }
}
